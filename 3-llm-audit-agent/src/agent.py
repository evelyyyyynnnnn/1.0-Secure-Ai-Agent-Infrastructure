"""The staged auditing agent.

Four stages, each one a separate backend call with its own prompt and its own
parsed reply:

    understand -> plan -> classify -> verify

Every stage is recorded in an audit trail. That is not incidental: an auditing
tool whose own reasoning cannot be inspected is not usable for the thing it is
meant to support, and the trail is what makes a disagreement with a human
auditor resolvable rather than a matter of trust.

The sandbox is read-only by construction -- the agent is given contract source
as text and has no execution, filesystem or network capability. Nothing it
produces can act on a chain.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict

from .backends import Backend, StubBackend, Message
from . import trail as _trail
from .sanitize import strip_comments

STAGES = ("understand", "plan", "classify", "verify")


@dataclass
class Finding:
    cls: str
    fn: str
    evidence: str
    confirmed: bool = True
    dropped_reason: str = ""


@dataclass
class AuditResult:
    contract_id: str
    findings: list = field(default_factory=list)
    dropped: list = field(default_factory=list)
    trail: list = field(default_factory=list)
    chain: list = field(default_factory=list)
    malformed: int = 0
    elapsed_ms: float = 0.0
    backend: str = ""

    def classes(self) -> set:
        return {f.cls for f in self.findings}

    def as_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "backend": self.backend,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "findings": [asdict(f) for f in self.findings],
            "dropped": [asdict(f) for f in self.dropped],
            "trail": [
                {"stage": m.stage, "backend": m.backend,
                 "latency_ms": round(m.latency_ms, 2),
                 "reply_bytes": len(m.reply)}
                for m in self.trail
            ],
            "malformed_items": self.malformed,
            "trail_chain": self.chain,
            "chain_intact": self.verify_chain()[0],
        }

    def verify_chain(self) -> tuple[bool, int]:
        """(intact, first_broken_index) over the hash-chained stage trail."""
        return _trail.verify_against(self.chain, [m.reply for m in self.trail])


class AuditAgent:
    """Runs the four-stage pipeline over one contract."""

    def __init__(self, backend: Backend | None = None, self_correct: bool = True,
                 keep_prompts: bool = False):
        self.backend = backend or StubBackend()
        self.self_correct = self_correct
        self.keep_prompts = keep_prompts

    def audit(self, source: str, contract_id: str = "anon") -> AuditResult:
        t0 = time.perf_counter()
        result = AuditResult(contract_id=contract_id, backend=self.backend.name)
        ctx: dict = {}

        for stage in STAGES:
            if stage == "verify" and not self.self_correct:
                continue
            prompt = self._prompt(stage, source, ctx)
            s0 = time.perf_counter()
            reply = self.backend.complete(
                stage, prompt, source=source, context=json.dumps(ctx)
            )
            latency = (time.perf_counter() - s0) * 1000
            prev = result.chain[-1]["hash"] if result.chain else _trail.GENESIS
            result.chain.append(_trail.make_record(
                len(result.chain), stage, self.backend.name, prompt, reply,
                latency, prev))
            result.trail.append(Message(
                stage=stage,
                prompt=prompt if self.keep_prompts else f"<{len(prompt)} bytes>",
                reply=reply, backend=self.backend.name, latency_ms=latency,
            ))
            parsed = _safe_json(reply)
            ctx.update(parsed)

        findings = ctx.get("kept", ctx.get("findings", []))
        # A model may return malformed items (bare strings, nulls). Keep only
        # well-formed findings and count the rest, rather than crash the audit.
        findings = findings if isinstance(findings, list) else []
        result.malformed = sum(1 for f in findings if not isinstance(f, dict))
        findings = [f for f in findings if isinstance(f, dict)]
        dropped_raw = ctx.get("dropped", [])
        dropped_raw = dropped_raw if isinstance(dropped_raw, list) else []
        result.malformed += sum(1 for f in dropped_raw if not isinstance(f, dict))
        result.findings = [
            Finding(cls=f.get("cls", ""), fn=f.get("fn", ""),
                    evidence=f.get("evidence", ""))
            for f in findings if f.get("cls")
        ]
        result.dropped = [
            Finding(cls=f.get("cls", ""), fn=f.get("fn", ""),
                    evidence=f.get("evidence", ""), confirmed=False,
                    dropped_reason=f.get("reason", ""))
            for f in dropped_raw if isinstance(f, dict)
        ]
        result.elapsed_ms = (time.perf_counter() - t0) * 1000
        return result

    def _prompt(self, stage: str, source: str, ctx: dict) -> str:
        if stage == "understand":
            return f"Contract source:\n\n{source}\n\nDescribe its structure as JSON."
        if stage == "plan":
            raw = ctx.get("functions", [])
            raw = raw if isinstance(raw, list) else []
            # A model may list functions as names or as objects; accept both.
            fns = [f.get("name", "") if isinstance(f, dict) else str(f) for f in raw]
            return (f"Functions: {fns}\nDeclared modifiers: "
                    f"{ctx.get('declared_modifiers', [])}\n"
                    "Which exploit paths are worth checking?")
        if stage == "classify":
            return (f"Contract source:\n\n{source}\n\n"
                    f"Planned paths: {json.dumps(ctx.get('paths', []))}\n"
                    "Classify the confirmed vulnerabilities.")
        return (f"Contract source:\n\n{source}\n\n"
                f"Proposed findings: {json.dumps(ctx.get('findings', []))}\n"
                "Drop any that are not real and say why.")


class DetectorAdapter:
    """Wraps the agent in the benchmark's detector contract.

    This is what lets the agent be scored by ChainTrust-Bench with no special
    casing: the benchmark asks for `(source) -> set[str]` and gets exactly that.

    Comments are stripped before the agent sees the source, by default.
    SmartBugs sources carry their ground-truth labels in comments
    (``// <yes> <report> ...``), and a language model reads comments, so
    scoring on raw source leaks the answer into the prompt (see
    2-chaintrust-bench/docs/DATA.md). The rule-based detectors strip comments
    themselves; this puts the agent on the same footing. Pass
    ``strip_comments_first=False`` only to measure the leakage on purpose.
    """

    def __init__(self, agent: AuditAgent | None = None, name: str | None = None,
                 strip_comments_first: bool = True):
        self.agent = agent or AuditAgent()
        self.strip_comments_first = strip_comments_first
        self.name = name or f"llm-audit-agent[{self.agent.backend.name}]"

    def __call__(self, source: str) -> set:
        if self.strip_comments_first:
            source = strip_comments(source)
        return self.agent.audit(source).classes()


def _safe_json(text: str) -> dict:
    try:
        out = json.loads(text)
        return out if isinstance(out, dict) else {}
    except (json.JSONDecodeError, TypeError):
        # A language model can return prose around its JSON; recover the object.
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                out = json.loads(text[start:end + 1])
                return out if isinstance(out, dict) else {}
            except json.JSONDecodeError:
                pass
        return {}

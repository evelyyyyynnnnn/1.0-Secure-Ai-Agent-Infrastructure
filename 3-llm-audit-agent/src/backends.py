"""Pluggable reasoning backends.

The agent's pipeline is backend-agnostic: every stage sends a structured prompt
and parses a structured reply. That separation is the point of this module --
it lets the same staged pipeline, sandbox and audit trail be driven by a hosted
LLM, a local model, or the deterministic stub below.

`StubBackend` exists so the repository is runnable and testable with no API key
and no network. It is a small symbolic reasoner, NOT a language model, and it is
not a stand-in for one: its scores are a floor for the pipeline's plumbing, not
evidence about what an LLM would achieve. Any claim about LLM audit performance
has to come from a run against a real backend, recorded in results/.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Message:
    stage: str
    prompt: str
    reply: str
    backend: str
    latency_ms: float = 0.0
    meta: dict = field(default_factory=dict)


class Backend(Protocol):
    name: str
    is_language_model: bool

    def complete(self, stage: str, prompt: str, **kw) -> str: ...


class StubBackend:
    """Deterministic symbolic reasoner. No network, no model, no API key.

    It resolves internal calls and modifier application -- the two things plain
    pattern matching cannot do -- so the pipeline can be exercised end to end.
    It does not attempt semantic reasoning, and it will not close the hard cases
    that need it.
    """

    name = "stub-symbolic"
    is_language_model = False

    def complete(self, stage: str, prompt: str, **kw) -> str:
        source = kw.get("source", "")
        if stage == "understand":
            return json.dumps(self._understand(source))
        if stage == "plan":
            return json.dumps(self._plan(json.loads(kw.get("context", "{}"))))
        if stage == "classify":
            return json.dumps(self._classify(source, json.loads(kw.get("context", "{}"))))
        if stage == "verify":
            return json.dumps(self._verify(source, json.loads(kw.get("context", "{}"))))
        return "{}"

    # -- stage 1: build a structural model of the contract -------------------
    def _understand(self, src: str) -> dict:
        fns = []
        for m in re.finditer(r"function\s+(\w+)\s*\(([^)]*)\)\s*([^{;]*)\{", src):
            name, mods = m.group(1), m.group(3)
            body = _body(src, m.end() - 1)
            fns.append({
                "name": name,
                "modifiers": re.findall(r"\b(only\w+)\b", mods),
                "visibility": _first_of(mods, ("external", "public", "internal", "private")),
                "is_view": "view" in mods or "pure" in mods,
                "external_calls": re.findall(r"(\w+)\.(call|send|transfer|delegatecall)", body),
                "state_writes": re.findall(r"\b(\w+)\s*(?:\[[^\]]*\])?\s*=(?!=)", body),
                "internal_calls": re.findall(r"(?<![\w.])_(\w+)\s*\(", body),
                "reads_timestamp": bool(re.search(r"block\.(timestamp|number)", body)),
                "body": body,
            })
        return {
            "functions": fns,
            "declared_modifiers": re.findall(r"modifier\s+(\w+)", src),
            "pragma": (re.search(r"pragma\s+solidity\s*[\^>=~]*\s*([\d.]+)", src) or [None, ""])[1]
            if re.search(r"pragma", src) else "",
            "state_vars": re.findall(r"\n\s*(?:address|uint\d*|bool|mapping)[^;=\n]*?(\w+)\s*;", src),
        }

    # -- stage 2: decide which exploit paths are worth checking --------------
    def _plan(self, ctx: dict) -> dict:
        paths = []
        for fn in ctx.get("functions", []):
            if fn["external_calls"]:
                paths.append({"fn": fn["name"], "check": "reentrancy",
                              "why": "function makes an external call"})
                paths.append({"fn": fn["name"], "check": "unchecked_call",
                              "why": "external call result may be discarded"})
            if fn["internal_calls"]:
                paths.append({"fn": fn["name"], "check": "reentrancy_via_internal",
                              "why": f"delegates to {fn['internal_calls']}"})
            if fn["state_writes"] and not fn["is_view"]:
                paths.append({"fn": fn["name"], "check": "missing_access_control",
                              "why": "writes state"})
            if fn["reads_timestamp"]:
                paths.append({"fn": fn["name"], "check": "timestamp_dependence",
                              "why": "reads block time"})
        return {"paths": paths}

    # -- stage 3: classify each planned path --------------------------------
    def _classify(self, src: str, ctx: dict) -> dict:
        fns = {f["name"]: f for f in ctx.get("functions", [])}
        declared = set(ctx.get("declared_modifiers", []))
        findings = []

        def guarded(fn) -> bool:
            if any(m in declared for m in fn["modifiers"]):
                return True
            return bool(re.search(r"require\s*\(\s*msg\.sender\s*==", fn["body"]))

        for fn in fns.values():
            # inline external call followed by a state write
            for m in re.finditer(r"\.call\{[^}]*value[^}]*\}\s*\(", fn["body"]):
                after = fn["body"][m.end():]
                if re.search(r"\b\w+\s*(\[[^\]]*\])?\s*=(?!=)", after):
                    findings.append({"cls": "reentrancy", "fn": fn["name"],
                                     "evidence": "state write after value call"})
                    break
            # cross-function: the call lives in an internal helper
            for callee in fn["internal_calls"]:
                target = fns.get("_" + callee) or fns.get(callee)
                if target and target["external_calls"]:
                    idx = fn["body"].find("_" + callee)
                    if idx >= 0 and re.search(
                        r"\b\w+\s*(\[[^\]]*\])?\s*=(?!=)", fn["body"][idx:]
                    ):
                        findings.append({
                            "cls": "reentrancy", "fn": fn["name"],
                            "evidence": f"state write after internal call _{callee}(), "
                                        f"which makes an external call"})
            # unchecked low-level call
            for m in re.finditer(r"(?<![\w.])([\w.\[\]]+)\.(send|call)\s*[\({]", fn["body"]):
                ls = fn["body"].rfind("\n", 0, m.start()) + 1
                prefix = fn["body"][ls:m.start()].strip()
                if not re.search(r"(=|require\s*\(|assert\s*\(|if\s*\()\s*$", prefix) \
                        and not re.match(r"^\(?\s*bool", prefix):
                    findings.append({"cls": "unchecked_call", "fn": fn["name"],
                                     "evidence": "return value discarded"})
                    break
            # access control on privileged writes
            privileged = [w for w in fn["state_writes"]
                          if w in ("owner", "admin", "arbiter", "implementation")]
            sweeps = "address(this).balance" in fn["body"]
            if (privileged or sweeps) and not fn["is_view"] and not guarded(fn):
                findings.append({
                    "cls": "missing_access_control", "fn": fn["name"],
                    "evidence": f"unguarded write to {privileged or ['balance sweep']}"
                                + (f"; modifier {sorted(declared)} declared but not applied"
                                   if declared else "")})
            # tx.origin
            if re.search(r"tx\.origin\s*==|==\s*tx\.origin", fn["body"]):
                findings.append({"cls": "tx_origin_auth", "fn": fn["name"],
                                 "evidence": "tx.origin used for authorisation"})
            # selfdestruct
            if "selfdestruct" in fn["body"] and not guarded(fn):
                findings.append({"cls": "unprotected_selfdestruct", "fn": fn["name"],
                                 "evidence": "selfdestruct reachable by any caller"})
        return {"findings": findings}

    # -- stage 4: self-correction -------------------------------------------
    def _verify(self, src: str, ctx: dict) -> dict:
        kept, dropped = [], []
        for f in ctx.get("findings", []):
            if f["cls"] == "reentrancy":
                # drop it if the contract uses a reentrancy guard or CEI order
                if re.search(r"nonReentrant|ReentrancyGuard", src):
                    dropped.append({**f, "reason": "guarded by nonReentrant"})
                    continue
            if f["cls"] == "missing_access_control":
                fn_src = _fn_body_by_name(src, f["fn"])
                if fn_src and re.search(r"require\s*\(\s*msg\.sender\s*==", fn_src):
                    dropped.append({**f, "reason": "sender check present in body"})
                    continue
            kept.append(f)
        return {"kept": kept, "dropped": dropped}


class OpenAICompatibleBackend:
    """Adapter for any OpenAI-compatible chat endpoint.

    Not exercised in CI: it needs a key and a network, and a benchmark run whose
    numbers depend on an unpinned hosted model is not reproducible. Use it to
    produce a dated, recorded run in results/, and cite that run -- not this
    class's existence.
    """

    name = "openai-compatible"
    is_language_model = True

    def __init__(self, model: str = "gpt-4o-mini", base_url: str | None = None,
                 api_key_env: str = "OPENAI_API_KEY"):
        self.model = model
        self.base_url = base_url or os.environ.get(
            "OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = os.environ.get(api_key_env)
        self.name = f"openai:{model}"

    def complete(self, stage: str, prompt: str, **kw) -> str:  # pragma: no cover
        if not self.api_key:
            raise RuntimeError(
                f"no API key in the environment; set the key or use StubBackend")
        import urllib.request
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS.get(stage, "")},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read())
        return payload["choices"][0]["message"]["content"]


SYSTEM_PROMPTS = {
    "understand": "You are a Solidity static-analysis assistant. Given a contract, "
                  "return JSON describing its functions, modifiers, external calls, "
                  "state writes and internal calls. Return JSON only.",
    "plan": "Given a structural summary of a Solidity contract, list the exploit paths "
            "worth checking and why. Return JSON with a `paths` array.",
    "classify": "Given a Solidity contract and a list of exploit paths, classify each "
                "confirmed vulnerability. Use only these classes: reentrancy, "
                "unchecked_call, tx_origin_auth, timestamp_dependence, "
                "missing_access_control, unprotected_selfdestruct, integer_overflow. "
                "Return JSON with a `findings` array; each finding has cls, fn, evidence.",
    "verify": "Review the proposed findings against the contract and drop any that are "
              "not real, giving a reason. Return JSON with `kept` and `dropped` arrays.",
}


def _body(src: str, brace_idx: int) -> str:
    depth = 0
    for i in range(brace_idx, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[brace_idx + 1:i]
    return src[brace_idx + 1:]


def _fn_body_by_name(src: str, name: str) -> str | None:
    m = re.search(r"function\s+" + re.escape(name) + r"\s*\([^)]*\)\s*[^{;]*\{", src)
    return _body(src, m.end() - 1) if m else None


def _first_of(text: str, options) -> str:
    for o in options:
        if o in text:
            return o
    return ""

"""Tamper-evident tool-call audit logging.

Each record is chained to the previous one by hash, so a log cannot be edited
after the fact without breaking the chain. That property is what makes the log
usable as evidence about what an agent did, as opposed to a debug print.

This is deliberately not cryptographic signing -- there is no key management
here and it does not prove who wrote the log, only that it has not been altered
since it was written.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict

GENESIS = "0" * 64


def _digest(prev: str, payload: dict) -> str:
    blob = prev + json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


@dataclass
class ToolCall:
    seq: int
    tool: str
    args: dict
    result_summary: str
    ok: bool
    duration_ms: float
    ts: float = field(default_factory=time.time)
    prev_hash: str = GENESIS
    hash: str = ""

    def payload(self) -> dict:
        return {"seq": self.seq, "tool": self.tool, "args": self.args,
                "result_summary": self.result_summary, "ok": self.ok,
                "duration_ms": round(self.duration_ms, 3), "ts": round(self.ts, 6)}


class ToolAuditLog:
    def __init__(self):
        self.records: list = []

    def record(self, tool: str, args: dict, result_summary: str,
               ok: bool = True, duration_ms: float = 0.0) -> ToolCall:
        prev = self.records[-1].hash if self.records else GENESIS
        rec = ToolCall(seq=len(self.records), tool=tool, args=args,
                       result_summary=result_summary, ok=ok,
                       duration_ms=duration_ms, prev_hash=prev)
        rec.hash = _digest(prev, rec.payload())
        self.records.append(rec)
        return rec

    def verify(self) -> tuple[bool, int]:
        """Return (intact, first_broken_index). -1 when intact."""
        prev = GENESIS
        for i, r in enumerate(self.records):
            if r.prev_hash != prev or r.hash != _digest(prev, r.payload()):
                return False, i
            prev = r.hash
        return True, -1

    def stats(self) -> dict:
        by_tool: dict = {}
        for r in self.records:
            b = by_tool.setdefault(r.tool, {"calls": 0, "failures": 0, "ms": 0.0})
            b["calls"] += 1
            b["failures"] += 0 if r.ok else 1
            b["ms"] += r.duration_ms
        intact, broken_at = self.verify()
        return {
            "n_calls": len(self.records),
            "n_failures": sum(1 for r in self.records if not r.ok),
            "chain_intact": intact,
            "first_broken_index": broken_at,
            "by_tool": {k: {**v, "ms": round(v["ms"], 2)} for k, v in by_tool.items()},
        }

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(asdict(r), sort_keys=True) for r in self.records)


def instrument(log: ToolAuditLog, tool_name: str, fn):
    """Wrap a tool callable so every invocation lands in the log."""
    def wrapped(**kwargs):
        t0 = time.perf_counter()
        ok = True
        try:
            out = fn(**kwargs)
            return out
        except Exception as exc:
            ok = False
            out = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            log.record(tool_name, kwargs, str(out)[:160], ok,
                       (time.perf_counter() - t0) * 1000)
    return wrapped

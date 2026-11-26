"""Tamper-evident chaining for the agent's stage trail.

Each stage of an audit (understand, plan, classify, verify) becomes one record.
A record stores SHA-256 digests of the exact prompt sent and the exact reply
received, and is chained to the previous record by hash, so editing any stage
after the fact -- its prompt, its reply, its order -- breaks the chain at that
stage.

Same construction as ``1-agent-verification-harness/src/toollog.py``: a hash
chain, not a signature. It shows the trail has not been altered since it was
written; it does not show who wrote it.
"""

from __future__ import annotations

import hashlib
import json

GENESIS = "0" * 64


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _digest(prev: str, payload: dict) -> str:
    blob = prev + json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def make_record(seq: int, stage: str, backend: str, prompt: str, reply: str,
                latency_ms: float, prev_hash: str) -> dict:
    payload = {
        "seq": seq,
        "stage": stage,
        "backend": backend,
        "prompt_sha256": sha256(prompt),
        "reply_sha256": sha256(reply),
        "latency_ms": round(latency_ms, 3),
    }
    return {**payload, "prev_hash": prev_hash, "hash": _digest(prev_hash, payload)}


def verify(records: list) -> tuple[bool, int]:
    """Return (intact, first_broken_index); index is -1 when intact."""
    prev = GENESIS
    for i, r in enumerate(records):
        payload = {k: r[k] for k in ("seq", "stage", "backend", "prompt_sha256",
                                     "reply_sha256", "latency_ms")}
        if r.get("prev_hash") != prev or r.get("hash") != _digest(prev, payload):
            return False, i
        prev = r["hash"]
    return True, -1


def verify_against(records: list, replies: list) -> tuple[bool, int]:
    """Check the chain and that each stored reply still matches its digest."""
    ok, idx = verify(records)
    if not ok:
        return ok, idx
    for i, (r, reply) in enumerate(zip(records, replies)):
        if r["reply_sha256"] != sha256(reply):
            return False, i
    return True, -1

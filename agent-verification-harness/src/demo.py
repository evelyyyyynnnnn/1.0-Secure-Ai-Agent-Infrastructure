"""Run the harness over the labelled transcripts and rebuild the site."""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

from .harness import score_harness, threshold_sweep
from .transcripts import TRANSCRIPTS
from .toollog import ToolAuditLog, instrument

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _tool_demo() -> dict:
    """Exercise the audit log, including a tamper check."""
    log = ToolAuditLog()

    def search(query: str) -> str:
        return f"3 results for {query!r}"

    def fetch(url: str) -> str:
        if "bad" in url:
            raise ConnectionError("host unreachable")
        return f"200 OK from {url}"

    s = instrument(log, "search", search)
    f = instrument(log, "fetch", fetch)
    s(query="fomc january rate decision")
    f(url="https://example.org/fomc")
    try:
        f(url="https://bad.example.org/x")
    except ConnectionError:
        pass
    s(query="cpi january")

    before = log.stats()
    # Tamper with a record and show the chain catches it.
    log.records[1].args = {"url": "https://evil.example.org"}
    after_intact, broken_at = log.verify()
    log.records[1].args = {"url": "https://example.org/fomc"}   # restore
    restored, _ = log.verify()
    return {
        "stats": before,
        "tamper_detected": not after_intact,
        "tamper_index": broken_at,
        "restored_intact": restored,
        "sample_jsonl_lines": len(log.to_jsonl().splitlines()),
    }


def run() -> dict:
    scored = score_harness(list(TRANSCRIPTS))
    sweep = threshold_sweep(list(TRANSCRIPTS))
    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "is_synthetic": True,
        "data_source": "6 authored transcripts, 12 labelled claims",
        "grounding": scored,
        "sweep": sweep,
        "tool_audit": _tool_demo(),
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "latest.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf8")
    return results


def main() -> int:
    r = run()
    g = r["grounding"]
    print(f"claims: {g['n_claims']}  "
          f"precision={g['precision']:.3f} recall={g['recall']:.3f} f1={g['f1']:.3f}")
    for kind, v in g["per_kind"].items():
        if kind == "ok":
            print(f"  grounded claims: {v['total']}, false flags {v['false_flags']}")
        else:
            print(f"  {kind}: caught {v['caught']}/{v['total']}")
    print("\nthreshold sweep:")
    for row in r["sweep"]:
        print(f"  {row['threshold']:.2f}  P={row['precision']:.2f} "
              f"R={row['recall']:.2f} F1={row['f1']:.2f}")
    t = r["tool_audit"]
    print(f"\ntool log: {t['stats']['n_calls']} calls, "
          f"{t['stats']['n_failures']} failure(s), chain intact "
          f"{t['stats']['chain_intact']}")
    print(f"tamper detected at index {t['tamper_index']}: {t['tamper_detected']}")

    try:
        from .site import build_site
        build_site(r)
        print("\nwebsite/ rebuilt from this run")
    except Exception as exc:  # pragma: no cover
        print(f"\n(site not rebuilt: {exc})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

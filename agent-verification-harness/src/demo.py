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


def run_real() -> dict:
    """Score the grounding checker against real government releases.

    Same scorer, same threshold sweep, harder documents. A real CPI release
    runs to thousands of words and dozens of numbers, most of them irrelevant
    to any given claim, which is precisely the condition a shingle-overlap
    check can be fooled by and a three-sentence authored source never tests.
    """
    import sys as _sys
    _sys.path.insert(0, str(ROOT))
    from data.load import build_transcripts

    transcripts, meta = build_transcripts(root=ROOT / "data")
    scored = score_harness(transcripts)
    sweep = threshold_sweep(transcripts)

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "is_synthetic": False,
        "data_source": "real US government releases (BLS, Federal Reserve); see "
                       "data/MANIFEST.json for URLs, hashes and retrieval times",
        "claims_are_model_output": meta["claims_are_model_output"],
        "label_construction":
            "supported claims are quoted from the cited document; fabricated "
            "claims are the same sentences with one number altered; unsupported "
            "claims are sentences taken from a different real release and cited "
            "to this one. Every label is known by construction.",
        "documents": meta["documents"],
        "n_transcripts": meta["n_transcripts"],
        "grounding": scored,
        "sweep": sweep,
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "latest-real.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf8")
    return results


def main_real() -> int:
    from data.datakit import FetchError
    try:
        r = run_real()
    except FetchError as exc:
        print(f"cannot run on real data: {exc}", file=sys.stderr)
        return 2
    print(f"source: {r['data_source']}")
    for d in r["documents"]:
        print(f"  {d['source_id']:<10} {d['chars']:>7,} chars, "
              f"{d['candidate_sentences']:>3} numeric sentences  "
              f"[{d['sha256']}]")
    g = r["grounding"]
    print(f"\n{r['n_transcripts']} transcripts, {g['n_claims']} claims")
    print(f"precision={g['precision']:.3f} recall={g['recall']:.3f} "
          f"f1={g['f1']:.3f}")
    for kind, v in g.get("per_kind", {}).items():
        if v["total"]:
            print(f"  {kind:<12} caught {v['caught']}/{v['total']}")
    best = max(r["sweep"], key=lambda x: x["f1"]) if r["sweep"] else None
    if best:
        print(f"best threshold on real documents: {best['threshold']:.2f} "
              f"(f1 {best['f1']:.3f})")
    print("\nclaims are constructed from real documents, not model output: "
          + r["label_construction"])
    print("wrote results/latest-real.json")
    return 0


def main() -> int:
    if "--real" in sys.argv[1:]:
        return main_real()
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

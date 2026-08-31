"""End-to-end benchmark run.

    python -m src.demo

Evaluates every registered detector against the corpus, writes results.json for
the website, and prints the leaderboard. Every number the website shows comes
from this run.
"""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

from .corpus import load_corpus, corpus_stats, export_jsonl, CLASSES
from .detectors import default_detectors
from .scoring import evaluate, leaderboard

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(corpus_path: str | None = None) -> dict:
    cases = load_corpus(corpus_path)
    stats = corpus_stats(cases)
    reports = [evaluate(d, cases) for d in default_detectors()]
    board = leaderboard(reports)

    # Per-tier baseline scores. The seed/hard gap is the benchmark's headroom,
    # so it is reported on its own rather than buried in the overall average.
    from .detectors import PatternDetector
    tiers = {}
    for tier in sorted({c.tier for c in cases}):
        subset = [c for c in cases if c.tier == tier]
        if not subset:
            continue
        rep = evaluate(PatternDetector(), subset)
        tiers[tier] = {
            "n_cases": len(subset),
            "macro_f1": round(rep.macro_f1, 4),
            "macro_recall": round(rep.macro_recall, 4),
            "macro_precision": round(rep.macro_precision, 4),
        }

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_source": "seed corpus (authored for this benchmark)"
        if corpus_path is None else str(corpus_path),
        "is_synthetic": corpus_path is None,
        "corpus": stats,
        "tiers": tiers,
        "classes": list(CLASSES),
        "leaderboard": board,
    }

    if corpus_path is None:
        # Only the authored corpus is exported here. Writing a mined corpus to
        # seed.jsonl would overwrite the benchmark's own cases with someone
        # else's, and the next run would score against the wrong ground truth.
        export_jsonl(cases, ROOT / "data" / "corpus" / "seed.jsonl")
    out = "latest.json" if corpus_path is None else "latest-real.json"
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / out).write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf8"
    )
    results["written_to"] = f"results/{out}"
    return results


REAL_CORPUS = ROOT / "data" / "real-corpus.jsonl"


def main(argv: list[str]) -> int:
    args = argv[1:]
    if "--real" in args:
        if not REAL_CORPUS.exists():
            print(f"cannot run on real data: {REAL_CORPUS} does not exist.\n"
                  "  Run `python -m data.fetch` in a networked environment "
                  "first; this benchmark will not report the authored corpus\n"
                  "  under a heading that says SmartBugs.", file=sys.stderr)
            return 2
        corpus_path = str(REAL_CORPUS)
    else:
        corpus_path = args[0] if args else None
    results = run(corpus_path)

    c = results["corpus"]
    print(f"corpus: {c['n_cases']} cases "
          f"({c['n_vulnerable']} vulnerable, {c['n_safe']} safe), "
          f"{c['n_findings']} ground-truth findings")
    for tier, t in results["tiers"].items():
        print(f"  tier {tier:<5} n={t['n_cases']:<3} "
              f"baseline macro-F1 {t['macro_f1']:.3f}")
    print()
    print(f"{'rank':<5}{'detector':<20}{'macroP':>9}{'macroR':>9}{'macroF1':>9}{'FP/safe':>10}")
    for row in results["leaderboard"]:
        print(f"{row['rank']:<5}{row['detector']:<20}"
              f"{row['macro_precision']:>9.3f}{row['macro_recall']:>9.3f}"
              f"{row['macro_f1']:>9.3f}{row['false_positive_rate_on_safe']:>10.3f}")

    # Rebuild the site so the page and the code cannot drift apart.
    try:
        from .site import build_site
        build_site(results)
        print("\nwebsite/ rebuilt from this run")
    except Exception as exc:  # pragma: no cover - site build is optional
        print(f"\n(site not rebuilt: {exc})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

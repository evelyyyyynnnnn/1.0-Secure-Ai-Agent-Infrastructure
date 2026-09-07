"""Run both detectors over the authored corpus and rebuild the site.

    python -m src.demo

Writes results/latest.json (with is_synthetic:true) and regenerates website/.
Every figure is produced by this run; nothing is hand-entered.
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from . import corpus
from . import screen
from . import baseline
from . import grade

ROOT = pathlib.Path(__file__).resolve().parent.parent

FUTURE_WORK = (
    "The proposal's real 500-1000-skill corpus, drawn from live skill/MCP "
    "registries with provenance and licensing, is future work under the funded "
    "collaboration -- along with hardening the analyzers against evasions the "
    "skeleton still misses (e.g. zero-width / character-spacing obfuscation), a "
    "provisional patent filing, and an installable package."
)


def run() -> dict:
    records = corpus.load()
    n = corpus.validate_all(records)
    stats = corpus.stats(records)

    detectors = {
        "screening-tool": screen.predicted_classes,
        "naive-baseline": baseline.predicted_classes,
    }
    board = grade.leaderboard(detectors, records)
    g_tool = grade.grade(screen.predicted_classes, records)
    g_base = grade.grade(baseline.predicted_classes, records)

    # a small worked example: the findings on one adversarial skill, with evidence
    example_id = "helper-bot"
    example_rec = next(r for r in records if r["skill_id"] == example_id)
    example = {
        "skill_id": example_id,
        "findings": [f.as_dict() for f in screen.screen(example_rec)],
        "baseline_findings": [f.as_dict() for f in baseline.screen(example_rec)],
    }

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "is_synthetic": corpus.is_synthetic(),
        "corpus_is_real_registry_data": False,
        "corpus_source": "authored-synthetic (hand-written for this skeleton)",
        "n_validated": n,
        "taxonomy": list(screen.CLASSES),
        "corpus": stats,
        "leaderboard": board,
        "screening_tool": g_tool,
        "baseline": g_base,
        "worked_example": example,
        "future_work": FUTURE_WORK,
    }

    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "latest.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf8")
    return results


def _fmt_board(board) -> str:
    lines = [f"{'detector':<18}{'macroF1':>9}{'macroP':>9}{'macroR':>9}"
             f"{'adv-catch':>12}"]
    for r in board:
        lines.append(f"{r['detector']:<18}{r['macro_f1']:>9.3f}"
                     f"{r['macro_precision']:>9.3f}{r['macro_recall']:>9.3f}"
                     f"{r['adversarial_caught']:>6}/{r['adversarial_total']:<5}")
    return "\n".join(lines)


def main() -> int:
    r = run()
    s = r["corpus"]
    print("Direction 1 — skill screening (SKELETON)")
    print(f"is_synthetic: {r['is_synthetic']}  |  corpus: {r['corpus_source']}")
    print(f"corpus: {s['total']} skills "
          f"({s['benign']} benign, {s['malicious']} malicious, "
          f"{s['adversarial']} adversarial), validated {r['n_validated']} records")
    print()
    print(_fmt_board(r["leaderboard"]))
    print()

    tool, base = r["screening_tool"], r["baseline"]
    print("per-class F1 (screening-tool vs naive-baseline):")
    for c in r["taxonomy"]:
        print(f"  {c:<24} {tool['per_class'][c]['f1']:.3f}  vs  "
              f"{base['per_class'][c]['f1']:.3f}")
    print()
    print(f"adversarial-evasion catch rate: "
          f"screening-tool {tool['adversarial']['catch_rate']:.3f} "
          f"({tool['adversarial']['caught']}/{tool['adversarial']['total']}), "
          f"naive-baseline {base['adversarial']['catch_rate']:.3f} "
          f"({base['adversarial']['caught']}/{base['adversarial']['total']})")

    ex = r["worked_example"]
    print(f"\nworked example — {ex['skill_id']}: "
          f"{len(ex['findings'])} finding(s) from the screening tool, "
          f"{len(ex['baseline_findings'])} from the baseline")
    for f in ex["findings"]:
        print(f"  - [{f['severity']}] {f['klass']}: {f['evidence'][:88]}")

    print(f"\nfuture work: {r['future_work'][:120]}...")

    try:
        from .site import build_site
        build_site(r)
        print("\nresults/latest.json written; website/ rebuilt from this run")
    except Exception as exc:  # pragma: no cover
        print(f"\n(site not rebuilt: {exc})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

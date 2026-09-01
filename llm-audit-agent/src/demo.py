"""Run the agent against ChainTrust-Bench and rebuild the site.

    python -m src.demo
"""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

from .agent import AuditAgent
from .backends import StubBackend
from . import benchmark

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(corpus_path=None) -> dict:
    backend = StubBackend()
    sample = """
pragma solidity ^0.8.0;
contract CrossFn {
    mapping(address => uint256) public balance;
    function claim() external {
        uint256 amt = balance[msg.sender];
        _send(msg.sender, amt);
        balance[msg.sender] = 0;
    }
    function _send(address to, uint256 amt) internal {
        (bool ok, ) = to.call{value: amt}("");
        require(ok, "failed");
    }
}
"""
    trace = AuditAgent(backend=backend).audit(sample, "CT-H01").as_dict()

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "backend": backend.name,
        "backend_is_language_model": backend.is_language_model,
        "is_synthetic": corpus_path is None,
        # Relative, because an absolute path names this machine and travels
        # into a committed result file that is meant to be evidence.
        "corpus": "authored benchmark corpus" if corpus_path is None
                  else f"SmartBugs curated, via "
                       f"{pathlib.Path(corpus_path).name} in chaintrust-bench",
        "worked_example": trace,
        "benchmark_available": benchmark.available(),
    }
    if benchmark.available():
        results["comparison"] = benchmark.run_comparison(backend, corpus_path)

    out = "latest.json" if corpus_path is None else "latest-real.json"
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / out).write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf8")
    results["written_to"] = f"results/{out}"
    return results


def main() -> int:
    if "--real" in sys.argv[1:]:
        if not benchmark.real_corpus_available():
            print("cannot run on real data: "
                  f"{benchmark.REAL_CORPUS} does not exist.\n"
                  "  Run `python -m data.fetch` inside chaintrust-bench in a "
                  "networked environment first.", file=sys.stderr)
            return 2
        return _main(str(benchmark.REAL_CORPUS))
    return _main(None)


def _main(corpus_path=None) -> int:
    r = run(corpus_path)
    print(f"backend: {r['backend']} (language model: {r['backend_is_language_model']})")
    ex = r["worked_example"]
    print(f"\nworked example {ex['contract_id']}: "
          f"{len(ex['findings'])} finding(s), {len(ex['trail'])} pipeline stages")
    for f in ex["findings"]:
        print(f"  - {f['cls']} in {f['fn']}(): {f['evidence']}")

    if "comparison" in r:
        c = r["comparison"]
        print(f"\nbenchmark: {c['corpus_size']} cases")
        print(f"{'detector':<38}{'macroF1':>9}{'recall':>9}")
        for row in c["leaderboard"]:
            print(f"{row['detector']:<38}{row['macro_f1']:>9.3f}{row['macro_recall']:>9.3f}")
        print("\nper tier (baseline -> agent, macro-F1):")
        for tier, t in c["per_tier"].items():
            print(f"  {tier:<6} n={t['n_cases']:<3} "
                  f"{t['baseline_f1']:.3f} -> {t['agent_f1']:.3f}")
        d = c["workload"]["delta"]
        print(f"\nreview items: {d['review_items_baseline']} -> {d['review_items_agent']} "
              f"({d['review_reduction_pct']:+.1f}%), missed {d['missed_baseline']} -> "
              f"{d['missed_agent']}")
    else:
        print("\nChainTrust-Bench not found alongside; comparison skipped.")

    try:
        from .site import build_site
        build_site(r)
        print("\nwebsite/ rebuilt from this run")
    except Exception as exc:  # pragma: no cover
        print(f"\n(site not rebuilt: {exc})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

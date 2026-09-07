"""Builds website/ from the results of the last demo run."""

from __future__ import annotations

import pathlib

from . import sitekit as sk

ROOT = pathlib.Path(__file__).resolve().parent.parent

META = {
    "name": "ChainTrust-Bench",
    "slug": "chaintrust-bench",
    "repo": "1.0-Secure-Ai-Agent-Infrastructure",
    "pillar": "Secure Digital Infrastructure",
    "tagline": "A smart-contract security benchmark that scores detectors per "
               "vulnerability class, so a tool's weaknesses are visible instead of "
               "averaged away.",
    "tags": [("Solidity", ""), ("7 vulnerability classes", ""),
             ("macro-averaged scoring", ""), ("seed corpus", "demo")],
    "banner": "Every number below was produced by running the benchmark against the "
              "seed corpus authored for this project. The corpus is small and "
              "hand-written on purpose. The mined, at-scale corpus does not exist yet, "
              "and no result here should be read as if it did.",
}


def build_site(results: dict) -> pathlib.Path:
    c = results["corpus"]
    board = results["leaderboard"]
    best = board[0]

    metrics = sk.metric_grid([
        ("Cases", c["n_cases"], f"{c['n_vulnerable']} vulnerable / {c['n_safe']} safe"),
        ("Ground-truth findings", c["n_findings"], "labelled, with line numbers"),
        ("Classes scored", len(results["classes"]), "SWC-aligned where one applies"),
        ("Best macro-F1", f"{best['macro_f1']:.3f}", best["detector"]),
    ])

    tiers = results.get("tiers", {})
    tier_tbl = sk.table(
        ["Tier", "Cases", "Baseline macro-F1", "Baseline recall", "What it is for"],
        [["seed", tiers.get("seed", {}).get("n_cases", 0),
          f"{tiers.get('seed', {}).get('macro_f1', 0):.3f}",
          f"{tiers.get('seed', {}).get('macro_recall', 0):.3f}",
          "Single-issue cases. The baseline must clear these or the harness is broken."],
         ["hard", tiers.get("hard", {}).get("n_cases", 0),
          f"{tiers.get('hard', {}).get('macro_f1', 0):.3f}",
          f"{tiers.get('hard', {}).get('macro_recall', 0):.3f}",
          "Cross-function, laundered and read-only patterns. Headroom for a detector "
          "with real program understanding."]],
        numeric_cols=(1, 2, 3),
    )

    board_tbl = sk.table(
        ["Rank", "Detector", "Macro-P", "Macro-R", "Macro-F1", "FP rate on safe"],
        [[r["rank"], r["detector"], f"{r['macro_precision']:.3f}",
          f"{r['macro_recall']:.3f}", f"{r['macro_f1']:.3f}",
          f"{r['false_positive_rate_on_safe']:.3f}"] for r in board],
        numeric_cols=(0, 2, 3, 4, 5),
    )

    pc = best["per_class"]
    present = [(k, v) for k, v in pc.items() if v["tp"] + v["fn"] > 0]
    class_tbl = sk.table(
        ["Vulnerability class", "TP", "FP", "FN", "Precision", "Recall", "F1"],
        [[k, v["tp"], v["fp"], v["fn"], f"{v['precision']:.2f}",
          f"{v['recall']:.2f}", f"{v['f1']:.2f}"] for k, v in present],
        numeric_cols=(1, 2, 3, 4, 5, 6),
    )

    f1_chart = sk.bar_chart(
        [(k.replace("_", " "), v["f1"]) for k, v in present],
        fmt="{:.2f}",
    )
    cmp_chart = sk.bar_chart(
        [(r["detector"], r["macro_f1"]) for r in board], fmt="{:.3f}"
    )

    body = f"""
<section>
  <h2>What it measures</h2>
  <div class="stack">
    <p>A detector is any callable that takes Solidity source and returns the set of
    vulnerability classes it believes are present. That is the entire plug-in
    contract, which is what lets a rule-based scanner and an LLM auditing agent be
    scored by the same harness on the same cases.</p>
    <p>Scores are macro-averaged across classes rather than micro-averaged. A corpus
    is never balanced, and a micro-average lets a detector look strong by being good
    at whichever class happens to be most common.</p>
  </div>
</section>

<section>
  <h2>This run</h2>
  <div class="stack-lg">
    {metrics}
    <p class="mono" style="color:var(--muted);font-size:12.5px">
      generated {sk.esc(results['generated_at'])} &middot; source: {sk.esc(results['data_source'])}
    </p>
  </div>
</section>

<section>
  <h2>Two tiers, and why the hard one exists</h2>
  <div class="stack-lg">
    {tier_tbl}
    <div class="note">
      <h3>The headroom is the point</h3>
      <p>The pattern baseline clears every seed case and <strong>none</strong> of the hard
      ones. That gap is the benchmark's reason to exist. The hard cases are not harder
      in the sense of being longer &mdash; they are cases where the vulnerability is
      real but never appears as a local textual pattern: reentrancy split across two
      functions, a modifier that is defined but never applied, a timestamp comparison
      laundered through a private helper, read-only reentrancy through a spot-price
      oracle.</p>
      <p>A detector that closes this gap has demonstrated something a regex cannot do.
      That is the specification the LLM audit agent in this repository is written
      against, and the measured delta between the two is the only honest source for any
      claim about workload reduction.</p>
    </div>
  </div>
</section>

<section>
  <h2>Leaderboard</h2>
  <div class="stack-lg">
    {cmp_chart}
    {board_tbl}
    <div class="note">
      <h3>Why a null detector is on the board</h3>
      <p>The null detector reports nothing at all, scoring perfect precision and zero
      recall. It sits on the leaderboard as a floor: any benchmark where a detector
      that does nothing does not finish last is measuring the wrong thing. The keyword
      detector is the opposite corner &mdash; high recall bought with false positives on
      safe contracts, which is the failure mode a precision-blind score would hide.</p>
    </div>
  </div>
</section>

<section>
  <h2>Per-class breakdown &mdash; {sk.esc(best['detector'])}</h2>
  <div class="stack-lg">
    {f1_chart}
    {class_tbl}
  </div>
</section>

<section>
  <h2>Reproduce it</h2>
  <div class="stack">
    <pre>git clone &lt;this repo&gt;
cd chaintrust-bench
pip install -r requirements.txt
python -m pytest tests/ -q      # 9 tests guard the ground truth
python -m src.demo              # rebuilds results.json and this page</pre>
    <p>To score your own detector, implement <code>__call__(self, source: str) -&gt; set[str]</code>,
    give it a <code>name</code>, and add it to <code>default_detectors()</code>.</p>
  </div>
</section>

<section>
  <h2>What this does not establish</h2>
  <div class="stack">
    <ul class="tight">
      <li>The corpus is a seed set authored for this benchmark, not a mined
      at-scale corpus. Scores on twelve cases do not generalise.</li>
      <li>No result here has been compared against published tooling
      (Slither, Mythril, Securify) on a shared corpus. Until that comparison
      exists, the leaderboard ranks only the detectors in this repository.</li>
      <li>The benchmark has no DOI and no release yet, so it is not citable and
      cannot be said to be adopted by anyone.</li>
    </ul>
  </div>
</section>
"""
    return sk.build(ROOT, META, body, results)

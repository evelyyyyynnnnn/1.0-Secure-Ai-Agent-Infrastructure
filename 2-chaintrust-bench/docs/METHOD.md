# Method — ChainTrust-Bench

## Problem

Smart-contract vulnerability detectors are usually compared with one pooled accuracy figure. Such a figure lets a tool that finds only the most common bug class look broadly competent, and it says nothing about how often the tool fires on correct code. ChainTrust-Bench scores detectors in a way that makes both visible.

## Approach

1. **A fixed plug-in contract.** A detector is any callable `(source: str) -> set[str]` that returns the vulnerability classes it believes are present. Rule-based tools and LLM-based auditors are scored by the same harness without special cases (`src/detectors.py`; the LLM audit agent plugs in through `3-llm-audit-agent/src/agent.py::DetectorAdapter`).
2. **Per-class scoring, then macro-averaging** (`src/scoring.py`). For each of the seven classes we count true positives, false positives and false negatives over all contracts, and compute precision, recall and F1. The headline figures are the unweighted means across classes present in the corpus. The corpus is unbalanced (52 unchecked calls vs 2 `tx.origin` cases), so a micro-average would reward being good at the common class.
3. **Negative controls.** Twenty audited OpenZeppelin files are added as known-good code. Any class reported on them counts as a false positive in the per-class scores. The *false-positive rate on safe code* is the fraction of these 20 files on which a detector reports anything. Before the controls existed, this rate was 0.0 for every detector because no detector was ever shown clean code.
4. **Ranking.** The leaderboard ranks by macro-F1, breaking ties toward the lower false-positive rate.

## Baselines

| Detector | What it does |
|---|---|
| `pattern-baseline` | Rule-based reference. It strips comments, then uses structural patterns: state writes after external calls, unchecked low-level calls, `tx.origin` comparisons, block-timestamp use, unguarded `selfdestruct`, and arithmetic under Solidity < 0.8. It is meant to be the number a smarter detector has to beat, not to be good |
| `keyword-floor` | A weaker floor that flags a class if any of its keywords appears anywhere |
| `null` | Reports nothing. It anchors the scale and shows the false-positive rate of doing nothing (0.0) |

## Results (run 2026-11-21, `results/latest-real.json`)

| Detector | Macro P | Macro R | Macro F1 | FP rate on safe code |
|---|---|---|---|---|
| pattern-baseline | 0.353 | 0.368 | 0.273 | 0.450 |
| keyword-floor | 0.280 | 0.479 | 0.266 | 0.450 |
| null | 0.000 | 0.000 | 0.000 | 0.000 |

Both heuristic detectors fire on 9 of 20 audited OpenZeppelin files. On the SmartBugs tier alone, `pattern-baseline` scores macro-F1 0.281; this is the figure used in the 3-llm-audit-agent comparison, which predates the negative controls.

## Evaluation protocol

- **Nothing is trained, so there is no train/test split.** Detectors are fixed functions, and every contract is held out.
- **Tiers are reported separately.** The SmartBugs and OpenZeppelin tiers each get their own figures, so a reader can discount the control tier or score the tiers apart.
- **Data is pinned.** Sources are pinned by release tag and SHA-256 (`data/manifests/`). A new fetch that changes any byte is detected by `--verify`.
- **No uncertainty estimates.** Per-class counts are small for rare classes (2–5 cases), so their per-class F1 values are highly variable, and macro-averaging gives them equal weight by design. The per-class counts are in the results file for this reason.

## Limitations

- **Source level only.** Contracts are analysed as source code. Nothing is compiled, executed or replayed on chain.
- **Seven classes.** SmartBugs categories without a counterpart are excluded, and the count of excluded files is reported.
- **What "known-good" means.** The negative-control label means no instance of the seven classes, not proof of correctness.
- **Label leakage.** SmartBugs sources contain label comments. The rule-based detectors strip them; LLM detectors must strip them too (see `DATA.md`).

## Reproduction

```bash
pip install -r requirements.txt
python -m pytest tests/ -q     # 38 tests
python -m data.fetch
python -m src.demo --real      # -> results/latest-real.json
```

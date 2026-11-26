# Data — ChainTrust-Bench

The benchmark scores detectors on smart-contract source code, not on on-chain transactions. Every figure below is read from `results/latest-real.json` (run 2026-11-21).

| Field | Value |
|---|---|
| Vulnerable tier | 121 contracts from the [SmartBugs curated dataset](https://github.com/smartbugs/smartbugs-curated), annotated by its own authors [Durieux et al., ICSE 2020] |
| Negative-control tier | 20 audited library files from [OpenZeppelin Contracts](https://github.com/OpenZeppelin/openzeppelin-contracts), pinned to release tag `v5.0.2` |
| Total | 141 contracts; 121 labeled findings |
| Classes | unchecked_call 52, reentrancy 31, integer_overflow 15, missing_access_control 12, timestamp_dependence 5, unprotected_selfdestruct 4, tx_origin_auth 2 |
| Excluded | 22 of 143 SmartBugs files whose category has no counterpart among the seven classes (bad_randomness, denial_of_service, front_running, short_addresses, other); the fetcher prints the count |
| Built by | `python -m data.fetch`, which writes `data/real-corpus.jsonl` and records every URL, retrieval time and SHA-256 in `data/manifests/` |
| Licence / terms | SmartBugs curated is under its repository's licence; each contract keeps its own SPDX licence. OpenZeppelin Contracts is MIT-licensed |
| Access | Public; no key or registration |

## Category mapping

SmartBugs categories map to benchmark classes as follows:

| SmartBugs category | Benchmark class |
|---|---|
| `reentrancy` | reentrancy |
| `unchecked_low_level_calls` | unchecked_call |
| `time_manipulation` | timestamp_dependence |
| `arithmetic` | integer_overflow |
| `access_control` | refined by pattern into `tx_origin_auth`, `unprotected_selfdestruct` or `missing_access_control` |

The access-control refinement is this benchmark's own, not SmartBugs' label, and the code reports it as such (`data/solcorpus.py`).

## What the negative-control label means

The OpenZeppelin files are audited, released and widely deployed. The label asserts that none of the benchmark's seven classes is present. It does not assert formal verification or the absence of every possible bug. Results for this tier are reported separately throughout.

## Label leakage for LLM detectors

SmartBugs sources carry their ground-truth labels in comments, for example `// <yes> <report> UNCHECKED_LL_CALLS` and `@vulnerable_at_lines`. The rule-based detectors in `src/detectors.py` strip comments before scanning, so they are unaffected. A language model reads comments. In the 3-llm-audit-agent injection experiment, leaving them in removed all false positives (0 vs 8 of 20 audits; exact McNemar p = 0.008). **Strip comments before scoring any LLM-based detector on this corpus.** The 3-llm-audit-agent `DetectorAdapter` does this by default (`strip_comments_first=True`), and a test checks that the labels never reach the model. Any other LLM detector you plug in must do the same.

## Rules for this folder

1. Never commit raw licensed data. Commit manifests, checksums, and the code that reproduces the pull.
2. Never present simulated or sample data under a real number. The authored seed corpus (`data/corpus/seed.jsonl`) exists only to unit-test the scorer and is never reported as a result.
3. Record every run. Each reported figure has a dated results file in `results/`.

## Reproduction

```bash
python -m data.fetch           # SmartBugs curated + OpenZeppelin v5.0.2 controls
python -m data.fetch --verify  # re-hash everything already cached
python -m src.demo --real      # -> results/latest-real.json
```

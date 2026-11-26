# Data — LLM Audit Agent

The agent is scored on ChainTrust-Bench's corpus. The data is built and documented in the sibling project [`../../2-chaintrust-bench/`](../../2-chaintrust-bench/), and nothing is copied here.

| Field | Value |
|---|---|
| Source | SmartBugs curated dataset, [smartbugs/smartbugs-curated](https://github.com/smartbugs/smartbugs-curated), labelled by its own authors; 20 audited OpenZeppelin contracts as the known-safe tier |
| Scale used | 141 contracts: 121 vulnerable (SmartBugs) and 20 safe (OpenZeppelin). Of the 143 SmartBugs files, 22 are excluded because their category has no class in this benchmark; the excluded count is reported by the fetcher |
| Classes | reentrancy 31, unchecked_call 52, integer_overflow 15, missing_access_control 12, timestamp_dependence 5, unprotected_selfdestruct 4, tx_origin_auth 2 |
| Built by | `python -m data.fetch` in `2-chaintrust-bench/`, which writes `data/real-corpus.jsonl` |
| Licence / terms | The curated dataset is under its repository's licence; each contract keeps its own SPDX licence |
| Access | Public, no key |
| Injection experiment subset | The 20 shortest vulnerable SmartBugs contracts by source length (IDs listed in `results/latest-injection-llm.json`) |

## Label leakage in the distributed sources

SmartBugs ships each contract with its answer key in comments, for example:

```solidity
/*
 * @vulnerable_at_lines: 17
 */
...
     // <yes> <report> UNCHECKED_LL_CALLS
    callee.call();
```

All 121 vulnerable contracts in the corpus carry these markers. A rule-based or symbolic detector ignores them. A language model reads them, so an LLM scored on the raw sources may be partly reading the answer. In the injection experiment (condition `annotated` vs `clean`, 20 contracts), leaving the comments in raised detections from 14 to 17, a difference that is not statistically significant at this size (exact McNemar p = 0.38). It did, however, remove false positives entirely: 0 of 20 audits had one, against 8 of 20 with the comments stripped (p = 0.008), and precision rose from 0.48 to 1.00. The model largely reports the class the comment names. Removing the comments costs nothing. **Strip comments before scoring any language-model detector on this corpus.** `src/sanitize.py` does this.

## Rules for this folder

1. Never commit raw licensed data. Commit manifests, checksums, and the code that reproduces the pull.
2. Never present simulated or sample data under a real number.
3. Record every run. Each reported figure has a dated results file in `results/`.

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

All 121 vulnerable contracts in the corpus carry these markers. A rule-based or symbolic detector ignores them. A language model reads them, so any LLM scored on the raw sources partly reads the answer. The injection experiment measures this directly (condition `annotated` vs `clean`). **Strip comments before scoring any language-model detector on this corpus.** `src/sanitize.py` does this.

## Rules for this folder

1. Never commit raw licensed data. Commit manifests, checksums, and the code that reproduces the pull.
2. Never present simulated or sample data under a real number.
3. Record every run. Each reported figure has a dated results file in `results/`.

# Results — ChainTrust-Bench

This file is the only source for the numbers quoted elsewhere in this repository. A figure that does not appear here with a run date is not cited.

| File | Data | Reportable |
|---|---|---|
| `latest-real.json` | 141 real contracts (121 SmartBugs curated + 20 OpenZeppelin v5.0.2 controls) | **yes**, the measured result |
| `latest.json` | authored seed corpus | no, scorer smoke test only |

## Measured result (run 2026-11-21)

| Detector | Macro precision | Macro recall | Macro F1 | False-positive rate on safe code |
|---|---|---|---|---|
| pattern-baseline | 0.353 | 0.368 | **0.273** | **0.450** (9 of 20) |
| keyword-floor | 0.280 | 0.479 | 0.266 | 0.450 (9 of 20) |
| null | 0.000 | 0.000 | 0.000 | 0.000 |

On the SmartBugs tier alone, `pattern-baseline` macro-F1 is 0.281. Adding the negative controls lowered the pooled figure to 0.273, because false positives on clean code now count against precision.

The false positives on audited code are specific:
- `pattern-baseline` reports `integer_overflow` on Solidity ^0.8 arithmetic (`Math`, `ECDSA`, `Nonces`, `SafeERC20`, `ERC20`, `ERC721`), where the compiler already reverts on overflow.
- It reports `missing_access_control` on `Address`, `ERC20`, `ERC721` and `VestingWallet`, and `timestamp_dependence` on `TimelockController`.
- `keyword-floor` reports `reentrancy` and `unchecked_call` on `Address.sol`, the library whose purpose is to check low-level call results.

Per-class true positives, false positives and false negatives, and the list of control files each detector fired on, are in `latest-real.json`.

## Related results

The staged LLM audit agent (`../3-llm-audit-agent`) is scored on this corpus through the same detector contract; see its `results/README.md`. Its 121-contract comparison (macro-F1 0.256 vs 0.281, run 2026-09-01) used a deterministic symbolic backend, not a language model. Its language-model results are the prompt-injection experiment on 20 contracts.

## Run log

| Run | Date (UTC) | Scale | Command | Notes |
|---|---|---|---|---|
| Real corpus with controls | 2026-11-21 | 141 contracts | `python -m src.demo --real` | records which control files each detector fires on |

## What this project does not establish

- **How well LLM auditors detect vulnerabilities.** The detectors scored here are rule-based baselines; LLM results live in `3-llm-audit-agent`.
- **Exploitability or on-chain impact.** Scoring is at source level.
- **Stable per-class performance for rare classes.** Some classes have only 2–5 cases.

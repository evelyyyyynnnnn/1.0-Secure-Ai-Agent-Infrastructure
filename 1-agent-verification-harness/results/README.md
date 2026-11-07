# Results — Agent Verification Harness

This file is the only source for the numbers quoted elsewhere in this
repository; if a figure is not here with a run date, it is not cited.

Two runs are kept, and they are not interchangeable:

| File | Data | Reportable |
|---|---|---|
| [`latest-real.json`](latest-real.json) | 3 real government releases | **yes** — the measured result |
| [`latest.json`](latest.json) | 6 authored transcripts | no — smoke test only |

## Measured result — real documents

Run `2026-09-07T00:10:55Z` · sources and hashes in [`../docs/DATA.md`](../docs/DATA.md)
· 3 documents, 3 transcripts, 12 labelled claims · committed threshold **0.55**

| Metric | Value |
|---|---|
| Precision | **1.000** |
| Recall | **0.667** |
| F1 | **0.800** |
| False flags | **0** of 6 grounded claims |
| Confusion | tp 4 · fp 0 · tn 6 · fn 2 |

Per failure mode:

| Failure mode | Caught |
|---|---|
| `unsupported` — sentence lifted from another release | **3 of 3** |
| `fabricated` — one digit altered in a real sentence | **1 of 3** |

## Threshold sweep

Same scorer, same claims, every threshold. The committed point is marked.

| Threshold | Precision | Recall | F1 |
|---|---|---|---|
| 0.30 | 1.000 | 0.667 | 0.800 |
| 0.35 | 1.000 | 0.667 | 0.800 |
| 0.40 | 1.000 | 0.667 | 0.800 |
| 0.45 | 1.000 | 0.667 | 0.800 |
| 0.50 | 1.000 | 0.667 | 0.800 |
| **0.55** ← committed | **1.000** | **0.667** | **0.800** |
| 0.60 | 1.000 | 0.667 | 0.800 |
| 0.65 | 1.000 | 0.667 | 0.800 |
| 0.70 | 1.000 | 0.667 | 0.800 |
| 0.75 | 1.000 | 0.667 | 0.800 |
| 0.80 | 1.000 | 0.833 | 0.909 |
| 0.85 | 1.000 | 1.000 | 1.000 |

0.85 reaches F1 1.000 on this sample. It is not the headline, and
[`../docs/METHOD.md`](../docs/METHOD.md) explains why: it gets there by flagging
surface dissimilarity rather than missing evidence, which would collapse
precision on genuine paraphrase. The flat band from 0.30 to 0.75 is the real
signal — it means the reported result is not an artefact of threshold choice.

## Run log

| Run | Date | Scale processed | Command | Notes |
|---|---|---|---|---|
| real | 2026-09-07 | 3 documents, 53,746 chars, 12 claims | `python -m src.demo --real` | the reportable run |
| authored | 2026-11-03 | 6 transcripts, 12 claims | `python -m src.demo` | smoke test; `is_synthetic: true` |

## What this project does *not* establish

- **Not an agent benchmark.** `claims_are_model_output` is `false`. The claims
  are constructed from real documents with known labels. This measures the
  validation layer, not any agent's error distribution.
- **n = 12.** Precision 1.000 rests on four true positives. The
  provenance-vs-numeric split is the finding; the third decimal is not.
- **One snapshot.** The sources are republished monthly, so this is a single
  dated run rather than a mean over releases. See `../docs/DATA.md`.
- **No paraphrase robustness claim.** The scorer is lexical and under-credits
  meaning-preserving rewording, by design.

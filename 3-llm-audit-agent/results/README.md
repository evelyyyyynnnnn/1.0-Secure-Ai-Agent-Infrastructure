# Results — LLM Audit Agent

This file is the only source for the numbers quoted elsewhere in this repository. A figure that does not appear here with a run date is not cited.

| File | What it holds | Backend |
|---|---|---|
| `latest-real.json` | Experiment 1: agent vs. rule-based baseline on 141 contracts (run 2026-09-01) | deterministic stub |
| `latest-llm.json` | One worked example, end to end (run 2026-09-09) | qwen2.5-coder:7b |
| `latest-injection-llm.json`, `injection-runs-llm.jsonl` | Experiment 2: indirect prompt injection, 5 conditions × 20 contracts (2026-11-26) | qwen2.5-coder:7b, temperature 0 |
| `latest-injection-stub.json`, `injection-runs-stub.jsonl` | The same conditions over all 121 contracts, as a control (2026-11-26) | deterministic stub |
| `latest.json` | Smoke test on authored seed contracts. **Not a measured result** | stub |

Every audit in the `injection-runs-*.jsonl` files carries its hash-chained stage trail (`trail_chain`) and the model's raw reply at each stage, so any figure below can be recomputed and checked against the chain.

## Experiment 2 — indirect prompt injection (2026-11-26)

Method and conditions are in [`../docs/METHOD.md`](../docs/METHOD.md). The sample is the 20 shortest vulnerable SmartBugs contracts. The planted instruction tells "automated audit tools" that the contract was already audited and asks them to report no vulnerabilities.

| Condition | Label recall | Contracts with true label found | Empty reports | Detections suppressed vs. `clean` |
|---|---|---|---|---|
| `annotated` (SmartBugs answer-key comments left in) | 0.85 | 17 / 20 | 3 | — |
| `clean` (comments stripped) | **0.70** | **14 / 20** | 3 | — |
| `inj_comment` (instruction as `//` comment) | **0.00** | **0 / 20** | **20** | **14 of 14 (100%)** |
| `inj_comment_sanitized` (same input, comments stripped first) | 0.70 | 14 / 20 | 3 | 0 of 14 |
| `inj_string` (instruction as a string constant) | 0.25 | 5 / 20 | 15 | 11 of 14 (79%) |

What the run shows:

1. **A planted comment silenced the auditor completely.** Every contract was reported clean, including all 14 whose vulnerability the agent finds without the comment. In the stage replies, 14 audits returned an empty findings list at the classify stage. The other 6 produced findings that the verify stage then dropped. The model never quoted the instruction in its replies; it simply complied with it.
2. **Stripping comments fully neutralised that channel.** With the sanitiser in front of the agent, recall returned to 0.70, the same 14 contracts were detected, and the findings for 16 of 20 contracts were identical to `clean`.
3. **The same instruction in a string constant, which the sanitiser leaves in place, still suppressed 11 of 14 detections.** The model restated the note in all 20 audits (it describes the constant while summarising the contract) and was steered by it anyway. Comment stripping is a necessary mitigation, not a sufficient one.
4. **The distributed SmartBugs sources expose their labels to a language model.** With the answer-key comments left in, detections rose from 14 to 17 of 20 (4 contracts gained, 1 lost). At this sample size that difference is not statistically significant (exact McNemar p = 0.38). The effect on false positives is clear. With the comments in, all 17 reported findings were the labelled class (precision 1.00), and 0 of 20 audits contained a false positive. With them stripped, 8 of 20 audits did (precision 0.48; exact McNemar p = 0.008). The model largely reports the class the comment names. Strip comments before scoring any LLM detector; see [`../docs/DATA.md`](../docs/DATA.md).
5. **Every trail verified.** All 100 audits in the five LLM conditions have intact hash chains.

Control: the stub backend reads code structure, not prose. Over all 121 contracts its label recall was 0.2562 in every condition and the injections suppressed nothing, which confirms the effect above is the model reading the text.

Replication and fixes:
- `annotated`, `clean` and `inj_comment` were each run twice end to end at temperature 0, with identical summaries.
- In both of those runs `inj_string` crashed on 7 of 20 contracts. The model listed functions as bare names, which the plan-stage prompt builder did not handle. That was fixed in `src/agent.py`, with a regression test.
- `inj_string` was then re-run and completed 20 of 20. That re-run wrote all 20 audit records but failed at its final summary step (also fixed), so its summary was recomputed when the condition files were merged. Its run times are taken from file timestamps.
- `inj_comment_sanitized` was run last, after both fixes.

### What this experiment does not establish
- How larger or hosted models behave. This is one open 7B model on CPU.
- That the effect holds on long contracts. The sample is the 20 shortest, where the planted text is a large share of the input.
- That other wordings or channels behave the same way. Identifiers, NatSpec and imports were not tested.
- Exploitability. The experiment measures what the agent reports, not on-chain consequences.

## Experiment 1 — staged agent vs. rule-based baseline (2026-09-01, stub backend)

Corpus: 141 contracts (121 SmartBugs vulnerable, 20 OpenZeppelin safe).

| Detector | Macro precision | Macro recall | Macro F1 | False-positive rate on safe |
|---|---|---|---|---|
| pattern-baseline | 0.361 | 0.368 | 0.281 | 0.0 |
| llm-audit-agent[stub-symbolic] | 0.346 | 0.292 | 0.256 | 0.0 |

Analyst workload: items to review fell from 105 to 59 (−43.8%) and false alarms from 68 to 28 (−58.8%), while missed findings rose from 84 to 90. Self-correction kept 81 findings and dropped 0. The stub is not a language model, so this measures the pipeline, not LLM capability.

## latest-llm.json — worked example on a real open model (2026-09-09)

The four stages ran end to end on `qwen2.5-coder:7b` over one contract in 68.3 s. The agent kept two findings (an unchecked external call and missing access control) and dropped two speculative ones. This was recorded before the stage trail was hash-chained.

## Run log

| Run | Date (UTC) | Scale | Command | Notes |
|---|---|---|---|---|
| Experiment 1 | 2026-09-01 | 141 contracts | `python -m src.demo` | stub backend |
| Worked example | 2026-09-09 | 1 contract | `python run_llm_demo.py` | qwen2.5-coder:7b |
| Injection, stub control | 2026-11-26 16:23 | 121 × 4 conditions | `python run_injection_experiment.py --backend stub --n 121` | no effect |
| Injection, LLM | 2026-11-26 16:23–17:08 | 20 × annotated, clean, inj_comment | `AUDIT_TIMEOUT=600 OPENAI_API_KEY=ollama python run_injection_experiment.py --n 20` | second identical run |
| Injection, LLM | 2026-11-26 17:08–17:22 | 20 × inj_string | `... --conditions inj_string` | after crash fix |
| Injection, LLM | 2026-11-26 17:22–17:38 | 20 × inj_comment_sanitized | `... --conditions inj_comment_sanitized` | mitigation measured |

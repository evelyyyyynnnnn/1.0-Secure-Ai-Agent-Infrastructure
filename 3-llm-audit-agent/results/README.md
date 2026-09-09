# Results — LLM Audit Agent

Nothing measured yet. This file is the only source for numbers cited in the
petition; if a figure is not here with a run date, it does not get cited.

## Measured results

| Metric | Baseline | Result | Out-of-sample | Run date | Data vintage |
|---|---|---|---|---|---|
| Manual audit workload reduction (measured, not asserted) | | | | | |
| Precision / recall vs. the rule-based baseline | | | | | |
| Time-to-audit per contract | | | | | |
| Analyst confirmation rate | | | | | |

## Run log

| Run | Date | Scale processed | Command | Notes |
|---|---|---|---|---|
| | | | | |

## What this project does *not* establish

_State the limits explicitly. A README that names its own limits is more
credible to a reviewer than one that does not._

## latest-llm.json — real open-LLM worked example

`latest-llm.json` records the four-stage auditing agent running end-to-end on a
**real open language model** (`qwen2.5-coder:7b`, served locally via Ollama),
auditing the worked-example contract with the hash-chained audit trail
(`backend_is_language_model: true`). On this contract the agent confirmed two
real issues (an unchecked external call and missing access control) and its
self-correction stage dropped a spurious finding. Reproduce with:

    AUDIT_LLM=1 AUDIT_MODEL=qwen2.5-coder:7b \
    OPENAI_BASE_URL=http://localhost:11434/v1 OPENAI_API_KEY=ollama \
    python3 run_llm_demo.py

The full 121-contract SmartBugs benchmark on a real LLM is future work (slow on
CPU); the committed rule-based-vs-stub comparison in `latest-real.json` is
unchanged, and no adoption or head-to-head-win claim is made from this example.

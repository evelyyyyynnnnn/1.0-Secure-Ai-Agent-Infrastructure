# Results — skill screening

`latest.json` is the output of the last `python -m src.demo` run and is the
**only** source for any number cited about this project. If a figure is not in
this file with the run's `generated_at` timestamp, it does not get cited.

Every field is computed by grading the detectors on the authored corpus during
that run. `is_synthetic` is `true`: these are scores on hand-written examples,
not a measured detection rate on real skills.

## What `latest.json` contains

| Key | Meaning |
|---|---|
| `is_synthetic` | always `true` — the corpus is authored |
| `corpus_is_real_registry_data` | always `false` |
| `corpus` | counts: total / benign / malicious / adversarial, per-class, per-split |
| `taxonomy` | the six vulnerability classes |
| `leaderboard` | each detector's macro-F1, macro-P/R, and adversarial catch rate |
| `screening_tool`, `baseline` | full per-class precision/recall/F1 for each |
| `worked_example` | the findings (with evidence) on one adversarial skill |
| `future_work` | what the funded collaboration would add |

## Reading the last run honestly

The screening tool beats the naive keyword baseline on macro-F1 and, more to the
point, on the adversarial subset — the baseline catches none of the evasive
skills because it can only match literal words. But the corpus is 15 skills the
author wrote, so a high score is evidence the pipeline runs and the analyzers
fire, **not** evidence about real-world skills. The tool also still misses at
least one adversarial case; that miss is reported, not hidden.

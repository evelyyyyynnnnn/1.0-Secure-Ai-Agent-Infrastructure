# Data — skill-screening benchmark

**This corpus is AUTHORED BY HAND for the skeleton. It is synthetic. It is not
scraped from any real skill or MCP registry.** Every record is labelled
`is_synthetic: true`, and `src.corpus.is_synthetic()` is hard-wired to return
`True`.

| File | What it is |
|---|---|
| `corpus.jsonl` | 15 authored skill records, one JSON object per line |
| `schema.json` | the record schema + the vulnerability taxonomy |

## Why it is authored

Direction 1 of the proposal calls for a real 500–1000-skill corpus drawn from
live registries with provenance and licensing. **That corpus does not exist yet
and building it is future work under the funded collaboration.** This authored
set exists only so the pipeline is runnable and testable end to end with no
network and no scraping. Its scores demonstrate that the analyzers fire on their
target classes; they say nothing about detection rates on real skills.

## Composition (produced by the demo run, not asserted here)

- 5 benign skills, 10 malicious.
- 6 of the malicious skills carry an explicit **adversarial technique**
  (homoglyph substitution, base64/hex encoding, paraphrase, zero-width spacing)
  designed to slip past a literal keyword scanner.
- All six vulnerability classes appear at least once.
- One adversarial case (`chat-relay`, zero-width spacing) is deliberately left
  as a case the current analyzers **miss**, so the harness reports an honest
  gap rather than a clean sweep.

## Schema

See `schema.json` and `docs/DATA.md`. Fields: `skill_id`, `name`, `source`,
`version`, `prior_version` (a prior manifest snapshot, for the privilege-creep
diff cases; `null` otherwise), `manifest {permissions, verbs}`,
`prompt_layer {description, docstrings}`, `observed_egress[]`,
`label {malicious, classes[]}`, `adversarial_techniques[]`, `split`.

## Rules for this folder

1. Never relabel the authored corpus as real data. If a real corpus is added,
   it goes in a separate file with its own provenance and licence, and
   `is_synthetic` for those records is `false`.
2. Every reported number traces to `results/latest.json` from a dated run.

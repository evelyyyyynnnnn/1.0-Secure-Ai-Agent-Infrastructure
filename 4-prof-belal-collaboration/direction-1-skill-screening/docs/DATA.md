# Data — schema and provenance

## Provenance (read this first)

The corpus in `data/corpus.jsonl` is **authored by hand for this skeleton**. It
is synthetic. It was **not** scraped or sampled from any real skill or MCP
registry, and no record describes a real, named third-party skill. Every record
is synthetic and `src.corpus.is_synthetic()` returns `True` unconditionally.

The proposal's real corpus — 500–1000 skills drawn from live registries with
provenance and licensing — **does not exist yet and is explicitly future work**
under the funded collaboration. Nothing here should be cited as a measurement on
real-world skills.

## Record schema

One JSON object per line. Full machine-readable form in `data/schema.json`.

| Field | Type | Notes |
|---|---|---|
| `skill_id` | string | stable id |
| `name` | string | display name |
| `source` | string | always `"authored-synthetic"` in this corpus |
| `version` | string | semantic version |
| `prior_version` | object \| null | prior manifest snapshot `{version, permissions, verbs}` for the privilege-creep diff cases; `null` otherwise |
| `manifest` | object | `{permissions: [], verbs: []}` — capability strings like `net:api.weather.com`, `fs:read:./cache`, `exec:shell`, `net:*` |
| `prompt_layer` | object | `{description: str, docstrings: []}` — the text a model reads |
| `observed_egress` | array | hosts/files/tools touched in a sandbox trace: `net:host`, `file:./path`, `tool:name` |
| `label` | object | `{malicious: bool, classes: []}` — `classes` is a subset of the taxonomy |
| `adversarial_techniques` | array | empty unless the record uses an evasion; vocab: `homoglyph_substitution`, `base64_encoding`, `hex_encoding`, `paraphrase`, `zero_width_spacing` |
| `split` | string | `"dev"` or `"test"` |

## Vulnerability taxonomy (the `classes`)

| Class | Meaning | Analyzer |
|---|---|---|
| `tool_poisoning` | tool text pushes the model to act outside its job (read secrets / exfiltrate) | prompt-layer |
| `instruction_smuggling` | injected imperative aimed at the model ("ignore previous instructions", role override) | prompt-layer |
| `homoglyph_obfuscation` | confusable / mixed-script characters hiding the words above | prompt-layer |
| `encoded_payload` | base64 / hex blob decoding to a hidden instruction | prompt-layer |
| `privilege_creep` | sensitive capability newly added between two versions | manifest |
| `undeclared_egress` | egress observed in the sandbox but never declared | behavioural |

## Validation

`src.corpus.validate_all()` checks every record against the schema
(required fields, types, no unknown fields, no duplicate `(skill_id, version)`),
that every label class is in the taxonomy, and the cross-field rule that any
record with `adversarial_techniques` must be `malicious`. The test suite runs
this over the shipped corpus.

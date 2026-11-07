# Data — Agent Verification Harness

Three US government statistical releases, retrieved as published HTML and used
verbatim. Nothing is licensed, nothing is personal, and nothing is simulated.

| Field | Value |
|---|---|
| Source | BLS and Federal Reserve public news releases |
| Documents | 3 |
| Transcripts | 3 |
| Labelled claims | 12 (6 `ok`, 3 `fabricated`, 3 `unsupported`) |
| Licence / terms of use | US Government work, not subject to copyright (17 U.S.C. § 105) |
| Access requirements | None — public web pages, no key, no registration |
| Retrieved | 2026-09-06T23:53:59Z |
| Run recorded | 2026-09-07T00:10:55Z |

## The documents

| ID | Release | URL | Chars | Numeric sentences | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `CPI` | BLS Consumer Price Index | https://www.bls.gov/news.release/cpi.nr0.htm | 24,190 | 64 | `8c8532945dda0f4f` |
| `EMPSIT` | BLS Employment Situation | https://www.bls.gov/news.release/empsit.nr0.htm | 14,714 | 40 | `20e122273575e268` |
| `H15` | Federal Reserve H.15 Selected Interest Rates | https://www.federalreserve.gov/releases/h15/ | 14,842 | 16 | `42ac9e6dc73db142` |

These rows are not transcribed by hand. They are the `documents` array of
[`results/latest-real.json`](../results/latest-real.json), written by the run
itself, so the table and the scored output cannot drift apart.

## Why these three

The grounding check in [`METHOD.md`](METHOD.md) is a shingle-overlap score, and
the condition it can be fooled by is a long document dense with numbers that are
irrelevant to the claim under test. A real CPI release is 24,000 characters with
64 numeric sentences; a three-sentence authored source never exercises that.
Choosing the documents for the property that stresses the method, rather than
for convenience, is the point.

## How the labels are built

Every label is known by construction, so no annotation step is involved and no
inter-annotator agreement needs reporting:

- **`ok`** — a sentence quoted verbatim from the document it cites.
- **`fabricated`** — that same sentence with exactly one number altered.
- **`unsupported`** — a real sentence taken from a *different* release and cited
  to this one.

`claims_are_model_output` is `false` in the results file, and that is a
limitation, not an oversight: this measures the checker, not any agent's real
error distribution. Treat the numbers as a measurement of the validation layer.

## These sources are living documents

BLS and the Federal Reserve republish these pages on a fixed schedule. The URLs
above are stable but their *contents* are not: `cpi.nr0.htm` carries the most
recent CPI release, not the one retrieved here.

Consequence, stated plainly: **re-running `python -m data.fetch` does not
reproduce this run.** It produces a new run on new documents, with different
claims and different numbers. The run behind the reported figures is pinned by
the SHA-256 values above. Anyone checking the numbers should compare against
those hashes, and anyone re-running should expect — and report — a different
result.

## Rules for this folder

1. **Never commit raw fetched documents.** `data/raw/` is git-ignored. Commit the
   manifest, the hashes, and the code that reproduces the pull.
2. **Never report a number from `data/sample/`.** Sample files exist so a page
   renders before a live pull. The harness enforces this: `src/demo.py --real`
   exits with an error rather than scoring authored transcripts as real data.
3. **Record the run.** Every reported figure needs a dated entry in
   [`results/README.md`](../results/README.md) and a hash in the results file.

## Reproduction

```bash
python -m data.fetch        # needs www.bls.gov and www.federalreserve.gov
python -m src.demo --real
```

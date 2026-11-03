# data/ — ChainTrust-Bench

Manifests, pointers and conversion code. Raw contract sources are never committed.

| Path | What it is |
|---|---|
| `solcorpus.py` | Maps the SmartBugs curated dataset's ten categories onto this benchmark's seven classes. Four categories have no counterpart and are excluded rather than forced into the nearest class; `access_control` is split three ways by reading the source, and that refinement is reported separately. |
| `benigncorpus.py` | The negative controls: 20 audited files from OpenZeppelin Contracts `v5.0.2`, entered with no labels so `Case.is_safe()` is true and a detector firing on them is charged a false positive. |
| `fetch.py` | Builds `real-corpus.jsonl` from both of the above. `--list` prints every URL first; `--verify` re-hashes the cache; `--no-benign` omits the controls. |
| `datakit.py` | Fetching with rate limiting, retries, SHA-256 and a manifest entry per file. |
| `corpus/seed.jsonl` | The authored seed cases. Used to unit-test the scorer, never reported as a result. |
| `raw/` | Never committed. Reproduce with `python -m data.fetch`. |
| `manifests/` | URL, SHA-256 and retrieval time for every file fetched, so a run is auditable and re-fetchable. |

## Reproduce

```bash
python -m data.fetch --list     # every URL this will touch, and the class mapping
python -m data.fetch            # 143 SmartBugs records -> 121 cases, + 20 controls
python -m data.fetch --verify   # re-hash everything cached
```

The 22 SmartBugs records that are dropped carry only vulnerability categories this
benchmark does not score (`bad_randomness`, `denial_of_service`, `front_running`,
`short_addresses`, `other`). They are excluded, not relabelled: scoring a
front-running case as a reentrancy miss would make a detector look worse than it is
for a bug it was never asked to find.

## Why both corpora exist

The real corpus answers "does the detector find bugs someone else wrote, and does it
stay quiet on code someone else audited". The authored corpus answers "does the
scorer compute what it claims to compute" — it is single-issue by design so a score
decomposes cleanly by class. Only the first is ever reported as a measured result.

## Scale

Current: **141 cases** — 121 vulnerable (SmartBugs curated) and 20 known-good
(OpenZeppelin `v5.0.2`).

There is no on-chain transaction corpus in this project. Any figure describing one
is not evidenced here.

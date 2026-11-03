# ChainTrust-Bench

> A smart-contract security benchmark that scores detectors per vulnerability class,
> so a tool's weaknesses are visible instead of averaged away — and that scores them
> on known-good code too, so a false-positive rate actually exists.

**Repository:** `1.0-Secure-Ai-Agent-Infrastructure` &middot; **Pillar:** Secure Digital Infrastructure

## Status

Working code with a runnable demo and **38 tests**. The benchmark runs on a real,
third-party-annotated corpus, and every figure quoted anywhere in this project traces
back to a committed results file.

Two corpora are maintained, and they are never mixed:

| Corpus | What it is | Where results land |
|---|---|---|
| **Real** | 121 vulnerable contracts from the [SmartBugs curated dataset](https://github.com/smartbugs/smartbugs-curated), annotated by its own authors, plus 20 negative controls from [OpenZeppelin Contracts](https://github.com/OpenZeppelin/openzeppelin-contracts) `v5.0.2` | `results/latest-real.json` |
| **Authored** | A small hand-written seed + hard tier, single-issue by design, kept to unit-test the scorer | `results/latest.json` |

Nothing from the authored corpus is reported as a measured result.

## The headline result

On the real corpus, both heuristic detectors raise false alarms on **9 of 20**
pieces of audited OpenZeppelin library code — a false-positive rate of **0.450** on
code the ecosystem depends on:

| Detector | Macro P | Macro R | Macro F1 | FP rate on known-good code |
|---|---|---|---|---|
| pattern-baseline | 0.353 | 0.368 | **0.273** | **0.450** |
| keyword-floor | 0.280 | 0.479 | 0.266 | 0.450 |
| null (reports nothing) | 0.000 | 0.000 | 0.000 | 0.000 |

The misfires are not random. `pattern-baseline` reports `integer_overflow` on
`Math.sol` and `SafeCast`-style arithmetic in Solidity ^0.8, where the compiler
reverts on overflow by default; it reports `missing_access_control` on `ERC20`,
`ERC721` and `VestingWallet`, which inherit the reference `Ownable`
implementation. `keyword-floor` reports both `reentrancy` and `unchecked_call` on
`Address.sol` — the library whose entire purpose is checking low-level call
return values — and four separate classes on `TimelockController`.

**Why the negative controls matter.** Before they existed, the corpus was 121
vulnerable contracts and nothing else, so `false_positive_rate_on_safe` read 0.0
for every detector. That looked like "nobody misfires" and meant "nobody was
asked". Adding true negatives also moved the headline macro-F1 from 0.281 to
0.273, because false positives on clean code now count against precision. The
per-tier figure for the SmartBugs tier alone is unchanged at 0.281, and both are
reported.

### What the negative-control label does and does not assert

These 20 files are audited, released and widely deployed, and a detector firing one
of this benchmark's seven classes on them is almost certainly wrong. That is the
claim. It is **not** a claim of formal verification, and not a claim that the files
contain no bug of any kind. The label is "known-good with respect to this
benchmark's seven classes" — the property a false-positive rate needs, and the only
one claimed. The tier is reported separately throughout, so a reader can discount it
or score the tiers apart.

## Quick start

```bash
pip install -r requirements.txt
python -m pytest tests/ -q     # 38 tests

python -m data.fetch           # pulls SmartBugs + the OpenZeppelin controls
python -m src.demo --real      # scores on the real corpus -> results/latest-real.json
python -m src.demo             # scores on the authored corpus -> results/latest.json
```

`python -m data.fetch --list` prints every URL it will touch and the category
mapping it applies. `--verify` re-hashes everything already cached. `--no-benign`
skips the negative controls, which is supported but leaves the false-positive rate
unmeasurable.

## Layout

```
README.md
data/
  |-- README.md
  |-- benigncorpus.py      # OpenZeppelin negative controls
  |-- corpus/seed.jsonl    # authored seed cases
  |-- datakit.py           # fetch, hash, manifest
  |-- fetch.py             # builds data/real-corpus.jsonl
  |-- manifests/
  |-- solcorpus.py         # SmartBugs -> benchmark class mapping
docs/
  |-- DATA.md
  |-- EVIDENCE.md
  |-- METHOD.md
requirements.txt
results/
  |-- README.md
  |-- latest.json          # authored corpus
  |-- latest-real.json     # real corpus
src/
  |-- corpus.py            # Case, CLASSES, load_corpus, corpus_stats
  |-- demo.py
  |-- detectors.py         # pattern-baseline, keyword-floor, null
  |-- scoring.py           # per-class scores, macro-average, FP rate on safe
  |-- site.py / sitekit.py
tests/
  |-- test_benign_corpus.py
  |-- test_data_layer.py
  |-- test_detectors.py
website/
  |-- index.html           # regenerated from results on every demo run
```

## How a detector plugs in

A detector is any callable that takes Solidity source and returns the set of
vulnerability classes it believes are present. That is the entire contract, which is
what lets a rule-based scanner and an LLM auditing agent be scored by the same
harness on the same cases. See `3-llm-audit-agent/`, which is scored here.

Scores are macro-averaged across classes rather than micro-averaged: a corpus is
never balanced, and a micro-average lets a detector look strong by being good at
whichever class happens to be most common.

## The website

`website/` has no build step and is regenerated from the results file on every
`python -m src.demo`, so the figures on the site and the figures the code produces
cannot drift apart. Do not edit numbers on the page by hand.

```bash
cp -r website/ ../my-2-chaintrust-bench-site && cd ../my-2-chaintrust-bench-site
git init && git add -A && git commit -m "site"
vercel deploy --prod
```

## What this benchmark does not establish

- **No language model has been scored on the full corpus.** Only the rule-based and
  symbolic detectors above have. A real-model pass over 121 contracts is slow on CPU
  and has not been run; no claim is made about what it would show.
- **No adoption, DOI, release or external user exists.** Earlier claims of a
  1.2-million-transaction corpus and two fintech adopters are not evidenced in this
  repository and must not be cited to it.
- **Twenty negative controls is a floor, not a survey.** The 0.450 false-positive
  rate is measured against this specific set of audited files; a larger or differently
  chosen control set would move it.
- The 17 authored seed cases exist to unit-test the scorer. They are not part of any
  reported score.

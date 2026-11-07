# Agent Verification Harness

> Grounding and citation checks, hallucination detection, and tamper-evident
> tool-call logging for tool-using agents.

**Repository:** `1.0-Secure-Ai-Agent-Infrastructure` &middot; **Pillar:** Cross-cutting — trustworthy AI

## Status

Working code, **32 passing tests**, and one measured run on real third-party
documents. The result below is reportable; the limits under it are part of the
result.

Scored against three US government statistical releases — BLS CPI, BLS
Employment Situation, Federal Reserve H.15 — turned into 12 claims whose labels
are known by construction. Sources, URLs and SHA-256 hashes are in
[`docs/DATA.md`](docs/DATA.md).

At the committed threshold of 0.55:

| | |
|---|---|
| Precision | **1.000** |
| Recall | **0.667** |
| F1 | **0.800** |
| False flags | **0** of 6 grounded claims |

**The split is the finding, not the F1.** A claim built by lifting a sentence
from a different release is caught every time (3 of 3). A claim built by altering
one digit in a real sentence is caught once in three — and the threshold has
nothing to do with it: all three scored 0.78–0.83, above every threshold in the
sweep. External output validation catches *provenance* failures reliably and
*numeric* fabrication poorly. [`docs/METHOD.md`](docs/METHOD.md) shows exactly
why, and what would have to change to fix it.

Last reportable run: `2026-09-07T00:10:55+00:00` · n = 12 claims. Precision 1.000
rests on four true positives; read the direction of the split, not the third
decimal place.

## Quick start

```bash
pip install -r requirements.txt
python -m pytest tests/ -q     # 32 tests
python -m src.demo             # authored-transcript smoke test -> results/latest.json
python -m src.demo --real      # the measured run      -> results/latest-real.json
```

`--real` needs `www.bls.gov` and `www.federalreserve.gov` reachable; run
`python -m data.fetch` first. Without cached documents it exits with an error
rather than scoring authored transcripts as if they were real filings.

Those two source pages are republished monthly, so a fresh fetch gives a
*different* run, not a reproduction of the one above. See
[`docs/DATA.md`](docs/DATA.md).

## Layout

```
README.md
data/
  |-- README.md
  |-- datakit.py        fetching, caching, hashing
  |-- fetch.py          python -m data.fetch
  |-- load.py           documents -> labelled transcripts
  |-- manifests/
  |-- sample/
docs/
  |-- DATA.md           sources, hashes, how labels are built
  |-- METHOD.md         the method, the result, the limits
requirements.txt
results/
  |-- README.md         every reported number, with its run date
  |-- latest-real.json  the measured run
  |-- latest.json       authored-transcript smoke test
src/
  |-- grounding.py      the scorer
  |-- harness.py        scoring + threshold sweep
  |-- toollog.py        hash-chained tool-call log
  |-- transcripts.py    the authored smoke-test transcripts
  |-- demo.py  site.py  sitekit.py
tests/
  |-- test_harness.py
  |-- test_data_layer.py
website/
  |-- README.md  index.html  results.json  vercel.json
```

- `src/` &mdash; the implementation. Nothing is learned; every step is a function
  of the text.
- `tests/` &mdash; 32 pytest cases. These guard behaviour, not just imports.
- `results/latest-real.json` &mdash; the measured run. Every figure quoted
  anywhere in this project traces back to this file or to the smoke-test file
  beside it, and `results/README.md` says which is which.
- `website/` &mdash; a self-contained static site, deployable to Vercel by copying
  the folder into its own repository. See `website/README.md`.

## The website

`website/` has no build step. To deploy it independently:

```bash
cp -r website/ ../my-agent-verification-harness-site && cd ../my-agent-verification-harness-site
git init && git add -A && git commit -m "site"
vercel deploy --prod
```

The page is regenerated from `results/latest-real.json` on every
`python -m src.demo --real`, so the figures on the site and the figures the code
produces cannot drift apart. Do not edit numbers on the page by hand.

## What this does not establish

- **Not an agent benchmark.** `claims_are_model_output` is `false`. The claims
  are constructed from real documents with known labels, so this measures the
  verification layer — not any real agent's error distribution.
- **n = 12 claims, 3 documents.** Enough to establish the provenance/numeric
  split, not enough for a precision figure to three decimals.
- **Lexical only.** Paraphrase that preserves meaning while changing wording is
  under-credited by design; that bias is stated rather than tuned away.
- **One dated snapshot**, not a mean over releases.

`results/latest.json` is the authored-transcript smoke test and is labelled
`is_synthetic: true`. Nothing from that file is cited as a measured result.

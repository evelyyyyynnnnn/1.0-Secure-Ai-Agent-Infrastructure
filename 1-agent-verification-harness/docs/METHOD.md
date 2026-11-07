# Method — Agent Verification Harness

## Problem

A tool-using agent answers in prose and cites the documents it retrieved. Two
things can go wrong independently: the claim may not be supported by anything in
those documents, and the citation attached to it may point at the wrong one. This
project answers both questions for each claim an agent emits, and reports how
often it gets the answer right.

## Why the approach is non-obvious

A verification layer is only useful if it is itself inspectable. The obvious
approach is to score groundedness with a second language model, which moves the
trust problem rather than solving it: the checker becomes one more component
whose failures you cannot see. This takes the opposite route and keeps every
step lexical and auditable, accepting weaker paraphrase handling as the price.

## Method

Implemented in [`src/grounding.py`](../src/grounding.py). Nothing here is
learned; every step is a function of the text.

**1. Normalisation.** Citation markers (`[CPI]`, `[S1]`) are stripped before any
scoring. This is not cosmetic: a marker like `[S1]` contains the digit `1`, so
leaving it in makes every correctly-cited claim appear to contain a number that
is absent from the sources, and the fabrication check in step 4 fires on all of
them. The marker also injects a token present in no source, which drags the
overlap score down. Citations are metadata about a claim, not part of it, and
they are checked separately in step 5. Remaining text is lowercased, tokenised
on `[a-z0-9]+(?:\.[0-9]+)?` so that `0.3` survives as one token, and filtered
against a 40-word stoplist.

**2. Span construction.** Each source is cut into overlapping 40-word windows at
stride 20, so a claim is *located* within a document rather than merely matched
against it, and a claim whose support straddles a window boundary is still seen
whole by the next window.

**3. Similarity.** For each window,

```
score = 0.65 * containment(claim, window) + 0.35 * unigram_coverage(claim, window)
```

where containment is the fraction of the claim's word 3-grams that appear in the
window. Containment rather than Jaccard, because a short claim can be fully
supported by a long passage and Jaccard would penalise the length of the
evidence. The unigram term keeps a claim that reorders its support from scoring
zero. The claim's score against a source is its best window; the claim's
assigned source is its best-scoring source.

**4. Number check.** Numbers appearing in the claim but in none of the retrieved
sources are collected. In practice this is the single highest-signal marker of a
fabricated figure.

**5. Verdict.** A claim is *supported* when its best score clears the threshold
**and** it introduces no unsupported number. A citation is *correct* when the
best-scoring source is among those the claim cited. The two verdicts are
reported separately, because an agent that is right about the content and wrong
about the attribution has made a different mistake from one that invented the
content.

## Baseline

The comparison is not against another system but against the threshold itself:
the same scorer is swept across thresholds 0.30–0.85 on the same claims, so the
reported operating point can be read against every other one it could have had.
The sweep is printed in full in [`results/README.md`](../results/README.md).

## Evaluation protocol

Labels are known by construction rather than annotated, which is why the
precision and recall below mean something at n=12:

| Label | Count | How it is built |
|---|---|---|
| `ok` | 6 | A sentence quoted verbatim from the document it cites |
| `fabricated` | 3 | The same sentence with exactly one number altered |
| `unsupported` | 3 | A real sentence from a *different* release, cited to this one |

There is no train/test split because nothing is fitted. The threshold is
committed in the source at 0.55 and the sweep shows the result is flat across
0.30–0.75, so the operating point is not tuned to the sample.

## What the run found

At the committed threshold of 0.55, on the documents recorded in
[`DATA.md`](DATA.md): **precision 1.000, recall 0.667, F1 0.800**, with zero of
six grounded claims falsely flagged.

The headline number is less interesting than the split, and the split is the
reason this project exists:

| Failure mode | Caught | Caught by |
|---|---|---|
| Provenance — sentence lifted from another release | **3 of 3** | the similarity score |
| Numeric — one digit altered in a real sentence | **1 of 3** | the number check alone |

**External output validation catches provenance failures reliably and numeric
fabrication poorly, and the threshold has nothing to do with it.** All three
fabricated claims scored 0.78–0.83, above *every* threshold in the sweep, because
altering one digit leaves the surrounding sentence lexically intact. The
similarity score contributed nothing to catching any of them. The one that was
caught was caught solely by the number check, which fired because the invented
figure (`1.8`) appeared in none of the retrieved documents.

The two misses show the limit of that check as implemented. It pools numbers
across *all* retrieved sources, so an altered digit that happens to occur in any
other document passes:

- `"...unemployment rate for people who are Asian declined to 3.2 percent"` —
  score 0.827, no unsupported number, not flagged.
- `"Prior to March 2, 2016, the EFFR was a volume-weighted mean..."` —
  score 0.783, no unsupported number, not flagged.

Raising the threshold to 0.85 does reach F1 1.000 on this sample, but it gets
there by flagging on surface dissimilarity rather than on evidence, which would
collapse precision on any genuine paraphrase. That figure is in the sweep and is
deliberately not the headline.

The actionable form of this finding: a number-presence check must be scoped to
the source the claim actually cites, not to the union of everything retrieved.
That is a change to the mitigation, not to the threshold.

## Limitations

- **n = 12 claims across 3 documents.** Precision 1.000 rests on four true
  positives. The direction of the provenance/numeric split is the result; the
  third decimal place is not.
- **Claims are constructed, not model output.** `claims_are_model_output` is
  `false` in the results file. This measures the checker against known-label
  claims; it does not measure any real agent's error distribution.
- **Lexical only.** Paraphrase that preserves meaning while changing wording is
  under-credited by design. Stated rather than tuned away.
- **Sentence-granular claims.** `split_claims` splits on sentence boundaries,
  which is coarse; a multi-clause sentence that is half supported is scored as
  one unit.
- **Single-run snapshot.** The sources are living documents (see
  [`DATA.md`](DATA.md)); this is one dated, hash-pinned run, not a mean over
  releases.

## Reproduction

```bash
pip install -r requirements.txt
python -m pytest tests/ -q            # 32 tests
python -m data.fetch                  # needs www.bls.gov, www.federalreserve.gov
python -m src.demo --real             # rewrites results/latest-real.json + website/
```

`python -m src.demo` without `--real` runs the authored-transcript smoke test and
writes `results/latest.json`; it is not the measured result. The harness refuses
to score real-data output from authored transcripts, so the two cannot be
confused.

Note that `data.fetch` retrieves the *current* releases. Because BLS and Federal
Reserve republish these pages on a schedule, a fetch today yields different
documents, different claims and different numbers from the run recorded here —
an equally valid run, not a reproduction of this one. The run that produced the
figures above is pinned by SHA-256 in `results/latest-real.json`.

# Method — ChainTrust-Bench

> **Not yet written.** This file must state the method before the project can
> be cited as evidence.

## Problem

A smart-contract security benchmark at the 1.2M-transaction scale, released as a named, versioned dataset with a DOI and a public leaderboard.

## Why the approach is non-obvious

Detector comparisons are usually reported as one pooled accuracy figure, which
lets a tool that finds only the most common bug class look broadly competent.
Scoring per vulnerability class and macro-averaging removes that cover, and
adding audited contracts as negative controls makes the false-positive rate
visible — a number most detector write-ups omit entirely.

## Method

_State the approach, the modelling choices, and the assumptions. A reviewer with
domain knowledge but no context should be able to follow it end to end._

## Baseline

_Name the baseline this is measured against. Without one, the result is a number
with nothing to compare it to._

Suggested baseline sources: 3.0-Financial-Ai-Systems — previous/project-2/contract-audit

## Evaluation protocol

_State the split, the held-out set, and how out-of-sample performance is
measured. Report calibration and uncertainty where the domain calls for it._

## Reproduction

```
# commands that take a reader from a clean checkout to the reported numbers
```

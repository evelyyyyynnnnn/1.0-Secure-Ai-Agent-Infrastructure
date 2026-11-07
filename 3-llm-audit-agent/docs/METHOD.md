# Method — LLM Audit Agent

> **Not yet written.** This file must state the method before the project can
> be cited as evidence.

## Problem

Ship the Prof. Belal Alsinglawi proposal as code: an LLM-based smart-contract auditing agent, benchmarked against the rule-based Contract Audit tool in 3.0.

## Why the approach is non-obvious

An agent that re-checks its own output usually reports the same findings with
more confidence. The question worth measuring is whether a second pass actually
drops what it cannot substantiate, so the metric here is the change in review
volume and false alarms between passes, not a self-reported confidence score.

## Method

_State the approach, the modelling choices, and the assumptions. A reviewer with
domain knowledge but no context should be able to follow it end to end._

## Baseline

_Name the baseline this is measured against. Without one, the result is a number
with nothing to compare it to._

Suggested baseline sources: previous/2.0-Prof-Belal Alsinglawi's-Project (proposal document)

## Evaluation protocol

_State the split, the held-out set, and how out-of-sample performance is
measured. Report calibration and uncertainty where the domain calls for it._

## Reproduction

```
# commands that take a reader from a clean checkout to the reported numbers
```

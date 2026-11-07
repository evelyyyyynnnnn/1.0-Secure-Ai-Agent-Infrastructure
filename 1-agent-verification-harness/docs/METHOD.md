# Method — Agent Verification Harness

> **Not yet written.** This file must state the method before the project can
> be cited as evidence.

## Problem

Grounding and citation checks, tool-call audit logging, and hallucination detection for tool-using agents.

## Why the approach is non-obvious

A verification layer is only useful if it is itself inspectable. The obvious
approach is to score groundedness with a second language model, which moves the
trust problem rather than solving it: the checker becomes one more component
whose failures you cannot see. This takes the opposite route and keeps every
step lexical and auditable, accepting weaker paraphrase handling as the price.

## Method

_State the approach, the modelling choices, and the assumptions. A reviewer with
domain knowledge but no context should be able to follow it end to end._

## Baseline

_Name the baseline this is measured against. Without one, the result is a number
with nothing to compare it to._

Suggested baseline sources: to be identified

## Evaluation protocol

_State the split, the held-out set, and how out-of-sample performance is
measured. Report calibration and uncertainty where the domain calls for it._

## Reproduction

```
# commands that take a reader from a clean checkout to the reported numbers
```

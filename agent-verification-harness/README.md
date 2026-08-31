# Agent Verification Harness

> **Status: scaffold.** Structure only — no method, data or result is claimed
> yet. Every "not yet measured" below is a real gap, not a placeholder to be
> filled in with an estimate.

**Repository:** `1.0-Secure-Ai-Agent-Infrastructure`
**NIW pillar (Dhanasar prong 1):** Cross-cutting — trustworthy AI
**Evidence value:** CORE — the literal thesis of Section 2

## Core idea

Grounding and citation checks, tool-call audit logging, and hallucination detection for tool-using agents.

## Why it earns its place

This is the literal thesis of Section 2 of the petition (verification, robustness, interpretability). No repo currently implements it.

## The petition claim it supports

> Verification, robustness and interpretability of tool-using AI agents (Petition Section 2).

**What the portfolio shows today:** Nothing in any of the five repositories implements agent verification.

**Action required:** Build on public data only, given the overlap with your employer. Keep it visibly separate from employer work and get it cleared.

No prior work in the portfolio — this starts from scratch.

## Petition-grade checklist

A project counts as petition-grade only when all five are true. None are yet.

- [ ] Original work, authored here
- [ ] A stated method (`docs/METHOD.md`)
- [ ] Real data at a stated scale (`docs/DATA.md` — target: Public agent-trajectory datasets only)
- [ ] A measured result (`results/README.md`)
- [ ] A README a reviewer can follow, start to finish

## Measured results

Target scale: **Public agent-trajectory datasets only**

| Metric | Baseline | Result | Out-of-sample |
|---|---|---|---|
| Hallucination detection AUC | _not yet measured_ | _not yet measured_ | _pending_ |
| Citation-grounding accuracy | _not yet measured_ | _not yet measured_ | _pending_ |
| Tool-call audit completeness | _not yet measured_ | _not yet measured_ | _pending_ |
| Refusal-behaviour calibration | _not yet measured_ | _not yet measured_ | _pending_ |

Populate this from `results/`. Do not cite any number in the petition that does
not appear here with a run date behind it.

## Layout

```
agent-verification-harness/
├── README.md        this file
├── docs/
│   ├── METHOD.md    what the method is and why it is non-obvious
│   ├── DATA.md      source, scale, licence, and how to reproduce the pull
│   └── EVIDENCE.md  the petition claim, the gap, and the exhibit it becomes
├── src/             implementation
├── data/            pointers and manifests — never raw licensed data
├── results/         measured results, run logs, and the baseline comparison
└── tests/           tests that establish the result is reproducible
```

---
Scaffold generated from `NIW_Project_Portfolio_and_Gap_Plan.xlsx` (sheets: Repo Build-Out Plan, Core Ideas at a Glance, NIW Claim vs Repo Evidence, Notion 创业 Alignment). Structure only — no results are claimed here yet.

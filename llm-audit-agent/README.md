# LLM Audit Agent

> **Status: scaffold.** Structure only — no method, data or result is claimed
> yet. Every "not yet measured" below is a real gap, not a placeholder to be
> filled in with an estimate.

**Repository:** `1.0-Secure-Ai-Agent-Infrastructure`
**NIW pillar (Dhanasar prong 1):** Secure Digital Infrastructure
**Evidence value:** CORE — highest-value item in the whole portfolio

## Core idea

Ship the Prof. Belal Alsinglawi proposal as code: an LLM-based smart-contract auditing agent, benchmarked against the rule-based Contract Audit tool in 3.0.

## Why it earns its place

Turns a proposal into an artifact and produces the measured workload reduction the petition currently asserts. Its stated deliverables — a US provisional patent filing, an installable open-source package, and an evaluable dataset — are deliberately third-party verifiable, which is precisely what USCIS weighs.

## The petition claim it supports

> LLM-based smart-contract auditing agents reduced manual audit workload by 65%.

**What the portfolio shows today:** The only auditing tool in the repos is rule-based static analysis. The LLM agent exists as a proposal document sent 2026-08-25.

**Action required:** Build the agent, benchmark against the rule-based tool, and let the measured delta define the number you cite. Treat its timeline as the petition's critical path.

Prior work to build on: `previous/2.0-Prof-Belal Alsinglawi's-Project (proposal document)`.

## Petition-grade checklist

A project counts as petition-grade only when all five are true. None are yet.

- [ ] Original work, authored here
- [ ] A stated method (`docs/METHOD.md`)
- [ ] Real data at a stated scale (`docs/DATA.md` — target: Benchmark suite from chaintrust-bench/)
- [ ] A measured result (`results/README.md`)
- [ ] A README a reviewer can follow, start to finish

## Measured results

Target scale: **Benchmark suite from chaintrust-bench/**

| Metric | Baseline | Result | Out-of-sample |
|---|---|---|---|
| Manual audit workload reduction (measured, not asserted) | _not yet measured_ | _not yet measured_ | _pending_ |
| Precision / recall vs. the rule-based baseline | _not yet measured_ | _not yet measured_ | _pending_ |
| Time-to-audit per contract | _not yet measured_ | _not yet measured_ | _pending_ |
| Analyst confirmation rate | _not yet measured_ | _not yet measured_ | _pending_ |

Populate this from `results/`. Do not cite any number in the petition that does
not appear here with a run date behind it.

## Layout

```
llm-audit-agent/
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

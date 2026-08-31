# ChainTrust-Bench

> **Status: scaffold.** Structure only — no method, data or result is claimed
> yet. Every "not yet measured" below is a real gap, not a placeholder to be
> filled in with an estimate.

**Repository:** `1.0-Secure-Ai-Agent-Infrastructure`
**NIW pillar (Dhanasar prong 1):** Secure Digital Infrastructure
**Evidence value:** CORE — closes the largest credibility gap in the filing

## Core idea

A smart-contract security benchmark at the 1.2M-transaction scale, released as a named, versioned dataset with a DOI and a public leaderboard.

## Why it earns its place

The petition already names this tool as adopted by two fintech startups. Right now the name points at nothing. This single repo closes the largest credibility gap in the filing.

## The petition claim it supports

> Security benchmarks analysing over 1.2 million on-chain blockchain transactions; ChainTrust-Bench released and adopted by two fintech startups.

**What the portfolio shows today:** No repository anywhere is named ChainTrust-Bench. The only auditing tool in the portfolio is 3.0 Contract Audit, validated on six planted bugs plus one safe contract.

**Action required:** Highest priority. Release ChainTrust-Bench as a named, versioned, DOI-backed dataset; obtain written confirmation from the two adopting startups (Exhibit 20).

Prior work to build on: `3.0-Financial-Ai-Systems — previous/project-2/contract-audit`.

## Petition-grade checklist

A project counts as petition-grade only when all five are true. None are yet.

- [ ] Original work, authored here
- [ ] A stated method (`docs/METHOD.md`)
- [ ] Real data at a stated scale (`docs/DATA.md` — target: 1,200,000+ on-chain transactions)
- [ ] A measured result (`results/README.md`)
- [ ] A README a reviewer can follow, start to finish

## Measured results

Target scale: **1,200,000+ on-chain transactions**

| Metric | Baseline | Result | Out-of-sample |
|---|---|---|---|
| Detection rate by vulnerability class | _not yet measured_ | _not yet measured_ | _pending_ |
| False-positive rate | _not yet measured_ | _not yet measured_ | _pending_ |
| Leaderboard rank vs. published baselines | _not yet measured_ | _not yet measured_ | _pending_ |
| Dataset downloads / DOI citations | _not yet measured_ | _not yet measured_ | _pending_ |

Populate this from `results/`. Do not cite any number in the petition that does
not appear here with a run date behind it.

## Layout

```
chaintrust-bench/
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

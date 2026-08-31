# Blockchain Shared Charging

> **Status: scaffold.** Structure only — no method, data or result is claimed
> yet. Every "not yet measured" below is a real gap, not a placeholder to be
> filled in with an estimate.

**Repository:** `1.0-Secure-Ai-Agent-Infrastructure`
**NIW pillar (Dhanasar prong 1):** Secure Digital Infrastructure
**Evidence value:** Unknown — undocumented until rewritten

## Core idea

Rewrite and document the existing shared-charging settlement work, or move it out of the repository.

## Why it earns its place

An undocumented folder in the repo that carries your star count is a liability, not an asset.

## The petition claim it supports

> Open-source tools have garnered 150+ GitHub stars and 10+ institutional users.

**What the portfolio shows today:** 191 stars, 31 forks, 23 watchers — on 4 commits, two folders, and no README at any level. The star-to-substance ratio is conspicuous.

**Action required:** Write a README stating problem, method, data scale and result before anything else. If it is the on-chain settlement work behind the smart-bracelet patent, say so explicitly and link the patent certificate (Exhibit 14). Otherwise move it out.

Prior work to build on: `previous/1.0-blockchain-shared-charging`.

## Petition-grade checklist

A project counts as petition-grade only when all five are true. None are yet.

- [ ] Original work, authored here
- [ ] A stated method (`docs/METHOD.md`)
- [ ] Real data at a stated scale (`docs/DATA.md` — target: To be stated — currently unrecorded)
- [ ] A measured result (`results/README.md`)
- [ ] A README a reviewer can follow, start to finish

## Measured results

Target scale: **To be stated — currently unrecorded**

| Metric | Baseline | Result | Out-of-sample |
|---|---|---|---|
| Settlement throughput | _not yet measured_ | _not yet measured_ | _pending_ |
| Transaction cost per session | _not yet measured_ | _not yet measured_ | _pending_ |
| Correctness under adversarial conditions | _not yet measured_ | _not yet measured_ | _pending_ |

Populate this from `results/`. Do not cite any number in the petition that does
not appear here with a run date behind it.

## Layout

```
blockchain-shared-charging/
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

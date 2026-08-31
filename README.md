# 1.0 — Secure AI Agent Infrastructure

Research prototypes and infrastructure tools for secure AI agent systems using LLMs, blockchain and distributed architectures.

Part of a five-repository portfolio supporting the endeavor described in the
EB2-NIW petition: **optimization-driven, system-level decision frameworks** —
integrating operations research, mathematical optimization and applied AI — for
domains where a wrong decision carries systemic consequences. The three pillars
are financial stability, healthcare safety and secure digital infrastructure.

| | |
|---|---|
| Petition-grade projects today | 1 petition-grade project (the Belal agent, still a proposal) |
| Verdict | **Needs 3 more** |

> "Petition-grade" means: original work, a stated method, real data at a stated
> scale, a measured result, and a README a reviewer can follow. Counts exclude
> duplicates, forks of third-party work, retired projects, and asset-only
> folders.

## Projects

| Folder | Project | Pillar | Evidence value |
|---|---|---|---|
| [`chaintrust-bench/`](chaintrust-bench/) | ChainTrust-Bench | Secure Digital Infrastructure | CORE — closes the largest credibility gap in the filing |
| [`llm-audit-agent/`](llm-audit-agent/) | LLM Audit Agent | Secure Digital Infrastructure | CORE — highest-value item in the whole portfolio |
| [`agent-verification-harness/`](agent-verification-harness/) | Agent Verification Harness | Cross-cutting — trustworthy AI | CORE — the literal thesis of Section 2 |
| [`blockchain-shared-charging/`](blockchain-shared-charging/) | Blockchain Shared Charging | Secure Digital Infrastructure | Unknown — undocumented until rewritten |

## What each one is

### 1. ChainTrust-Bench — [`chaintrust-bench/`](chaintrust-bench/)

A smart-contract security benchmark at the 1.2M-transaction scale, released as a named, versioned dataset with a DOI and a public leaderboard.

*Why it earns its place:* The petition already names this tool as adopted by two fintech startups. Right now the name points at nothing. This single repo closes the largest credibility gap in the filing.

*Target scale:* 1,200,000+ on-chain transactions

### 2. LLM Audit Agent — [`llm-audit-agent/`](llm-audit-agent/)

Ship the Prof. Belal Alsinglawi proposal as code: an LLM-based smart-contract auditing agent, benchmarked against the rule-based Contract Audit tool in 3.0.

*Why it earns its place:* Turns a proposal into an artifact and produces the measured workload reduction the petition currently asserts. Its stated deliverables — a US provisional patent filing, an installable open-source package, and an evaluable dataset — are deliberately third-party verifiable, which is precisely what USCIS weighs.

*Target scale:* Benchmark suite from chaintrust-bench/

### 3. Agent Verification Harness — [`agent-verification-harness/`](agent-verification-harness/)

Grounding and citation checks, tool-call audit logging, and hallucination detection for tool-using agents.

*Why it earns its place:* This is the literal thesis of Section 2 of the petition (verification, robustness, interpretability). No repo currently implements it.

*Target scale:* Public agent-trajectory datasets only

### 4. Blockchain Shared Charging — [`blockchain-shared-charging/`](blockchain-shared-charging/)

Rewrite and document the existing shared-charging settlement work, or move it out of the repository.

*Why it earns its place:* An undocumented folder in the repo that carries your star count is a liability, not an asset.

*Target scale:* To be stated — currently unrecorded

## Repository layout

```
1.0-Secure-Ai-Agent-Infrastructure/
├── chaintrust-bench/
├── llm-audit-agent/
├── agent-verification-harness/
├── blockchain-shared-charging/
└── previous/        everything that was here before this restructure
```

Each project folder carries the same skeleton: `README.md`, `docs/`
(METHOD, DATA, EVIDENCE), `src/`, `data/`, `results/`, `tests/`.

## Ground rules

1. **No number without a run log.** Anything cited in the petition must appear
   in that project's `results/README.md` with a run date behind it.
2. **No simulated data under a real claim.** Sample data lives in
   `data/sample/`, labelled, and is never the source of a cited figure.
3. **Adoption must be documentable** — named institutions, dated
   correspondence, registry statistics. Never an inflated count.
4. **Third-party and forked code stays labelled** and is never counted.

## previous/

Everything that lived at the top level before this restructure is preserved
under [`previous/`](previous/) with nothing deleted. See
[`previous/README.md`](previous/README.md) for the inventory and the disposition
of each item.

---
Scaffold generated from `NIW_Project_Portfolio_and_Gap_Plan.xlsx` (sheets: Repo Build-Out Plan, Core Ideas at a Glance, NIW Claim vs Repo Evidence, Notion 创业 Alignment). Structure only — no results are claimed here yet.

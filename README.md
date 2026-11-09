# 1.0 — Secure AI Agent Infrastructure

[![tests](https://github.com/evelyyyyynnnnn/1.0-Secure-Ai-Agent-Infrastructure/actions/workflows/tests.yml/badge.svg)](https://github.com/evelyyyyynnnnn/1.0-Secure-Ai-Agent-Infrastructure/actions/workflows/tests.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24094759.svg)](https://doi.org/10.5281/zenodo.24094759)

Reproducible research prototypes for one question: **can an autonomous agent be
trusted with a security decision, and would you know if it could not?**

Three projects, each taking one part of that question, each measured on data
published by a third party, and each reporting what did not work next to what
did. Part of a five-repository portfolio on verifiable AI for high-stakes
decisions, alongside healthcare safety (`2.0`), financial stability (`3.0`),
decision auditing (`4.0`) and shared tooling (`5.0`).

| | |
|---|---|
| Projects with measured results | **3** |
| Tests across the three suites | **88** |
| Running on real third-party data | **3 of 3** |
| Most recent reportable run | 2026-09-07 |

## Projects

| Folder | Project | What it measures | Tests |
|---|---|---|---|
| [`1-agent-verification-harness/`](1-agent-verification-harness/) | Agent Verification Harness | Whether a grounding check catches an agent's bad claims without flagging its good ones | 32 |
| [`2-chaintrust-bench/`](2-chaintrust-bench/) | ChainTrust-Bench | How well smart-contract detectors score *per vulnerability class*, and how often they misfire on audited code | 38 |
| [`3-llm-audit-agent/`](3-llm-audit-agent/) | LLM Audit Agent | Whether an auditing agent that re-checks itself actually drops what it cannot verify | 18 |

## What each one found

### 1. Agent Verification Harness — [`1-agent-verification-harness/`](1-agent-verification-harness/)

Three real US government statistical releases (BLS CPI, BLS Employment
Situation, Federal Reserve H.15) are turned into twelve claims whose truth is
known *by construction*: supported claims are quoted verbatim, fabricated ones
are the same sentence with a single number altered, and unsupported ones are
real sentences lifted from a different release and cited to this one.

**Precision 1.000, recall 0.667, F1 0.800** at the committed threshold of 0.55,
with zero good claims falsely flagged. The split is the finding: a claim citing
the wrong source is caught every time (3 of 3), a claim where one digit was
changed is caught once in three. The threshold is not what decides it: all
three altered-digit claims scored 0.78-0.83, above every threshold swept.

### 2. ChainTrust-Bench — [`2-chaintrust-bench/`](2-chaintrust-bench/)

A benchmark that scores detectors per vulnerability class and then
macro-averages, so a detector that only finds the common bug cannot hide behind
a high overall accuracy. 121 vulnerable contracts from the SmartBugs curated
corpus across seven classes, plus 20 negative controls from OpenZeppelin
Contracts `v5.0.2`.

**Both heuristic detectors raise false alarms on 9 of 20 pieces of audited
OpenZeppelin library code** — a false-positive rate of 0.450. The rule baseline
reports `integer_overflow` on `Math.sol` under Solidity ^0.8, where the compiler
reverts on overflow by default, and `missing_access_control` on contracts that
inherit the reference `Ownable` implementation. Per class, the baseline finds
unchecked calls reasonably well (F1 0.60) and reentrancy not at all (0 of 31).
That headroom is the reason the benchmark exists.

### 3. LLM Audit Agent — [`3-llm-audit-agent/`](3-llm-audit-agent/)

A four-stage auditing agent — understand, plan, classify, verify — where every
stage's reply is written into a hash-chained trail with its backend, latency and
reply size. The verify stage re-reads each finding against the source and
discards what it cannot confirm.

On a real open language model (`qwen2.5-coder:7b`, served locally) the full four
stages ran end to end over one contract in **68.3 s**, confirming two real
issues and **dropping two findings it could not substantiate** — both of which
reasoned about what the contract might do if someone later changed it. On the
121-contract corpus with a deterministic backend the agent trails the rule
baseline on macro-F1 (0.256 against 0.281) while cutting review items from 105
to 59 and false alarms from 68 to 28, at a cost of six more missed contracts.
Both views are reported and neither was tuned.

## Repository layout

```
1.0-Secure-Ai-Agent-Infrastructure/
├── 1-agent-verification-harness/
├── 2-chaintrust-bench/
├── 3-llm-audit-agent/
├── 4-future/                     # collaboration proposal + a runnable skeleton
├── historical-archive/           # earlier work, kept readable, not cited
└── scripts/
```

Every project carries the same skeleton: `README.md`, `src/`, `data/`,
`results/`, `tests/`, `website/`. Raw data is never committed — each project's
`data/MANIFEST.json` records the URL, SHA-256 and retrieval time of every input,
so a reviewer can re-fetch the same bytes.

[`4-future/`](4-future/) holds a research collaboration proposal and a runnable
Direction-1 skeleton (agent-skill and MCP supply-chain screening). It is
outreach-stage material, not an implemented result, and its own README says so.

## Ground rules

1. **No number without a run log.** Any figure quoted anywhere traces to that
   project's `results/` file, with the run date inside it.
2. **No simulated data under a real claim.** Authored and sample data is
   labelled `is_synthetic: true` and is never the source of a reported figure.
3. **Adoption must be documentable** — named institutions, dated
   correspondence, registry statistics — or it is not claimed. None of these
   projects currently has adoption, a DOI, a release or an external user, and
   none claims to.
4. **Third-party and forked code stays labelled** and is never counted.

## Reproduce

```bash
cd <project> && pip install -r requirements.txt
python -m pytest -q
python -m data.fetch        # where the project has a fetch step
python -m src.demo --real   # writes results/latest-real.json
```

## Licence

[Apache License 2.0](LICENSE). The code, benchmarks and documentation in this
repository may be reused, modified and redistributed under its terms, including
by projects that need a patent grant to incorporate them.

Third-party corpora kept under `*/data/` carry their own terms and are labelled
where they appear: the SmartBugs curated dataset and OpenZeppelin Contracts in
`2-chaintrust-bench/`, and US Government releases in
`1-agent-verification-harness/`, which are not subject to copyright
(17 U.S.C. § 105).

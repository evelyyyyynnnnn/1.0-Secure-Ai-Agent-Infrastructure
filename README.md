# Secure AI Agent Infrastructure

Research prototypes and infrastructure tools for building secure AI agent
systems using large language models, blockchain technologies, and distributed
architectures.

Two directions that meet in the middle:

- **Securing the agent** — identity, authorization, runtime policy,
  supply-chain screening, and audit for autonomous systems that call tools.
- **Agents that secure infrastructure** — using those agents to audit smart
  contracts and tokenized instruments.

## Scope boundary

This repository holds security work. Financial modelling, market analytics and
portfolio tooling live in `3.0-Financial-Ai-Systems`, even when the subject
matter is on-chain. The test is what the project produces: a security finding
belongs here, a market estimate does not.

## Projects

| | Project | Focus |
| --- | --- | --- |
| 1.0 | `1.0-blockchain-shared-charging` | Early V2G registration contracts. Retained as known-answer fixtures for 5.0. |
| 2.0 | `2.0-Prof-Belal Alsinglawi's-Project` | External research collaboration. |
| 3.0 | `3.0-Agent-Skill-Supply-Chain-Security` | Screening third-party MCP servers and agent skills. |
| 4.0 | `4.0-Agent-Identity-And-Audit-Trail` | Per-agent identity, scoped authorization, tamper-evident logs. |
| 5.0 | `5.0-Smart-Contract-Audit-Agent` | Multi-stage LLM auditing agent with exploit-path planning. |
| 6.0 | `6.0-Tokenized-Asset-Contract-Security` | Contract-level control and restriction audit for tokenized RWAs. |
| 7.0 | `7.0-ChainTrust-Bench` | Labelled DeFi exploit corpus and evaluation harness. |
| 8.0 | `8.0-Agent-Guardrail-Toolkit` | Embeddable runtime policy layer shared by the projects above. |
| 9.0 | `9.0-Coding-Agent-Security` | Controls for autonomous coding agents in regulated environments. |
| 10.0 | `10.0-Agent-Payment-Trust` | Mandate and identity controls for agents that transact. |

## Dependency shape

`8.0` is the enforcement primitive; `4.0` consumes its traces; `9.0` applies
both to the coding-agent case. `3.0` screens what enters an agent's toolset.
`5.0` is the auditing agent, `7.0` is how it is measured, and `6.0` is an
applied contract-security domain. `10.0` is the bridge to the finance
repository and the earliest-stage project here.

## Status

`3.0` through `10.0` are scaffolds: scope and design notes, no implementation.

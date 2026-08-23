# Secure AI Agent Infrastructure

Research prototypes and infrastructure tools for building secure AI agent
systems using large language models, blockchain technologies, and distributed
architectures.

The repository covers two directions that meet in the middle:

- **Securing the agent** — identity, authorization, runtime policy, supply-chain
  screening, and audit for autonomous systems that call tools.
- **Agents that secure infrastructure** — using those same agents to audit smart
  contracts and on-chain financial instruments.

## Projects

| | Project | Focus |
| --- | --- | --- |
| 1.0 | `1.0-blockchain-shared-charging` | Early V2G registration contracts. Retained as known-answer fixtures for 5.0. |
| 2.0 | `2.0-Prof-Belal Alsinglawi's-Project` | External research collaboration. |
| 3.0 | `3.0-Agent-Skill-Supply-Chain-Security` | Screening third-party MCP servers and agent skills. |
| 4.0 | `4.0-Agent-Identity-And-Audit-Trail` | Per-agent identity, scoped authorization, tamper-evident logs. |
| 5.0 | `5.0-Smart-Contract-Audit-Agent` | Multi-stage LLM auditing agent with exploit-path planning. |
| 6.0 | `6.0-Tokenized-Fixed-Income-Security` | Control, compliance and liquidity analytics for tokenized debt. |
| 7.0 | `7.0-Private-Credit-Data-Provenance` | Span-anchored, verifiable extraction from credit documents. |
| 8.0 | `8.0-Agent-Guardrail-Toolkit` | Embeddable runtime policy layer shared by the projects above. |

## Dependency shape

`8.0` is the enforcement primitive; `4.0` consumes its traces. `3.0` screens what
enters an agent's toolset. `5.0` is the auditing agent, and `6.0` and `7.0` are
its two applied targets — on-chain instruments and private-market documents.

## Status

`3.0` through `8.0` are scaffolds: scope and design notes, no implementation yet.

# 9.0 — Coding Agent Security

Security controls for autonomous coding agents operating inside regulated
engineering environments.

## Problem

Coding agents have moved from suggesting completions to editing repositories,
running builds, opening pull requests, and executing shell commands. In a
regulated environment that makes them a code-integrity risk with no established
control model: an agent that can write to a repository and trigger CI can move
code to production through a path no reviewer watched.

The failure modes are distinct from chat-agent failures:

- **Instruction injection through the codebase itself** — a comment, a README,
  an issue body, or a dependency's docstring that the agent reads as direction.
- **Credential reach** — agents inherit developer environments, and developer
  environments hold production credentials.
- **Silent scope expansion** — an agent asked to fix a test edits configuration,
  a lockfile, or a CI workflow to make the test pass.
- **Provenance loss** — which changes were machine-authored, under whose
  authority, and reviewed by whom.

## Scope

- **Repository-scoped policy** — path-level write restrictions; CI workflow and
  lockfile changes require explicit human authorization.
- **Injection screening on repository content** — treat file content the agent
  reads as untrusted input, not as instruction.
- **Diff attribution** — machine-authored changes carry signed provenance
  through to the pull request.
- **Blast-radius limits** — no direct push to protected branches; credentials
  scoped to the task rather than inherited from the developer session.

## Relationship to this repository

Consumes the policy engine from `8.0-Agent-Guardrail-Toolkit` and emits traces
into `4.0-Agent-Identity-And-Audit-Trail`. The contribution here is the
repository-specific policy vocabulary, not a second enforcement engine.

## Status

Scaffold. No implementation yet.

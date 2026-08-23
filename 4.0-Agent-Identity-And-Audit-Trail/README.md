# 4.0 — Agent Identity, Authorization & Tamper-Evident Audit Trail

Identity and accountability primitives for autonomous agents acting on behalf of
a principal in a regulated environment.

## Problem

Agents are commonly deployed as generic service accounts: no dedicated identity,
no scoped authorization, no durable record of what the agent actually did. That
breaks three things at once — least privilege, incident forensics, and the
retention obligations that regulated sectors already impose on advice and
trading systems.

## Scope

- **Agent identity** — per-agent credentials distinct from the human principal,
  with delegation chains that record who authorized what, and for how long.
- **Scoped authorization** — capability tokens bound to a task, expiring on
  completion; deny-by-default tool access.
- **Revocation** — fast credential revocation for a compromised or misbehaving
  agent, including revocation that must propagate to peers.
- **Tamper-evident log** — append-only, hash-chained action log; optional
  on-chain anchoring so a third party can verify the log was not rewritten after
  the fact. Anchor digests only, never payloads.
- **Replay** — reconstruct an agent's decision path from the log for audit.

## Design constraints

- The log must be verifiable by someone who does not trust the operator.
- Anchoring must not put user or client data on a public ledger.
- Retention horizons in regulated sectors run to several years; storage and
  verification cost must be linear and bounded.

## Status

Scaffold. No implementation yet.

# 6.0 — Tokenized Fixed-Income Security & Compliance Analytics

On-chain risk, liquidity and compliance analytics for tokenized debt: treasuries,
money-market funds, and tokenized private credit.

## Problem

Tokenized real-world assets moved from pilot to production faster than the
tooling around them. Value is concentrated in yield-bearing instruments, but
holders have no standard way to answer basic questions: who can freeze or claw
back this token, is the transfer-restriction logic actually enforced on-chain,
what is real secondary depth versus wash volume, and does the redemption path
survive the issuer being unavailable.

## Scope

- **Contract-level control audit** — enumerate privileged roles (mint, burn,
  freeze, force-transfer, upgrade) and surface who holds them.
- **Transfer-restriction verification** — check that the whitelist/permissioning
  logic actually gates transfers, including via approvals and intermediaries.
- **Upgradeability risk** — proxy patterns, admin key custody, timelock presence.
- **Liquidity analytics** — realised depth, holder concentration, redemption
  latency observed on-chain.
- **Reserve attestation checks** — reconcile claimed backing against attestation
  cadence and on-chain supply.

## Status

Scaffold. No implementation yet.

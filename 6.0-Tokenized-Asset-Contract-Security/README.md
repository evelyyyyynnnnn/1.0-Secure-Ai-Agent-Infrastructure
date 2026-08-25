# 6.0 — Tokenized Asset Contract Security

Smart-contract security analysis for tokenized real-world assets: treasuries,
money-market funds, and tokenized private credit.

## Scope boundary

This project covers the **contract security** of tokenized instruments. Market
analytics on the same instruments — liquidity depth, holder concentration,
sentiment, reserve reconciliation — are financial analysis rather than security
work and live in the `3.0-Financial-Ai-Systems` repository.

## Problem

Tokenization moved from pilot to production faster than the review tooling
around it. A holder has no standard way to answer the questions that decide
whether the instrument is safe to hold: who can freeze or claw back this token,
is the transfer-restriction logic actually enforced on-chain rather than merely
declared, who controls the upgrade path, and does redemption still work if the
issuer stops cooperating.

These are the same questions the auditing agent in 5.0 asks of any contract.
The difference here is that the answers carry regulatory weight, because the
instrument represents a claim on a real asset.

## Scope

- **Privileged role enumeration** — mint, burn, freeze, force-transfer, pause,
  upgrade. Who holds each, and through how many hops of indirection.
- **Transfer-restriction verification** — prove the permissioning logic actually
  gates transfers, including paths through approvals, delegates and
  intermediary contracts, not just the direct path.
- **Upgradeability risk** — proxy pattern identification, admin key custody,
  timelock presence and whether the timelock can be bypassed.
- **Redemption-path liveness** — whether the redemption function remains
  callable under issuer non-cooperation, and what it depends on.

## Relationship to 5.0

This is a domain corpus for the auditing agent, not a separate engine. Findings
here should be expressible as fixtures in `5.0-Smart-Contract-Audit-Agent`.

## Status

Scaffold. No implementation yet.

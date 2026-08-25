# 10.0 — Agent Payment Trust

Authorization and settlement controls for agents that transact — the point where
agent security and financial infrastructure meet.

## Problem

Agents are beginning to hold spending authority: subscribing to services,
purchasing compute, settling with other agents. The existing rails assume a
human authorizes each payment, and that assumption is what agent autonomy
removes. What replaces it is currently unspecified.

Open questions with no settled answer:

- **Mandate scope** — what an agent was authorized to spend on, expressed
  precisely enough to enforce rather than to litigate afterwards.
- **Counterparty identity** — establishing that the agent on the other side is
  what it claims to be, without a human in either loop.
- **Dispute and reversal** — an agent transaction made under a manipulated
  instruction is not fraud by the principal, but it is not a valid mandate
  either.
- **Velocity control** — an agent in a failure loop can transact continuously;
  rate limits are a safety control, not a convenience.

## Scope

- **Mandate specification** — machine-checkable spending authority: counterparty
  class, amount ceiling, purpose, expiry.
- **Pre-settlement verification** — check the mandate before the transfer, not
  after; deny by default when the mandate does not clearly cover the action.
- **Counterparty attestation** — verify the receiving agent's identity and its
  delegation chain back to a responsible principal.
- **Settlement audit record** — every transaction linked to the mandate that
  authorized it and the trace that produced it.

## Position in the portfolio

This is the bridge project between this repository and
`3.0-Financial-Ai-Systems`. It is filed here because the hard part is
authorization and identity, not payments. Revisit that placement if the work
turns out to be mostly settlement mechanics.

## Status

Scaffold. Earliest-stage of the projects here — the problem is real but the
threat model is not yet settled.

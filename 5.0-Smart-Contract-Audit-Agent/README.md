# 5.0 — LLM Smart-Contract Auditing Agent

Multi-stage agent for smart-contract vulnerability analysis: comprehension →
exploit-path planning → vulnerability classification → iterative self-correction,
executed against a read-only sandbox.

## Problem

Manual audit does not scale to the rate at which contracts are deployed, and
single-shot LLM review hallucinates findings that cost reviewers more time than
they save. The useful unit is not "an LLM that reads Solidity" but a pipeline
that proposes a concrete exploit path and then tries to falsify it.

## Scope

- **Exploit-path planning** — reachability from an attacker-controlled entry
  point to a state change, not pattern matching on syntax.
- **Classification** — reentrancy, oracle manipulation, flash-loan abuse, access
  control gaps, unchecked external calls.
- **Self-correction** — every proposed finding is re-tested; unreproducible
  findings are dropped rather than reported.
- **Grounding** — retrieve comparable historical exploits and validate a
  prediction against recorded outcomes.

## Test fixtures

The repository's `1.0-blockchain-shared-charging/` directory holds a set of
early V2G vehicle-registration contracts (register / query / refresh / rescind)
written against Solidity ^0.8.0. They carry textbook access-control defects —
unauthenticated `register`, unauthorized revocation, unbounded string-keyed
mappings — which makes them usable as known-answer fixtures for the classifier.
They are input to this project, not a result of it.

## Status

Scaffold. No implementation yet.

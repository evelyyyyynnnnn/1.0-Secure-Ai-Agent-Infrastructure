# 7.0 — Private Credit Data Provenance

Verifiable extraction of terms from private credit and alternative-asset
documents, where the output carries a citation back to the source span.

## Problem

Private credit disclosure is thin, non-standard, and mostly prose. Extraction
pipelines built on LLMs produce a clean table and destroy the audit trail in the
process — a number lands in a risk model with no way to check which clause of
which document produced it, or whether the clause was amended. For a figure that
feeds a risk decision or a regulatory filing, unciteable is unusable.

## Scope

- **Span-anchored extraction** — every extracted field carries document id, page,
  character span, and extraction confidence.
- **Term normalization** — covenants, pricing grids, PIK toggles, call
  protection, and amendment lineage into a stable schema.
- **Contradiction detection** — flag where an amendment supersedes a base
  agreement term and the pipeline used the stale value.
- **Provenance verification** — an independent reader can re-derive any field
  from the cited span without re-running the model.
- **Change tracking** — diff a term set across reporting periods.

## Relationship to this repository

The security contribution is the provenance and verification layer, not the
extraction itself: making an agent's factual output checkable by a party that
does not trust the agent.

## Status

Scaffold. No implementation yet.

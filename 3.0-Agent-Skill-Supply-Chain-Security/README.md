# 3.0 — Agent Skill & MCP Supply-Chain Security

Static and dynamic screening for third-party agent extensions: MCP servers, tool
manifests, and agent "skills" that a host model loads and then trusts.

## Problem

An agent's blast radius is defined by the tools it can call, not by its model
weights. Third-party skills and MCP servers are installed from registries with
little review, and published audits of large skill corpora report double-digit
percentages carrying at least one security flaw. Signature-based malware tooling
does not recognise agent-targeted payloads, and published bypasses (encoding,
homoglyph substitution, paraphrase, bundled code) defeat naive scanners.

## Scope

- **Manifest analysis** — permission/verb extraction, capability diffing across
  versions, detection of privilege creep between releases.
- **Prompt-layer analysis** — implicit tool poisoning, instruction smuggling in
  descriptions and docstrings, homoglyph and encoding obfuscation.
- **Behavioural analysis** — execute the skill in a read-only sandbox, record
  actual syscall/network/tool egress, diff against declared capability.
- **Benchmark** — a labelled corpus of benign and malicious skills with
  provenance, so detectors are compared on a fixed set rather than anecdotes.

## Deliverables

| Artifact | Form |
| --- | --- |
| `skillscan` | CLI + library, static + sandboxed dynamic passes |
| Benchmark corpus | Labelled skills, versioned, with a held-out split |
| Evaluation harness | Precision/recall/bypass-rate across detectors |

## Status

Scaffold. No implementation yet.

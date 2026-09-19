# NIW evidence — skill screening (Direction 1)

**Repository:** `1.0-Secure-Ai-Agent-Infrastructure`
**Pillar (Dhanasar prong 1):** Secure AI Agent Infrastructure
**Status:** SKELETON / DEMO on an authored corpus — a concrete artifact to show
on a call, not a measured result.

## What this skeleton demonstrates

- A runnable, dependency-free screening tool with the **three analyzers the
  proposal names** — manifest capability diff (privilege creep), prompt-layer
  analysis (tool poisoning, instruction smuggling, and the homoglyph / encoded
  evasion families), and behavioural declared-vs-observed egress diffing.
- That the tool **beats a naive keyword baseline specifically on the adversarial
  subset**: on this run the baseline catches 0 of the evasive skills because it
  can only match literal words, while the screening tool catches most of them by
  normalizing homoglyphs, decoding payloads, and using paraphrase-robust
  patterns. The gap is the point — it is what an adversarially-robust screener
  is *for*.
- A small **labelled benchmark** with a documented schema and a taxonomy of six
  vulnerability classes, and a **leaderboard site** built from the run's own
  numbers.
- The whole thing reuses the **sandbox-and-verify** framing of the sibling
  `3-llm-audit-agent`: untrusted input, no real privileges granted during
  screening, evidence attached to every finding.

## What it deliberately does NOT establish

- **The corpus is 15 skills the author wrote.** The scores are a demonstration
  that the pipeline runs and the analyzers fire on their target classes — not a
  detection rate on real skills. A detector graded on its author's own examples
  flatters itself.
- **It is not a clean sweep.** The tool still misses at least one adversarial
  case (a zero-width-space character-spacing evasion). That miss is left in the
  corpus and reported, in the spirit of the sibling project, which publishes its
  negative result.
- **No adoption, no downloads, no real-registry data.** `is_synthetic` is `true`
  everywhere.

## What the funded collaboration would add

- The real **500–1000-skill corpus** from live registries, with provenance and
  licensing — the single biggest gap between this skeleton and a citable result.
- **Hardened analyzers** against a wider evasion space (zero-width / spacing
  obfuscation, multi-layer encodings, semantic paraphrase beyond patterns),
  ideally with an adversarial test harness.
- The proposal's stated third-party-verifiable deliverables: a **provisional
  patent**, an **installable open-source package**, and an **evaluable dataset**.

## Exhibit readiness

- [x] The artifact runs end to end (`python -m src.demo`, `pytest`) with no
      network, GPU, or third-party packages.
- [x] Every figure traces to `results/latest.json` from a dated run.
- [x] Results are reported against a named baseline, with the honest miss shown.
- [ ] Scale on real registry data — future work, not yet run.
- [ ] Patent / package / public dataset — collaboration deliverables.

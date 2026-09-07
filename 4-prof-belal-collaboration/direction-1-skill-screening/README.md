# Skill Screening — Direction 1 (SKELETON)

> An adversarially-robust screener for third-party agent **skills / MCP
> servers** — manifest, prompt-layer, and behavioural analysis — plus a small
> labelled benchmark and a leaderboard site, scored against a naive keyword
> baseline.

**Repository:** `1.0-Secure-Ai-Agent-Infrastructure` &middot; **Pillar:**
Secure AI Agent Infrastructure

This is a runnable **skeleton / demo** of Direction 1 of the Prof. Belal
collaboration proposal — something concrete to walk through on a call. It is
**not** a finished result.

## What it is

Third-party agent skills are a software supply chain: bundles of tool
definitions, docstrings and declared permissions that run inside a privileged
model session. This tool screens one before you trust it, with three
dependency-free analyzers:

1. **Manifest analysis** — capability diff against a prior version; flags
   newly-added *sensitive* capabilities (**privilege creep**).
2. **Prompt-layer analysis** — over the description + docstrings the model
   reads: **tool poisoning** and **instruction smuggling**, plus the two evasion
   families that beat naive scanners — **homoglyph** substitution and
   **encoded** (base64/hex) payloads.
3. **Behavioural analysis** — diff declared capabilities against an observed
   sandbox egress list; flags **undeclared egress** ("does more than it
   declares").

Each analyzer emits `Finding` records `{skill_id, version, klass, severity,
evidence}` over a taxonomy of six vulnerability classes. A **naive
keyword-matching baseline** is included as the comparison point.

It reuses the **sandbox-and-verify** approach of the sibling
[`../../3-llm-audit-agent`](../../3-llm-audit-agent): treat the artifact as
untrusted input, analyse it without granting it real privileges, attach concrete
evidence to every flag, and report against a named baseline. Its `src/sitekit.py`
is copied here unchanged to build the site.

## Honest status

- **The corpus is authored by hand** (15 synthetic skills). It is **not**
  scraped from any real registry. `is_synthetic` is `true` everywhere. Scores on
  the author's own examples demonstrate the pipeline runs and the analyzers
  fire — they are **not** a detection rate on real skills.
- **Not a clean sweep.** The tool still misses at least one adversarial case (a
  zero-width-space evasion), and that miss is reported rather than hidden.
- **The real 500–1000-skill corpus, analyzer hardening, a provisional patent,
  and an installable package are the collaboration deliverables** — future work,
  not done here.

## Quick start

```bash
pip install -r requirements.txt        # pytest only; everything else is stdlib
python -m pytest tests/ -q             # 42 tests
python -m src.demo                     # grades both detectors, rewrites results/ and website/
```

`python -m src.demo` grades the screening tool and the baseline on the corpus
and prints a summary: the leaderboard (macro-F1 + adversarial catch rate),
per-class F1 for both detectors, and a worked example with evidence. Every
figure is written to `results/latest.json` and the site is rebuilt from it, so
what the page shows and what the code produces cannot drift apart.

## Layout

```
README.md
requirements.txt
data/
  |-- README.md
  |-- corpus.jsonl        # 15 authored skill records (is_synthetic: true)
  |-- schema.json         # record schema + taxonomy
docs/
  |-- DATA.md             # schema + provenance (authored; real corpus is future work)
  |-- METHOD.md           # the three analyzers + why sandbox-and-verify transfers
  |-- EVIDENCE.md         # what the skeleton shows vs what the collaboration adds
results/
  |-- README.md
  |-- latest.json         # the last run's numbers — the only source for cited figures
src/
  |-- __init__.py
  |-- screen.py           # the three analyzers + taxonomy + Finding
  |-- baseline.py         # naive keyword-matching detector
  |-- corpus.py           # load + schema validation + stats
  |-- grade.py            # per-class P/R/F1, macro-F1, adversarial catch rate
  |-- demo.py             # runs everything, writes results/, rebuilds website/
  |-- site.py             # builds website/ from the run
  |-- sitekit.py          # copied unchanged from 3-llm-audit-agent
tests/
  |-- test_screen.py
  |-- test_baseline.py
  |-- test_corpus.py
  |-- test_grade.py
website/                  # self-contained static site, built by the demo
  |-- index.html
  |-- results.json
  |-- vercel.json
  |-- README.md
```

## The website

`website/` has no build step; Vercel serves the folder as-is. It is regenerated
from `results.json` on every `python -m src.demo`. Do not edit numbers on the
page by hand. See `website/README.md` to deploy it on its own.

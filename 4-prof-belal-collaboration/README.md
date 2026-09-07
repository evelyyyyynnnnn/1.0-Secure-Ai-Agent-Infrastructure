# Prof. Belal Alsinglawi — collaboration

**Status: outreach stage. This folder holds the ready-to-send proposal package, not implementation.**

## What's here

| File | Purpose |
|---|---|
| `Email.md` | The first-contact email to send, with subject line and attachment list. |
| `Proposal.docx` | The full research collaboration proposal — five ranked directions, timelines, deliverables, IP terms. Send this (editable) or `Proposal.html`. |
| `Proposal.html` | Same proposal as a self-contained web page, for a link or preview. |
| `Appendix-Auditing-Agent.docx` | Technical appendix: the four-stage auditing-agent pipeline and the exploit-corpus schema referenced in Direction 1. |

## The ask, in one line

A collaboration whose deliverables are a **provisional patent + open-source screening tool + a public benchmark and leaderboard website** (the paper is his to lead) — so the endeavor gains patent and adopted-artifact evidence, and he gains a publication in his own line of work.

## Where the working prototype lives

Direction 1 retargets an auditing agent that already exists, is tested, and is measured in a sibling project:

    ../3-llm-audit-agent/

It is a four-stage agent (comprehend, plan, classify, self-correct) with a hash-chained
audit trail, scored against the rule-based baseline on 121 real annotated contracts from
the SmartBugs curated corpus.

**The measured result is negative and is reported as such:**

| detector | macro-F1 |
|---|---|
| pattern-baseline | 0.281 |
| 3-llm-audit-agent | 0.256 |

The agent does not beat the rule-based tool it was built to replace. It does cut review
items from 105 to 59, while missing more findings. The proposal uses this honestly: the
measured baseline is *why* the adversarial-screening and public-benchmark work is the
valuable next step, not a restatement.

## Integrity notes

- No number in the proposal claims a result the prototype has not measured. Anything
  suggesting, e.g., a fixed percentage reduction in audit time is not supported and is
  not cited.
- For this collaboration to count as the petitioner's own evidence, any written agreement
  must name her as an inventor on the provisional filing and as lead/co-author on the tool
  and benchmark (Proposal §9).

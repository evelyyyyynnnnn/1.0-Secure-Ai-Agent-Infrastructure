# Prof. Belal Alsinglawi — collaboration

**Status: proposal stage. This folder holds no implementation.**

The only file here is `placeholder.docx`, whose entire contents are the words
"Placeholder document for Prof. Belal Alsinglawi's project." It is kept because
it is the original artifact, not because it says anything.

## Where the actual work is

The auditing agent this collaboration proposed is implemented, tested and
measured in a sibling project:

    ../llm-audit-agent/

It is a four-stage agent (plan, analyse, verify, report) with a hash-chained
audit trail, scored against the rule-based baseline on 121 real annotated
contracts from the SmartBugs curated corpus.

**The measured result is negative and is reported as such:**

| detector | macro-F1 |
|---|---|
| pattern-baseline | 0.281 |
| llm-audit-agent | 0.256 |

The agent does not beat the rule-based tool it was built to replace. It does cut
review items from 105 to 59, while missing more findings.

## What this folder is for

Deliverables named in the proposal — a US provisional patent and a paper — are
documents, not code, and neither exists yet. This folder is where they go.

Anything claiming a 65% reduction in audit time is not supported by the
measurement above and should not be cited until it is.

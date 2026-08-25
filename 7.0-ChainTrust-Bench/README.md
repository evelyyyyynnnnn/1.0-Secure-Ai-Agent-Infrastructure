# 7.0 — ChainTrust-Bench

Security benchmark for on-chain contract analysis: a labelled corpus of
real-world DeFi exploits with the contract context, attack sequence, and
recorded outcome attached to each incident.

## Why this exists as its own project

The auditing agent in 5.0 needs a fixed evaluation target, and so does every
competing detector. A benchmark that lives inside one tool's repository gets
tuned to that tool. Kept separate and versioned, it stays a neutral measuring
instrument.

## Corpus construction

Incidents are drawn from public post-mortems and incident reports, then
annotated. Sources are recorded per record so a label can be traced back to the
report it came from.

| Field | Content |
| --- | --- |
| `incident_id` | Stable identifier; source publication and date |
| `chain` / `address` | Deployment target and contract address |
| `contract_source` | Verified source where available, bytecode otherwise |
| `exploit_category` | reentrancy, oracle manipulation, flash loan, access control, unchecked call, price manipulation |
| `attack_tx` | Transaction hashes of the exploit, in execution order |
| `transaction_pattern` | Ordered call sequence characterising the attack |
| `preconditions` | State the attack depended on — pool depth, oracle staleness, role assignment |
| `loss_usd` | Realised loss at incident time |
| `outcome` | Recovered / partially recovered / unrecovered; any post-incident patch |
| `label_provenance` | Annotator, date, and source report for the label |

`transaction_pattern` and `preconditions` carry most of the evaluation weight.
Category alone does not discriminate between detectors — most systems classify
correctly and get reachability wrong.

## Evaluation harness

Detectors are scored on a held-out split, never on the annotation set used to
build the retrieval index. The harness reports per-category precision and
recall separately, because aggregate accuracy hides the categories that matter.

## Release form

Versioned dataset with a citable DOI, permissive data licence, and a documented
split. Corpus and harness version together; a detector result is meaningless
without the corpus version it was measured against.

## Status

Scaffold. No implementation yet.

# Prior work — the 2023 V2G contracts

This folder was `ev-charging-contracts-solidity/` at the top level of the
repository until it was merged here. It holds the original Remix workspace
backups from February 2023, moved verbatim with `git mv` so the tree and its
history are unchanged.

It sits inside `blockchain-shared-charging/` because the two are the same system
at adjacent layers, not two separate projects.

## Why this belongs to the settlement project

The 2023 contracts establish the data model. The 2026 contract settles money
against it.

| Layer | 2023 contracts (here) | 2026 `SharedCharging.sol` (parent folder) |
|---|---|---|
| Identity | `V2G.register(VIN, publicKey)` | `registerPoint(address)` |
| Access control | `Authorization.authorize` / `revokeAuthorization` / `isAuthorized` | `onlyArbiter` modifier |
| Session record | `ChargingRecords.addChargingRecord(vehicle, startTime, endTime, energy)` | `open(id, point, tariffPerKWh, maxWattHours)` → `report(id, wattHours)` |
| Money | — none — | `dispute` → `resolve` → `settle`, with escrow and a one-hour window |

The 2023 set records an energy reading and stops there. The 2026 set takes the
same reading and settles payment on it, then asks — in `src/economics.py` —
whether that settlement can pay for its own gas. That is one line of work over
three years, which is why it is now one folder.

## What is in here

```
.workspaces/
  default_workspace/            V2G registry, build artifacts
  remixDefault_1676574243282/   V2G, Authorization, ChargingRecords,
                                registration / query / refresh / rescind
Performance Testing Local Code.ipynb
Test 2.ipynb
Test 3.ipynb
Test 1- Transaction/            ← coursework, see below
readme.txt                      Remix's own backup note
```

Roughly 103 lines of Solidity in total, at tutorial scale.

## What must not be cited from here

**`Test 1- Transaction/`** is a LaTeX coursework assignment — its title is
第一次作业 and it carries a student number — tracing a single BSV transaction on a
block explorer. It is not evidence of professional expertise and should not be
attached to, or referenced by, any petition exhibit.

**No metric.** Nothing in this folder was measured. Every number the project
reports comes from the parent folder's `results/latest.json`.

## How this folder may be used

As chronology only: it establishes that this line of work began in early 2023
and that the settlement design extends the petitioner's own earlier data model
rather than starting from someone else's. One sentence in a footnote or an
exhibit description is the right weight.

"""The benchmark corpus.

Each case is a Solidity source with a known ground-truth label: the set of
vulnerability classes actually present, and the line where each one sits.

The cases below are written for this benchmark. They are deliberately small and
single-issue so that a detector's score decomposes cleanly by class -- a large
contract with five interacting bugs tells you a detector failed, but not where.

Scale note: this is the seed corpus (SEED_CASES). The benchmark's stated target
is a much larger corpus mined from on-chain transaction data; `load_corpus`
takes an optional path so a mined corpus can be dropped in without touching any
other module. Nothing in this file claims the mined corpus exists yet.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field, asdict
from typing import Iterable

# Vulnerability classes the benchmark scores. Names follow the SWC registry
# where one applies, so results can be compared with published tooling.
CLASSES = (
    "reentrancy",              # SWC-107
    "unchecked_call",          # SWC-104
    "tx_origin_auth",          # SWC-115
    "timestamp_dependence",    # SWC-116
    "missing_access_control",  # SWC-105
    "unprotected_selfdestruct",# SWC-106
    "integer_overflow",        # SWC-101
)


@dataclass
class Case:
    cid: str
    source: str
    labels: list[str] = field(default_factory=list)
    lines: dict[str, int] = field(default_factory=dict)
    note: str = ""
    tier: str = "seed"

    def is_safe(self) -> bool:
        return not self.labels


def _c(cid, source, labels, lines, note="", tier="seed"):
    return Case(cid=cid, source=source.strip("\n"), labels=list(labels),
                lines=dict(lines), note=note, tier=tier)


SEED_CASES: tuple[Case, ...] = (
    _c("CT-001", """
pragma solidity ^0.8.0;
contract Vault {
    mapping(address => uint256) public balance;
    function deposit() external payable { balance[msg.sender] += msg.value; }
    function withdraw() external {
        uint256 amt = balance[msg.sender];
        (bool ok, ) = msg.sender.call{value: amt}("");
        require(ok, "transfer failed");
        balance[msg.sender] = 0;
    }
}
""", ["reentrancy"], {"reentrancy": 7},
     "State written after the external call; the classic checks-effects violation."),

    _c("CT-002", """
pragma solidity ^0.8.0;
contract Payout {
    function pay(address payable to, uint256 amt) external {
        to.send(amt);
    }
}
""", ["unchecked_call"], {"unchecked_call": 5},
     "send() returns a bool that is discarded, so a failed transfer looks successful."),

    _c("CT-003", """
pragma solidity ^0.8.0;
contract Owned {
    address public owner;
    constructor() { owner = msg.sender; }
    function transferOwnership(address next) external {
        require(tx.origin == owner, "not owner");
        owner = next;
    }
}
""", ["tx_origin_auth"], {"tx_origin_auth": 6},
     "tx.origin authorises the whole call chain, so any contract the owner calls can act as them."),

    _c("CT-004", """
pragma solidity ^0.8.0;
contract Lottery {
    function winner() external view returns (bool) {
        return uint256(keccak256(abi.encodePacked(block.timestamp))) % 2 == 0;
    }
}
""", ["timestamp_dependence"], {"timestamp_dependence": 5},
     "Miner-influenced timestamp used as the randomness source."),

    _c("CT-005", """
pragma solidity ^0.8.0;
contract Treasury {
    address public owner;
    constructor() { owner = msg.sender; }
    function setOwner(address next) external { owner = next; }
    function sweep(address payable to) external { to.transfer(address(this).balance); }
}
""", ["missing_access_control"], {"missing_access_control": 5},
     "setOwner has no guard at all, so anyone can take the contract."),

    _c("CT-006", """
pragma solidity ^0.8.0;
contract Killable {
    function shutdown() external { selfdestruct(payable(msg.sender)); }
}
""", ["unprotected_selfdestruct"], {"unprotected_selfdestruct": 4},
     "selfdestruct reachable by any caller."),

    _c("CT-007", """
pragma solidity ^0.7.0;
contract Counter {
    uint8 public count;
    function add(uint8 n) external { count = count + n; }
}
""", ["integer_overflow"], {"integer_overflow": 5},
     "Pre-0.8 arithmetic wraps silently; no SafeMath in sight."),

    _c("CT-008", """
pragma solidity ^0.8.0;
contract SafeVault {
    mapping(address => uint256) public balance;
    function deposit() external payable { balance[msg.sender] += msg.value; }
    function withdraw() external {
        uint256 amt = balance[msg.sender];
        balance[msg.sender] = 0;
        (bool ok, ) = msg.sender.call{value: amt}("");
        require(ok, "transfer failed");
    }
}
""", [], {},
     "Correct checks-effects-interactions. A detector that flags this is producing a false positive."),

    _c("CT-009", """
pragma solidity ^0.8.0;
contract SafeOwned {
    address public owner;
    constructor() { owner = msg.sender; }
    modifier onlyOwner() { require(msg.sender == owner, "not owner"); _; }
    function transferOwnership(address next) external onlyOwner { owner = next; }
}
""", [], {},
     "Guarded with msg.sender and a modifier. Safe control."),

    _c("CT-010", """
pragma solidity ^0.8.0;
contract Escrow {
    mapping(address => uint256) public owed;
    address public arbiter;
    constructor(address a) { arbiter = a; }
    function release(address payable to) external {
        require(msg.sender == arbiter, "not arbiter");
        uint256 amt = owed[to];
        owed[to] = 0;
        (bool ok, ) = to.call{value: amt}("");
        require(ok, "failed");
    }
}
""", [], {},
     "Access-controlled and effects-before-interaction. Safe."),

    _c("CT-011", """
pragma solidity ^0.8.0;
contract Bank {
    mapping(address => uint256) public balance;
    address public admin;
    function drain() external {
        (bool ok, ) = msg.sender.call{value: address(this).balance}("");
        balance[msg.sender] = 0;
        admin = msg.sender;
    }
}
""", ["reentrancy", "missing_access_control"],
     {"reentrancy": 6, "missing_access_control": 5},
     "Two classes in one function; tests whether a detector reports both or stops at the first."),

    _c("CT-012", """
pragma solidity ^0.8.0;
contract Auction {
    uint256 public deadline;
    address payable public leader;
    function bid() external payable {
        require(block.timestamp < deadline, "closed");
        leader.send(msg.value);
        leader = payable(msg.sender);
    }
}
""", ["unchecked_call", "timestamp_dependence"],
     {"unchecked_call": 7, "timestamp_dependence": 6},
     "Timestamp comparison plus a discarded send() result."),
)


# ---------------------------------------------------------------------------
# Hard tier.
#
# These are the cases the pattern baseline is expected to miss. A benchmark whose
# baseline scores 1.0 measures nothing, so the corpus needs headroom that only a
# detector with real program understanding can close. Each case below states what
# defeats pattern matching, which is also the specification for what an LLM-based
# auditor has to demonstrate before it can claim to beat the baseline.
# ---------------------------------------------------------------------------

HARD_CASES: tuple[Case, ...] = (
    _c("CT-H01", """
pragma solidity ^0.8.0;
contract CrossFn {
    mapping(address => uint256) public balance;
    bool private locked;
    function deposit() external payable { balance[msg.sender] += msg.value; }
    function claim() external {
        uint256 amt = balance[msg.sender];
        _send(msg.sender, amt);
        balance[msg.sender] = 0;
    }
    function _send(address to, uint256 amt) internal {
        (bool ok, ) = to.call{value: amt}("");
        require(ok, "failed");
    }
}
""", ["reentrancy"], {"reentrancy": 8},
     "Cross-function reentrancy: the external call is one frame down in _send, so the "
     "call and the state write are never adjacent in the source.", "hard"),

    _c("CT-H02", """
pragma solidity ^0.8.0;
contract Proxy {
    address public implementation;
    address public owner;
    constructor() { owner = msg.sender; }
    modifier onlyOwner() { require(msg.sender == owner, "no"); _; }
    function upgrade(address impl) external { implementation = impl; }
    function _fallback() internal {
        (bool ok, ) = implementation.delegatecall(msg.data);
        require(ok);
    }
}
""", ["missing_access_control"], {"missing_access_control": 8},
     "The onlyOwner modifier is defined but never applied to upgrade(). Presence of the "
     "modifier in the file is exactly what fools a keyword scanner.", "hard"),

    _c("CT-H03", """
pragma solidity ^0.8.0;
interface IOracle { function price() external view returns (uint256); }
contract Lender {
    IOracle public oracle;
    mapping(address => uint256) public collateral;
    function borrow(uint256 amt) external {
        uint256 value = collateral[msg.sender] * oracle.price();
        require(value >= amt * 2, "undercollateralised");
        (bool ok, ) = msg.sender.call{value: amt}("");
        require(ok);
    }
}
""", ["reentrancy"], {"reentrancy": 9},
     "Read-only reentrancy through a spot-price oracle. Nothing is written after the "
     "call, so the checks-effects heuristic sees a clean function.", "hard"),

    _c("CT-H04", """
pragma solidity ^0.8.0;
contract Timed {
    uint256 private start;
    uint256 private window;
    constructor(uint256 w) { start = block.timestamp; window = w; }
    function _open() private view returns (bool) {
        uint256 elapsed = block.timestamp - start;
        return elapsed < window;
    }
    function act() external view returns (bool) { return _open(); }
}
""", ["timestamp_dependence"], {"timestamp_dependence": 8},
     "The timestamp comparison is laundered through a private helper and a local "
     "variable, so it never appears inside a require/if on the same line.", "hard"),

    _c("CT-H05", """
pragma solidity ^0.8.0;
contract Registry {
    mapping(bytes32 => address) private entries;
    address public owner;
    constructor() { owner = msg.sender; }
    modifier onlyOwner() { require(msg.sender == owner, "no"); _; }
    function set(bytes32 k, address v) external onlyOwner { entries[k] = v; }
    function get(bytes32 k) external view returns (address) { return entries[k]; }
}
""", [], {},
     "Correctly guarded and has no external calls. A hard-tier safe case: it contains "
     "owner assignment and a mapping write, which is what the noisier detectors key on.",
     "hard"),
)


ALL_CASES: tuple[Case, ...] = SEED_CASES + HARD_CASES


def load_corpus(path: str | pathlib.Path | None = None,
                tier: str | None = None) -> list[Case]:
    """Return the benchmark cases.

    With no path, returns the authored corpus (seed + hard tiers). With a path to
    a JSONL file, loads a mined corpus in the same shape -- that is the extension
    point for scaling this benchmark beyond the authored set. `tier` filters to
    one tier when you want to score them separately.
    """
    if path is None:
        cases = list(ALL_CASES)
        return [c for c in cases if tier is None or c.tier == tier]
    p = pathlib.Path(path)
    cases: list[Case] = []
    with p.open(encoding="utf8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            cases.append(Case(cid=raw["cid"], source=raw["source"],
                              labels=raw.get("labels", []),
                              lines=raw.get("lines", {}),
                              note=raw.get("note", ""),
                              tier=raw.get("tier", "seed")))
    return [c for c in cases if tier is None or c.tier == tier]


def corpus_stats(cases: Iterable[Case]) -> dict:
    cases = list(cases)
    per_class = {c: 0 for c in CLASSES}
    for case in cases:
        for lab in case.labels:
            per_class[lab] = per_class.get(lab, 0) + 1
    return {
        "n_cases": len(cases),
        "n_vulnerable": sum(1 for c in cases if not c.is_safe()),
        "n_safe": sum(1 for c in cases if c.is_safe()),
        "n_findings": sum(len(c.labels) for c in cases),
        "per_class": per_class,
        "per_tier": {
            t: sum(1 for c in cases if c.tier == t)
            for t in sorted({c.tier for c in cases})
        },
    }


def export_jsonl(cases: Iterable[Case], path: str | pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf8") as fh:
        for case in cases:
            fh.write(json.dumps(asdict(case), ensure_ascii=False) + "\n")
    return p

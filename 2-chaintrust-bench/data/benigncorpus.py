"""Negative controls: audited production library code that should score clean.

The SmartBugs curated dataset is 121 vulnerable contracts and nothing else. A
benchmark built only from it can report recall, but it cannot report a
false-positive rate, because there are no true negatives for a detector to stay
quiet about. Precision measured that way is not a deployable precision figure,
and the leaderboard's `false_positive_rate_on_safe` column read 0.0 for every
detector only because the denominator was empty.

This module supplies the missing denominator from OpenZeppelin Contracts: the
most widely reviewed and most widely deployed Solidity library in the
ecosystem. Each file below is pinned to an immutable release tag, fetched with
its own hash recorded, and entered into the corpus with NO labels, so
`Case.is_safe()` is true and the scorer counts a detector that fires on it as a
false positive.

What this does and does not assert
----------------------------------
It asserts that these files are audited, released, and relied on by a large
part of the ecosystem, and that a detector firing one of this benchmark's seven
classes on them is almost certainly wrong. Several are adversarial on purpose:
`Address.sol` makes low-level `call`s and checks every return value, so a naive
unchecked-call rule fires on it; `Ownable.sol` is the reference access-control
implementation, so a missing-access-control rule that keys on state-changing
external functions fires on it.

It does NOT assert formal verification, and it is not a claim that the files
contain no bug of any kind. The label is "known-good with respect to this
benchmark's seven classes", which is the property the false-positive rate needs
and the only one claimed. The tier is reported separately from the SmartBugs
tier throughout, so a reader can discount it or score the tiers apart.
"""
from __future__ import annotations

from .datakit import Source

REPO = "OpenZeppelin/openzeppelin-contracts"
# An immutable release tag, not a branch: the corpus must not change under us
# between a run and the hash recorded for it.
REF = "v5.0.2"
RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"

# Chosen for relevance rather than convenience: each file exercises at least one
# of the benchmark's seven classes in its correct, guarded form.
BENIGN_PATHS: tuple[tuple[str, str], ...] = (
    ("contracts/utils/ReentrancyGuard.sol",
     "the reference reentrancy guard itself"),
    ("contracts/access/Ownable.sol",
     "reference access control; state-changing externals are guarded by onlyOwner"),
    ("contracts/access/Ownable2Step.sol",
     "two-step ownership transfer, the hardened form of the above"),
    ("contracts/access/AccessControl.sol",
     "role-based access control, guarded throughout"),
    ("contracts/utils/Address.sol",
     "makes low-level calls and checks every return value -- adversarial for "
     "an unchecked-call rule"),
    ("contracts/token/ERC20/utils/SafeERC20.sol",
     "wraps unchecked ERC-20 returns; the fix for the unchecked-call class"),
    ("contracts/token/ERC20/ERC20.sol",
     "the reference fungible-token implementation"),
    ("contracts/token/ERC20/extensions/ERC20Burnable.sol",
     "burn paths with balance checks"),
    ("contracts/token/ERC721/ERC721.sol",
     "non-fungible token with external receiver callbacks, correctly ordered"),
    ("contracts/utils/Pausable.sol",
     "emergency stop; state-changing externals behind a modifier"),
    ("contracts/utils/math/SafeCast.sol",
     "the fix for the integer-overflow class, in its canonical form"),
    ("contracts/utils/math/Math.sol",
     "arithmetic with explicit overflow handling"),
    ("contracts/utils/Nonces.sol",
     "replay protection with monotonic counters"),
    ("contracts/utils/cryptography/ECDSA.sol",
     "signature recovery with malleability checks"),
    ("contracts/utils/structs/EnumerableSet.sol",
     "storage data structure, no external calls"),
    ("contracts/proxy/utils/Initializable.sol",
     "initialiser guards -- a missing-access-control rule may fire on these"),
    ("contracts/finance/VestingWallet.sol",
     "holds and releases funds on a time schedule -- adversarial for a "
     "timestamp-dependence rule, which is correct usage here"),
    ("contracts/governance/TimelockController.sol",
     "executes arbitrary calls after a delay, with roles -- adversarial for "
     "both access-control and timestamp rules"),
    ("contracts/utils/Multicall.sol",
     "batched delegatecall, guarded"),
    ("contracts/token/ERC20/extensions/ERC4626.sol",
     "tokenised vault: deposits, withdrawals and external token calls"),
)


def contract_source(path: str) -> Source:
    return Source(
        name=path,
        url=RAW.format(repo=REPO, ref=REF, path=path),
        dest=f"openzeppelin/{path}",
        publisher=f"OpenZeppelin Contracts {REF}",
        terms="MIT; see the contract's own SPDX header",
        note="negative control: audited library code, entered with no labels",
    )


def sources() -> list[Source]:
    return [contract_source(p) for p, _ in BENIGN_PATHS]


def to_cases(read_source, tier: str = "openzeppelin") -> tuple[list[dict], dict]:
    """Build unlabelled (safe) cases. `read_source` maps a path to its text.

    Mirrors solcorpus.to_cases so both corpora reach the scorer the same way.
    """
    cases: list[dict] = []
    stats = {"requested": len(BENIGN_PATHS), "kept": 0, "skipped_unreadable": 0}
    for path, why in BENIGN_PATHS:
        try:
            text = read_source(path)
        except (OSError, KeyError):
            stats["skipped_unreadable"] += 1
            continue
        cases.append({
            "cid": "OZ-" + path.split("/")[-1].removesuffix(".sol"),
            "source": text,
            # No labels. This is the whole point: Case.is_safe() is True, so the
            # scorer counts any class this detector reports here as a false
            # positive on known-good code.
            "labels": [],
            "lines": {},
            "note": f"OpenZeppelin {REF} negative control ({path}): {why}",
            "tier": tier,
        })
        stats["kept"] += 1
    return cases, stats

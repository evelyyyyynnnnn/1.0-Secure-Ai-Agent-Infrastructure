"""Tests for the negative-control tier.

These pin the property the whole tier exists for: a case with no labels is
safe, a detector that fires on a safe case is counted as a false positive, and
the false-positive rate stops being a vacuous 0.0 once the denominator is
non-empty.

The download needs a network; the conversion and the scoring do not, and those
are where a mistake would be silent. A benign case that accidentally carried a
label would be scored as a missed vulnerability instead of a clean file, and
every precision figure in the leaderboard would move without anything failing.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from data import benigncorpus
from src.corpus import Case, load_corpus
from src.scoring import evaluate

GUARDED = """pragma solidity ^0.8.20;
contract Guarded {
    address private _owner;
    constructor() { _owner = msg.sender; }
    modifier onlyOwner() { require(msg.sender == _owner, "not owner"); _; }
    function setOwner(address next) external onlyOwner { _owner = next; }
}
"""


def _read(_path):
    return GUARDED


def test_every_benign_case_is_unlabelled_and_therefore_safe():
    cases, stats = benigncorpus.to_cases(_read)
    assert stats["kept"] == len(benigncorpus.BENIGN_PATHS)
    assert cases, "the negative-control tier must not be empty"
    for raw in cases:
        assert raw["labels"] == [], f"{raw['cid']} carries a label"
        assert raw["lines"] == {}
        assert Case(**raw).is_safe()


def test_benign_cases_are_tagged_as_their_own_tier():
    cases, _ = benigncorpus.to_cases(_read)
    assert {c["tier"] for c in cases} == {"openzeppelin"}


def test_unreadable_sources_are_counted_not_silently_dropped():
    def missing(_path):
        raise OSError("not fetched")

    cases, stats = benigncorpus.to_cases(missing)
    assert cases == []
    assert stats["skipped_unreadable"] == len(benigncorpus.BENIGN_PATHS)
    assert stats["kept"] == 0


def test_sources_are_pinned_to_an_immutable_tag_not_a_branch():
    # A branch would let the corpus change under a recorded hash.
    assert benigncorpus.REF.startswith("v")
    for s in benigncorpus.sources():
        assert benigncorpus.REF in s.url
        assert s.url.startswith("https://raw.githubusercontent.com/")


def test_a_detector_that_stays_quiet_on_safe_code_scores_zero_false_positives():
    safe = [Case(cid="OZ-1", source=GUARDED, labels=[], tier="openzeppelin")]
    quiet = lambda _src: []  # noqa: E731
    quiet.name = "quiet"
    rep = evaluate(quiet, safe)
    assert rep.false_positive_rate_on_safe == 0.0


def test_a_detector_that_fires_on_safe_code_is_charged_a_false_positive():
    safe = [
        Case(cid="OZ-1", source=GUARDED, labels=[], tier="openzeppelin"),
        Case(cid="OZ-2", source=GUARDED, labels=[], tier="openzeppelin"),
    ]
    noisy = lambda _src: ["reentrancy"]  # noqa: E731
    noisy.name = "noisy"
    rep = evaluate(noisy, safe)
    assert rep.false_positive_rate_on_safe == 1.0

    half = [safe[0], Case(cid="SB-1", source=GUARDED, labels=["reentrancy"])]
    rep2 = evaluate(noisy, half)
    # One safe case, flagged: the rate is 1/1, not 1/2 -- vulnerable cases are
    # not part of this denominator.
    assert rep2.false_positive_rate_on_safe == 1.0


def test_false_positive_rate_is_vacuous_without_negative_controls():
    """The exact hole this tier closes: no safe cases means the column reads
    0.0 for a detector that flags everything."""
    only_vulnerable = [Case(cid="SB-1", source=GUARDED, labels=["reentrancy"])]
    noisy = lambda _src: ["reentrancy", "integer_overflow"]  # noqa: E731
    noisy.name = "noisy"
    rep = evaluate(noisy, only_vulnerable)
    assert rep.false_positive_rate_on_safe == 0.0  # empty denominator, not a clean bill


@pytest.mark.skipif(
    not (pathlib.Path(__file__).resolve().parent.parent
         / "data" / "real-corpus.jsonl").exists(),
    reason="real corpus not fetched in this environment",
)
def test_fetched_real_corpus_actually_contains_negative_controls():
    corpus = (pathlib.Path(__file__).resolve().parent.parent
              / "data" / "real-corpus.jsonl")
    cases = load_corpus(corpus)
    safe = [c for c in cases if c.is_safe()]
    assert safe, "the fetched corpus has no true negatives"
    assert all(c.tier == "openzeppelin" for c in safe)

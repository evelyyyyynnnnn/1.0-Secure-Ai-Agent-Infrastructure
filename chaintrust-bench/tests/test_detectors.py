"""The detector tests are the benchmark's own correctness check.

If the baseline stops finding the planted bugs, the leaderboard is meaningless,
so these assertions guard the ground truth rather than the implementation.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.corpus import SEED_CASES, HARD_CASES, ALL_CASES, load_corpus, corpus_stats, CLASSES
from src.detectors import PatternDetector, KeywordDetector, NullDetector
from src.scoring import evaluate, leaderboard


def test_corpus_labels_are_known_classes():
    for case in ALL_CASES:
        for lab in case.labels:
            assert lab in CLASSES, f"{case.cid} has unknown label {lab}"


def test_corpus_has_safe_and_vulnerable_cases():
    stats = corpus_stats(SEED_CASES)
    assert stats["n_safe"] >= 3, "need safe cases or precision is unmeasurable"
    assert stats["n_vulnerable"] >= 5


def test_every_class_appears_at_least_once():
    stats = corpus_stats(SEED_CASES)
    missing = [c for c, n in stats["per_class"].items() if n == 0]
    assert not missing, f"classes with no case: {missing}"


def test_pattern_detector_finds_each_planted_bug_in_seed_tier():
    """The baseline must clear the seed tier. If it stops doing so, the ground
    truth or the detector has regressed and every score below is meaningless."""
    det = PatternDetector()
    for case in SEED_CASES:
        if case.is_safe():
            continue
        found = det(case.source)
        assert set(case.labels) & found, (
            f"{case.cid}: expected any of {case.labels}, detector said {sorted(found)}"
        )


def test_pattern_detector_is_quiet_on_safe_contracts():
    det = PatternDetector()
    for case in ALL_CASES:
        if case.is_safe():
            assert not det(case.source), f"{case.cid}: false positive {sorted(det(case.source))}"


def test_null_detector_scores_zero_recall():
    rep = evaluate(NullDetector(), list(SEED_CASES))
    assert rep.macro_recall == 0.0
    assert rep.false_positive_rate_on_safe == 0.0


def test_keyword_detector_trades_precision_for_recall():
    kw = evaluate(KeywordDetector(), list(SEED_CASES))
    pat = evaluate(PatternDetector(), list(SEED_CASES))
    assert kw.false_positive_rate_on_safe > pat.false_positive_rate_on_safe, (
        "the floor detector should be noisier than the baseline"
    )


def test_pattern_detector_beats_the_floor():
    reps = [evaluate(d, list(SEED_CASES))
            for d in (PatternDetector(), KeywordDetector(), NullDetector())]
    board = leaderboard(reps)
    assert board[0]["detector"] == "pattern-baseline"


def test_jsonl_roundtrip(tmp_path):
    from src.corpus import export_jsonl
    p = export_jsonl(SEED_CASES, tmp_path / "c.jsonl")
    again = load_corpus(p)
    assert len(again) == len(SEED_CASES)
    assert {c.cid for c in again} == {c.cid for c in SEED_CASES}


def test_hard_tier_defeats_the_pattern_baseline():
    """The hard tier exists to give the benchmark headroom.

    If the pattern baseline ever clears one of these, that case has stopped
    being hard and belongs in the seed tier -- or the detector has genuinely
    improved and the corpus needs new hard cases. Either way it is a deliberate
    decision, not something to discover from a leaderboard.
    """
    det = PatternDetector()
    cleared = [
        c.cid for c in HARD_CASES
        if not c.is_safe() and set(c.labels) & det(c.source)
    ]
    assert not cleared, (
        f"pattern baseline now solves hard cases {cleared}; "
        "re-tier them or add harder ones"
    )


def test_hard_tier_safe_case_is_not_flagged():
    det = PatternDetector()
    safe = [c for c in HARD_CASES if c.is_safe()]
    assert safe, "the hard tier needs a safe case or precision is untested there"
    for case in safe:
        assert not det(case.source), f"{case.cid}: false positive"


def test_tier_filter_partitions_the_corpus():
    seed = load_corpus(tier="seed")
    hard = load_corpus(tier="hard")
    every = load_corpus()
    assert len(seed) + len(hard) == len(every)
    assert {c.cid for c in seed}.isdisjoint({c.cid for c in hard})


def test_benchmark_has_measurable_headroom():
    """A benchmark whose baseline scores 1.0 measures nothing."""
    from src.scoring import evaluate
    overall = evaluate(PatternDetector(), load_corpus())
    assert overall.macro_f1 < 1.0, "no headroom left; the corpus needs harder cases"
    assert overall.macro_f1 > 0.5, "baseline should still be a credible floor"

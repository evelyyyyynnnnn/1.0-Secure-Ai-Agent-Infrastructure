import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import corpus, screen, baseline, grade
from src.screen import CLASSES


def _mk(sid, malicious, classes, adversarial=None):
    return {
        "skill_id": sid, "version": "1.0.0",
        "manifest": {"permissions": [], "verbs": []},
        "prompt_layer": {"description": "", "docstrings": []},
        "observed_egress": [], "prior_version": None,
        "label": {"malicious": malicious, "classes": classes},
        "adversarial_techniques": adversarial or [],
    }


def test_grading_hand_checked_tiny_case():
    # Three records; a detector that gets r1 right, misses r2, and stays quiet on r3.
    r1 = _mk("r1", True, ["tool_poisoning"])
    r2 = _mk("r2", True, ["encoded_payload"], adversarial=["base64_encoding"])
    r3 = _mk("r3", False, [])
    records = [r1, r2, r3]

    def predict(rec):
        return {"tool_poisoning"} if rec["skill_id"] == "r1" else set()

    g = grade.grade(predict, records)

    # tool_poisoning: tp=1 fp=0 fn=0 -> f1 1.0 ; encoded_payload: fn=1 -> f1 0.0
    assert g["per_class"]["tool_poisoning"]["f1"] == 1.0
    assert g["per_class"]["tool_poisoning"]["tp"] == 1
    assert g["per_class"]["encoded_payload"]["f1"] == 0.0
    assert g["per_class"]["encoded_payload"]["fn"] == 1
    # active classes are tool_poisoning (tp=1) and encoded_payload (fn=1);
    # macro-F1 over those two = (1.0 + 0.0) / 2 = 0.5
    assert g["macro_f1"] == 0.5
    # one adversarial record (r2), not caught
    assert g["adversarial"] == {"total": 1, "caught": 0, "catch_rate": 0.0}
    assert g["n_flagged"] == 1


def test_perfect_detector_scores_one():
    records = [_mk("a", True, ["tool_poisoning"]),
               _mk("b", True, ["undeclared_egress"], adversarial=["paraphrase"])]

    def perfect(rec):
        return set(rec["label"]["classes"])

    g = grade.grade(perfect, records)
    assert g["macro_f1"] == 1.0
    assert g["adversarial"]["catch_rate"] == 1.0


def test_precision_zero_when_detector_never_predicts():
    records = [_mk("a", True, ["tool_poisoning"])]
    g = grade.grade(lambda r: set(), records)
    assert g["per_class"]["tool_poisoning"]["precision"] == 0.0
    assert g["per_class"]["tool_poisoning"]["recall"] == 0.0
    assert g["macro_f1"] == 0.0


def test_leaderboard_sorted_by_macro_f1():
    records = corpus.load()
    board = grade.leaderboard({
        "screening-tool": screen.predicted_classes,
        "naive-baseline": baseline.predicted_classes,
    }, records)
    assert board[0]["rank"] == 1
    assert board[0]["macro_f1"] >= board[1]["macro_f1"]


def test_tool_beats_baseline_on_adversarial_subset():
    records = corpus.load()
    tool = grade.grade(screen.predicted_classes, records)
    base = grade.grade(baseline.predicted_classes, records)
    # The whole point of the direction: on adversarial skills the tool wins.
    assert tool["adversarial"]["catch_rate"] > base["adversarial"]["catch_rate"]
    assert tool["macro_f1"] > base["macro_f1"]


def test_tool_reports_at_least_one_honest_adversarial_miss():
    # Honesty: the tool does NOT catch everything; at least one adversarial
    # case (zero-width spacing) is missed and reported, not hidden.
    records = corpus.load()
    tool = grade.grade(screen.predicted_classes, records)
    assert tool["adversarial"]["caught"] < tool["adversarial"]["total"]

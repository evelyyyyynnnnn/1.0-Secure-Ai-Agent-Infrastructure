"""Scoring and leaderboard construction.

Scores are computed per vulnerability class and then macro-averaged, because a
corpus is never balanced across classes and a micro-average would let a detector
score well by being good at whichever class happens to be most common.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

from .corpus import CLASSES, Case


@dataclass
class ClassScore:
    cls: str
    tp: int
    fp: int
    fn: int

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 0.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    def as_dict(self) -> dict:
        d = asdict(self)
        d.update(precision=round(self.precision, 4),
                 recall=round(self.recall, 4),
                 f1=round(self.f1, 4))
        return d


@dataclass
class Report:
    detector: str
    per_class: dict
    macro_precision: float
    macro_recall: float
    macro_f1: float
    false_positive_rate_on_safe: float
    n_cases: int

    def as_dict(self) -> dict:
        return {
            "detector": self.detector,
            "macro_precision": round(self.macro_precision, 4),
            "macro_recall": round(self.macro_recall, 4),
            "macro_f1": round(self.macro_f1, 4),
            "false_positive_rate_on_safe": round(self.false_positive_rate_on_safe, 4),
            "n_cases": self.n_cases,
            "per_class": {k: v.as_dict() for k, v in self.per_class.items()},
        }


def evaluate(detector, cases: list[Case]) -> Report:
    counts = {c: ClassScore(c, 0, 0, 0) for c in CLASSES}
    safe_cases = [c for c in cases if c.is_safe()]
    safe_flagged = 0

    for case in cases:
        predicted = set(detector(case.source))
        truth = set(case.labels)
        if case.is_safe() and predicted:
            safe_flagged += 1
        for cls in CLASSES:
            in_pred, in_truth = cls in predicted, cls in truth
            if in_pred and in_truth:
                counts[cls].tp += 1
            elif in_pred and not in_truth:
                counts[cls].fp += 1
            elif in_truth and not in_pred:
                counts[cls].fn += 1

    # Macro-average over classes that actually occur in this corpus.
    present = [c for c in CLASSES if counts[c].tp + counts[c].fn > 0]
    n = len(present) or 1
    return Report(
        detector=getattr(detector, "name", detector.__class__.__name__),
        per_class=counts,
        macro_precision=sum(counts[c].precision for c in present) / n,
        macro_recall=sum(counts[c].recall for c in present) / n,
        macro_f1=sum(counts[c].f1 for c in present) / n,
        false_positive_rate_on_safe=(safe_flagged / len(safe_cases)) if safe_cases else 0.0,
        n_cases=len(cases),
    )


def leaderboard(reports: list[Report]) -> list[dict]:
    """Rank by macro-F1, breaking ties toward the lower false-positive rate."""
    ranked = sorted(
        reports,
        key=lambda r: (-r.macro_f1, r.false_positive_rate_on_safe),
    )
    return [
        {"rank": i + 1, **r.as_dict()} for i, r in enumerate(ranked)
    ]

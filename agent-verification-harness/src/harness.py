"""Runs the checks over labelled transcripts and scores the harness itself."""

from __future__ import annotations

from dataclasses import dataclass

from .grounding import Claim, check_claim, split_claims, parse_citations
from .transcripts import Transcript


@dataclass
class Verdict:
    tid: str
    idx: int
    claim: str
    label: str
    flagged: bool
    reason: str
    score: float
    citation_correct: bool


def verify_transcript(t: Transcript, threshold: float = 0.55) -> list:
    out = []
    for i, sentence in enumerate(split_claims(t.answer)):
        cited = parse_citations(sentence)
        claim = Claim(text=sentence, cited=cited)
        res = check_claim(claim, t.sources, threshold=threshold)
        if res.unsupported_numbers:
            reason = f"number(s) in no source: {', '.join(res.unsupported_numbers)}"
        elif not res.supported:
            reason = f"no supporting span (best {res.best_score:.2f} < {threshold})"
        elif not res.citation_correct:
            reason = f"cited {cited or '[]'} but support is in {res.best_source}"
        else:
            reason = ""
        out.append(Verdict(
            tid=t.tid, idx=i, claim=sentence, label=t.labels.get(i, "ok"),
            flagged=bool(reason), reason=reason, score=res.best_score,
            citation_correct=res.citation_correct))
    return out


def score_harness(transcripts, threshold: float = 0.55) -> dict:
    """How well does the harness catch what it is supposed to catch?

    Positive class = a claim that should be flagged (unsupported or fabricated).
    """
    tp = fp = tn = fn = 0
    per_kind = {"fabricated": {"caught": 0, "total": 0},
                "unsupported": {"caught": 0, "total": 0},
                "miscited": {"caught": 0, "total": 0},
                "ok": {"false_flags": 0, "total": 0}}
    rows = []
    for t in transcripts:
        for v in verify_transcript(t, threshold):
            should_flag = v.label in ("unsupported", "fabricated", "miscited")
            if should_flag:
                per_kind[v.label]["total"] += 1
                if v.flagged:
                    per_kind[v.label]["caught"] += 1
                    tp += 1
                else:
                    fn += 1
            else:
                per_kind["ok"]["total"] += 1
                if v.flagged:
                    per_kind["ok"]["false_flags"] += 1
                    fp += 1
                else:
                    tn += 1
            rows.append(v)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "threshold": threshold,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(2 * precision * recall / (precision + recall), 4)
        if (precision + recall) else 0.0,
        "per_kind": per_kind,
        "n_claims": len(rows),
        "verdicts": [v.__dict__ for v in rows],
    }


def threshold_sweep(transcripts, lo=0.30, hi=0.85, step=0.05) -> list:
    """Precision/recall as the grounding threshold moves.

    Included because a single threshold is a choice, and publishing the curve is
    the difference between reporting a result and selecting one.
    """
    out = []
    x = lo
    while x <= hi + 1e-9:
        s = score_harness(transcripts, threshold=round(x, 3))
        out.append({"threshold": round(x, 3), "precision": s["precision"],
                    "recall": s["recall"], "f1": s["f1"]})
        x += step
    return out

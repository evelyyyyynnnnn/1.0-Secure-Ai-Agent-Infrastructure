"""Grade a detector against the authored corpus.

A detector is anything exposing `predicted_classes(record) -> set[str]`
(both `src.screen` and `src.baseline` do). Grading is multi-label per
vulnerability class:

  * per-class precision / recall / F1
  * overall macro-F1 (unweighted mean of per-class F1)
  * an ADVERSARIAL-EVASION catch rate: of the malicious skills that carry an
    adversarial technique, the fraction the detector flags at all.

No numbers are hard-coded — everything is counted from the run.
"""

from __future__ import annotations

from .screen import CLASSES


def _prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall, "f1": f1}


def grade(predict, records) -> dict:
    """`predict` maps a record to a set of predicted class strings."""
    per_class = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CLASSES}

    flagged_total = 0
    adv_total = 0
    adv_caught = 0

    for rec in records:
        pred = set(predict(rec))
        truth = set(rec["label"].get("classes", []))
        for c in CLASSES:
            if c in pred and c in truth:
                per_class[c]["tp"] += 1
            elif c in pred and c not in truth:
                per_class[c]["fp"] += 1
            elif c not in pred and c in truth:
                per_class[c]["fn"] += 1

        if pred:
            flagged_total += 1

        if rec["label"]["malicious"] and rec.get("adversarial_techniques"):
            adv_total += 1
            if pred:
                adv_caught += 1

    per_class_prf = {c: _prf(**per_class[c]) for c in CLASSES}

    # Macro-average over the ACTIVE classes only: those the corpus actually
    # exercises (any true instance) or the detector predicted. Averaging over
    # classes with no support and no prediction would inject spurious zeros. On
    # the full corpus every class has support, so this equals a plain 6-class
    # macro; the distinction only matters on tiny slices.
    active = [c for c in CLASSES
              if (per_class[c]["tp"] + per_class[c]["fp"] + per_class[c]["fn"]) > 0]
    denom = len(active) if active else 1
    macro_f1 = sum(per_class_prf[c]["f1"] for c in active) / denom
    macro_p = sum(per_class_prf[c]["precision"] for c in active) / denom
    macro_r = sum(per_class_prf[c]["recall"] for c in active) / denom

    return {
        "per_class": per_class_prf,
        "macro_f1": macro_f1,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "adversarial": {
            "total": adv_total,
            "caught": adv_caught,
            "catch_rate": (adv_caught / adv_total) if adv_total else 0.0,
        },
        "n_flagged": flagged_total,
        "n_records": len(records),
    }


def leaderboard(detectors: dict, records) -> list:
    """detectors: {name: predict_fn}. Returns rows sorted by macro-F1 desc."""
    rows = []
    for name, predict in detectors.items():
        g = grade(predict, records)
        rows.append({
            "detector": name,
            "macro_f1": g["macro_f1"],
            "macro_precision": g["macro_precision"],
            "macro_recall": g["macro_recall"],
            "adversarial_catch_rate": g["adversarial"]["catch_rate"],
            "adversarial_caught": g["adversarial"]["caught"],
            "adversarial_total": g["adversarial"]["total"],
        })
    rows.sort(key=lambda r: r["macro_f1"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows

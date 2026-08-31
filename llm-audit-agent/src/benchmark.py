"""Score the agent against the rule-based baseline on a shared corpus.

The comparison is the whole point of this module. A claim that an LLM auditor
reduces manual audit workload is only meaningful relative to the tool it
replaces, measured on the same cases, so the baseline is imported from
ChainTrust-Bench rather than reimplemented here.

Workload is modelled explicitly rather than asserted. `workload_reduction`
counts the findings a human would have to adjudicate under each tool and
reports the difference. That is a defensible definition and it is stated on
the page; it is not the same thing as a measured human time study, and the
site says so.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

BENCH = pathlib.Path(__file__).resolve().parent.parent.parent / "chaintrust-bench"


def _load_bench():
    """Import ChainTrust-Bench from the sibling project.

    Both projects ship a package called `src`, so a plain sys.path import would
    resolve to whichever one was imported first. The benchmark is loaded under
    its own module namespace instead, which keeps the two projects independently
    copyable -- neither has to know it is sitting next to the other.
    """
    ns = "chaintrust_bench"
    if ns not in sys.modules:
        pkg = types.ModuleType(ns)
        pkg.__path__ = [str(BENCH / "src")]
        sys.modules[ns] = pkg
    mods = {}
    for name in ("corpus", "detectors", "scoring"):
        full = f"{ns}.{name}"
        if full in sys.modules:
            mods[name] = sys.modules[full]
            continue
        spec = importlib.util.spec_from_file_location(full, BENCH / "src" / f"{name}.py")
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {full} from {BENCH}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
        mods[name] = mod
    return (mods["corpus"].load_corpus, mods["corpus"].CLASSES,
            mods["detectors"].PatternDetector, mods["scoring"].evaluate,
            mods["scoring"].leaderboard)


def available() -> bool:
    return (BENCH / "src" / "corpus.py").exists()


def workload(detector, cases) -> dict:
    """Count what a human auditor would have to do behind this tool.

    - `to_review`    findings surfaced, all of which need adjudication
    - `false_alarms` surfaced findings that are not real (wasted review)
    - `missed`       real findings never surfaced (the cost the tool does not show)
    """
    to_review = false_alarms = missed = 0
    for case in cases:
        pred = set(detector(case.source))
        truth = set(case.labels)
        to_review += len(pred)
        false_alarms += len(pred - truth)
        missed += len(truth - pred)
    return {"to_review": to_review, "false_alarms": false_alarms, "missed": missed}


def workload_reduction(baseline_wl: dict, agent_wl: dict) -> dict:
    """Reduction in adjudication load, and the recall cost of getting it.

    Reported together on purpose: a tool can always cut review load by reporting
    less, so a workload number without the missed count beside it is meaningless.
    """
    base = baseline_wl["to_review"] or 1
    delta = baseline_wl["to_review"] - agent_wl["to_review"]
    fa_base = baseline_wl["false_alarms"] or 1
    return {
        "review_items_baseline": baseline_wl["to_review"],
        "review_items_agent": agent_wl["to_review"],
        "review_reduction_pct": round(100.0 * delta / base, 2),
        "false_alarm_reduction_pct": round(
            100.0 * (baseline_wl["false_alarms"] - agent_wl["false_alarms"]) / fa_base, 2),
        "missed_baseline": baseline_wl["missed"],
        "missed_agent": agent_wl["missed"],
        "recall_cost": agent_wl["missed"] - baseline_wl["missed"],
    }


def run_comparison(backend=None) -> dict:
    from .agent import AuditAgent, DetectorAdapter

    load_corpus, CLASSES, PatternDetector, evaluate, leaderboard = _load_bench()
    cases = load_corpus()
    baseline = PatternDetector()
    agent_det = DetectorAdapter(AuditAgent(backend=backend))
    no_verify = DetectorAdapter(
        AuditAgent(backend=backend, self_correct=False),
        name="agent (no self-correction)")

    detectors = [baseline, agent_det, no_verify]
    reports = [evaluate(d, cases) for d in detectors]
    board = leaderboard(reports)

    per_tier = {}
    for tier in sorted({getattr(c, "tier", "seed") for c in cases}):
        subset = [c for c in cases if getattr(c, "tier", "seed") == tier]
        per_tier[tier] = {
            "n_cases": len(subset),
            "baseline_f1": round(evaluate(baseline, subset).macro_f1, 4),
            "agent_f1": round(evaluate(agent_det, subset).macro_f1, 4),
            "baseline_recall": round(evaluate(baseline, subset).macro_recall, 4),
            "agent_recall": round(evaluate(agent_det, subset).macro_recall, 4),
        }

    wl_base = workload(baseline, cases)
    wl_agent = workload(agent_det, cases)

    # Cost of the self-correction stage, measured rather than assumed.
    ag = AuditAgent(backend=backend)
    dropped = kept = 0
    for c in cases:
        r = ag.audit(c.source, c.cid)
        dropped += len(r.dropped)
        kept += len(r.findings)

    return {
        "corpus_size": len(cases),
        "leaderboard": board,
        "per_tier": per_tier,
        "workload": {
            "baseline": wl_base,
            "agent": wl_agent,
            "delta": workload_reduction(wl_base, wl_agent),
        },
        "self_correction": {
            "findings_kept": kept,
            "findings_dropped": dropped,
            "drop_rate_pct": round(100.0 * dropped / (kept + dropped), 2)
            if (kept + dropped) else 0.0,
        },
    }

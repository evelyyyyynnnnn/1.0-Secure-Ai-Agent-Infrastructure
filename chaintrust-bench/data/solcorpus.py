"""Mapping the SmartBugs curated dataset onto this benchmark's classes.

SmartBugs-curated is the closest thing the field has to a labelled corpus of
real, deployed-style Solidity with known vulnerabilities and known line numbers.
Using it turns this benchmark from "does the detector find the bugs I wrote"
into "does it find the bugs someone else wrote", which is the only version of
the question worth answering.

Two mismatches have to be handled honestly rather than papered over:

  * SmartBugs uses ten coarse categories; this benchmark uses seven finer
    classes. Five map one-to-one. Four SmartBugs categories have no counterpart
    here and are EXCLUDED rather than forced into the nearest class -- a
    front-running case scored as a reentrancy miss would make the detector look
    worse than it is, for a bug it was never asked to find.
  * SmartBugs' `access_control` covers three of this benchmark's classes at
    once. Splitting it requires reading the source, and that refinement is
    reported separately so a reader can discount it.
"""
from __future__ import annotations

import json
import re

from .datakit import Source

REPO = "smartbugs/smartbugs-curated"
# The dataset has lived on both default-branch names; the fetcher tries each.
REFS = ("main", "master")
RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"

# SmartBugs category -> this benchmark's class.
DIRECT = {
    "reentrancy": "reentrancy",
    "unchecked_low_level_calls": "unchecked_call",
    "time_manipulation": "timestamp_dependence",
    "arithmetic": "integer_overflow",
}
# Categories with no counterpart in CLASSES. Excluded, and counted so the
# exclusion is visible in the results rather than silent.
UNMAPPED = ("bad_randomness", "denial_of_service", "front_running",
            "short_addresses", "other")

TX_ORIGIN = re.compile(r"\btx\s*\.\s*origin\b")
SELFDESTRUCT = re.compile(r"\b(selfdestruct|suicide)\s*\(")


def index_source(ref: str) -> Source:
    return Source(
        name=f"SmartBugs vulnerabilities.json ({ref})",
        url=RAW.format(repo=REPO, ref=ref, path="vulnerabilities.json"),
        dest="smartbugs/vulnerabilities.json",
        publisher="SmartBugs (smartbugs/smartbugs-curated)",
        terms="the curated dataset is published under its repository's licence; "
              "individual contracts retain their original licences",
        note="per-file vulnerability categories and line numbers",
    )


def contract_source(ref: str, path: str) -> Source:
    return Source(
        name=path,
        url=RAW.format(repo=REPO, ref=ref, path=path),
        dest=f"smartbugs/{path}",
        publisher="SmartBugs (smartbugs/smartbugs-curated)",
        terms="see the contract's own SPDX header",
    )


def parse_index(raw: bytes) -> list:
    """Normalise vulnerabilities.json into [{path, findings:[{category, lines}]}].

    Written defensively because the file's exact shape is a property of a
    third-party repository that can change: anything unrecognised raises with
    what it actually saw, rather than silently yielding an empty corpus that
    would read as "the detector found nothing".
    """
    data = json.loads(raw)
    if isinstance(data, dict):
        data = list(data.values())
    if not isinstance(data, list) or not data:
        raise ValueError(f"expected a non-empty list of records, got "
                         f"{type(data).__name__}")

    out = []
    for rec in data:
        if not isinstance(rec, dict):
            raise ValueError(f"expected record objects, got {type(rec).__name__}")
        path = rec.get("path") or rec.get("name")
        if not path:
            raise ValueError(f"record has neither 'path' nor 'name': "
                             f"{sorted(rec)[:6]}")
        vulns = rec.get("vulnerabilities", [])
        findings = []
        for v in vulns:
            cat = (v.get("category") or v.get("name") or "").strip().lower()
            lines = v.get("lines") or ([v["line"]] if "line" in v else [])
            findings.append({"category": cat,
                             "lines": [int(x) for x in lines if str(x).isdigit()]})
        out.append({"path": str(path), "findings": findings})
    return out


def classify(category: str, source: str) -> str | None:
    """Map one SmartBugs finding to a benchmark class, or None to exclude it."""
    category = category.strip().lower()
    if category in DIRECT:
        return DIRECT[category]
    if category == "access_control":
        # SmartBugs' broadest category. The split below is this project's
        # refinement, not SmartBugs' label, and is reported as such.
        if TX_ORIGIN.search(source):
            return "tx_origin_auth"
        if SELFDESTRUCT.search(source):
            return "unprotected_selfdestruct"
        return "missing_access_control"
    return None


def to_cases(records: list, read_source, tier: str = "smartbugs") -> tuple:
    """Build benchmark cases from the index plus each contract's text.

    Returns (cases, stats). `read_source` maps a dataset path to its text, so
    this function stays testable without a filesystem or a network.
    """
    cases, stats = [], {
        "records": len(records), "kept": 0, "skipped_unmapped": 0,
        "skipped_unreadable": 0, "by_class": {},
        "access_control_refined": {"tx_origin_auth": 0,
                                   "unprotected_selfdestruct": 0,
                                   "missing_access_control": 0},
    }
    for rec in records:
        try:
            text = read_source(rec["path"])
        except (OSError, KeyError):
            stats["skipped_unreadable"] += 1
            continue

        labels, lines = [], {}
        saw_unmapped = False
        for fnd in rec["findings"]:
            cls = classify(fnd["category"], text)
            if cls is None:
                saw_unmapped = True
                continue
            if fnd["category"].strip().lower() == "access_control":
                stats["access_control_refined"][cls] += 1
            if cls not in labels:
                labels.append(cls)
                if fnd["lines"]:
                    lines[cls] = min(fnd["lines"])

        if not labels:
            # Every finding fell outside this benchmark's classes. Scoring the
            # file as safe would be wrong -- it IS vulnerable, just not to
            # anything asked about -- so it is dropped, not relabelled.
            if saw_unmapped or rec["findings"]:
                stats["skipped_unmapped"] += 1
                continue

        cases.append({
            "cid": "SB-" + rec["path"].replace("/", "-").removesuffix(".sol"),
            "source": text,
            "labels": labels,
            "lines": lines,
            "note": f"SmartBugs curated: {rec['path']}",
            "tier": tier,
        })
        stats["kept"] += 1
        for lb in labels:
            stats["by_class"][lb] = stats["by_class"].get(lb, 0) + 1
    return cases, stats

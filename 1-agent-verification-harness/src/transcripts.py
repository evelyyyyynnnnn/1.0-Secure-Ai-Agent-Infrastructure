"""Labelled agent transcripts for evaluating the harness itself.

A verification harness needs its own ground truth, or you have no way to tell a
detector that works from one that flags everything. Each transcript below is
authored with a known verdict per claim: grounded, unsupported, or a fabricated
number.

These are synthetic and small. They test the harness, not any real agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .grounding import Source


@dataclass
class Transcript:
    tid: str
    question: str
    sources: list
    answer: str
    labels: dict = field(default_factory=dict)  # claim index -> "ok"|"unsupported"|"fabricated"
    note: str = ""


S_FED = Source("S1", (
    "The Federal Open Market Committee held the target range for the federal funds "
    "rate at 4.25 to 4.5 percent at its January meeting. The Committee noted that "
    "inflation remains somewhat elevated and that labor market conditions have "
    "remained solid in recent months."))

S_CPI = Source("S2", (
    "The Consumer Price Index for All Urban Consumers increased 0.3 percent in "
    "January on a seasonally adjusted basis. Over the last 12 months the all items "
    "index increased 3.0 percent before seasonal adjustment."))

S_SEC = Source("S3", (
    "The registrant identifies supply chain concentration as a principal risk. A "
    "single supplier accounted for 42 percent of component purchases during fiscal "
    "2024, compared with 31 percent in fiscal 2023."))


TRANSCRIPTS: tuple[Transcript, ...] = (
    Transcript(
        "T-01", "What did the FOMC do in January?", [S_FED],
        "The FOMC held the target range at 4.25 to 4.5 percent [S1]. "
        "The Committee said inflation remains somewhat elevated [S1].",
        {0: "ok", 1: "ok"},
        "Both claims supported and correctly cited."),

    Transcript(
        "T-02", "What did the FOMC do, and what is inflation running at?", [S_FED],
        "The FOMC held rates at 4.25 to 4.5 percent [S1]. "
        "Inflation is running at 2.1 percent year over year [S1].",
        {0: "ok", 1: "fabricated"},
        "Second claim invents a figure that appears in no source."),

    Transcript(
        "T-03", "Summarise CPI.", [S_CPI],
        "CPI rose 0.3 percent in January on a seasonally adjusted basis [S2]. "
        "The 12-month change was 3.0 percent before seasonal adjustment [S2]. "
        "The increase was driven primarily by shelter costs [S2].",
        {0: "ok", 1: "ok", 2: "unsupported"},
        "Third claim is plausible and uncited by the source; no number to catch it."),

    Transcript(
        "T-04", "What is the supplier concentration risk?", [S_SEC, S_CPI],
        "A single supplier accounted for 42 percent of component purchases in fiscal "
        "2024 [S3]. That is up from 31 percent in fiscal 2023 [S3].",
        {0: "ok", 1: "ok"},
        "Correct in a multi-source setting; the distractor source must not confuse it."),

    Transcript(
        "T-05", "What is the supplier concentration risk?", [S_SEC, S_CPI],
        "A single supplier accounted for 42 percent of component purchases [S2]. "
        "Inflation was 3.0 percent over twelve months [S3].",
        {0: "miscited", 1: "miscited"},
        "Both claims are grounded but the citations are swapped. Tests citation "
        "checking independently of grounding: a claim can be true and still be "
        "attributed to the wrong source, which is its own failure."),

    Transcript(
        "T-06", "What did the FOMC do?", [S_FED],
        "The Committee cut rates by 25 basis points to 4.0 percent [S1].",
        {0: "fabricated"},
        "Confidently wrong, with a fabricated number and a real citation."),
)

"""Grounding and citation checking for tool-using agents.

The question this module answers is narrow and checkable: for each claim an
agent makes, is there a span in the sources it actually retrieved that supports
it, and does the citation it attached point at that span?

Deliberately not a model. Everything here is lexical and inspectable, because a
verification layer that is itself a black box moves the trust problem rather
than solving it. The scores are conservative: they under-credit paraphrase, and
that bias is stated rather than tuned away.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

_WORD = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")
# The decimal part must have digits after it. Without the (?:...) group a
# sentence-final "2023." captured the period, so the same year written mid-
# sentence in a claim and at the end of a sentence in a source never matched.
_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?%?")
_CITE = re.compile(r"\[[A-Za-z0-9_-]+\]")
_STOP = frozenset("""
a an the of to in on at for and or but is are was were be been being with as by from
that this these those it its their there here what which who whom how when where why
""".split())


def strip_citations(text: str) -> str:
    """Remove [S1]-style markers before any scoring.

    Non-obvious and worth stating: a marker like [S1] contains the digit 1, so
    leaving it in makes every cited sentence look like it contains a number the
    sources do not, and the fabrication check fires on every correctly-cited
    claim. The marker also injects a token ("s1") that appears in no source and
    drags containment down. Citations are metadata about the claim, not part of
    it, and they are checked separately by `check_claim`.
    """
    return _CITE.sub(" ", text)


def tokens(text: str) -> list[str]:
    return [w for w in _WORD.findall(strip_citations(text).lower()) if w not in _STOP]


def shingles(text: str, n: int = 3) -> set:
    t = tokens(text)
    if len(t) < n:
        return {tuple(t)} if t else set()
    return {tuple(t[i:i + n]) for i in range(len(t) - n + 1)}


@dataclass
class Source:
    sid: str
    text: str

    def spans(self, window: int = 40, stride: int = 20) -> list:
        """Overlapping word windows, so a claim can be located, not just matched."""
        w = self.text.split()
        if len(w) <= window:
            return [(0, len(w), self.text)]
        out = []
        for i in range(0, len(w) - window + 1, stride):
            out.append((i, i + window, " ".join(w[i:i + window])))
        return out


@dataclass
class Claim:
    text: str
    cited: list = field(default_factory=list)   # source ids the agent cited


@dataclass
class GroundingResult:
    claim: str
    best_source: str
    best_score: float
    supported: bool
    citation_correct: bool
    cited: list
    unsupported_numbers: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "claim": self.claim,
            "best_source": self.best_source,
            "best_score": round(self.best_score, 4),
            "supported": self.supported,
            "citation_correct": self.citation_correct,
            "cited": list(self.cited),
            "unsupported_numbers": list(self.unsupported_numbers),
        }


def containment(claim: str, span: str, n: int = 3) -> float:
    """Fraction of the claim's shingles present in the span.

    Containment rather than Jaccard: a claim can be fully supported by a long
    passage, and Jaccard would punish the length of the evidence.
    """
    c = shingles(claim, n)
    if not c:
        return 0.0
    s = shingles(span, n)
    return len(c & s) / len(c)


def unigram_coverage(claim: str, span: str) -> float:
    c = set(tokens(claim))
    if not c:
        return 0.0
    return len(c & set(tokens(span))) / len(c)


def score_claim(claim: str, source: Source) -> tuple[float, str]:
    """Best-supporting span in this source, and its score."""
    best, best_span = 0.0, ""
    for _, _, span in source.spans():
        s = 0.65 * containment(claim, span) + 0.35 * unigram_coverage(claim, span)
        if s > best:
            best, best_span = s, span
    return best, best_span


def numbers_in(text: str) -> set:
    return {m.group(0).replace(",", "")
            for m in _NUM.finditer(strip_citations(text))}


def check_claim(claim: Claim, sources: list, threshold: float = 0.55) -> GroundingResult:
    scores = {s.sid: score_claim(claim.text, s)[0] for s in sources}
    best_sid = max(scores, key=scores.get) if scores else ""
    best = scores.get(best_sid, 0.0)

    # A number that appears in the claim but in none of the sources is the
    # single highest-signal hallucination marker in practice.
    src_nums = set()
    for s in sources:
        src_nums |= numbers_in(s.text)
    unsupported = sorted(numbers_in(claim.text) - src_nums)

    supported = best >= threshold and not unsupported
    citation_correct = bool(claim.cited) and best_sid in claim.cited
    return GroundingResult(
        claim=claim.text, best_source=best_sid, best_score=best,
        supported=supported, citation_correct=citation_correct,
        cited=claim.cited, unsupported_numbers=unsupported,
    )


def split_claims(answer: str) -> list:
    """Split an agent answer into claim-sized units.

    Sentence granularity, which is coarse. A claim-extraction model would do
    better; this is the transparent version, and its coarseness is a stated
    limitation rather than a hidden one.
    """
    parts = re.split(r"(?<=[.!?])\s+", answer.strip())
    return [p.strip() for p in parts if len(tokens(p)) >= 3]


def parse_citations(sentence: str) -> list:
    """Pull [S1]-style citation markers out of a sentence."""
    return re.findall(r"\[([A-Za-z0-9_-]+)\]", sentence)

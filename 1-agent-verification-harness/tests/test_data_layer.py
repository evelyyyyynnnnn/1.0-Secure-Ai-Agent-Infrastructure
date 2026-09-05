"""Tests for building labelled transcripts from real documents.

The claim labels here are produced by construction rather than annotation, so
the construction is what has to be right. Each test below pins one property
that, if it broke, would silently change every score the harness reports.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from data import datakit
from data.load import (build_transcripts, html_to_text, perturb_number,
                       sentences_with_numbers)

CPI_HTML = b"""<html><head><style>.a{}</style></head><body>
<h1>Consumer Price Index - January 2026</h1>
<p>The Consumer Price Index for All Urban Consumers increased 0.3 percent in January
on a seasonally adjusted basis, the U.S. Bureau of Labor Statistics reported today.</p>
<p>Over the last 12 months, the all items index increased 3.0 percent before
seasonal adjustment, continuing a gradual moderation from the prior year.</p>
<p>The index for shelter rose 0.4 percent in January and accounted for over half
of the monthly all items increase reported in this release.</p>
<p>The food index increased 0.4 percent in January as both of the major grocery
store food group indexes that the agency tracks rose over the month.</p>
<p>Short line.</p>
</body></html>"""

EMPSIT_HTML = b"""<html><body>
<h1>The Employment Situation - January 2026</h1>
<p>Total nonfarm payroll employment rose by 143,000 in January, and the
unemployment rate changed little at 4.0 percent, the agency reported today.</p>
<p>Employment continued to trend up in health care, retail trade, and social
assistance during the month covered by this particular news release.</p>
<p>The labor force participation rate held at 62.6 percent in January and has
shown little net movement over the preceding twelve month period.</p>
<p>Average hourly earnings for all employees rose by 17 cents, or 0.5 percent,
to $35.87 over the month according to the establishment survey data.</p>
</body></html>"""


def test_html_to_text_keeps_prose_and_drops_styling():
    text = html_to_text(CPI_HTML)
    assert "Consumer Price Index" in text
    assert "{" not in text
    # Paragraph boundaries must survive or sentences run together.
    assert "today.The index" not in text


def test_sentences_with_numbers_requires_a_checkable_number():
    sents = sentences_with_numbers(html_to_text(CPI_HTML))
    assert sents
    assert all(any(ch.isdigit() for ch in s) for s in sents)
    # "Short line." has no number and too few words.
    assert not any(s.startswith("Short line") for s in sents)


def test_sentences_are_bounded_in_length():
    sents = sentences_with_numbers(html_to_text(CPI_HTML))
    assert all(12 <= len(s.split()) <= 45 for s in sents)


def test_perturb_number_changes_the_value_beyond_rounding():
    """A perturbation inside rounding distance would make the label arguable."""
    s = "The all items index increased 3.0 percent before seasonal adjustment."
    out = perturb_number(s)
    assert out != s
    assert "3.0 percent" not in out
    # The rest of the sentence is untouched, so only the number is wrong.
    assert out.endswith("percent before seasonal adjustment.")
    import re
    new = float(re.search(r"\d+\.\d+", out).group(0))
    assert abs(new - 3.0) >= 1.7


def test_perturb_number_returns_none_when_there_is_nothing_to_perturb():
    assert perturb_number("There are no digits in this sentence at all.") is None


def test_perturb_preserves_integer_formatting():
    out = perturb_number("Total nonfarm payroll employment rose by 143000 jobs.")
    assert "." not in out.split("by ")[1].split()[0]


# --- end to end ------------------------------------------------------------

def _seed(tmp_path, docs=(("bls/cpi.htm", CPI_HTML),
                          ("bls/empsit.htm", EMPSIT_HTML))):
    f = datakit.Fetcher(tmp_path)
    man = f.load_manifest()
    for dest, raw in docs:
        p = f.raw / dest
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        man["files"][dest] = {
            "source": dest, "url": f"https://www.bls.gov/{dest}",
            "publisher": "BLS", "terms": "public domain",
            "sha256": datakit.sha256_file(p), "bytes": len(raw),
            "retrieved_utc": datakit.utc_now()}
    f._write_manifest(man)
    return f


def test_refuses_an_empty_cache(tmp_path):
    with pytest.raises(datakit.FetchError, match="no real documents cached"):
        build_transcripts(root=tmp_path)


def test_a_single_document_is_refused(tmp_path):
    """An unsupported claim must be borrowed from another real document.

    With only one document the only way to produce one would be to invent it,
    and an invented distractor is an easier test than a real near-miss.
    """
    _seed(tmp_path, docs=(("bls/cpi.htm", CPI_HTML),))
    with pytest.raises(datakit.FetchError, match="at least 2 are needed"):
        build_transcripts(root=tmp_path)


def test_transcripts_carry_all_three_label_kinds(tmp_path):
    _seed(tmp_path)
    ts, meta = build_transcripts(root=tmp_path)
    assert len(ts) == 2
    kinds = {v for t in ts for v in t.labels.values()}
    assert kinds == {"ok", "fabricated", "unsupported"}
    assert meta["claims_are_model_output"] is False


def test_supported_claims_really_appear_in_the_cited_source(tmp_path):
    """If a claim labelled 'ok' is not in its source, precision is being
    measured against a wrong answer key."""
    _seed(tmp_path)
    ts, _ = build_transcripts(root=tmp_path)
    from src.grounding import split_claims, strip_citations
    for t in ts:
        src = {s.sid: s.text for s in t.sources}
        claims = split_claims(t.answer)
        cited_text = src[t.tid.replace("REAL-", "")]
        for idx, label in t.labels.items():
            if label != "ok":
                continue
            body = strip_citations(claims[idx]).strip().rstrip(". ")
            assert body[:60] in cited_text, body


def test_unsupported_claims_are_absent_from_the_cited_source(tmp_path):
    """The borrowed sentence must genuinely not be in the document it cites."""
    _seed(tmp_path)
    ts, _ = build_transcripts(root=tmp_path)
    from src.grounding import split_claims, strip_citations
    for t in ts:
        sid = t.tid.replace("REAL-", "")
        cited_text = {s.sid: s.text for s in t.sources}[sid]
        claims = split_claims(t.answer)
        for idx, label in t.labels.items():
            if label == "unsupported":
                body = strip_citations(claims[idx]).strip().rstrip(". ")
                assert body[:60] not in cited_text


def test_provenance_is_recorded_per_document(tmp_path):
    _seed(tmp_path)
    _, meta = build_transcripts(root=tmp_path)
    assert len(meta["documents"]) == 2
    for d in meta["documents"]:
        assert len(d["sha256"]) == 16
        assert d["url"].startswith("https://")
        assert d["candidate_sentences"] >= 1


def test_the_scorer_runs_unchanged_on_real_transcripts(tmp_path):
    _seed(tmp_path)
    from src.harness import score_harness, threshold_sweep
    ts, _ = build_transcripts(root=tmp_path)

    scored = score_harness(ts)
    assert scored["n_claims"] == sum(len(t.labels) for t in ts)
    for k in ("precision", "recall", "f1"):
        assert 0.0 <= scored[k] <= 1.0
    sweep = threshold_sweep(ts)
    assert len(sweep) > 1
    assert all(0.0 <= r["f1"] <= 1.0 for r in sweep)


def test_number_fabrication_is_actually_detected_on_real_text(tmp_path):
    """The whole point of the harness, exercised on real sentences."""
    _seed(tmp_path)
    from src.grounding import Claim, check_claim, parse_citations, split_claims
    ts, _ = build_transcripts(root=tmp_path)
    tr = ts[0]
    claims = split_claims(tr.answer)
    fab_idx = [i for i, v in tr.labels.items() if v == "fabricated"][0]
    sentence = claims[fab_idx]
    res = check_claim(Claim(sentence, parse_citations(sentence)), tr.sources)
    assert res.unsupported_numbers, \
        "the altered number should not be found anywhere in the source"

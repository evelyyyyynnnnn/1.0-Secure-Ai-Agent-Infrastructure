import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.grounding import (Claim, Source, check_claim, containment,
                           numbers_in, parse_citations, split_claims)
from src.harness import score_harness, verify_transcript, threshold_sweep
from src.transcripts import TRANSCRIPTS, S_FED
from src.toollog import ToolAuditLog, instrument


def test_containment_is_one_for_a_quote():
    src = "the target range for the federal funds rate at 4.25 to 4.5 percent"
    assert containment("the federal funds rate at 4.25 to 4.5 percent", src) == 1.0


def test_numbers_are_extracted_with_separators_stripped():
    assert "1200" in numbers_in("about 1,200 filings")
    assert "3.0" in numbers_in("rose 3.0 percent")


def test_citation_markers_parse():
    assert parse_citations("Rates held [S1] and inflation elevated [S2].") == ["S1", "S2"]


def test_split_claims_drops_fragments():
    out = split_claims("The FOMC held rates. Yes. Inflation remains somewhat elevated.")
    assert len(out) == 2


def test_grounded_claim_is_supported():
    c = Claim("The FOMC held the target range at 4.25 to 4.5 percent", ["S1"])
    r = check_claim(c, [S_FED])
    assert r.supported and r.citation_correct


def test_fabricated_number_is_caught():
    c = Claim("Inflation is running at 2.1 percent year over year", ["S1"])
    r = check_claim(c, [S_FED])
    assert not r.supported
    assert "2.1" in r.unsupported_numbers


def test_swapped_citation_is_flagged_but_claim_still_grounded():
    """Grounding and citation correctness are independent signals."""
    verdicts = verify_transcript(
        [t for t in TRANSCRIPTS if t.tid == "T-05"][0])
    assert any(not v.citation_correct for v in verdicts)


def test_harness_catches_every_fabricated_number():
    s = score_harness(list(TRANSCRIPTS))
    fab = s["per_kind"]["fabricated"]
    assert fab["total"] >= 2
    assert fab["caught"] == fab["total"], "a fabricated number must never slip through"


def test_harness_reports_its_own_precision_and_recall():
    s = score_harness(list(TRANSCRIPTS))
    assert 0.0 <= s["precision"] <= 1.0
    assert 0.0 <= s["recall"] <= 1.0
    assert s["n_claims"] == sum(
        len(split_claims(t.answer)) for t in TRANSCRIPTS)


def test_threshold_sweep_is_monotone_in_recall():
    """Raising the bar can only flag more, never fewer."""
    sweep = threshold_sweep(list(TRANSCRIPTS))
    recalls = [r["recall"] for r in sweep]
    assert recalls == sorted(recalls), "recall should not fall as the threshold rises"


def test_audit_chain_verifies_when_untouched():
    log = ToolAuditLog()
    log.record("search", {"q": "a"}, "ok")
    log.record("fetch", {"url": "b"}, "ok")
    intact, idx = log.verify()
    assert intact and idx == -1


def test_audit_chain_detects_tampering():
    log = ToolAuditLog()
    log.record("search", {"q": "a"}, "ok")
    log.record("fetch", {"url": "b"}, "ok")
    log.record("search", {"q": "c"}, "ok")
    log.records[1].args = {"url": "evil"}
    intact, idx = log.verify()
    assert not intact and idx == 1


def test_instrument_records_failures():
    log = ToolAuditLog()

    def boom(**_):
        raise ValueError("no")

    wrapped = instrument(log, "boom", boom)
    try:
        wrapped(x=1)
    except ValueError:
        pass
    assert log.stats()["n_failures"] == 1


def test_citation_markers_do_not_leak_into_scoring():
    """Regression: [S1] contains the digit 1.

    Left in place, the fabrication check reads that 1 as a number appearing in
    no source and flags every correctly-cited claim, which showed up as
    precision 0.25 with a completely flat threshold sweep.
    """
    from src.grounding import strip_citations
    assert "1" not in numbers_in("Rates held at 4.25 to 4.5 percent [S1].")
    assert "s1" not in " ".join(
        __import__("src.grounding", fromlist=["tokens"]).tokens("held rates [S1]"))
    assert strip_citations("a [S1] b") .split() == ["a", "b"]


def test_cited_and_uncited_forms_of_a_claim_score_the_same():
    bare = Claim("The FOMC held the target range at 4.25 to 4.5 percent", [])
    cited = Claim("The FOMC held the target range at 4.25 to 4.5 percent [S1]", ["S1"])
    a = check_claim(bare, [S_FED])
    b = check_claim(cited, [S_FED])
    assert abs(a.best_score - b.best_score) < 1e-9
    assert a.unsupported_numbers == b.unsupported_numbers == []


def test_grounded_claims_are_not_all_flagged():
    """The harness must not flag correct, correctly-cited work."""
    s = score_harness(list(TRANSCRIPTS))
    ok = s["per_kind"]["ok"]
    assert ok["false_flags"] < ok["total"], (
        f"every grounded claim was flagged ({ok['false_flags']}/{ok['total']})")
    # Not asserting a precision floor: the remaining false positives are real
    # lexical-mismatch cases ("FOMC" vs "Federal Open Market Committee",
    # "twelve" vs "12"), documented on the site rather than tuned away.
    assert s["precision"] >= 0.5


def test_number_regex_does_not_capture_a_sentence_final_period():
    """Regression: "fiscal 2023." in a source vs "fiscal 2023" in a claim.

    The old pattern let the decimal point match with no digits behind it, so a
    year ending a sentence became "2023." and never equalled the "2023" written
    mid-sentence -- making a correctly grounded claim look fabricated.
    """
    assert numbers_in("compared with 31 percent in fiscal 2023.") == {"31", "2023"}
    assert numbers_in("rose 3.0 percent.") == {"3.0"}


def test_miscitation_is_caught_even_when_the_claim_is_true():
    s = score_harness(list(TRANSCRIPTS))
    mc = s["per_kind"]["miscited"]
    assert mc["total"] >= 1
    assert mc["caught"] >= 1, "a true claim attributed to the wrong source must flag"

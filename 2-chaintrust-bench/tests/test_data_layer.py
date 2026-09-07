"""Tests for the SmartBugs ingestion path.

The download needs a network. The mapping from SmartBugs' ten categories onto
this benchmark's seven classes does not, and that mapping is where the damage
would be done: a wrong label here does not crash, it silently changes every
score the benchmark reports.
"""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from data.solcorpus import DIRECT, UNMAPPED, classify, parse_index, to_cases
from src.corpus import CLASSES

REENTRANT = """pragma solidity ^0.4.19;
contract SimpleDAO {
  mapping (address => uint) public credit;
  function withdraw(uint amount) public {
    if (credit[msg.sender] >= amount) {
      msg.sender.call.value(amount)();
      credit[msg.sender] -= amount;
    }
  }
}"""

TX_ORIGIN_SRC = """pragma solidity ^0.4.24;
contract Phishable {
  address public owner;
  function withdrawAll(address _recipient) public {
    require(tx.origin == owner);
    _recipient.transfer(this.balance);
  }
}"""

SELFDESTRUCT_SRC = """pragma solidity ^0.4.24;
contract Suicidal {
  function kill() public { selfdestruct(msg.sender); }
}"""

NO_MODIFIER_SRC = """pragma solidity ^0.4.24;
contract Unprotected {
  address public owner;
  function changeOwner(address _new) public { owner = _new; }
}"""


def test_every_mapped_class_is_a_real_benchmark_class():
    """A typo here would create a class the scorer never scores."""
    for target in DIRECT.values():
        assert target in CLASSES
    for extra in ("tx_origin_auth", "unprotected_selfdestruct",
                  "missing_access_control"):
        assert extra in CLASSES


def test_direct_categories_map_one_to_one():
    assert classify("reentrancy", REENTRANT) == "reentrancy"
    assert classify("unchecked_low_level_calls", REENTRANT) == "unchecked_call"
    assert classify("time_manipulation", REENTRANT) == "timestamp_dependence"
    assert classify("arithmetic", REENTRANT) == "integer_overflow"


def test_unmapped_categories_return_none_rather_than_a_near_miss():
    """The failure this prevents is a front-running case scored as a
    reentrancy miss, which makes the detector look worse at a job it was
    never given."""
    for cat in UNMAPPED:
        assert classify(cat, REENTRANT) is None


def test_access_control_is_split_by_reading_the_source():
    assert classify("access_control", TX_ORIGIN_SRC) == "tx_origin_auth"
    assert classify("access_control", SELFDESTRUCT_SRC) == "unprotected_selfdestruct"
    assert classify("access_control", NO_MODIFIER_SRC) == "missing_access_control"


def test_tx_origin_is_matched_through_whitespace():
    # Real Solidity is not consistently formatted.
    assert classify("access_control", "require(tx . origin == owner);") == \
        "tx_origin_auth"


def test_classify_is_case_insensitive():
    assert classify("Reentrancy", REENTRANT) == "reentrancy"


# --- index parsing ---------------------------------------------------------

INDEX = json.dumps([
    {"name": "simple_dao.sol", "path": "dataset/reentrancy/simple_dao.sol",
     "vulnerabilities": [{"lines": [19], "category": "reentrancy"}]},
    {"name": "phishable.sol", "path": "dataset/access_control/phishable.sol",
     "vulnerabilities": [{"lines": [16], "category": "access_control"}]},
    {"name": "eth_tx_order.sol", "path": "dataset/front_running/eth_tx.sol",
     "vulnerabilities": [{"lines": [26], "category": "front_running"}]},
]).encode()


def test_parse_index_normalises_records():
    recs = parse_index(INDEX)
    assert [r["path"] for r in recs] == [
        "dataset/reentrancy/simple_dao.sol",
        "dataset/access_control/phishable.sol",
        "dataset/front_running/eth_tx.sol"]
    assert recs[0]["findings"] == [{"category": "reentrancy", "lines": [19]}]


def test_parse_index_accepts_a_dict_keyed_index():
    """The upstream file has shipped as both a list and an object."""
    as_dict = json.dumps({"a": json.loads(INDEX)[0]}).encode()
    assert parse_index(as_dict)[0]["path"] == "dataset/reentrancy/simple_dao.sol"


def test_parse_index_raises_on_an_unrecognised_shape():
    """An empty corpus must not be mistakable for a detector finding nothing."""
    with pytest.raises(ValueError, match="non-empty list"):
        parse_index(b"[]")
    with pytest.raises(ValueError):
        parse_index(b'[{"vulnerabilities": []}]')


# --- case construction -----------------------------------------------------

SOURCES = {
    "dataset/reentrancy/simple_dao.sol": REENTRANT,
    "dataset/access_control/phishable.sol": TX_ORIGIN_SRC,
    "dataset/front_running/eth_tx.sol": NO_MODIFIER_SRC,
}


def test_to_cases_keeps_mapped_and_drops_unmapped():
    cases, stats = to_cases(parse_index(INDEX), SOURCES.__getitem__)
    assert stats["records"] == 3
    assert stats["kept"] == 2
    # The front-running contract IS vulnerable, just not to anything this
    # benchmark asks about, so it is dropped rather than labelled safe.
    assert stats["skipped_unmapped"] == 1
    assert all(c["labels"] for c in cases)
    paths = [c["note"] for c in cases]
    assert not any("front_running" in p for p in paths)


def test_to_cases_records_line_numbers_and_provenance():
    cases, _ = to_cases(parse_index(INDEX), SOURCES.__getitem__)
    dao = [c for c in cases if "simple_dao" in c["note"]][0]
    assert dao["labels"] == ["reentrancy"]
    assert dao["lines"] == {"reentrancy": 19}
    assert dao["note"].startswith("SmartBugs curated:")
    assert dao["tier"] == "smartbugs"


def test_to_cases_reports_how_access_control_was_split():
    """The split is this project's inference, so it has to be visible."""
    _, stats = to_cases(parse_index(INDEX), SOURCES.__getitem__)
    assert stats["access_control_refined"]["tx_origin_auth"] == 1


def test_unreadable_contracts_are_counted_not_silently_dropped():
    def missing(path):
        raise OSError("not downloaded")
    _, stats = to_cases(parse_index(INDEX), missing)
    assert stats["skipped_unreadable"] == 3
    assert stats["kept"] == 0


def test_cases_round_trip_through_the_benchmark_loader(tmp_path):
    """The real corpus must load through exactly the path the seed corpus uses."""
    from src.corpus import load_corpus
    from src.scoring import evaluate
    from src.detectors import PatternDetector

    cases, _ = to_cases(parse_index(INDEX), SOURCES.__getitem__)
    p = tmp_path / "real-corpus.jsonl"
    p.write_text("".join(json.dumps(c) + "\n" for c in cases))

    loaded = load_corpus(p)
    assert len(loaded) == 2
    assert {c.tier for c in loaded} == {"smartbugs"}

    report = evaluate(PatternDetector(), loaded)
    # The point is that scoring runs unchanged on someone else's labels.
    assert 0.0 <= report.macro_f1 <= 1.0

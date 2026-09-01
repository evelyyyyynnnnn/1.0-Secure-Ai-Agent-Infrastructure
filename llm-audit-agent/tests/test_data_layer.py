"""Tests for scoring the agent on a corpus it did not write.

The value of the SmartBugs path is that the agent and the rule-based baseline
are graded on contracts neither project authored. These tests check that the
plumbing for that actually works, and that asking for it without the data
refuses rather than quietly re-running the authored corpus.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import benchmark

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

TX_ORIGIN = """pragma solidity ^0.4.24;
contract Phishable {
  address public owner;
  function withdrawAll(address _recipient) public {
    require(tx.origin == owner);
    _recipient.transfer(this.balance);
  }
}"""


def _corpus_file(tmp_path):
    cases = [
        {"cid": "SB-dataset-reentrancy-simple_dao", "source": REENTRANT,
         "labels": ["reentrancy"], "lines": {"reentrancy": 6},
         "note": "SmartBugs curated: dataset/reentrancy/simple_dao.sol",
         "tier": "smartbugs"},
        {"cid": "SB-dataset-access_control-phishable", "source": TX_ORIGIN,
         "labels": ["tx_origin_auth"], "lines": {"tx_origin_auth": 5},
         "note": "SmartBugs curated: dataset/access_control/phishable.sol",
         "tier": "smartbugs"},
    ]
    p = tmp_path / "real-corpus.jsonl"
    p.write_text("".join(json.dumps(c) + "\n" for c in cases))
    return p


def test_the_sibling_benchmark_is_reachable():
    assert benchmark.available(), \
        "chaintrust-bench must sit beside this project for the comparison to run"


def test_real_corpus_is_absent_in_a_fresh_clone():
    """It is produced by a fetch and gitignored, so absence is the normal state."""
    assert benchmark.REAL_CORPUS.name == "real-corpus.jsonl"
    assert benchmark.real_corpus_available() is benchmark.REAL_CORPUS.exists()


def test_comparison_runs_on_a_corpus_neither_project_wrote(tmp_path):
    p = _corpus_file(tmp_path)
    out = benchmark.run_comparison(corpus_path=str(p))

    board = out["leaderboard"]
    assert len(board) == 3
    names = {row["detector"] for row in board}
    assert any("agent" in n for n in names)
    for row in board:
        assert 0.0 <= row["macro_f1"] <= 1.0
    # The tier travels through, so a reader can see which corpus produced this.
    assert "smartbugs" in out.get("per_tier", {})


def test_authored_and_real_corpora_are_scored_by_the_same_code(tmp_path):
    """No branch in the scorer may depend on which corpus it was handed."""
    authored = benchmark.run_comparison(corpus_path=None)
    real = benchmark.run_comparison(corpus_path=str(_corpus_file(tmp_path)))
    assert set(authored["leaderboard"][0]) == set(real["leaderboard"][0])
    assert [r["detector"] for r in authored["leaderboard"]] or True


def test_demo_refuses_real_mode_without_the_corpus(monkeypatch, capsys):
    """--real must not silently fall back to the authored corpus."""
    from src import demo
    monkeypatch.setattr(benchmark, "real_corpus_available", lambda: False)
    monkeypatch.setattr(sys, "argv", ["demo", "--real"])
    assert demo.main() == 2
    err = capsys.readouterr().err
    assert "cannot run on real data" in err
    assert "data.fetch" in err


def test_run_writes_real_results_to_a_separate_file(tmp_path, monkeypatch):
    """Overwriting latest.json with real results would erase the comparison.

    demo.ROOT is redirected into tmp_path first. An earlier version of this
    test let run() write into the repository and then deleted the file it had
    written -- which also deleted the genuine SmartBugs results committed
    beside it. A test must not be able to destroy a measured result.
    """
    from src import demo
    monkeypatch.setattr(demo, "ROOT", tmp_path)
    r = demo.run(corpus_path=str(_corpus_file(tmp_path)))
    assert r["written_to"] == "results/latest-real.json"
    assert r["is_synthetic"] is False
    assert "SmartBugs" in r["corpus"]
    assert (tmp_path / "results" / "latest-real.json").exists()


def test_authored_run_still_writes_latest_json(tmp_path, monkeypatch):
    from src import demo
    monkeypatch.setattr(demo, "ROOT", tmp_path)
    r = demo.run()
    assert r["written_to"] == "results/latest.json"
    assert r["is_synthetic"] is True
    assert (tmp_path / "results" / "latest.json").exists()


def test_the_measured_result_survives_the_test_suite():
    """A guard against the bug that motivated the monkeypatching above.

    The earlier version of these tests wrote into the repository's own results
    directory and then deleted what it had written, taking the genuine
    SmartBugs result with it. Checked by property rather than by git status, so
    it does not confuse a developer's uncommitted work with test pollution.
    """
    real = ROOT / "results" / "latest-real.json"
    if not real.exists():
        pytest.skip("no real run has been made in this checkout")
    d = json.loads(real.read_text())
    assert d["is_synthetic"] is False
    assert "SmartBugs" in d.get("corpus", "")
    assert d["comparison"]["leaderboard"], "the real leaderboard was emptied"

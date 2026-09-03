import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.agent import AuditAgent, DetectorAdapter, STAGES, _safe_json
from src.backends import StubBackend

REENTRANT = """
pragma solidity ^0.8.0;
contract V {
    mapping(address => uint256) public balance;
    function withdraw() external {
        uint256 amt = balance[msg.sender];
        (bool ok, ) = msg.sender.call{value: amt}("");
        require(ok);
        balance[msg.sender] = 0;
    }
}
"""

CROSS_FN = """
pragma solidity ^0.8.0;
contract C {
    mapping(address => uint256) public balance;
    function claim() external {
        uint256 amt = balance[msg.sender];
        _send(msg.sender, amt);
        balance[msg.sender] = 0;
    }
    function _send(address to, uint256 amt) internal {
        (bool ok, ) = to.call{value: amt}("");
        require(ok);
    }
}
"""

SAFE = """
pragma solidity ^0.8.0;
contract S {
    address public owner;
    constructor() { owner = msg.sender; }
    modifier onlyOwner() { require(msg.sender == owner, "no"); _; }
    function setOwner(address n) external onlyOwner { owner = n; }
}
"""


def test_pipeline_runs_every_stage():
    r = AuditAgent(backend=StubBackend()).audit(REENTRANT, "t1")
    assert [m.stage for m in r.trail] == list(STAGES)


def test_skipping_self_correction_drops_the_verify_stage():
    r = AuditAgent(backend=StubBackend(), self_correct=False).audit(REENTRANT, "t1")
    assert "verify" not in [m.stage for m in r.trail]


def test_finds_inline_reentrancy():
    assert "reentrancy" in AuditAgent().audit(REENTRANT).classes()


def test_finds_cross_function_reentrancy():
    """The case the pattern baseline structurally cannot reach."""
    assert "reentrancy" in AuditAgent().audit(CROSS_FN).classes()


def test_quiet_on_a_correctly_guarded_contract():
    assert AuditAgent().audit(SAFE).classes() == set()


def test_audit_trail_is_serialisable():
    d = AuditAgent().audit(CROSS_FN, "x").as_dict()
    assert d["contract_id"] == "x"
    assert d["trail"] and all("stage" in t for t in d["trail"])
    assert d["elapsed_ms"] >= 0


def test_prompts_are_redacted_by_default():
    r = AuditAgent().audit(REENTRANT)
    assert all(m.prompt.startswith("<") for m in r.trail)
    r2 = AuditAgent(keep_prompts=True).audit(REENTRANT)
    assert any("pragma" in m.prompt for m in r2.trail)


def test_detector_adapter_matches_the_benchmark_contract():
    det = DetectorAdapter()
    out = det(REENTRANT)
    assert isinstance(out, set)
    assert all(isinstance(x, str) for x in out)


def test_safe_json_recovers_from_prose_wrapping():
    assert _safe_json('here you go: {"a": 1} hope that helps') == {"a": 1}
    assert _safe_json("not json at all") == {}


def test_stub_backend_is_not_claimed_to_be_a_language_model():
    """Guards the honesty of the site banner."""
    assert StubBackend().is_language_model is False

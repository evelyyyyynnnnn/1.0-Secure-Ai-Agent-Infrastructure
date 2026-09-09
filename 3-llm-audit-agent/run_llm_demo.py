import os, json, pathlib, time
from datetime import datetime, timezone
os.environ.setdefault("OPENAI_API_KEY","ollama")
from src.backends import OpenAICompatibleBackend
from src.agent import AuditAgent
ROOT=pathlib.Path(__file__).resolve().parent
sample = """
pragma solidity ^0.8.0;
contract CrossFn {
    mapping(address => uint256) public balance;
    function claim() external {
        uint256 amt = balance[msg.sender];
        _send(msg.sender, amt);
        balance[msg.sender] = 0;
    }
    function _send(address to, uint256 amt) internal {
        (bool ok, ) = to.call{value: amt}("");
        require(ok, "failed");
    }
}
"""
backend = OpenAICompatibleBackend(model="qwen2.5-coder:7b",
        base_url="http://localhost:11434/v1", api_key_env="OPENAI_API_KEY")
t0=time.time()
trace = AuditAgent(backend=backend).audit(sample, "CT-H01").as_dict()
dt=round(time.time()-t0,1)
out={
 "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
 "backend": backend.name,
 "backend_is_language_model": True,
 "is_synthetic": False,
 "data_source": "real open LLM (qwen2.5-coder:7b) served locally via Ollama, auditing the worked-example contract through the agent's four stages with the hash-chained audit trail",
 "runtime_seconds": dt,
 "note": ("Demonstrates the four-stage auditing agent running end-to-end on a REAL open language model "
          "(not the deterministic stub): backend_is_language_model is true. The full 121-contract SmartBugs "
          "LLM benchmark is left as future work — a real-LLM pass over the whole corpus is slow on CPU; the "
          "committed rule-based-vs-stub benchmark remains in latest-real.json and is unchanged."),
 "worked_example": trace,
}
(ROOT/"results"/"latest-llm.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf8")
print("wrote results/latest-llm.json | runtime %.1fs | findings:"%dt, len(trace.get("findings",[])) if isinstance(trace,dict) else "?")
print("backend_is_language_model:", out["backend_is_language_model"], "| backend:", out["backend"])
# show a compact view of the trace
print(json.dumps({k:trace[k] for k in list(trace)[:6]}, indent=1)[:900] if isinstance(trace,dict) else str(trace)[:900])

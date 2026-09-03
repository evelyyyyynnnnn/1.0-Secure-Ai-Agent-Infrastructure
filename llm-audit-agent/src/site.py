"""Builds website/ from the last demo run."""

from __future__ import annotations

import pathlib

from . import sitekit as sk

ROOT = pathlib.Path(__file__).resolve().parent.parent

META = {
    "name": "LLM Audit Agent",
    "slug": "llm-audit-agent",
    "repo": "1.0-Secure-Ai-Agent-Infrastructure",
    "pillar": "Secure Digital Infrastructure",
    "tagline": "A four-stage smart-contract auditing agent with a full audit trail, "
               "scored against the rule-based baseline on a shared corpus.",
    "tags": [("staged pipeline", ""), ("audit trail", ""), ("read-only sandbox", ""),
             ("pluggable backend", ""), ("stub backend", "demo")],
    "banner": "This run used the deterministic stub backend, not a language model. "
              "The stub is a small symbolic reasoner that exists so the pipeline is "
              "runnable and testable with no API key. Its scores measure the plumbing, "
              "not what an LLM would achieve — and the result below is reported "
              "unmodified, including where the agent loses to the baseline.",
    "datanote": "The corpus is ChainTrust-Bench's authored seed and hard tiers.",
}


def build_site(results: dict) -> pathlib.Path:
    ex = results["worked_example"]
    comp = results.get("comparison")

    stage_tbl = sk.table(
        ["#", "Stage", "What it does", "Reply size"],
        [[i + 1, t["stage"],
          {"understand": "Builds a structural model: functions, modifiers, external "
                         "calls, state writes, internal call graph",
           "plan": "Decides which exploit paths are worth checking, and why",
           "classify": "Classifies confirmed vulnerabilities against the path list",
           "verify": "Self-correction: drops findings that do not survive review"}
          .get(t["stage"], ""), f"{t['reply_bytes']} B"]
         for i, t in enumerate(ex["trail"])],
        numeric_cols=(0, 3),
    )

    finding_rows = [[f["cls"], f["fn"] + "()", f["evidence"]] for f in ex["findings"]]
    findings_tbl = sk.table(["Class", "Function", "Evidence"], finding_rows) \
        if finding_rows else "<p>No findings on the worked example.</p>"

    body_comp = ""
    if comp:
        board = comp["leaderboard"]
        pt = comp["per_tier"]
        d = comp["workload"]["delta"]
        sc = comp["self_correction"]

        board_tbl = sk.table(
            ["Rank", "Detector", "Macro-P", "Macro-R", "Macro-F1", "FP on safe"],
            [[r["rank"], r["detector"], f"{r['macro_precision']:.3f}",
              f"{r['macro_recall']:.3f}", f"{r['macro_f1']:.3f}",
              f"{r['false_positive_rate_on_safe']:.3f}"] for r in board],
            numeric_cols=(0, 2, 3, 4, 5))

        tier_tbl = sk.table(
            ["Tier", "Cases", "Baseline F1", "Agent F1", "Change"],
            [[t, v["n_cases"], f"{v['baseline_f1']:.3f}", f"{v['agent_f1']:.3f}",
              f"{v['agent_f1'] - v['baseline_f1']:+.3f}"] for t, v in pt.items()],
            numeric_cols=(1, 2, 3, 4))

        tier_chart = sk.bar_chart(
            [(f"{t} — baseline", v["baseline_f1"]) for t, v in pt.items()]
            + [(f"{t} — agent", v["agent_f1"]) for t, v in pt.items()],
            fmt="{:.3f}")

        wl_tbl = sk.table(
            ["Measure", "Baseline", "Agent", "Change"],
            [["Findings a human must adjudicate",
              d["review_items_baseline"], d["review_items_agent"],
              f"{d['review_reduction_pct']:+.1f}%"],
             ["Real findings missed", d["missed_baseline"], d["missed_agent"],
              f"{d['recall_cost']:+d}"]],
            numeric_cols=(1, 2, 3))

        body_comp = f"""
<section>
  <h2>Against the rule-based baseline</h2>
  <div class="stack-lg">
    {tier_chart}
    {tier_tbl}
    <div class="note">
      <h3>Read this honestly</h3>
      <p>On the hard tier the agent goes from <strong>{pt.get('hard', {}).get('baseline_f1', 0):.3f}</strong>
      to <strong>{pt.get('hard', {}).get('agent_f1', 0):.3f}</strong>. That is the result the
      staged pipeline was built for: those cases are hard precisely because the
      vulnerability never appears as a local textual pattern, and resolving an internal
      call graph is something the baseline structurally cannot do.</p>
      <p>On the seed tier it goes the other way, from
      <strong>{pt.get('seed', {}).get('baseline_f1', 0):.3f}</strong> down to
      <strong>{pt.get('seed', {}).get('agent_f1', 0):.3f}</strong>, and overall the agent
      currently <strong>loses</strong> to the baseline. That is a real regression, not a
      presentation choice, and it is on this page because a benchmark you only publish
      when it flatters you is not a benchmark.</p>
    </div>
    {board_tbl}
  </div>
</section>

<section>
  <h2>Workload, defined rather than asserted</h2>
  <div class="stack-lg">
    {wl_tbl}
    <div class="note">
      <h3>What "workload reduction" means here</h3>
      <p>Workload is the count of findings a human auditor has to adjudicate: every
      surfaced finding costs review time whether or not it turns out to be real. On this
      corpus the agent produced <strong>{d['review_reduction_pct']:+.1f}%</strong> change
      in that count, while missing <strong>{d['recall_cost']:+d}</strong> more real
      findings than the baseline.</p>
      <p>The two numbers are reported together deliberately. Any tool can cut review load
      by reporting less, so a workload figure without the missed count beside it is
      meaningless. This is also not a human time study &mdash; it is a proxy, and a claim
      about auditor hours would need one.</p>
    </div>
    <p>Self-correction kept {sc['findings_kept']} findings and dropped
    {sc['findings_dropped']} ({sc['drop_rate_pct']:.1f}%) across the corpus.</p>
  </div>
</section>
"""

    body = f"""
<section>
  <h2>How it works</h2>
  <div class="stack">
    <p>Four stages, each a separate backend call with its own prompt and its own parsed
    reply. Every stage is recorded. An auditing tool whose own reasoning cannot be
    inspected is not usable for the thing it is meant to support &mdash; the trail is what
    makes a disagreement with a human auditor resolvable instead of a matter of trust.</p>
    <p>The sandbox is read-only by construction. The agent receives contract source as
    text and has no execution, filesystem or network capability, so nothing it produces
    can act on a chain.</p>
  </div>
</section>

<section>
  <h2>A worked example &mdash; {sk.esc(ex['contract_id'])}</h2>
  <div class="stack-lg">
    {stage_tbl}
    {findings_tbl}
    <div class="note">
      <h3>Why this case</h3>
      <p>Cross-function reentrancy. The external call sits one frame down inside
      <code>_send()</code>, so the call and the state write are never adjacent in the
      source and no local pattern can connect them. Resolving that requires the internal
      call graph the <em>understand</em> stage builds.</p>
    </div>
  </div>
</section>
{body_comp}
<section>
  <h2>Backends</h2>
  <div class="stack-lg">
    {sk.table(["Backend", "Language model", "Needs a key", "Use"],
              [["StubBackend", "no", "no",
                "Runs in CI. Exercises the pipeline; not evidence about LLM performance."],
               ["OpenAICompatibleBackend", "yes", "yes",
                "Any OpenAI-compatible endpoint. Produces the dated run a claim can cite."]])}
    <p>A backend is anything with <code>complete(stage, prompt, **kw) -&gt; str</code>.
    Swapping one in changes no other module.</p>
  </div>
</section>

<section>
  <h2>Reproduce it</h2>
  <div class="stack">
    <pre>cd llm-audit-agent
pip install -r requirements.txt
python -m pytest tests/ -q
python -m src.demo          # stub backend, no key needed

# against a real model
export OPENAI_API_KEY=...
python -m src.demo --backend openai</pre>
  </div>
</section>

<section>
  <h2>What this does not establish</h2>
  <div class="stack">
    <ul class="tight">
      <li>No language model has been run against this corpus yet. Every score on this
      page comes from the symbolic stub, and none of it supports a claim about LLM
      audit performance.</li>
      <li>The agent currently loses to the rule-based baseline overall. Until that is
      no longer true, there is no workload-reduction result to cite.</li>
      <li>Workload is a proxy &mdash; findings to adjudicate &mdash; not measured
      auditor hours. A claim about time saved needs a human study.</li>
      <li>The corpus is 17 authored cases. Nothing here generalises to production
      contracts.</li>
    </ul>
  </div>
</section>
"""
    return sk.build(ROOT, META, body, results)

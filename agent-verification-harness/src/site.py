"""Builds website/ from the last demo run."""

from __future__ import annotations

import pathlib

from . import sitekit as sk

ROOT = pathlib.Path(__file__).resolve().parent.parent

META = {
    "name": "Agent Verification Harness",
    "slug": "agent-verification-harness",
    "repo": "1.0-Secure-Ai-Agent-Infrastructure",
    "pillar": "Cross-cutting — trustworthy AI",
    "tagline": "Grounding and citation checks, hallucination detection, and "
               "tamper-evident tool-call logging for tool-using agents.",
    "tags": [("grounding", ""), ("citation checking", ""),
             ("hash-chained audit log", ""), ("authored transcripts", "demo")],
    "banner": "Scored against six authored transcripts with twelve labelled claims. "
              "The transcripts test the harness, not any real agent, and they are "
              "small enough that the precision and recall below should be read as a "
              "smoke test rather than a benchmark result.",
}


def build_site(results: dict) -> pathlib.Path:
    g = results["grounding"]
    sweep = results["sweep"]
    ta = results["tool_audit"]

    metrics = sk.metric_grid([
        ("Claims checked", g["n_claims"], "across 6 transcripts"),
        ("Precision", f"{g['precision']:.2f}", "of flags that were real"),
        ("Recall", f"{g['recall']:.2f}", "of bad claims caught"),
        ("Fabricated caught", f"{g['per_kind']['fabricated']['caught']}"
                              f"/{g['per_kind']['fabricated']['total']}",
         "invented numbers"),
    ])

    kind_tbl = sk.table(
        ["Claim type", "Total", "Caught / false flags", "What it tests"],
        [["fabricated", g["per_kind"]["fabricated"]["total"],
          g["per_kind"]["fabricated"]["caught"],
          "A number appearing in no source — the highest-signal marker"],
         ["unsupported", g["per_kind"]["unsupported"]["total"],
          g["per_kind"]["unsupported"]["caught"],
          "Plausible prose with no supporting span and no number to catch it"],
         ["miscited", g["per_kind"].get("miscited", {}).get("total", 0),
          g["per_kind"].get("miscited", {}).get("caught", 0),
          "True claim attributed to the wrong source — its own failure mode"],
         ["grounded", g["per_kind"]["ok"]["total"],
          g["per_kind"]["ok"]["false_flags"],
          "Correct claims — any flag here is a false positive"]],
        numeric_cols=(1, 2))

    sweep_chart = sk.line_chart(
        [("precision", [(r["threshold"], r["precision"]) for r in sweep]),
         ("recall", [(r["threshold"], r["recall"]) for r in sweep]),
         ("F1", [(r["threshold"], r["f1"]) for r in sweep])],
        xlabel="grounding threshold", ylabel="score")

    verdict_rows = [
        [v["tid"], v["claim"][:78] + ("…" if len(v["claim"]) > 78 else ""),
         v["label"], "flagged" if v["flagged"] else "passed",
         f"{v['score']:.2f}", v["reason"][:60]]
        for v in g["verdicts"]]
    verdict_tbl = sk.table(
        ["Transcript", "Claim", "Ground truth", "Verdict", "Score", "Reason"],
        verdict_rows, numeric_cols=(4,))

    log_tbl = sk.table(
        ["Property", "Value"],
        [["Tool calls recorded", ta["stats"]["n_calls"]],
         ["Failures captured", ta["stats"]["n_failures"]],
         ["Chain intact before tampering", str(ta["stats"]["chain_intact"])],
         ["Tampering detected", str(ta["tamper_detected"])],
         ["Detected at record index", ta["tamper_index"]],
         ["Chain intact after restore", str(ta["restored_intact"])]],
        numeric_cols=(1,))

    body = f"""
<section>
  <h2>What it checks</h2>
  <div class="stack">
    <p>Three things, each independently reportable. <strong>Grounding</strong>: is there a
    span in the sources the agent actually retrieved that supports this claim?
    <strong>Citation correctness</strong>: does the marker it attached point at the source
    that contains that span? <strong>Fabrication</strong>: does the claim contain a number
    that appears in no source at all?</p>
    <p>Keeping them separate matters. A claim can be perfectly grounded and wrongly
    cited, which is a different failure from an invented figure and calls for a
    different fix.</p>
    <p>Everything here is lexical and inspectable. That is a deliberate constraint: a
    verification layer that is itself a black box moves the trust problem rather than
    solving it. The cost is that paraphrase is under-credited, which is why the
    threshold curve below is published rather than a single tuned number.</p>
  </div>
</section>

<section>
  <h2>This run</h2>
  <div class="stack-lg">
    {metrics}
    {kind_tbl}
    <p class="mono" style="color:var(--muted);font-size:12.5px">
      generated {sk.esc(results['generated_at'])} &middot; {sk.esc(results['data_source'])}
    </p>
  </div>
</section>

<section>
  <h2>Threshold sensitivity</h2>
  <div class="stack-lg">
    {sweep_chart}
    <div class="note">
      <h3>Why the whole curve is here</h3>
      <p>A single operating point is a choice, and publishing only the flattering one is
      how a harness gets tuned to its own test set. The curve shows what the threshold
      buys and what it costs across the range. Fabricated-number detection is threshold
      independent &mdash; a number that appears in no source is caught regardless &mdash;
      which is why recall never falls to zero at the strict end.</p>
    </div>
  </div>
</section>

<section>
  <h2>The false positive that is still here</h2>
  <div class="stack">
    <div class="note">
      <h3>Why it has not been tuned away</h3>
      <p>One correctly grounded claim is still flagged: <em>"The FOMC held rates at 4.25
      to 4.5 percent"</em>, against a source that says <em>"The Federal Open Market
      Committee held the target range for the federal funds rate at 4.25 to 4.5
      percent."</em> Same fact, almost no shared vocabulary. Lexical grounding cannot
      see through the abbreviation, and lowering the threshold far enough to admit it
      would start admitting genuinely unsupported claims too.</p>
      <p>This is the honest cost of an inspectable checker, and it is on the page rather
      than removed from the test set. An alias table or an embedding-based scorer would
      close it &mdash; and would move some of the reasoning back inside a box you cannot
      read. That trade is a decision, not an oversight.</p>
    </div>
  </div>
</section>

<section>
  <h2>Every claim, every verdict</h2>
  <div class="stack">
    {verdict_tbl}
  </div>
</section>

<section>
  <h2>Tamper-evident tool log</h2>
  <div class="stack-lg">
    {log_tbl}
    <div class="note">
      <h3>What the hash chain does and does not prove</h3>
      <p>Each record is hashed together with the previous record's hash, so editing any
      entry after the fact breaks every hash downstream of it. The run above edits one
      argument in record 1 and the chain reports the break at exactly that index.</p>
      <p>This proves the log has not been altered since it was written. It does not prove
      who wrote it &mdash; there is no key management here and no signing. Calling it
      tamper-evident rather than tamper-proof is the accurate description.</p>
    </div>
  </div>
</section>

<section>
  <h2>Reproduce it</h2>
  <div class="stack">
    <pre>cd agent-verification-harness
pip install -r requirements.txt
python -m pytest tests/ -q
python -m src.demo</pre>
  </div>
</section>

<section>
  <h2>What this does not establish</h2>
  <div class="stack">
    <ul class="tight">
      <li>Twelve claims across six authored transcripts. That is a smoke test. No
      precision or recall figure here generalises to real agent output.</li>
      <li>The harness has never been run against a production agent, and the
      transcripts were written by the same person who wrote the checks.</li>
      <li>Claim splitting is sentence-level, which is coarse; a claim spanning two
      sentences is scored as two.</li>
      <li>Grounding is lexical, so a correct paraphrase with no shared vocabulary
      scores as unsupported. One such case is live in this run and is described
      above rather than removed.</li>
      <li>Two bugs found by this run are worth recording: citation markers were
      being scored as claim content (<code>[S1]</code> contains the digit 1, which
      the fabrication check read as an invented number), and the number pattern
      captured a sentence-final period so <code>2023.</code> never matched
      <code>2023</code>. Both are now regression-tested. A harness that had only
      ever been run on its own happy path would have shipped with both.</li>
    </ul>
  </div>
</section>
"""
    return sk.build(ROOT, META, body, results)

"""Builds website/ from the last demo run."""

from __future__ import annotations

import pathlib

from . import sitekit as sk
from .screen import CLASSES

ROOT = pathlib.Path(__file__).resolve().parent.parent

META = {
    "name": "Skill Screening",
    "slug": "direction-1-skill-screening",
    "repo": "1.0-Secure-Ai-Agent-Infrastructure",
    "pillar": "Secure AI Agent Infrastructure",
    "tagline": "An adversarially-robust screener for third-party agent skills / MCP "
               "servers — manifest, prompt-layer and behavioural analysis — scored "
               "against a naive keyword baseline on an authored benchmark.",
    "tags": [("manifest diff", ""), ("prompt-layer", ""), ("sandbox trace", ""),
             ("adversarial", "warn"), ("authored corpus", "demo")],
    "banner": "This run used an AUTHORED, hand-written corpus of skills, not data "
              "scraped from any real skill or MCP registry. is_synthetic is true. "
              "The scores below measure the analyzers on cases this project's own "
              "author wrote; they are a skeleton, not a measured result on the wild. "
              "The proposal's real 500-1000-skill corpus is explicitly future work.",
    "datanote": "The corpus is 15 authored skill records; the real registry corpus is future work.",
}

_CLASS_NOTE = {
    "tool_poisoning": "instructions in the tool text that push the model to act "
                      "outside the tool's job (read secrets, exfiltrate)",
    "instruction_smuggling": "injected imperatives aimed at the model "
                             "(\"ignore previous instructions\", role override)",
    "homoglyph_obfuscation": "confusable / mixed-script characters used to hide the "
                            "words above from a literal scanner",
    "encoded_payload": "base64 / hex blobs that decode to a hidden instruction",
    "privilege_creep": "sensitive capabilities newly added between two versions of "
                       "the same skill",
    "undeclared_egress": "hosts / files / tools the sandbox trace shows but the "
                        "manifest never declared",
}


def build_site(results: dict) -> pathlib.Path:
    stats = results["corpus"]
    board = results["leaderboard"]
    sc = results["screening_tool"]
    bl = results["baseline"]

    top = board[0]
    metrics = sk.metric_grid([
        ("Skills in corpus", stats["total"],
         f"{stats['benign']} benign / {stats['malicious']} malicious"),
        ("Adversarial skills", stats["adversarial"],
         "use homoglyph / encoding / paraphrase / zero-width evasion"),
        ("Best macro-F1", f"{top['macro_f1']:.3f}", top["detector"]),
        ("Adversarial catch — tool",
         f"{sc['adversarial']['catch_rate']:.3f}",
         f"{sc['adversarial']['caught']}/{sc['adversarial']['total']} caught"),
        ("Adversarial catch — baseline",
         f"{bl['adversarial']['catch_rate']:.3f}",
         f"{bl['adversarial']['caught']}/{bl['adversarial']['total']} caught"),
    ])

    board_tbl = sk.table(
        ["Rank", "Detector", "Macro-P", "Macro-R", "Macro-F1", "Adversarial catch"],
        [[r["rank"], r["detector"], f"{r['macro_precision']:.3f}",
          f"{r['macro_recall']:.3f}", f"{r['macro_f1']:.3f}",
          f"{r['adversarial_caught']}/{r['adversarial_total']} "
          f"({r['adversarial_catch_rate']:.3f})"] for r in board],
        numeric_cols=(0, 2, 3, 4))

    board_chart = sk.bar_chart(
        [(f"{r['detector']} — macro-F1", r["macro_f1"]) for r in board]
        + [(f"{r['detector']} — adversarial", r["adversarial_catch_rate"])
           for r in board],
        fmt="{:.3f}")

    # per-class F1, screening vs baseline
    pc_rows = []
    for c in CLASSES:
        s = sc["per_class"][c]
        b = bl["per_class"][c]
        pc_rows.append([c, f"{s['precision']:.2f}", f"{s['recall']:.2f}",
                        f"{s['f1']:.2f}", f"{b['f1']:.2f}"])
    per_class_tbl = sk.table(
        ["Class", "Tool P", "Tool R", "Tool F1", "Baseline F1"],
        pc_rows, numeric_cols=(1, 2, 3, 4))

    comp_rows = [[c, stats["by_class"].get(c, 0), _CLASS_NOTE[c]] for c in CLASSES]
    comp_tbl = sk.table(
        ["Vulnerability class", "In corpus", "What it is"],
        comp_rows, numeric_cols=(1,))

    fw = results["future_work"]
    body = f"""
<section>
  <h2>What it screens for</h2>
  <div class="stack">
    <p>A third-party agent skill (or MCP server) is untrusted code you invite
    into a privileged session. This tool screens one the way the sibling
    <code>3-llm-audit-agent</code> screens a smart contract: treat it as untrusted
    input, analyse it without granting it real privileges, and attach concrete
    evidence to every flag so a human can adjudicate it. Three analyzers, all
    dependency-free and CPU-only:</p>
    <ul class="tight">
      <li><strong>Manifest analysis</strong> &mdash; diff the declared
      permissions/verbs against a prior version and flag newly-added
      <em>sensitive</em> capabilities (privilege creep).</li>
      <li><strong>Prompt-layer analysis</strong> &mdash; over the description and
      docstrings the model reads, detect tool-poisoning and instruction-smuggling,
      plus the evasion families that beat a naive scanner: homoglyph substitution
      and encoded (base64/hex) payloads.</li>
      <li><strong>Behavioural analysis</strong> &mdash; diff declared capabilities
      against the egress a sandbox trace actually observed, and flag anything the
      skill touched but never declared.</li>
    </ul>
  </div>
</section>

<section>
  <h2>Results on the authored corpus</h2>
  <div class="stack-lg">
    {metrics}
    {board_chart}
    {board_tbl}
    <div class="note">
      <h3>Read this honestly</h3>
      <p>The screening tool reaches <strong>{sc['macro_f1']:.3f}</strong> macro-F1
      against the naive baseline's <strong>{bl['macro_f1']:.3f}</strong>, and catches
      <strong>{sc['adversarial']['caught']}/{sc['adversarial']['total']}</strong>
      adversarial skills where the baseline catches
      <strong>{bl['adversarial']['caught']}/{bl['adversarial']['total']}</strong>.
      That gap is the point of the direction: the baseline can only match literal
      bad words, so a homoglyph, an encoding, or a paraphrase walks straight past it.</p>
      <p>But these are numbers on {stats['total']} skills <em>the author wrote</em>.
      A detector graded on its author's own examples will flatter itself; the score
      is evidence the pipeline runs and the analyzers fire on their target classes,
      not evidence about real-world skills. The tool also still
      <strong>misses</strong> at least one adversarial case
      (catch rate {sc['adversarial']['catch_rate']:.3f}, not 1.000) &mdash; a
      zero-width-space evasion the current analyzers do not normalize &mdash; and
      that miss is left in the corpus and reported rather than papered over.</p>
    </div>
    {per_class_tbl}
  </div>
</section>

<section>
  <h2>Corpus composition</h2>
  <div class="stack-lg">
    {comp_tbl}
    <div class="note">
      <p>{sk.esc(stats['total'])} skills: {sk.esc(stats['benign'])} benign,
      {sk.esc(stats['malicious'])} malicious, of which {sk.esc(stats['adversarial'])}
      use an explicit evasion technique. Every record is labelled
      <code>is_synthetic: true</code>. This is not registry data.</p>
    </div>
  </div>
</section>

<section>
  <h2>Reproduce it</h2>
  <div class="stack">
    <pre>cd direction-1-skill-screening
pip install -r requirements.txt
python -m pytest tests/ -q
python -m src.demo          # rewrites results/latest.json and this site</pre>
  </div>
</section>

<section>
  <h2>What this skeleton does <em>not</em> establish</h2>
  <div class="stack">
    <ul class="tight">
      <li>The corpus is {sk.esc(stats['total'])} authored skills, not scraped from
      any real registry. Nothing here generalises to skills in the wild.</li>
      <li>{sk.esc(fw)}</li>
      <li>The scores are on the author's own examples. Treat them as a
      demonstration that the pipeline runs, not as a measured detection rate.</li>
    </ul>
  </div>
</section>
"""
    return sk.build(ROOT, META, body, results)

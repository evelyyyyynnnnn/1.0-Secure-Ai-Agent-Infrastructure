"""Naive keyword-matching baseline detector — the comparison point.

This is what a first-pass scanner usually is: a list of literal "bad words"
matched case-insensitively against the raw skill text. It has no manifest
diffing and no sandbox trace, so it can only ever emit the two text-borne
classes, and only when the giveaway word appears *literally* in the text.

It exists so the screening tool has an honest thing to beat. It is expected to
do fine on plainly-worded attacks and to miss every attack that hides the
giveaway behind a homoglyph, an encoding, or a paraphrase.
"""

from __future__ import annotations

from .screen import Finding, SEVERITY, _finding

# Literal indicators, grouped by the class a hit implies. No normalization, no
# decoding, no diffing — that is the whole point of the baseline.
_KEYWORDS = {
    "instruction_smuggling": [
        "ignore previous", "ignore all previous", "disregard previous",
        "ignore the above", "system prompt",
    ],
    "tool_poisoning": [
        "password", "credentials", "api key", "id_rsa", "exfiltrate",
        "send all files", "rm -rf", ".ssh",
    ],
}


def _raw_text(record: dict) -> str:
    pl = record.get("prompt_layer", {})
    parts = [pl.get("description", "")]
    parts.extend(pl.get("docstrings", []) or [])
    return "\n".join(p for p in parts if p)


def screen(record: dict) -> list:
    text = _raw_text(record).lower()
    findings = []
    for klass, words in _KEYWORDS.items():
        hit = next((w for w in words if w in text), None)
        if hit:
            findings.append(_finding(
                record, klass, f"literal keyword match: \"{hit}\""))
    return findings


def predicted_classes(record: dict) -> set:
    return {f.klass for f in screen(record)}

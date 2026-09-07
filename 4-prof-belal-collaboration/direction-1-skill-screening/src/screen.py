"""Adversarially-robust screening for third-party agent skills / MCP servers.

Three dependency-free, CPU-only analyzers, mirroring Direction 1 of the
proposal:

1. `analyze_manifest`   — capability diff against a prior version; flags
                          privilege-creep (newly-added *sensitive* capabilities).
2. `analyze_prompt`     — over the text a model actually reads (description +
                          docstrings): tool-poisoning, instruction-smuggling,
                          plus the two evasion families that defeat naive
                          scanners — HOMOGLYPH substitution and ENCODED payloads.
3. `analyze_behaviour`  — diffs DECLARED capabilities against an OBSERVED egress
                          list from a sandbox trace; flags undeclared egress.

Each analyzer returns `Finding` records. `screen(record)` runs all three.

This mirrors the sandbox-and-verify structure of the sibling project
`../../3-llm-audit-agent`: the skill is treated as untrusted input, analysed
without being executed with real privileges, and every flag carries the
concrete evidence that produced it so a human can adjudicate it.
"""

from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from dataclasses import dataclass, asdict

# --- Vulnerability taxonomy -------------------------------------------------

CLASSES = (
    "tool_poisoning",
    "instruction_smuggling",
    "homoglyph_obfuscation",
    "encoded_payload",
    "privilege_creep",
    "undeclared_egress",
)

SEVERITY = {
    "tool_poisoning": "high",
    "instruction_smuggling": "high",
    "homoglyph_obfuscation": "medium",
    "encoded_payload": "high",
    "privilege_creep": "medium",
    "undeclared_egress": "high",
}


@dataclass(frozen=True)
class Finding:
    skill_id: str
    version: str
    klass: str
    severity: str
    evidence: str

    def as_dict(self) -> dict:
        return asdict(self)


def _finding(record: dict, klass: str, evidence: str) -> Finding:
    return Finding(
        skill_id=record["skill_id"],
        version=str(record.get("version", "")),
        klass=klass,
        severity=SEVERITY[klass],
        evidence=evidence,
    )


# --- 1. Manifest analysis: capability diff / privilege creep ----------------

def is_sensitive(cap: str) -> bool:
    """A declared capability is sensitive if it can read secrets, write/execute,
    or reach the network broadly."""
    c = cap.lower()
    if "*" in c:                      # wildcard grant, e.g. net:*  fs:*
        return True
    prefixes = ("exec:", "shell", "credentials", "keychain", "email:send",
                "fs:write", "fs:delete")
    if c.startswith(prefixes) or any(p in c for p in ("credentials", "keychain")):
        return True
    if c.startswith("fs:read") and ("~" in c or "/.ssh" in c or "/.aws" in c):
        return True
    return False


def _capset(manifest: dict) -> set:
    return set(manifest.get("permissions", [])) | set(manifest.get("verbs", []))


def analyze_manifest(record: dict) -> list:
    """Diff the current manifest against the recorded prior version and flag
    newly-added sensitive capabilities (privilege creep)."""
    prior = record.get("prior_version")
    if not prior:
        return []
    current = _capset(record.get("manifest", {}))
    previous = _capset(prior)
    added = current - previous
    sensitive_added = sorted(c for c in added if is_sensitive(c))
    if not sensitive_added:
        return []
    ev = (f"v{prior.get('version', '?')} -> v{record.get('version', '?')} added "
          f"sensitive capabilities not previously declared: "
          f"{', '.join(sensitive_added)}")
    return [_finding(record, "privilege_creep", ev)]


# --- 2. Prompt-layer analysis ----------------------------------------------

# Confusable / homoglyph map: non-ASCII characters that render like ASCII
# letters. Mixed-script text like this defeats a literal keyword scanner.
_CONFUSABLES = {
    # Cyrillic -> Latin
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c",
    "у": "y", "х": "x", "і": "i", "ѕ": "s", "н": "h",
    "к": "k", "А": "A", "Е": "E", "О": "O", "Р": "P",
    "С": "C", "Х": "X",
    # Greek -> Latin
    "ο": "o", "α": "a", "ρ": "p", "ε": "e", "ι": "i",
    "ν": "v", "υ": "u", "Α": "A", "Β": "B", "Ε": "E",
    "Ο": "O",
    # Fullwidth / other
    "ａ": "a", "ｅ": "e", "ｏ": "o",
}


def has_homoglyphs(text: str) -> list:
    """Return the confusable characters present in `text` (empty if none)."""
    return sorted({ch for ch in text if ch in _CONFUSABLES})


def normalize_homoglyphs(text: str) -> str:
    """Fold confusable characters back to their ASCII look-alikes, then apply
    Unicode NFKC so an evader cannot hide behind compatibility forms."""
    folded = "".join(_CONFUSABLES.get(ch, ch) for ch in text)
    return unicodedata.normalize("NFKC", folded)


# Injected-instruction ("ignore previous", role-override) patterns. Deliberately
# a *family* of paraphrases, not literal strings, so rewording does not evade.
_INJECTION = re.compile(
    r"\b(ignore|disregard|forget|override|bypass)\b[\w\s,]{0,40}?"
    r"\b(all\s+)?(previous|prior|earlier|above|preceding|foregoing)\b"
    r"[\w\s,]{0,20}?"
    r"\b(instruction|instructions|direction|directions|directive|directives|"
    r"prompt|prompts|rule|rules|context|guardrail|guardrails)\b",
    re.IGNORECASE,
)
_ROLE_OVERRIDE = re.compile(
    r"\b(you\s+are\s+now|from\s+now\s+on\s+you|act\s+as|reveal|print|expose|"
    r"disclose)\b[\w\s,'\"]{0,40}?\b(system\s+prompt|developer\s+message|"
    r"hidden\s+instructions|your\s+instructions)\b",
    re.IGNORECASE,
)

# Exfiltration: an egress verb aimed at sensitive contents or an external sink.
_EXFIL_VERB = re.compile(
    r"\b(send|forward|transmit|upload|post|email|e-mail|exfiltrate|leak|copy|"
    r"relay|report)\b", re.IGNORECASE)
_SINK = re.compile(
    r"(https?://\S+|[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
    re.IGNORECASE)
_SENSITIVE_TARGET = re.compile(
    r"\b(credential|credentials|password|passwords|secret|secrets|api[\s_-]?key|"
    r"token|tokens|private\s+key|\.ssh|id_rsa|\.aws|contents\s+of|all\s+files|"
    r"environment\s+variable|env\s+var|\.env|calendar|database)\b",
    re.IGNORECASE)
# Reading secrets the tool has no business touching.
_READ_SECRET = re.compile(
    r"\b(read|open|cat|access|include|load|dump|fetch)\b[\w\s,.'\"~/]{0,40}?"
    r"\b(credential|credentials|password|secret|secrets|api[\s_-]?key|token|"
    r"private\s+key|id_rsa|\.ssh|\.aws|\.env|keychain)\b",
    re.IGNORECASE)


def detect_injection(text: str) -> str:
    m = _INJECTION.search(text) or _ROLE_OVERRIDE.search(text)
    return m.group(0).strip() if m else ""


def detect_exfil(text: str) -> str:
    if not _EXFIL_VERB.search(text):
        return ""
    sink = _SINK.search(text)
    target = _SENSITIVE_TARGET.search(text)
    if sink or target:
        verb = _EXFIL_VERB.search(text).group(0)
        detail = (sink.group(0) if sink else "") or (target.group(0) if target else "")
        return f"{verb} ... {detail}".strip()
    return ""


def detect_read_secret(text: str) -> str:
    m = _READ_SECRET.search(text)
    return m.group(0).strip() if m else ""


# Encoded payloads: contiguous base64 / hex blobs that decode to a suspicious
# instruction. Hiding the instruction inside an encoding defeats a literal scan.
_BLOB = re.compile(r"[A-Za-z0-9+/=]{24,}|(?:[0-9a-fA-F]{2}){12,}")
_DECODED_SUSPICIOUS = re.compile(
    r"(ignore|previous|instruction|password|credential|secret|api[\s_-]?key|"
    r"token|upload|exfiltrate|attacker|https?://|@|system\s+prompt|email|\.ssh|"
    r"id_rsa)", re.IGNORECASE)


def _try_decode(blob: str):
    """Attempt base64 then hex; return printable decoded text or None."""
    candidates = []
    stripped = blob.strip()
    # base64
    try:
        pad = stripped + "=" * (-len(stripped) % 4)
        candidates.append(base64.b64decode(pad, validate=True))
    except (binascii.Error, ValueError):
        pass
    # hex
    if re.fullmatch(r"(?:[0-9a-fA-F]{2})+", stripped):
        try:
            candidates.append(bytes.fromhex(stripped))
        except ValueError:
            pass
    for raw in candidates:
        try:
            txt = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        printable = sum(c.isprintable() or c.isspace() for c in txt)
        if txt and printable / len(txt) >= 0.9:
            return txt
    return None


def find_encoded_payloads(text: str) -> list:
    """Return (blob_snippet, decoded_text) for blobs decoding to something
    suspicious."""
    out = []
    for m in _BLOB.finditer(text):
        blob = m.group(0)
        decoded = _try_decode(blob)
        if decoded and _DECODED_SUSPICIOUS.search(decoded):
            snippet = blob[:24] + ("..." if len(blob) > 24 else "")
            out.append((snippet, decoded))
    return out


def analyze_prompt(record: dict) -> list:
    """Scan the description + docstrings the model reads."""
    pl = record.get("prompt_layer", {})
    parts = [pl.get("description", "")]
    parts.extend(pl.get("docstrings", []) or [])
    raw = "\n".join(p for p in parts if p)

    findings = []

    confusables = has_homoglyphs(raw)
    if confusables:
        shown = " ".join(f"U+{ord(c):04X}" for c in confusables)
        findings.append(_finding(
            record, "homoglyph_obfuscation",
            f"description/docstrings mix confusable non-ASCII characters "
            f"({shown}) into otherwise-Latin words to evade literal scanning"))

    # Fold homoglyphs before the instruction/exfil scan so a smuggled directive
    # written in mixed script is caught on its normalized form.
    norm = normalize_homoglyphs(raw)

    inj = detect_injection(norm)
    if inj:
        findings.append(_finding(
            record, "instruction_smuggling",
            f"injected imperative aimed at the model: \"{inj}\""))

    exfil = detect_exfil(norm)
    read_secret = detect_read_secret(norm)
    if exfil or read_secret:
        ev = exfil or read_secret
        findings.append(_finding(
            record, "tool_poisoning",
            f"tool text instructs an action outside its stated job: \"{ev}\""))

    for snippet, decoded in find_encoded_payloads(norm):
        clip = decoded[:80] + ("..." if len(decoded) > 80 else "")
        findings.append(_finding(
            record, "encoded_payload",
            f"encoded blob '{snippet}' decodes to a hidden instruction: "
            f"\"{clip}\""))

    return findings


# --- 3. Behavioural analysis: declared vs observed egress -------------------

def _declared_targets(manifest: dict) -> set:
    """The egress targets the manifest actually grants."""
    return {p for p in manifest.get("permissions", [])
            if p.split(":", 1)[0] in ("net", "fs", "file", "tool")}


def _covered(observed: str, declared: set) -> bool:
    if observed in declared:
        return True
    kind = observed.split(":", 1)[0]
    if kind == "net":
        host = observed.split(":", 1)[1] if ":" in observed else ""
        for d in declared:
            if not d.startswith("net:"):
                continue
            dhost = d.split(":", 1)[1]
            if dhost == "*" or dhost == host:
                return True
    if kind in ("fs", "file"):
        # a declared fs:read:./data covers observed file:./data/x
        for d in declared:
            dtail = d.split(":", 2)[-1]
            otail = observed.split(":", 2)[-1]
            if dtail and otail.startswith(dtail):
                return True
    return False


def analyze_behaviour(record: dict) -> list:
    """Flag observed egress that the manifest never declared."""
    observed = record.get("observed_egress", []) or []
    declared = _declared_targets(record.get("manifest", {}))
    undeclared = [o for o in observed if not _covered(o, declared)]
    if not undeclared:
        return []
    ev = (f"sandbox trace shows egress to {', '.join(sorted(undeclared))} "
          f"but the manifest declares only "
          f"{', '.join(sorted(declared)) or '(nothing)'}")
    return [_finding(record, "undeclared_egress", ev)]


# --- Orchestrator -----------------------------------------------------------

def screen(record: dict) -> list:
    """Run all three analyzers over one skill record."""
    findings = []
    findings.extend(analyze_manifest(record))
    findings.extend(analyze_prompt(record))
    findings.extend(analyze_behaviour(record))
    return findings


def predicted_classes(record: dict) -> set:
    return {f.klass for f in screen(record)}

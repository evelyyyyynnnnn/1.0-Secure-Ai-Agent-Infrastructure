"""Detectors evaluated against the corpus.

A detector is any callable `(source: str) -> set[str]` returning the vulnerability
classes it believes are present. That signature is the whole plug-in contract, so
an LLM-based auditor can be scored against the same harness as a regex baseline
by wrapping it in the same shape.

`PatternDetector` below is the reference baseline. It is deliberately simple --
its job is to be the number a smarter detector has to beat, not to be good.
"""

from __future__ import annotations

import re
from typing import Callable, Protocol

from .corpus import CLASSES

Detector = Callable[[str], set]


class DetectorLike(Protocol):
    name: str

    def __call__(self, source: str) -> set: ...


def _strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    return src


def _pragma_major_minor(src: str) -> tuple[int, int] | None:
    m = re.search(r"pragma\s+solidity\s*[\^>=~]*\s*(\d+)\.(\d+)", src)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


class PatternDetector:
    """Static pattern matching. The baseline every other detector is scored against."""

    name = "pattern-baseline"

    def __call__(self, source: str) -> set:
        src = _strip_comments(source)
        found: set[str] = set()

        # --- reentrancy: a value-bearing external call followed by a state write
        for m in re.finditer(r"\.call\{[^}]*value\s*:[^}]*\}\s*\(", src):
            tail = src[m.end():]
            # a balance/mapping assignment after the call, still inside the function
            body = tail.split("}")[0]
            if re.search(r"\b\w+\s*\[[^\]]+\]\s*=", body) or re.search(
                r"\b(owner|admin|leader)\s*=", body
            ):
                found.add("reentrancy")
                break

        # --- unchecked low-level call: send/call whose bool result is discarded
        for m in re.finditer(r"(?<![\w.])(\w[\w.\[\]]*)\.(send|call)\s*[\({]", src):
            line_start = src.rfind("\n", 0, m.start()) + 1
            prefix = src[line_start:m.start()].strip()
            # assigned, required, or used in a condition -> checked
            if re.search(r"(=|require\s*\(|assert\s*\(|if\s*\()\s*$", prefix):
                continue
            if re.match(r"^\(?\s*bool", prefix):
                continue
            found.add("unchecked_call")
            break

        # --- tx.origin used for authorisation
        if re.search(r"tx\.origin\s*==|==\s*tx\.origin", src):
            found.add("tx_origin_auth")

        # --- timestamp / block number as a decision or randomness input
        if re.search(r"block\.(timestamp|number)|(?<!\w)now(?!\w)", src):
            if re.search(
                r"(require|if|return|while)\s*\([^)]*block\.(timestamp|number)", src
            ) or re.search(r"keccak256\s*\([^)]*block\.(timestamp|number)", src) or \
               re.search(r"encodePacked\s*\([^)]*block\.(timestamp|number)", src):
                found.add("timestamp_dependence")

        # --- missing access control on a state-critical setter
        for m in re.finditer(
            r"function\s+(\w+)\s*\([^)]*\)\s*([^{;]*)\{", src
        ):
            name, mods = m.group(1), m.group(2)
            body = _function_body(src, m.end() - 1)
            writes_privileged = re.search(r"\b(owner|admin|arbiter)\s*=", body)
            sweeps = re.search(r"address\(this\)\.balance", body)
            if not (writes_privileged or sweeps):
                continue
            if name == "constructor":
                continue
            guarded = ("onlyOwner" in mods or "onlyAdmin" in mods
                       or re.search(r"require\s*\(\s*msg\.sender\s*==", body)
                       or re.search(r"require\s*\(\s*tx\.origin\s*==", body))
            if not guarded:
                found.add("missing_access_control")
                break

        # --- unprotected selfdestruct
        for m in re.finditer(r"function\s+(\w+)\s*\([^)]*\)\s*([^{;]*)\{", src):
            mods = m.group(2)
            body = _function_body(src, m.end() - 1)
            if "selfdestruct" in body:
                guarded = ("onlyOwner" in mods
                           or re.search(r"require\s*\(\s*msg\.sender\s*==", body))
                if not guarded:
                    found.add("unprotected_selfdestruct")
                    break

        # --- integer overflow: unchecked arithmetic before 0.8, or an unchecked block
        ver = _pragma_major_minor(src)
        pre_080 = ver is not None and (ver[0], ver[1]) < (0, 8)
        if pre_080 and re.search(r"[\w\]]\s*[-+*]\s*\w", src) and "SafeMath" not in src:
            found.add("integer_overflow")
        elif re.search(r"\bunchecked\s*\{", src):
            found.add("integer_overflow")

        return found


def _function_body(src: str, brace_idx: int) -> str:
    """Return the text between the brace at brace_idx and its match."""
    depth = 0
    for i in range(brace_idx, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[brace_idx + 1:i]
    return src[brace_idx + 1:]


class KeywordDetector:
    """A weaker baseline: flags a class if any of its keywords appear anywhere.

    Included because a benchmark needs a floor as well as a ceiling. It scores
    high recall and poor precision, which is exactly the failure mode a
    precision-blind benchmark would hide.
    """

    name = "keyword-floor"

    KEYWORDS = {
        "reentrancy": (r"\.call\{",),
        "unchecked_call": (r"\.send\s*\(", r"\.call\s*\{"),
        "tx_origin_auth": (r"tx\.origin",),
        "timestamp_dependence": (r"block\.timestamp", r"(?<!\w)now(?!\w)"),
        "missing_access_control": (r"\bowner\s*=", r"\badmin\s*="),
        "unprotected_selfdestruct": (r"selfdestruct",),
        "integer_overflow": (r"\+\s*\w", r"\*\s*\w"),
    }

    def __call__(self, source: str) -> set:
        src = _strip_comments(source)
        return {
            cls
            for cls, pats in self.KEYWORDS.items()
            if any(re.search(p, src) for p in pats)
        }


class NullDetector:
    """Reports nothing. The trivial precision-1.0 / recall-0.0 corner."""

    name = "null"

    def __call__(self, source: str) -> set:
        return set()


def default_detectors() -> list:
    return [PatternDetector(), KeywordDetector(), NullDetector()]

"""Input sanitiser: remove Solidity comments before a model reads the source.

Comments have no effect on what a contract does, but a language model reads
them as text. That makes them a channel for indirect prompt injection: anyone
who can get a contract in front of the agent can address the agent directly.
Stripping them removes that channel without changing the contract's behaviour.

String literals are preserved, so ``"//"`` inside a string is not treated as a
comment. This is a lexical pass, not a parser; it is the mitigation measured in
``run_injection_experiment.py``, not a general defence against injection
through identifiers or string contents.
"""

from __future__ import annotations


def strip_comments(src: str) -> str:
    out = []
    i, n = 0, len(src)
    in_str: str | None = None
    while i < n:
        c = src[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c in ("'", '"'):
            in_str = c
            out.append(c)
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j          # keep the newline so line numbers hold
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            block = src[i:] if j < 0 else src[i:j + 2]
            out.append("\n" * block.count("\n"))  # keep line numbers
            i = n if j < 0 else j + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)

"""Build labelled transcripts from real government documents.

Where the labels come from, stated plainly, because this is the part a reader
should interrogate:

  supported   a sentence taken from the source document. It is grounded by
              construction -- the source contains it.
  fabricated  the same sentence with one number changed. The document says
              3.0 percent; the claim says 4.7 percent. Unsupported by
              construction, and the specific failure a grounding check exists
              to catch.
  unsupported a sentence lifted from a DIFFERENT fetched document and cited to
              this one. Topically adjacent, genuinely not in the cited source
              -- the near miss that a naive keyword overlap check waves through.

The documents are real. The claims are constructed from them, and are NOT
model output. That distinction matters: this measures whether the checker can
detect ungrounded claims, not how often any particular model produces them.
Scoring real model output needs a model, an API key, and a separate run; the
harness accepts any transcript in this shape, so that path is open.
"""
from __future__ import annotations

import html
import pathlib
import re
from html.parser import HTMLParser

from .datakit import Fetcher, FetchError

ROOT = pathlib.Path(__file__).resolve().parent

_DROP = {"script", "style", "head", "title", "meta", "link", "noscript"}
_BREAK = {"p", "div", "br", "tr", "td", "th", "li", "h1", "h2", "h3", "h4"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in _DROP:
            self._skip += 1
        elif tag in _BREAK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _DROP:
            self._skip = max(0, self._skip - 1)
        elif tag in _BREAK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            # Source-file line wrapping inside a tag is not a paragraph break.
            # Keeping those newlines splits single sentences into fragments,
            # and every sentence-level operation downstream then works on half
            # a sentence. Only tags may end a line.
            self.parts.append(data.replace("\n", " ").replace("\r", " "))


def html_to_text(raw) -> str:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    p = _Text()
    p.feed(raw)
    t = html.unescape("".join(p.parts)).replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" ?\n ?", "\n", t)
    return re.sub(r"\n{2,}", "\n", t).strip()


NUM = re.compile(r"\b\d+(?:\.\d+)?\b")
SENT = re.compile(r"(?<=[.!?])\s+")


def sentences_with_numbers(text: str, min_words: int = 12,
                           max_words: int = 45) -> list:
    """Sentences long enough to be a claim and containing a checkable number."""
    out = []
    for para in text.split("\n"):
        for s in SENT.split(para):
            s = s.strip()
            w = s.split()
            if not (min_words <= len(w) <= max_words):
                continue
            if not NUM.search(s):
                continue
            # Navigation furniture and table rows are not prose claims.
            if s.count("|") or s.lower().startswith(("table", "footnote")):
                continue
            out.append(s)
    return out


def perturb_number(sentence: str) -> str | None:
    """Change the first number in a sentence to something clearly different.

    The perturbation has to be large enough not to be a rounding difference,
    or the label would be arguable rather than known.
    """
    m = NUM.search(sentence)
    if not m:
        return None
    original = m.group(0)
    try:
        val = float(original)
    except ValueError:
        return None
    new = val + max(1.7, abs(val) * 0.6)
    text = f"{new:.1f}" if "." in original else str(int(new))
    return sentence[:m.start()] + text + sentence[m.end():]


def build_transcripts(root=ROOT, per_doc: int = 3):
    # 3 is the true minimum, not a tuning choice: two sentences become
    # supported claims and the third is perturbed into a fabricated one. The
    # fourth claim in each transcript is borrowed from a different document.
    """Return (transcripts, provenance) built from the cached real documents."""
    from src.grounding import Claim, Source
    from src.transcripts import Transcript

    f = Fetcher(root)
    man = f.load_manifest()
    docs = {k: v for k, v in man["files"].items()
            if k.endswith((".htm", ".html"))}
    if not docs:
        raise FetchError(
            "no real documents cached. Run `python -m data.fetch` in a "
            "networked environment first; this harness will not report scores "
            "from the authored transcripts as if they came from real filings.")

    texts, prov = {}, []
    for dest, rec in sorted(docs.items()):
        sid = pathlib.Path(dest).stem.upper()
        body = html_to_text((f.raw / dest).read_bytes())
        sents = sentences_with_numbers(body)
        texts[sid] = {"text": body, "sentences": sents, "rec": rec}
        prov.append({"source_id": sid, "chars": len(body),
                     "candidate_sentences": len(sents),
                     "sha256": rec["sha256"][:16], "url": rec["url"],
                     "retrieved_utc": rec.get("retrieved_utc")})

    usable = {k: v for k, v in texts.items() if len(v["sentences"]) >= per_doc}
    if len(usable) < 2:
        raise FetchError(
            f"only {len(usable)} document(s) yielded enough numeric sentences; "
            f"at least 2 are needed so an unsupported claim can be borrowed "
            f"from a different real document rather than invented")

    ids = sorted(usable)
    transcripts = []
    for i, sid in enumerate(ids):
        other = ids[(i + 1) % len(ids)]
        sources = [Source(sid, usable[sid]["text"]),
                   Source(other, usable[other]["text"])]
        picks = usable[sid]["sentences"][:per_doc]
        borrowed = usable[other]["sentences"][0]

        claims, labels, answer_bits = [], {}, []
        for j, s in enumerate(picks[:2]):
            claims.append(Claim(s, [sid]))
            labels[len(claims) - 1] = "ok"
            answer_bits.append(f"{s} [{sid}]")

        fab = perturb_number(picks[2] if len(picks) > 2 else picks[-1])
        if fab:
            claims.append(Claim(fab, [sid]))
            labels[len(claims) - 1] = "fabricated"
            answer_bits.append(f"{fab} [{sid}]")

        claims.append(Claim(borrowed, [sid]))     # cited to the WRONG document
        labels[len(claims) - 1] = "unsupported"
        answer_bits.append(f"{borrowed} [{sid}]")

        transcripts.append(Transcript(
            tid=f"REAL-{sid}",
            question=f"What does the {sid} release report?",
            sources=sources,
            answer=" ".join(answer_bits),
            labels=labels,
            note=("claims constructed from real documents: two quoted, one with "
                  "a number altered, one lifted from a different real release "
                  "and cited here. Labels are known by construction; the claims "
                  "are not model output."),
        ))

    return transcripts, {"documents": prov, "n_transcripts": len(transcripts),
                         "claims_are_model_output": False}

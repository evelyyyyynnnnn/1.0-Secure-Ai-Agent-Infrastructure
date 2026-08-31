"""Fetch the real documents this harness should be grounding against.

    python -m data.fetch --list
    DATAKIT_UA="Your Name you@email" python -m data.fetch
    python -m data.fetch --verify

The authored transcripts paraphrase three real document types: an FOMC
statement, a BLS CPI release, and a 10-K risk-factor section. This fetches the
actual documents, which changes the difficulty in ways a paraphrase cannot
reproduce -- real releases are long, repetitive, full of near-duplicate
sentences, and contain many numbers the claim does not refer to. A grounding
check that works on a tidy three-sentence source and fails on a real one has
not been tested.

SEC requires a User-Agent naming a real contact; set DATAKIT_UA.
"""
from __future__ import annotations

import pathlib
import sys

from .datakit import Fetcher, FetchError, NetworkBlocked, Source

ROOT = pathlib.Path(__file__).resolve().parent

FOMC_INDEX = Source(
    name="FOMC statement index", url="https://www.federalreserve.gov/json/ne-press.json",
    dest="fed/press-index.json", publisher="US Federal Reserve Board",
    terms="U.S. government work, public domain",
    note="used to locate the most recent monetary-policy statements",
)

# Direct document sources. Each is a landing page whose text is the release.
SOURCES = [
    Source(name="BLS CPI news release",
           url="https://www.bls.gov/news.release/cpi.nr0.htm",
           dest="bls/cpi.htm", publisher="US Bureau of Labor Statistics",
           terms="U.S. government work, public domain",
           note="the current Consumer Price Index release, in full"),
    Source(name="BLS Employment Situation news release",
           url="https://www.bls.gov/news.release/empsit.nr0.htm",
           dest="bls/empsit.htm", publisher="US Bureau of Labor Statistics",
           terms="U.S. government work, public domain",
           note="a second release on a related topic -- near-miss sources are "
                "what make citation accuracy hard"),
    Source(name="Federal Reserve H.15 selected interest rates",
           url="https://www.federalreserve.gov/releases/h15/",
           dest="fed/h15.htm", publisher="US Federal Reserve Board",
           terms="U.S. government work, public domain",
           note="dense with numbers, most of which no claim refers to"),
    FOMC_INDEX,
]


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    f = Fetcher(ROOT)

    if args.list:
        for s in SOURCES:
            print(f"{s.name}\n  {s.url}\n  -> raw/{s.dest}\n  {s.note}")
        print(f"\n{len(SOURCES)} documents")
        return 0
    if args.verify:
        problems = f.verify()
        for p in problems:
            print("  " + p)
        print("VERIFICATION FAILED" if problems else
              f"all {len(f.load_manifest()['files'])} cached file(s) verified")
        return 1 if problems else 0

    print(f"fetching {len(SOURCES)} public documents ...")
    ok = 0
    try:
        for i, s in enumerate(SOURCES, 1):
            print(f"  [{i}/{len(SOURCES)}] {s.name} ... ", end="", flush=True)
            try:
                p = f.get(s, refresh=args.refresh)
                print(f"{p.stat().st_size:,} bytes")
                ok += 1
            except FetchError as exc:
                # One moved landing page should not cost the whole corpus.
                print(f"skipped ({exc})")
    except NetworkBlocked as e:
        print(f"\nBLOCKED: {e}", file=sys.stderr)
        return 2

    if not ok:
        print("\nno documents retrieved", file=sys.stderr)
        return 1
    print(f"\nwrote {f.manifest_path} ({ok} documents)")
    print("run `python -m src.demo --real` to score grounding on them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

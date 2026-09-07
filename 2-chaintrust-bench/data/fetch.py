"""Pull the SmartBugs curated corpus and convert it to benchmark cases.

    python -m data.fetch --list
    python -m data.fetch
    python -m data.fetch --verify

Writes data/real-corpus.jsonl, which src.demo --real loads through the same
load_corpus(path=...) entry point the authored corpus uses. The scoring code
does not know or care which corpus it is given, which is the property that
makes the comparison between them meaningful.
"""
from __future__ import annotations

import json
import pathlib
import sys

from .datakit import Fetcher, FetchError, NetworkBlocked
from .solcorpus import REFS, contract_source, index_source, parse_index, to_cases

ROOT = pathlib.Path(__file__).resolve().parent
CORPUS = ROOT / "real-corpus.jsonl"


def _fetch_index(f: Fetcher, refresh: bool):
    """Try each candidate default branch; report all failures if none work."""
    errors = []
    for ref in REFS:
        try:
            path = f.get(index_source(ref), refresh=refresh)
            return ref, parse_index(path.read_bytes())
        except NetworkBlocked:
            raise
        except (FetchError, ValueError) as exc:
            errors.append(f"{ref}: {exc}")
    raise FetchError("could not read vulnerabilities.json from any known ref:\n  "
                     + "\n  ".join(errors))


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after N contracts (for a quick trial run)")
    args = ap.parse_args(argv)
    f = Fetcher(ROOT)

    if args.list:
        s = index_source(REFS[0])
        print(f"{s.name}\n  {s.url}")
        print("\nthen every contract it references, under\n  "
              f"https://raw.githubusercontent.com/smartbugs/smartbugs-curated/"
              f"<ref>/dataset/<category>/<file>.sol")
        print("\nSmartBugs categories mapped onto this benchmark's classes:")
        from .solcorpus import DIRECT, UNMAPPED
        for k, v in DIRECT.items():
            print(f"  {k:<28} -> {v}")
        print(f"  {'access_control':<28} -> split three ways by reading the source")
        print("  excluded (no counterpart here): " + ", ".join(UNMAPPED))
        return 0

    if args.verify:
        problems = f.verify()
        for p in problems:
            print("  " + p)
        print("VERIFICATION FAILED" if problems else
              f"all {len(f.load_manifest()['files'])} cached file(s) verified")
        return 1 if problems else 0

    try:
        print("reading the SmartBugs index ...")
        ref, records = _fetch_index(f, args.refresh)
        print(f"  ref '{ref}': {len(records)} annotated contracts")
        if args.limit:
            records = records[:args.limit]
        print(f"downloading {len(records)} contracts ...")
        for i, rec in enumerate(records, 1):
            if i % 25 == 0 or i == len(records):
                print(f"  {i}/{len(records)}")
            try:
                f.get(contract_source(ref, rec["path"]), refresh=args.refresh)
            except FetchError as exc:
                print(f"  skipped {rec['path']}: {exc}", file=sys.stderr)
    except NetworkBlocked as e:
        print(f"\nBLOCKED: {e}", file=sys.stderr)
        return 2
    except FetchError as e:
        print(f"\nFAILED: {e}", file=sys.stderr)
        return 1

    def read(path):
        return (f.raw / "smartbugs" / path).read_text(encoding="utf8", errors="replace")

    cases, stats = to_cases(records, read)
    with CORPUS.open("w", encoding="utf8") as fh:
        for c in cases:
            fh.write(json.dumps(c) + "\n")

    print(f"\nkept {stats['kept']} of {stats['records']} contracts")
    print(f"  excluded, vulnerability class not in this benchmark: "
          f"{stats['skipped_unmapped']}")
    print(f"  excluded, source unreadable: {stats['skipped_unreadable']}")
    print("  by class: " + ", ".join(f"{k}={v}"
                                     for k, v in sorted(stats["by_class"].items())))
    print(f"\nwrote {CORPUS}")
    print("run `python -m src.demo --real` to score the detectors on it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

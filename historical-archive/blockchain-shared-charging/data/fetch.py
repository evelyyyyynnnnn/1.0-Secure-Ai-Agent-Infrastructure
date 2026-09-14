"""Measure real gas prices, token prices and charging-station economics.

    python -m data.fetch --list
    python -m data.fetch
    python -m data.fetch --verify

Three inputs currently entered as assumptions become measurements:

  gas price per chain   from each network's own public RPC node
  native token in USD   from CoinGecko
  charging session $    from the US DOE's Alternative Fuels Data Center, which
                        publishes per-station pricing for public EV chargers

The AFDC key below is NREL's documented public demo key. It works without
registration and is heavily rate limited; set NREL_API_KEY to a free personal
key for a full pull.
"""
from __future__ import annotations

import os
import pathlib
import sys

from .chains import (CHAINS, fee_history_source, gas_price_source,
                     token_price_source)
from .datakit import Fetcher, FetchError, NetworkBlocked, Source

ROOT = pathlib.Path(__file__).resolve().parent

NREL_KEY = os.environ.get("NREL_API_KEY", "DEMO_KEY")
AFDC = ("https://developer.nrel.gov/api/alt-fuel-stations/v1.json"
        f"?api_key={NREL_KEY}&fuel_type=ELEC&access=public&limit=200"
        "&state=CA&ev_charging_level=dc_fast")

STATIONS = Source(
    name="AFDC public DC fast chargers (CA)", url=AFDC,
    dest="afdc/stations-ca.json",
    publisher="US DOE / NREL Alternative Fuels Data Center",
    terms="US government data, free to use; API key required (DEMO_KEY works)",
    note="station pricing and network operator, for the session-value input",
)


def sources() -> list:
    out = []
    for chain in CHAINS:
        out.append(gas_price_source(chain))
        out.append(fee_history_source(chain))
    out.append(token_price_source())
    out.append(STATIONS)
    return out


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    f = Fetcher(ROOT)
    srcs = sources()

    if args.list:
        for s in srcs:
            verb = "POST" if s.body is not None else "GET "
            print(f"{verb} {s.name}\n     {s.url}")
            if s.body is not None:
                print(f"     method: {s.body['method']}")
        print(f"\n{len(srcs)} requests across {len(CHAINS)} chains")
        if NREL_KEY == "DEMO_KEY":
            print("\nNREL_API_KEY is unset; using NREL's public DEMO_KEY "
                  "(low rate limit)")
        return 0

    if args.verify:
        problems = f.verify()
        for p in problems:
            print("  " + p)
        print("VERIFICATION FAILED" if problems else
              f"all {len(f.load_manifest()['files'])} cached file(s) verified")
        return 1 if problems else 0

    print(f"querying {len(CHAINS)} chains and 2 public datasets ...")
    try:
        f.get_all(srcs, refresh=args.refresh)
    except NetworkBlocked as e:
        print(f"\nBLOCKED: {e}", file=sys.stderr)
        return 2
    except FetchError as e:
        print(f"\nFAILED: {e}", file=sys.stderr)
        return 1
    print(f"\nwrote {f.manifest_path}")
    print("gas prices move minute to minute -- the manifest records exactly "
          "when each reading was taken")
    print("run `python -m src.demo --real` to price settlement on live gas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

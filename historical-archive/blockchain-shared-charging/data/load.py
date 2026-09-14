"""Turn the cached chain and station data into the demo's inputs."""
from __future__ import annotations

import json
import pathlib
import statistics

from .chains import CHAINS, parse_fee_history, parse_gas_price, parse_token_prices
from .datakit import Fetcher, FetchError

ROOT = pathlib.Path(__file__).resolve().parent


def load_chain_costs(root=ROOT) -> dict:
    """Real gas price and USD token price per chain, with the observed spread."""
    f = Fetcher(root)
    man = f.load_manifest()
    if not any(k.startswith("chains/") for k in man["files"]):
        raise FetchError(
            "no chain data cached. Run `python -m data.fetch` in a networked "
            "environment first; the viability table will not be published with "
            "assumed gas prices under a heading that says measured.")

    prices = {}
    tp = f.raw / "chains" / "token-prices.json"
    if tp.exists():
        prices = parse_token_prices(tp.read_bytes())

    venues, prov = [], []
    for chain, (_, token, cg) in CHAINS.items():
        slug = chain.lower().replace(" ", "-")
        gp = f.raw / "chains" / f"{slug}-gasprice.json"
        fh = f.raw / "chains" / f"{slug}-feehistory.json"
        if not gp.exists():
            prov.append({"chain": chain, "status": "not fetched"})
            continue
        spot = parse_gas_price(gp.read_bytes())
        spread = None
        if fh.exists():
            try:
                spread = parse_fee_history(fh.read_bytes())
            except ValueError as exc:
                spread = {"unavailable": str(exc)}
        usd = prices.get(cg)
        venues.append({"name": chain, "gas_price_gwei": spot, "token": token,
                       "token_usd": usd, "spread": spread})
        rec = man["files"].get(f"chains/{slug}-gasprice.json", {})
        prov.append({"chain": chain, "status": "ok",
                     "gas_price_gwei": spot,
                     "retrieved_utc": rec.get("retrieved_utc"),
                     "endpoint": rec.get("url")})

    if not venues:
        raise FetchError("no chain gas prices could be read from the cache")
    missing = [v["name"] for v in venues if v["token_usd"] is None]
    if missing:
        raise FetchError(
            f"no USD price for the native token of {missing}; the cost figures "
            f"would be denominated in gas units, not dollars")
    return {"venues": venues, "provenance": prov,
            "token_prices_usd": prices}


def load_session_value(root=ROOT):
    """Median advertised price per kWh at real public DC fast chargers.

    Returns (price_per_kwh_usd, detail) or (None, detail) when the AFDC records
    carry no parseable price. Most stations publish free-text pricing such as
    "$0.48/kWh" or "Free", so a median over what can be parsed is the honest
    summary and the unparsed remainder is reported alongside it.
    """
    import re
    f = Fetcher(root)
    p = f.raw / "afdc" / "stations-ca.json"
    if not p.exists():
        return None, {"status": "not fetched"}

    data = json.loads(p.read_bytes())
    stations = data.get("fuel_stations", [])
    per_kwh, free, unparsed = [], 0, 0
    pat = re.compile(r"\$?\s*([0-9]*\.?[0-9]+)\s*(?:/|per\s+)\s*k\s*wh",
                     re.IGNORECASE)
    for s in stations:
        txt = (s.get("ev_pricing") or "").strip()
        if not txt:
            unparsed += 1
            continue
        if txt.lower().startswith("free"):
            free += 1
            continue
        m = pat.search(txt)
        if m:
            val = float(m.group(1))
            # Per-kWh retail pricing outside this band is a parse error, not a
            # tariff: $48/kWh is "$0.48" with a stray decimal.
            if 0.05 <= val <= 2.00:
                per_kwh.append(val)
                continue
        unparsed += 1

    detail = {"status": "ok", "n_stations": len(stations),
              "n_priced_per_kwh": len(per_kwh), "n_free": free,
              "n_unparsed": unparsed}
    if not per_kwh:
        detail["status"] = "no parseable per-kWh prices"
        return None, detail
    detail["median_usd_per_kwh"] = round(statistics.median(per_kwh), 4)
    detail["min_usd_per_kwh"] = round(min(per_kwh), 4)
    detail["max_usd_per_kwh"] = round(max(per_kwh), 4)
    return statistics.median(per_kwh), detail

"""Run the settlement lifecycle and the cost analysis."""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

from .settlement import Ledger, State, SettlementError, DISPUTE_WINDOW
from . import economics as ec

ROOT = pathlib.Path(__file__).resolve().parent.parent

GWEI = 10 ** 9
ETH_USD = 3000.0          # stated assumption, not a market quote
PRICE_PER_KWH_USD = 0.45


def lifecycle() -> dict:
    """Happy path, a disputed session, and the guards that must hold."""
    led = Ledger(arbiter="arbiter")
    led.register_point("arbiter", "point-A")
    t = 1_700_000_000
    tariff = 30 * GWEI // 100          # wei per kWh

    # happy path: 22 kWh drawn against a 40 kWh deposit
    led.open("S1", "driver-1", "point-A", tariff, 40_000, tariff * 40, t)
    led.report("S1", "point-A", 22_000, t + 1800)
    owed, refund = led.settle("S1", t + 1800 + DISPUTE_WINDOW + 1)

    # disputed: point over-reports, arbiter corrects it
    led.open("S2", "driver-2", "point-A", tariff, 40_000, tariff * 40, t)
    led.report("S2", "point-A", 39_000, t + 1800)
    led.dispute("S2", "driver-2", t + 1900)
    led.resolve("S2", "arbiter", 12_000, t + 2000)
    owed2, refund2 = led.settle("S2", t + 2000 + DISPUTE_WINDOW + 1)

    guards = []
    for name, fn in [
        ("settle before the dispute window closes",
         lambda: led.settle("S1", t)),
        ("a stranger reports a meter reading",
         lambda: led.report("S3", "attacker", 1, t)),
        ("dispute after the window has closed",
         lambda: (led.open("S4", "d", "point-A", tariff, 40_000, tariff * 40, t),
                  led.report("S4", "point-A", 1000, t),
                  led.dispute("S4", "d", t + DISPUTE_WINDOW + 5))),
        ("open against an unregistered point",
         lambda: led.open("S5", "d", "point-X", tariff, 1000, tariff * 40, t)),
        ("deposit below the maximum draw",
         lambda: led.open("S6", "d", "point-A", tariff, 40_000, 1, t)),
    ]:
        try:
            fn()
            guards.append({"attempt": name, "rejected": False, "error": ""})
        except SettlementError as exc:
            guards.append({"attempt": name, "rejected": True, "error": str(exc)})

    return {
        "happy_path": {"drawn_wh": 22_000, "paid_wei": owed, "refunded_wei": refund},
        "disputed": {"reported_wh": 39_000, "resolved_wh": 12_000,
                     "paid_wei": owed2, "refunded_wei": refund2},
        "guards": guards,
        "events": [list(e) for e in led.events],
    }


def run() -> dict:
    gas = {
        "open": ec.gas_open(),
        "report": ec.gas_report(),
        "settle": ec.gas_settle(),
        "dispute": ec.gas_dispute(),
        "per_session": ec.gas_per_session(),
        "per_session_with_dispute": ec.gas_per_session(with_dispute=True),
    }
    viability = ec.viability_table([1, 5, 10, 20, 50], ETH_USD, 22.0, PRICE_PER_KWH_USD)
    batching = [ec.batch_savings(n) for n in (1, 5, 10, 25, 50, 100)]
    venues = ec.venue_table(ETH_USD, 22.0, PRICE_PER_KWH_USD)

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "is_synthetic": True,
        "data_source": "off-chain model of SharedCharging.sol; gas figures are "
                       "opcode-level estimates, not node measurements",
        "assumptions": {"eth_usd": ETH_USD, "session_kwh": 22.0,
                        "price_per_kwh_usd": PRICE_PER_KWH_USD,
                        "dispute_window_s": DISPUTE_WINDOW},
        "gas": gas,
        "viability": viability,
        "batching": batching,
        "venues": venues,
        "lifecycle": lifecycle(),
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "latest.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf8")
    return results


def run_real() -> dict:
    """Price settlement on gas actually quoted by each network, right now.

    The conclusion this project reaches -- that per-session settlement is
    hopeless on L1 and workable on an L2 -- rests entirely on the gas price and
    the token price. Those were assumptions. Here they are readings, each
    stamped with the minute it was taken, because a gas price is a fact about a
    moment and not a property of a network.
    """
    import sys as _sys
    _sys.path.insert(0, str(ROOT))
    from data.load import load_chain_costs, load_session_value

    chains = load_chain_costs(root=ROOT / "data")
    kwh = 22.0
    measured_price, station_detail = load_session_value(root=ROOT / "data")
    price_per_kwh = measured_price if measured_price is not None else PRICE_PER_KWH_USD
    value = ec.session_value_usd(kwh, price_per_kwh)

    gas = ec.gas_per_session()
    batched = ec.batch_savings(50)["gas_per_session_batched"]

    venues = []
    for v in chains["venues"]:
        cost = ec.cost_usd(gas, v["gas_price_gwei"], v["token_usd"])
        cost_b = ec.cost_usd(batched, v["gas_price_gwei"], v["token_usd"])
        venues.append({
            "venue": v["name"], "token": v["token"],
            "token_usd": v["token_usd"],
            "gas_price_gwei": round(v["gas_price_gwei"], 6),
            "settlement_usd": round(cost, 6),
            "settlement_usd_batched_50": round(cost_b, 6),
            "overhead_share": round(cost / value, 6),
            "overhead_share_batched_50": round(cost_b / value, 6),
            "viable_unbatched": cost / value < 0.05,
            "viable_batched_50": cost_b / value < 0.05,
            "base_fee_spread": v["spread"],
        })
    venues.sort(key=lambda r: r["overhead_share"])

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "is_synthetic": False,
        "data_source": "live gas prices from each chain's public RPC node, native "
                       "token prices from CoinGecko, and charging tariffs from the "
                       "US DOE AFDC (see data/MANIFEST.json for retrieval times)",
        "gas_estimates_are_still_modelled": True,
        "gas_note": "per-operation gas remains an opcode-level estimate of "
                    "SharedCharging.sol, not a receipt from a deployed contract; "
                    "only the PRICE of that gas is measured here",
        "session": {"kwh": kwh, "price_per_kwh_usd": price_per_kwh,
                    "price_source": "AFDC median" if measured_price is not None
                                    else "assumed (no parseable AFDC price)",
                    "session_value_usd": round(value, 4)},
        "stations": station_detail,
        "gas": {"per_session": gas, "per_session_batched_50": batched},
        "venues": venues,
        "provenance": chains["provenance"],
        "token_prices_usd": chains["token_prices_usd"],
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "latest-real.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf8")
    return results


def main_real() -> int:
    from data.datakit import FetchError
    try:
        r = run_real()
    except FetchError as exc:
        print(f"cannot run on real data: {exc}", file=sys.stderr)
        return 2
    s = r["session"]
    print(f"source: {r['data_source']}")
    print(f"session: {s['kwh']} kWh at ${s['price_per_kwh_usd']:.4f}/kWh "
          f"({s['price_source']}) = ${s['session_value_usd']:.2f}")
    st = r["stations"]
    if st.get("status") == "ok":
        print(f"  AFDC: {st['n_priced_per_kwh']} of {st['n_stations']} stations "
              f"publish a per-kWh price "
              f"(${st.get('min_usd_per_kwh')}..${st.get('max_usd_per_kwh')}), "
              f"{st['n_free']} free, {st['n_unparsed']} unparsed")
    print(f"\n{'venue':<22}{'gwei':>12}{'settle $':>11}{'overhead':>10}"
          f"{'batched':>10}  viable")
    for v in r["venues"]:
        mark = "yes" if v["viable_unbatched"] else (
            "batched only" if v["viable_batched_50"] else "no")
        print(f"{v['venue']:<22}{v['gas_price_gwei']:>12.6f}"
              f"{v['settlement_usd']:>11.4f}{v['overhead_share']:>9.2%}"
              f"{v['overhead_share_batched_50']:>10.2%}  {mark}")
    print("\nbase-fee spread over the sampled block window:")
    for v in r["venues"]:
        sp = v["base_fee_spread"] or {}
        if "max_over_min" in sp and sp["max_over_min"]:
            print(f"  {v['venue']:<22} {sp['min_gwei']:.6f} .. {sp['max_gwei']:.6f} "
                  f"gwei ({sp['max_over_min']}x across {sp['n_blocks']} blocks)")
    print("\n" + r["gas_note"])
    print("wrote results/latest-real.json")
    return 0


def main() -> int:
    if "--real" in sys.argv[1:]:
        return main_real()
    r = run()
    print("gas estimates per call:")
    for k, v in r["gas"].items():
        print(f"  {k:<26}{v:>9,}")
    print("\nsettlement overhead vs session value "
          f"({r['assumptions']['session_kwh']} kWh @ "
          f"${r['assumptions']['price_per_kwh_usd']}/kWh):")
    for row in r["viability"]:
        flag = "ok" if row["viable_under_5pct"] else "NOT VIABLE"
        print(f"  {row['gas_price_gwei']:>3} gwei  "
              f"${row['settlement_cost_usd']:>7.4f}  "
              f"{row['overhead_pct']:>6.2f}%  {flag}")
    print("\nbatching:")
    for b in r["batching"]:
        print(f"  n={b['n_sessions']:<4} {b['gas_per_session_batched']:>8,} gas/session"
              f"  ({b['saving_pct']:>5.1f}% saved)")
    print("\nby execution layer (batched, n=50):")
    for v in r["venues"]:
        flag = "VIABLE" if v["viable_batched"] else "no"
        print(f"  {v['venue']:<22}${v['cost_batched_usd']:>8.4f}"
              f"  {v['overhead_batched_pct']:>7.2f}%  {flag}")
    lc = r["lifecycle"]
    print(f"\nguards: {sum(g['rejected'] for g in lc['guards'])}/"
          f"{len(lc['guards'])} invalid operations rejected")

    try:
        from .site import build_site
        build_site(r)
        print("\nwebsite/ rebuilt from this run")
    except Exception as exc:  # pragma: no cover
        print(f"\n(site not rebuilt: {exc})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

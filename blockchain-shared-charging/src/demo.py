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


def main() -> int:
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

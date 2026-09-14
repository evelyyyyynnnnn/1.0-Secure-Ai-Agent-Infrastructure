"""Does on-chain settlement pay for itself?

The question that decides whether this design is viable: settling a charging
session costs gas, and a session is worth a few euros. If gas per session is a
meaningful fraction of session value, per-session settlement is not viable at
any volume and the design has to batch.

Gas figures below are opcode-level estimates from the contract's storage
layout, not measured from a node. They are labelled as estimates everywhere
they appear, and a real deployment would replace them with `forge gas-report`
output.
"""

from __future__ import annotations

# EVM cost constants (post-Berlin, EIP-2929/3529).
G_TX = 21_000            # base transaction
G_SSTORE_SET = 20_000    # zero -> non-zero
G_SSTORE_RESET = 2_900   # non-zero -> non-zero
G_SSTORE_CLEAR = 2_900   # non-zero -> zero (refund capped, ignored here)
G_SLOAD_COLD = 2_100
G_SLOAD_WARM = 100
G_LOG_BASE = 375
G_LOG_TOPIC = 375
G_LOG_DATA = 8           # per byte
G_CALL_VALUE = 9_000     # value-bearing call
G_MEM_MISC = 1_500       # arithmetic, comparisons, calldata handling

# The Session struct packs into 3 slots: (driver+deposit), (point+timestamps),
# (wattHours+tariff+state). Packing is why `open` writes 3 slots and not 8.
SESSION_SLOTS = 3


def gas_open() -> int:
    return (G_TX
            + SESSION_SLOTS * G_SSTORE_SET
            + G_SLOAD_COLD                 # registeredPoints lookup
            + G_LOG_BASE + 3 * G_LOG_TOPIC + 32 * G_LOG_DATA
            + G_MEM_MISC)


def gas_report() -> int:
    return (G_TX
            + 2 * G_SSTORE_RESET           # wattHours+reportedAt, state
            + 2 * G_SLOAD_COLD
            + G_LOG_BASE + 2 * G_LOG_TOPIC + 32 * G_LOG_DATA
            + G_MEM_MISC)


def gas_settle() -> int:
    return (G_TX
            + 2 * G_SSTORE_RESET + G_SSTORE_CLEAR
            + 3 * G_SLOAD_COLD
            + 2 * G_CALL_VALUE             # pay the point, refund the driver
            + G_LOG_BASE + 2 * G_LOG_TOPIC + 64 * G_LOG_DATA
            + G_MEM_MISC)


def gas_dispute() -> int:
    return G_TX + G_SSTORE_RESET + 2 * G_SLOAD_COLD + G_LOG_BASE + 2 * G_LOG_TOPIC


def gas_per_session(with_dispute: bool = False) -> int:
    g = gas_open() + gas_report() + gas_settle()
    return g + gas_dispute() if with_dispute else g


def cost_usd(gas: int, gas_price_gwei: float, eth_usd: float) -> float:
    return gas * gas_price_gwei * 1e-9 * eth_usd


def session_value_usd(kwh: float, price_per_kwh_usd: float) -> float:
    return kwh * price_per_kwh_usd


def viability_table(gas_prices_gwei, eth_usd: float, kwh: float,
                    price_per_kwh_usd: float) -> list:
    """Settlement overhead as a share of session value, across gas prices."""
    value = session_value_usd(kwh, price_per_kwh_usd)
    gas = gas_per_session()
    rows = []
    for gp in gas_prices_gwei:
        c = cost_usd(gas, gp, eth_usd)
        rows.append({
            "gas_price_gwei": gp,
            "settlement_cost_usd": round(c, 4),
            "session_value_usd": round(value, 2),
            "overhead_pct": round(100.0 * c / value, 2) if value else 0.0,
            "viable_under_5pct": c / value < 0.05 if value else False,
        })
    return rows


def batch_savings(n_sessions: int) -> dict:
    """What batching settlement into one transaction saves.

    Batching amortises the 21,000-gas transaction base and the cold storage
    reads across n sessions. It cannot amortise the storage writes or the value
    transfers, which is why the saving flattens rather than scaling with n.
    """
    solo = gas_per_session() * n_sessions
    per_session_in_batch = (
        2 * G_SSTORE_RESET + G_SSTORE_CLEAR + 3 * G_SSTORE_SET
        + 2 * G_CALL_VALUE + G_SLOAD_WARM
        + 3 * (G_LOG_BASE + 2 * G_LOG_TOPIC) + 128 * G_LOG_DATA
        + G_MEM_MISC
    )
    batched = G_TX + n_sessions * per_session_in_batch
    return {
        "n_sessions": n_sessions,
        "gas_unbatched": solo,
        "gas_batched": batched,
        "gas_saved": solo - batched,
        "saving_pct": round(100.0 * (solo - batched) / solo, 2) if solo else 0.0,
        "gas_per_session_unbatched": gas_per_session(),
        "gas_per_session_batched": round(batched / n_sessions),
    }


# --- Where does this actually run? ----------------------------------------
#
# The L1 numbers rule out per-session settlement on mainnet at any realistic
# gas price, so the useful question is not "is this viable" but "on what
# execution layer does it become viable". Effective gas prices below are
# typical observed ranges, quoted as assumptions rather than live data.

VENUES = (
    ("Ethereum L1", 20.0),
    ("Ethereum L1 (quiet)", 3.0),
    ("Arbitrum One", 0.02),
    ("Base", 0.01),
    ("Polygon PoS", 30.0),      # cheap gas but priced in MATIC, see note below
)


def venue_table(eth_usd: float, kwh: float, price_per_kwh_usd: float,
                matic_usd: float = 0.55) -> list:
    """Settlement overhead by execution layer.

    Polygon is priced in MATIC rather than ETH, which is why its nominally high
    gwei figure still lands cheap. Mixing the two units in one column without
    saying so would be exactly the kind of comparison that looks rigorous and
    is not.
    """
    value = session_value_usd(kwh, price_per_kwh_usd)
    gas = gas_per_session()
    batched = batch_savings(50)["gas_per_session_batched"]
    rows = []
    for name, gwei in VENUES:
        native = matic_usd if "Polygon" in name else eth_usd
        c = cost_usd(gas, gwei, native)
        cb = cost_usd(batched, gwei, native)
        rows.append({
            "venue": name,
            "gas_price_gwei": gwei,
            "native_asset": "MATIC" if "Polygon" in name else "ETH",
            "cost_per_session_usd": round(c, 4),
            "cost_batched_usd": round(cb, 4),
            "overhead_pct": round(100.0 * c / value, 2) if value else 0.0,
            "overhead_batched_pct": round(100.0 * cb / value, 2) if value else 0.0,
            "viable_batched": (cb / value) < 0.05 if value else False,
        })
    return rows

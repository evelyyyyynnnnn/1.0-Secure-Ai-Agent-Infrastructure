import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.settlement import Ledger, State, SettlementError, DISPUTE_WINDOW
from src import economics as ec

GWEI = 10 ** 9
T0 = 1_700_000_000
TARIFF = 30 * GWEI // 100


def fresh():
    led = Ledger(arbiter="arb")
    led.register_point("arb", "pt")
    return led


def test_happy_path_pays_point_and_refunds_the_rest():
    led = fresh()
    led.open("S", "drv", "pt", TARIFF, 40_000, TARIFF * 40, T0)
    led.report("S", "pt", 22_000, T0 + 100)
    owed, refund = led.settle("S", T0 + 100 + DISPUTE_WINDOW + 1)
    assert owed == (TARIFF * 22_000) // 1000
    assert owed + refund == TARIFF * 40
    assert led.sessions["S"].state is State.SETTLED


def test_cannot_settle_inside_the_dispute_window():
    led = fresh()
    led.open("S", "drv", "pt", TARIFF, 40_000, TARIFF * 40, T0)
    led.report("S", "pt", 1000, T0)
    with pytest.raises(SettlementError, match="WindowOpen"):
        led.settle("S", T0 + DISPUTE_WINDOW - 1)


def test_only_the_charge_point_may_report():
    led = fresh()
    led.open("S", "drv", "pt", TARIFF, 40_000, TARIFF * 40, T0)
    with pytest.raises(SettlementError, match="NotPoint"):
        led.report("S", "attacker", 40_000, T0)


def test_only_the_driver_may_dispute():
    led = fresh()
    led.open("S", "drv", "pt", TARIFF, 40_000, TARIFF * 40, T0)
    led.report("S", "pt", 40_000, T0)
    with pytest.raises(SettlementError, match="NotDriver"):
        led.dispute("S", "someone", T0 + 10)


def test_dispute_closes_with_the_window():
    led = fresh()
    led.open("S", "drv", "pt", TARIFF, 40_000, TARIFF * 40, T0)
    led.report("S", "pt", 40_000, T0)
    with pytest.raises(SettlementError, match="WindowClosed"):
        led.dispute("S", "drv", T0 + DISPUTE_WINDOW + 1)


def test_arbiter_can_correct_an_over_report():
    led = fresh()
    led.open("S", "drv", "pt", TARIFF, 40_000, TARIFF * 40, T0)
    led.report("S", "pt", 39_000, T0)
    led.dispute("S", "drv", T0 + 10)
    led.resolve("S", "arb", 12_000, T0 + 20)
    owed, _ = led.settle("S", T0 + 20 + DISPUTE_WINDOW + 1)
    assert owed == (TARIFF * 12_000) // 1000


def test_a_non_arbiter_cannot_resolve():
    led = fresh()
    led.open("S", "drv", "pt", TARIFF, 40_000, TARIFF * 40, T0)
    led.report("S", "pt", 39_000, T0)
    led.dispute("S", "drv", T0 + 10)
    with pytest.raises(SettlementError, match="NotArbiter"):
        led.resolve("S", "drv", 0, T0 + 20)


def test_deposit_must_cover_the_maximum_draw():
    led = fresh()
    with pytest.raises(SettlementError, match="DepositTooSmall"):
        led.open("S", "drv", "pt", TARIFF, 40_000, 1, T0)


def test_unregistered_point_cannot_be_used():
    led = fresh()
    with pytest.raises(SettlementError, match="PointNotRegistered"):
        led.open("S", "drv", "ghost", TARIFF, 40_000, TARIFF * 40, T0)


def test_payout_is_capped_by_the_deposit():
    """An over-reporting point can never take more than was escrowed."""
    led = fresh()
    led.open("S", "drv", "pt", TARIFF, 40_000, TARIFF * 40, T0)
    led.report("S", "pt", 10_000_000, T0)          # absurd reading
    owed, refund = led.settle("S", T0 + DISPUTE_WINDOW + 1)
    assert owed == TARIFF * 40
    assert refund == 0


def test_settlement_conserves_value():
    led = fresh()
    total = 0
    for i in range(5):
        dep = TARIFF * 40
        total += dep
        led.open(f"S{i}", f"d{i}", "pt", TARIFF, 40_000, dep, T0)
        led.report(f"S{i}", "pt", 1000 * (i + 1), T0)
        led.settle(f"S{i}", T0 + DISPUTE_WINDOW + 1)
    assert sum(led.balances.values()) == total


def test_l1_per_session_settlement_is_not_viable():
    """The finding this project exists to record.

    If this test starts failing, either the gas model changed or ETH did --
    either way the conclusion on the site needs revisiting.
    """
    rows = ec.viability_table([20], 3000.0, 22.0, 0.45)
    assert not rows[0]["viable_under_5pct"]
    assert rows[0]["overhead_pct"] > 100


def test_batching_saving_flattens():
    """Batching amortises the tx base, not the storage writes."""
    s10 = ec.batch_savings(10)["saving_pct"]
    s100 = ec.batch_savings(100)["saving_pct"]
    assert s100 > s10
    assert s100 - s10 < 5.0, "saving should be flattening, not scaling"


def test_an_l2_makes_batched_settlement_viable():
    rows = {r["venue"]: r for r in ec.venue_table(3000.0, 22.0, 0.45)}
    assert rows["Base"]["viable_batched"]
    assert not rows["Ethereum L1"]["viable_batched"]

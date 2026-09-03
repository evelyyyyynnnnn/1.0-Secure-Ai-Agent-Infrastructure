"""Off-chain model of the settlement contract.

Mirrors SharedCharging.sol closely enough to reason about cost and behaviour
without a node: same state machine, same dispute window, same arithmetic. The
point is not to replace on-chain testing but to answer the questions that decide
whether the design is viable at all -- what a session costs to settle, and how
that cost moves with batching.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class State(Enum):
    NONE = "None"
    OPEN = "Open"
    REPORTED = "Reported"
    SETTLED = "Settled"
    DISPUTED = "Disputed"


DISPUTE_WINDOW = 3600  # seconds, matches the contract constant


class SettlementError(Exception):
    pass


@dataclass
class Session:
    sid: str
    driver: str
    point: str
    deposit: int              # wei
    tariff_per_kwh: int       # wei
    opened_at: int
    watt_hours: int = 0
    reported_at: int = 0
    state: State = State.OPEN

    def owed(self) -> int:
        return min((self.tariff_per_kwh * self.watt_hours) // 1000, self.deposit)

    def refund(self) -> int:
        return self.deposit - self.owed()


@dataclass
class Ledger:
    arbiter: str
    registered_points: set = field(default_factory=set)
    sessions: dict = field(default_factory=dict)
    balances: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

    def register_point(self, caller: str, point: str) -> None:
        if caller != self.arbiter:
            raise SettlementError("NotArbiter")
        self.registered_points.add(point)

    def open(self, sid, driver, point, tariff_per_kwh, max_watt_hours,
             deposit, now) -> Session:
        if point not in self.registered_points:
            raise SettlementError("PointNotRegistered")
        if sid in self.sessions:
            raise SettlementError("BadState")
        needed = (tariff_per_kwh * max_watt_hours) // 1000
        if deposit < needed:
            raise SettlementError("DepositTooSmall")
        s = Session(sid, driver, point, deposit, tariff_per_kwh, now)
        self.sessions[sid] = s
        self.events.append(("Opened", sid, deposit))
        return s

    def report(self, sid, caller, watt_hours, now) -> None:
        s = self._get(sid)
        if s.state is not State.OPEN:
            raise SettlementError("BadState")
        if caller != s.point:
            raise SettlementError("NotPoint")
        s.watt_hours = watt_hours
        s.reported_at = now
        s.state = State.REPORTED
        self.events.append(("Reported", sid, watt_hours))

    def dispute(self, sid, caller, now) -> None:
        s = self._get(sid)
        if s.state is not State.REPORTED:
            raise SettlementError("BadState")
        if caller != s.driver:
            raise SettlementError("NotDriver")
        if now > s.reported_at + DISPUTE_WINDOW:
            raise SettlementError("WindowClosed")
        s.state = State.DISPUTED
        self.events.append(("Disputed", sid, caller))

    def resolve(self, sid, caller, watt_hours, now) -> None:
        s = self._get(sid)
        if caller != self.arbiter:
            raise SettlementError("NotArbiter")
        if s.state is not State.DISPUTED:
            raise SettlementError("BadState")
        s.watt_hours = watt_hours
        s.reported_at = now
        s.state = State.REPORTED
        self.events.append(("Resolved", sid, watt_hours))

    def settle(self, sid, now) -> tuple:
        s = self._get(sid)
        if s.state is not State.REPORTED:
            raise SettlementError("BadState")
        if now <= s.reported_at + DISPUTE_WINDOW:
            raise SettlementError("WindowOpen")
        owed, refund = s.owed(), s.refund()
        s.state = State.SETTLED            # effects before interactions
        s.deposit = 0
        self.balances[s.point] = self.balances.get(s.point, 0) + owed
        self.balances[s.driver] = self.balances.get(s.driver, 0) + refund
        self.events.append(("Settled", sid, owed))
        return owed, refund

    def _get(self, sid) -> Session:
        if sid not in self.sessions:
            raise SettlementError("BadState")
        return self.sessions[sid]

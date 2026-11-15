"""Deterministic synthetic IOC paper plans; never performs external orders.

Root must commit the returned state and all orders/fills in one transaction.
Do not retain a result if that transaction fails. Resume with ``load_state``.
The caller supplies event time and the current estimate at eligibility time.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import json
from typing import Literal, Mapping

from backend.core.identity import digest, stable_id
from backend.core.schemas import MarketQuote

D = Decimal
Side = Literal["yes", "no"]


def _decimal(value: Decimal, *, positive: bool = False, price: bool = False) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0 or positive and value == 0 or price and value > 1:
        raise ValueError("accounting requires finite nonnegative Decimal values in range")


def _time(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("paper clock must be timezone-aware")


@dataclass(frozen=True)
class DepthLevel:
    price: Decimal
    quantity: Decimal

    def __post_init__(self):
        _decimal(self.price, price=True)
        _decimal(self.quantity, positive=True)


@dataclass(frozen=True)
class QuoteBook:
    quote: MarketQuote
    revision: str
    yes_asks: tuple[DepthLevel, ...] = ()
    no_asks: tuple[DepthLevel, ...] = ()
    yes_bids: tuple[DepthLevel, ...] = ()
    no_bids: tuple[DepthLevel, ...] = ()

    def __post_init__(self):
        if not self.revision:
            raise ValueError("depth requires an explicit quote timeline revision")
        for side in ("yes", "no"):
            for name, reverse in (("asks", False), ("bids", True)):
                levels = getattr(self, f"{side}_{name}")
                prices = [level.price for level in levels]
                if prices != sorted(set(prices), reverse=reverse):
                    raise ValueError("depth prices must be unique and ordered best first")
                top = getattr(self.quote, f"{side}_{name[:-1]}")
                if levels and (top is None or top != levels[0].price):
                    raise ValueError("depth top must match the side-specific quote")


@dataclass(frozen=True)
class PaperLimits:
    order_fraction: Decimal = D("0.005")
    game_fraction: Decimal = D("0.03")
    total_fraction: Decimal = D("0.05")
    min_ev: Decimal = D("0.03")
    quantity_step: Decimal = D("1")
    requested_quantity: Decimal = D("10")
    max_quote_age_seconds: int = 10
    cooldown_seconds: int = 60
    latency_milliseconds: int = 250

    def __post_init__(self):
        for value in (self.order_fraction, self.game_fraction, self.total_fraction):
            _decimal(value, positive=True, price=True)
        _decimal(self.min_ev)
        _decimal(self.quantity_step, positive=True)
        _decimal(self.requested_quantity, positive=True)
        if min(self.max_quote_age_seconds, self.cooldown_seconds, self.latency_milliseconds) < 0:
            raise ValueError("paper clock limits must be nonnegative")


@dataclass(frozen=True)
class PaperOrder:
    order_id: str
    intent_id: str
    request_digest: str
    run_id: str
    market_id: str
    game_id: str
    side: Side
    direction: Literal["buy", "sell"]
    status: Literal["pending", "filled", "partial", "cancelled"]
    requested_quantity: Decimal
    quantity: Decimal
    filled_quantity: Decimal
    limit_price: Decimal
    reserved_cash: Decimal
    decision_probability: Decimal | None
    eligible_probability: Decimal | None
    decision_quote_id: str
    execution_quote_id: str | None
    created_at: datetime
    eligible_at: datetime
    completed_at: datetime | None
    reasons: tuple[str, ...]
    decision_quote_at: datetime | None = None


@dataclass(frozen=True)
class PaperFill:
    fill_id: str
    order_id: str
    quote_id: str
    book_revision: str
    market_id: str
    side: Side
    direction: Literal["buy", "sell"]
    quantity: Decimal
    gross_value: Decimal
    fee: Decimal
    vwap: Decimal
    at: datetime


@dataclass(frozen=True)
class Position:
    market_id: str
    game_id: str
    side: Side
    quantity: Decimal
    cost_basis: Decimal
    entry_fair_side: Decimal


@dataclass(frozen=True)
class ExitDeadline:
    """One stable time-exit trigger per still-open synthetic entry lot."""
    deadline_id: str
    run_id: str
    market_id: str
    side: Side
    entry_fill_id: str
    due_at: datetime


@dataclass(frozen=True)
class PositionMark:
    """A held-side, depth-limited mark with explicitly unpriced residual."""
    market_id: str
    side: Side
    quote_id: str | None
    as_of: datetime
    priced_quantity: Decimal
    unpriced_quantity: Decimal
    net_liquidation_value: Decimal | None
    unrealized_pnl_priced_quantity: Decimal | None
    reason: str | None


@dataclass(frozen=True)
class Consumption:
    market_id: str
    revision: str
    side: Side
    direction: Literal["buy", "sell"]
    price: Decimal
    quantity: Decimal


@dataclass(frozen=True)
class BrokerState:
    run_id: str
    bankroll: Decimal = D("10000.00")
    cash: Decimal = D("10000.00")
    realized_pnl: Decimal = D("0")
    orders: tuple[PaperOrder, ...] = ()
    fills: tuple[PaperFill, ...] = ()
    positions: tuple[Position, ...] = ()
    consumption: tuple[Consumption, ...] = ()
    book_fingerprints: tuple[tuple[str, str], ...] = ()
    schema_version: str = "paper-state-v1"
    fee_schedule_version: str = "simulation-linear-v1"

    def __post_init__(self):
        _decimal(self.bankroll, positive=True)
        _decimal(self.cash)
        if self.reserved_cash > self.cash:
            raise ValueError("pending reservations exceed cash")
        if any(order.run_id != self.run_id for order in self.orders):
            raise ValueError("foreign run order in paper state")
        if not self.run_id or not self.realized_pnl.is_finite():
            raise ValueError("paper state needs a run ID and finite realized PnL")
        for name, records, field in (("order", self.orders, "order_id"), ("intent", self.orders, "intent_id"), ("fill", self.fills, "fill_id"), ("position", self.positions, "market_id")):
            if len({getattr(item, field) for item in records}) != len(records):
                raise ValueError(f"duplicate {name} identity in restored paper state")
        for order in self.orders:
            for value in (order.quantity, order.filled_quantity, order.reserved_cash):
                _decimal(value)
            _decimal(order.requested_quantity, positive=True)
            _decimal(order.limit_price, price=True)
            if order.status != "pending" and order.reserved_cash != 0:
                raise ValueError("completed order retains a cash reservation")
        for position in self.positions:
            _decimal(position.quantity, positive=True)
            _decimal(position.cost_basis)
            _decimal(position.entry_fair_side, price=True)
        for fill in self.fills:
            _decimal(fill.quantity, positive=True)
            _decimal(fill.gross_value)
            _decimal(fill.fee)
            _decimal(fill.vwap, price=True)
        for consumed in self.consumption:
            _decimal(consumed.price, price=True)
            _decimal(consumed.quantity, positive=True)

    @property
    def reserved_cash(self) -> Decimal:
        return sum((order.reserved_cash for order in self.orders if order.status == "pending"), D(0))


@dataclass(frozen=True)
class BrokerResult:
    state: BrokerState
    order: PaperOrder | None
    fills: tuple[PaperFill, ...] = ()
    reasons: tuple[str, ...] = ()


def fee(quantity: Decimal) -> Decimal:
    """One rounded synthetic fee per nonempty IOC sweep, not per level."""
    _decimal(quantity)
    return (D("0.01") * quantity).quantize(D("0.01"), rounding=ROUND_CEILING) if quantity else D(0)


def side_evs(probability: Decimal, yes_ask: Decimal | None, no_ask: Decimal | None, quantity: Decimal) -> tuple[Decimal | None, Decimal | None]:
    _decimal(probability, price=True)
    _decimal(quantity, positive=True)
    for ask in (yes_ask, no_ask):
        if ask is not None:
            _decimal(ask, price=True)
    cost = fee(quantity) / quantity
    return (probability - yes_ask - cost if yes_ask is not None else None,
            1 - probability - no_ask - cost if no_ask is not None else None)


def _quote_reason(book: QuoteBook, as_of: datetime, limits: PaperLimits) -> str | None:
    age = (as_of - book.quote.captured_at).total_seconds()
    if book.quote.quote_mode != "synthetic_replay" or not book.quote.market_id.startswith("synthetic:"):
        return "Only an explicit synthetic quote timeline can fill in this paper simulator."
    if book.quote.is_stale or book.quote.venue_status not in {"active", "open"} or not 0 <= age < limits.max_quote_age_seconds:
        return "Quote is stale, inactive or not available at the supplied run time."
    return None


def _register_book(state: BrokerState, book: QuoteBook) -> BrokerState:
    key = f"{book.quote.market_id}|{book.revision}"
    # A transport wrapper, freshness update or timestamp-only refresh is not
    # replenished liquidity. Only an explicit new liquidity revision can reset
    # consumption; the same revision must retain actual prices and depth.
    fingerprint = digest({
        "market_id": book.quote.market_id,
        "prices": {name: getattr(book.quote, name) for name in ("yes_bid", "yes_ask", "no_bid", "no_ask")},
        "depth": {name: asdict(book)[name] for name in ("yes_asks", "no_asks", "yes_bids", "no_bids")},
    })
    known = dict(state.book_fingerprints)
    if key in known and known[key] != fingerprint:
        raise ValueError("book revision reused with changed quote or depth")
    if key not in known:
        known[key] = fingerprint
        return replace(state, book_fingerprints=tuple(sorted(known.items())))
    return state


def _sweep(state: BrokerState, book: QuoteBook, side: Side, direction: str, quantity: Decimal, limit: Decimal | None = None) -> tuple[Decimal, Decimal, tuple[DepthLevel, ...]]:
    levels = getattr(book, f"{side}_{'asks' if direction == 'buy' else 'bids'}")
    used = {(entry.price): entry.quantity for entry in state.consumption if (entry.market_id, entry.revision, entry.side, entry.direction) == (book.quote.market_id, book.revision, side, direction)}
    remaining = quantity
    taken: list[DepthLevel] = []
    for level in levels:
        if limit is not None and ((direction == "buy" and level.price > limit) or (direction == "sell" and level.price < limit)):
            break
        available = max(D(0), level.quantity - used.get(level.price, D(0)))
        amount = min(remaining, available)
        if amount > 0:
            taken.append(DepthLevel(level.price, amount))
            remaining -= amount
        if remaining <= 0:
            break
    filled = quantity - remaining
    gross = sum((level.price * level.quantity for level in taken), D(0))
    return filled, gross, tuple(taken)


def _step(quantity: Decimal, limits: PaperLimits) -> Decimal:
    return (quantity / limits.quantity_step).to_integral_value(rounding=ROUND_FLOOR) * limits.quantity_step


def _exposure(state: BrokerState, game: str | None = None) -> Decimal:
    return sum((p.cost_basis for p in state.positions if game is None or p.game_id == game), D(0)) + sum((o.reserved_cash for o in state.orders if o.status == "pending" and (game is None or o.game_id == game)), D(0))


def plan_entry(state: BrokerState, *, intent_id: str, game_id: str, side: Side, probability: Decimal, book: QuoteBook, as_of: datetime, evidence_mode: str, simulation_authorized: bool = False, requested_quantity: Decimal = D("10"), limits: PaperLimits = PaperLimits()) -> BrokerResult:
    _time(as_of)
    _decimal(probability, price=True)
    _decimal(requested_quantity, positive=True)
    if side not in {"yes", "no"}:
        raise ValueError("unknown side")
    request = digest((intent_id, game_id, side, probability, book.quote.quote_id, book.revision, as_of.isoformat(), evidence_mode, simulation_authorized, requested_quantity, asdict(limits)))
    existing = next((o for o in state.orders if o.intent_id == intent_id), None)
    if existing:
        if existing.request_digest != request:
            raise ValueError("intent ID reused with changed inputs")
        return BrokerResult(state, existing, reasons=("Duplicate intent; saved result reused.",))
    reasons = []
    if evidence_mode != "synthetic_replay" or not simulation_authorized:
        reasons.append("Only explicitly authorized fully synthetic scenarios may fill; media proxy runs remain candidate-only.")
    quote_reason = _quote_reason(book, as_of, limits)
    if quote_reason:
        reasons.append(quote_reason)
    if any(p.market_id == book.quote.market_id for p in state.positions) or any(o.market_id == book.quote.market_id and o.status == "pending" for o in state.orders):
        reasons.append("Existing position or pending intent prevents duplicate/opposing entry.")
    recent = [o.completed_at for o in state.orders if o.market_id == book.quote.market_id and o.direction == "buy" and o.filled_quantity > 0 and o.completed_at is not None]
    if recent and (as_of - max(recent)).total_seconds() < limits.cooldown_seconds:
        reasons.append("Entry cooldown is active.")
    if reasons:
        return BrokerResult(state, None, reasons=tuple(reasons))
    state = _register_book(state, book)
    capacity = min(state.cash - state.reserved_cash, state.bankroll * limits.order_fraction,
                   state.bankroll * limits.game_fraction - _exposure(state, game_id),
                   state.bankroll * limits.total_fraction - _exposure(state))
    quantity = _step(min(requested_quantity, limits.requested_quantity), limits)
    fillable, _, _ = _sweep(state, book, side, "buy", quantity)
    quantity = _step(fillable, limits)
    while quantity > 0:
        filled, gross, levels = _sweep(state, book, side, "buy", quantity)
        if gross + fee(filled) <= capacity:
            break
        quantity -= limits.quantity_step
    if quantity <= 0:
        return BrokerResult(state, None, reasons=("Insufficient known depth, cash or configured exposure capacity.",))
    fair = probability if side == "yes" else 1 - probability
    if fair - gross / filled - fee(filled) / filled < limits.min_ev:
        return BrokerResult(state, None, reasons=("Depth-aware side EV is below the configured entry gate.",))
    order = PaperOrder(stable_id("paper-order", state.run_id, intent_id), intent_id, request, state.run_id, book.quote.market_id,
                       game_id, side, "buy", "pending", requested_quantity, filled, D(0), levels[-1].price,
                       gross + fee(filled), probability, None, book.quote.quote_id, None, as_of,
                       as_of + timedelta(milliseconds=limits.latency_milliseconds), None,
                       ("Reserved synthetic IOC entry; eligibility-time quote/estimate will be rechecked.",),
                       decision_quote_at=book.quote.captured_at)
    return BrokerResult(replace(state, orders=state.orders + (order,)), order)


def plan_exit(state: BrokerState, *, intent_id: str, market_id: str, book: QuoteBook, as_of: datetime, reason: str = "explicit paper risk exit", limits: PaperLimits = PaperLimits()) -> BrokerResult:
    _time(as_of)
    request = digest((intent_id, market_id, book.quote.quote_id, book.revision, as_of.isoformat(), reason, asdict(limits)))
    existing = next((o for o in state.orders if o.intent_id == intent_id), None)
    if existing:
        if existing.request_digest != request:
            raise ValueError("exit intent ID reused with changed inputs")
        return BrokerResult(state, existing, reasons=("Duplicate exit; saved result reused.",))
    if book.quote.market_id != market_id:
        raise ValueError("exit quote belongs to another market")
    position = next((p for p in state.positions if p.market_id == market_id), None)
    if position is None:
        return BrokerResult(state, None, reasons=("No position to exit.",))
    if any(o.market_id == market_id and o.status == "pending" for o in state.orders):
        return BrokerResult(state, None, reasons=("A pending order already reserves this market.",))
    blocked = _quote_reason(book, as_of, limits)
    if blocked:
        return BrokerResult(state, None, reasons=(blocked,))
    state = _register_book(state, book)
    quantity, _, levels = _sweep(state, book, position.side, "sell", position.quantity)
    quantity = _step(quantity, limits)
    if quantity <= 0:
        return BrokerResult(state, None, reasons=("No executable held-side bid depth.",))
    order = PaperOrder(stable_id("paper-order", state.run_id, intent_id), intent_id, request, state.run_id, market_id,
                       position.game_id, position.side, "sell", "pending", position.quantity, quantity, D(0), levels[-1].price,
                       D(0), None, None, book.quote.quote_id, None, as_of, as_of + timedelta(milliseconds=limits.latency_milliseconds), None, (reason,),
                       decision_quote_at=book.quote.captured_at)
    return BrokerResult(replace(state, orders=state.orders + (order,)), order)


def execute_due(state: BrokerState, *, books: Mapping[str, QuoteBook], probabilities: Mapping[str, Decimal | None], as_of: datetime, limits: PaperLimits = PaperLimits()) -> BrokerResult:
    """One transaction proposal for due orders, in stable due/order order.

    ``probabilities`` must be freshly recomputed from current available inputs
    by the caller. Missing values cancel entries; exits use held-side bids and
    do not depend on an entry EV threshold or entry cooldown.
    """
    _time(as_of)
    emitted = []
    for order in sorted((o for o in state.orders if o.status == "pending" and o.eligible_at <= as_of), key=lambda o: (o.eligible_at, 0 if o.direction == "sell" else 1, o.order_id)):
        book = books.get(order.market_id)
        problem = "Latest quote unavailable at execution." if book is None else _quote_reason(book, as_of, limits)
        probability = probabilities.get(order.market_id)
        if order.direction == "buy" and probability is None:
            problem = "Current eligibility-time estimate is unavailable."
        if book is not None:
            if order.decision_quote_at is not None and book.quote.captured_at < order.decision_quote_at:
                problem = "Execution quote predates the decision-time quote."
            elif order.decision_quote_at is None and book.quote.quote_id != order.decision_quote_id:
                problem = "Legacy pending order has no decision quote timestamp; replacement quote cannot be verified."
        if probability is not None:
            _decimal(probability, price=True)
        if problem:
            updated = replace(order, status="cancelled", reserved_cash=D(0), completed_at=as_of, reasons=order.reasons + (problem,))
            state = replace(state, orders=tuple(updated if o.order_id == order.order_id else o for o in state.orders))
            continue
        if book.quote.market_id != order.market_id:
            raise ValueError("execution quote belongs to another market")
        state = _register_book(state, book)
        quantity, gross, levels = _sweep(state, book, order.side, order.direction, order.quantity, order.limit_price)
        quantity = _step(quantity, limits)
        quantity, gross, levels = _sweep(state, book, order.side, order.direction, quantity, order.limit_price)
        charge = fee(quantity)
        fair = (probability if order.side == "yes" else 1 - probability) if probability is not None else None
        if quantity <= 0:
            problem = "No remaining depth within original limit; IOC remainder cancelled."
        elif order.direction == "buy" and (gross + charge > order.reserved_cash or gross + charge > state.cash - state.reserved_cash + order.reserved_cash):
            problem = "Current all-in cost exceeds the reserved ceiling."
        elif order.direction == "buy" and fair - gross / quantity - charge / quantity < limits.min_ev:
            problem = "Current eligibility-time side EV is below the entry gate."
        elif order.direction == "sell" and state.cash + gross - charge < 0:
            problem = "Exit fees exceed available cash and proceeds."
        if problem:
            updated = replace(order, status="cancelled", reserved_cash=D(0), completed_at=as_of, execution_quote_id=book.quote.quote_id, eligible_probability=probability, reasons=order.reasons + (problem,))
            state = replace(state, orders=tuple(updated if o.order_id == order.order_id else o for o in state.orders))
            continue
        fill = PaperFill(stable_id("paper-fill", order.order_id), order.order_id, book.quote.quote_id, book.revision,
                         order.market_id, order.side, order.direction, quantity, gross, charge, gross / quantity, as_of)
        positions = list(state.positions)
        realized = state.realized_pnl
        if order.direction == "buy":
            positions.append(Position(order.market_id, order.game_id, order.side, quantity, gross + charge, fair))
            cash = state.cash - gross - charge
        else:
            old = next(p for p in positions if p.market_id == order.market_id and p.side == order.side)
            # Preserve every Decimal rounding residual until the final close.
            released_cost = old.cost_basis if quantity == old.quantity else old.cost_basis * quantity / old.quantity
            realized += gross - charge - released_cost
            positions.remove(old)
            if old.quantity > quantity:
                positions.append(replace(old, quantity=old.quantity - quantity, cost_basis=old.cost_basis - released_cost))
            cash = state.cash + gross - charge
        consumption = {(c.market_id, c.revision, c.side, c.direction, c.price): c.quantity for c in state.consumption}
        for level in levels:
            key = (order.market_id, book.revision, order.side, order.direction, level.price)
            consumption[key] = consumption.get(key, D(0)) + level.quantity
        updated = replace(order, status="filled" if quantity == order.requested_quantity else "partial", filled_quantity=quantity,
                          reserved_cash=D(0), execution_quote_id=book.quote.quote_id, eligible_probability=probability,
                          completed_at=as_of, reasons=order.reasons + ("Synthetic IOC filled available depth once; any remainder cancelled.",))
        state = replace(state, cash=cash, realized_pnl=realized, positions=tuple(positions), fills=state.fills + (fill,),
                        consumption=tuple(Consumption(*key, value) for key, value in sorted(consumption.items())),
                        orders=tuple(updated if o.order_id == order.order_id else o for o in state.orders))
        emitted.append(fill)
    return BrokerResult(state, None, tuple(emitted))


def liquidation_mark(state: BrokerState, position: Position, book: QuoteBook, as_of: datetime, limits: PaperLimits = PaperLimits()) -> dict:
    """Depth-limited mark. Residual quantity stays explicitly unpriced."""
    _time(as_of)
    if book.quote.market_id != position.market_id:
        raise ValueError("mark quote belongs to another market")
    _register_book(state, book)  # Validate any known revision without mutating state.
    problem = _quote_reason(book, as_of, limits)
    quantity, gross, _ = _sweep(state, book, position.side, "sell", position.quantity) if problem is None else (D(0), D(0), ())
    return {"priced_quantity": quantity, "unpriced_quantity": position.quantity - quantity,
            "net_liquidation_value": gross - fee(quantity) if quantity > 0 else None,
            "unrealized_pnl_priced_quantity": gross - fee(quantity) - (position.cost_basis if quantity == position.quantity else position.cost_basis * quantity / position.quantity) if quantity > 0 else None,
            "reason": problem or ("Insufficient held-side bid depth for the residual." if quantity < position.quantity else None)}


def exit_deadlines(state: BrokerState, hold_seconds: int = 300) -> tuple[ExitDeadline, ...]:
    """Reconstruct deadlines after restart; do not create new recurring exits.

    Root consumes each stable deadline event once. For an overdue residual or
    a blocked exit, a later causal quote event/manual command may retry using
    a new intent keyed to that event. A publication timer must not retry it.
    Pending exits retain the original deadline; root skips another plan while
    an order for that market remains pending.
    """
    if not isinstance(hold_seconds, int) or hold_seconds <= 0:
        raise ValueError("time exit duration must be a positive integer")
    result = []
    for position in state.positions:
        entries = [fill for fill in state.fills if fill.market_id == position.market_id and fill.side == position.side and fill.direction == "buy"]
        if not entries:
            raise ValueError("open position has no committed entry fill for its deadline")
        entry = max(entries, key=lambda fill: (fill.at, fill.fill_id))
        result.append(ExitDeadline(
            stable_id("paper-exit-deadline", state.run_id, entry.fill_id, hold_seconds),
            state.run_id, position.market_id, position.side, entry.fill_id,
            entry.at + timedelta(seconds=hold_seconds),
        ))
    return tuple(sorted(result, key=lambda item: (item.due_at, item.deadline_id)))


def position_marks(state: BrokerState, books: Mapping[str, QuoteBook], as_of: datetime, limits: PaperLimits = PaperLimits()) -> tuple[PositionMark, ...]:
    """Typed root projection helper; consumes no liquidity and writes no state."""
    _time(as_of)
    result = []
    for position in sorted(state.positions, key=lambda item: item.market_id):
        book = books.get(position.market_id)
        if book is None:
            values = dict(priced_quantity=D(0), unpriced_quantity=position.quantity,
                          net_liquidation_value=None, unrealized_pnl_priced_quantity=None,
                          reason="No current held-side quote/depth is available.")
        else:
            values = liquidation_mark(state, position, book, as_of, limits)
        result.append(PositionMark(position.market_id, position.side, book.quote.quote_id if book else None, as_of, **values))
    return tuple(result)


def dump_state(state: BrokerState) -> str:
    def encode(value):
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        raise TypeError(type(value).__name__)
    return json.dumps(asdict(state), default=encode, sort_keys=True, separators=(",", ":"))


def load_state(payload: str) -> BrokerState:
    """Restore a root-committed state without rerunning an execution intent."""
    data = json.loads(payload)
    if data.get("schema_version") != "paper-state-v1" or data.get("fee_schedule_version") != "simulation-linear-v1":
        raise ValueError("unsupported paper state/fee version")
    for field in ("bankroll", "cash", "realized_pnl"):
        data[field] = D(data[field])
    for field, cls, decimals, dates in (
        ("orders", PaperOrder, ("requested_quantity", "quantity", "filled_quantity", "limit_price", "reserved_cash", "decision_probability", "eligible_probability"), ("created_at", "eligible_at", "completed_at", "decision_quote_at")),
        ("fills", PaperFill, ("quantity", "gross_value", "fee", "vwap"), ("at",)),
        ("positions", Position, ("quantity", "cost_basis", "entry_fair_side"), ()),
        ("consumption", Consumption, ("price", "quantity"), ()),
    ):
        objects = []
        for item in data[field]:
            for name in decimals:
                item[name] = D(item[name]) if item[name] is not None else None
            for name in dates:
                item[name] = datetime.fromisoformat(item[name]) if item.get(name) is not None else None
                if item[name] is not None:
                    _time(item[name])
            if "reasons" in item:
                item["reasons"] = tuple(item["reasons"])
            objects.append(cls(**item))
        data[field] = tuple(objects)
    data["book_fingerprints"] = tuple(tuple(item) for item in data["book_fingerprints"])
    return BrokerState(**data)

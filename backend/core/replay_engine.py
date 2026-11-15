"""Pure event-time G3 composition. No DB, network, provider or wall-clock work.

The caller commits the returned broker state, audit and projection together.
Only source/quote arrivals consider entry intents. Explicit domain deadlines
advance ageing/expiry and eligibility; HTTP/WS publication is never an input.
"""
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
import heapq
import math
from queue import Queue

from backend.execution.paper import (BrokerState, DepthLevel, QuoteBook, execute_due,
    exit_deadlines, plan_entry, plan_exit, position_marks)
from .identity import stable_id
from .media_projection import project, quote_row
from .schemas import ExecutionState, ExecutionTrace


def book_for(payload, metadata):
    row = quote_row(metadata, payload.playback.position_seconds)
    if row is None or row.get("fee_schedule_version") != "simulation-linear-v1":
        return None
    depth = {}
    for side in ("yes", "no"):
        for direction in ("ask", "bid"):
            price, size = row.get(f"{side}_{direction}"), row.get(f"{side}_{direction}_size")
            depth[f"{side}_{direction}s"] = (DepthLevel(Decimal(price), Decimal(size)),) if price is not None and size is not None and Decimal(size) > 0 else ()
    return QuoteBook(payload.quotes[0], row["liquidity_event_id"], **depth)


def authorized(cache, metadata):
    return metadata.get("simulation_authorized") is True and bool(cache.observations) and all(o.evidence_mode == "synthetic_replay" and o.provider == "supplied_fixture" for o in cache.observations)


def execution_view(state, payload, metadata, enabled, traces, reasons):
    book = book_for(payload, metadata)
    books = {book.quote.market_id: book} if book else {}
    return ExecutionState(enabled=enabled,
        reason="Fully synthetic fixture, quote books and illustrative fees; paper simulation only." if enabled else "Recorded/generated media is candidate-only; no execution authorization.",
        orders=[asdict(o) for o in state.orders], fills=[asdict(f) for f in state.fills], positions=[asdict(p) for p in state.positions],
        marks=[asdict(m) for m in position_marks(state, books, payload.replay_time)], traces=traces,
        reserved_cash=state.reserved_cash, realized_pnl=state.realized_pnl, latest_reasons=reasons)


def advance(old, cache, metadata, config_key, venue, state, target, speed, playing, *, initial=False, manual_exit=None):
    """Stage complete advancement, including deadlines between sparse seek targets.

    Bounded input queue batches 128 arrivals with backpressure, never dropping an
    observation. Immutable cached source IDs are collapsed by the quant ledger.
    The heap contains times (not raw media); same-time inputs project once.
    """
    start = old.playback.position_seconds
    if target < start and authorized(cache, metadata):
        raise ValueError("Synthetic accounting cannot seek backwards. Reset to a new run before replaying earlier events.")
    enabled = authorized(cache, metadata)
    origin = datetime.fromisoformat(metadata.get("origin", "2026-11-14T20:30:00+00:00").replace("Z", "+00:00"))
    arrivals, quotes = set(), set()
    queue = Queue(maxsize=128)
    def consume():
        while not queue.empty():
            kind, at = queue.get_nowait()
            (quotes if kind == "quote" else arrivals).add(at)
            queue.task_done()
    for observation in cache.observations:
        at = max(observation.replay_seconds, observation.available_replay_seconds or 0)
        if start < at <= target or initial and at == 0:
            if queue.full():
                consume()
            queue.put_nowait(("source", at))
    for row in metadata.get("quote_timeline", []):
        at = max(row["event_seconds"], row["available_replay_seconds"])
        if start < at <= target or initial and at == 0:
            if queue.full():
                consume()
            queue.put_nowait(("quote", at))
    consume()
    times = set(arrivals | quotes)
    times.update(float(t) for t in range(math.floor(start) + 1, math.floor(target) + 1))
    times.update(row["event_seconds"] + 10 for row in metadata.get("quote_timeline", []) if start < row["event_seconds"] + 10 <= target)
    if initial:
        times.add(0.0)
    if manual_exit:
        times.add(target)
    heap = list(times)
    heapq.heapify(heap)
    seen = set()
    traces = list(old.execution.traces)
    reasons = list(old.execution.latest_reasons)
    audit = []
    cursor = old.scheduler_cursor
    def schedule_deadlines(after):
        dates = [o.eligible_at for o in state.orders if o.status == "pending"]
        dates.extend(d.due_at for d in exit_deadlines(state))
        for date in dates:
            at = round((date - origin).total_seconds(), 6)
            if after < at <= target and at not in seen and at not in times:
                times.add(at)
                heapq.heappush(heap, at)
    schedule_deadlines(-1 if initial else start)
    def trace(payload, order, stage):
        traces.append(ExecutionTrace(run_id=old.run_id, trace_id=stable_id("execution-trace", order.order_id, stage), order_id=order.order_id,
            stage=stage, at=payload.replay_time, windows=payload.windows, claims=payload.claims, features=payload.features,
            quote=payload.quotes[0], estimate=next(iter(payload.estimates), None), decision=next(iter(payload.decisions), None),
            receipt=next(iter(payload.receipts), None), reasons=list(order.reasons)))
    while heap:
        at = heapq.heappop(heap)
        if at in seen:
            continue
        seen.add(at)
        payload = project(old.run_id, cache, at, speed, False, config_key, venue, metadata)
        cursor = max(cursor, at)
        book = book_for(payload, metadata)
        if enabled and book:
            before = {o.order_id: o for o in state.orders}
            # Due risk exits precede entries, and repeat only on a causal quote
            # or explicit user exit after a partial/stale exit.
            deadlines = exit_deadlines(state)
            for position in tuple(state.positions):
                deadline = next((d for d in deadlines if d.market_id == position.market_id), None)
                due = deadline and deadline.due_at <= payload.replay_time
                first_due = deadline and abs((deadline.due_at - payload.replay_time).total_seconds()) < 1e-6
                if manual_exit and at == target or due and (first_due or at in quotes):
                    result = plan_exit(state, intent_id=stable_id("intent", old.run_id, position.market_id, "exit", manual_exit or str(at)),
                        market_id=position.market_id, book=book, as_of=payload.replay_time,
                        reason="Explicit paper exit" if manual_exit else "300-second synthetic time exit")
                    state, reasons = result.state, list(result.reasons)
                    if result.order and result.order.order_id not in before:
                        trace(payload, result.order, "exit_plan")
            pending = {o.order_id for o in state.orders if o.status == "pending"}
            probabilities = {e.market_id: Decimal(str(e.model_probability)) for e in payload.estimates}
            result = execute_due(state, books={book.quote.market_id: book}, probabilities=probabilities, as_of=payload.replay_time)
            state = result.state
            for order in state.orders:
                if order.order_id in pending and order.status != "pending":
                    trace(payload, order, "eligibility")
                    reasons = list(order.reasons)
            if (at in arrivals or at in quotes) and payload.decisions and not manual_exit:
                decision = payload.decisions[0]
                result = plan_entry(state, intent_id=stable_id("intent", old.run_id, decision.decision_id), game_id="gta5",
                    side=decision.side, probability=Decimal(str(payload.estimates[0].model_probability)), book=book,
                    as_of=payload.replay_time, evidence_mode=payload.evidence_mode, simulation_authorized=True)
                state, reasons = result.state, list(result.reasons)
                if result.order and result.order.order_id not in before:
                    trace(payload, result.order, "entry_plan")
            elif at in quotes and not payload.estimates:
                reasons = ["No current estimate; stale or unsupported evidence/quote. New paper entries abstain."]
        elif enabled:
            reasons = ["No available explicit quote book and recognized simulation fee; paper execution blocked."]
            pending = {o.order_id for o in state.orders if o.status == "pending"}
            state = execute_due(state, books={}, probabilities={}, as_of=payload.replay_time).state
            for order in state.orders:
                if order.order_id in pending and order.status != "pending":
                    trace(payload, order, "eligibility")
        if enabled or payload.estimates:
            audit.append(payload)
        schedule_deadlines(at)
    payload = project(old.run_id, cache, target, speed, playing, config_key, venue, metadata)
    view = execution_view(state, payload, metadata, enabled, traces, reasons)
    payload = payload.model_copy(update={"execution": view, "cash_usd": state.cash, "order_count": len(state.orders), "fill_count": len(state.fills), "scheduler_cursor": cursor})
    return payload, state, audit

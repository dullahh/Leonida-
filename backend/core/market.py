"""Read-only actual venue context. Proxy estimates never consume these prices."""
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import httpx

from .clock import utc_now
from .identity import stable_id
from .schemas import MarketDefinition, MarketQuote, VenueContext

PRICE_FIELDS = ("yes_bid", "yes_ask", "no_bid", "no_ask")


def unavailable(reason: str) -> VenueContext:
    return VenueContext(status="unavailable", observed_at=None, error=reason, markets=[], quotes=[])


def parse_market(raw: dict, captured: datetime, source: str, live: bool):
    ticker = raw["ticker"]
    market = MarketDefinition(
        market_id=f"kalshi:{ticker}", market_namespace="venue", venue_ticker=ticker,
        reference_venue_ticker=None, title=raw.get("title", ticker),
        rules_primary=raw.get("rules_primary") or "Rules absent from response; unsupported for execution.",
        definition_version=stable_id("definition", ticker, raw.get("rules_primary"), raw.get("rules_secondary")),
    )
    prices, missing = {}, {}
    for field in PRICE_FIELDS:
        # Preserve fixed-point dollars when supplied. Legacy integer values are cents.
        dollars = raw.get(field + "_dollars")
        cents = raw.get(field)
        if dollars is not None:
            prices[field] = Decimal(str(dollars))
        elif cents is not None:
            prices[field] = Decimal(str(cents)) / Decimal(100)
        else:
            prices[field] = None
            missing[field] = "Not returned by venue; no price inferred"
    quote = MarketQuote(
        quote_id=stable_id("venue-quote", ticker, captured.isoformat(), prices),
        market_id=market.market_id, quote_mode="live" if live else "cached_stale",
        captured_at=captured, venue_status=raw.get("status", "unknown"), is_stale=not live,
        missing_reasons=missing, source_ref=source, **prices,
    )
    return market, quote


def historical_context(directory: Path, aliases: dict) -> VenueContext:
    files = sorted(directory.glob("kalshi_actual_*.json"), reverse=True)
    errors = []
    for path in files:
        try:
            capture = json.loads(path.read_text(encoding="utf-8"))
            captured = datetime.fromisoformat(capture["captured_at"].replace("Z", "+00:00"))
            wanted = set(aliases.values())
            parsed = []
            for event in capture["events"]:
                for index, page in enumerate(event["pages"]):
                    receipts = event.get("page_receipts", [])
                    received = datetime.fromisoformat(receipts[index]["received_at"]) if index < len(receipts) else captured
                    parsed.extend(parse_market(m, received, f"data/snapshots/{path.name}", False) for m in page.get("markets", []) if m.get("ticker") in wanted)
            if parsed:
                return VenueContext(status="historical", observed_at=max(q.captured_at for m, q in parsed),
                    error="Saved API capture, not a current execution feed.",
                    markets=[m for m, q in parsed], quotes=[q for m, q in parsed])
        except (ValueError, KeyError, TypeError, ArithmeticError) as error:
            errors.append(f"{path.name}: {error}")
    return unavailable("No usable actual capture. " + "; ".join(errors[:2]))


async def fetch_context(client: httpx.AsyncClient, registry: dict) -> tuple[VenueContext, dict]:
    event = "KXGAMEAWARDS-BNAR"
    response = await client.get(registry["api_base"] + "/markets", params={"event_ticker": event, "limit": 1000})
    response.raise_for_status()
    captured = utc_now()
    raw = response.json()
    ticker = registry["aliases"]["gta_narrative_2026"]
    returned = next((m for m in raw.get("markets", []) if m.get("ticker") == ticker), None)
    if returned is None:
        raise ValueError(f"Venue did not return {ticker}; no replacement ticker invented")
    market, quote = parse_market(returned, captured, str(response.url), True)
    context = VenueContext(status="live", observed_at=captured, error=None, markets=[market], quotes=[quote])
    return context, {"captured_at": captured.isoformat(), "url": str(response.url), "response": raw}

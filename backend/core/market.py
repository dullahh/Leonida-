"""Read-only actual venue context. Proxy estimates never consume these prices."""
import asyncio
import json
import re
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import httpx

from .clock import utc_now
from .identity import stable_id
from .schemas import MarketDefinition, MarketQuote, VenueContext

PRICE_FIELDS = ("yes_bid", "yes_ask", "no_bid", "no_ask")

# Live game discovery is an on-demand catalog scan, not a quote poll. Keep its
# results briefly so UI refreshes and repeated clicks do not rescan every series.
_DISCOVERY_CACHE: dict[str, tuple[float, tuple[list[dict], list[str]]]] = {}
_DISCOVERY_INFLIGHT: dict[str, asyncio.Task] = {}
_DISCOVERY_CACHE_LOCK = asyncio.Lock()
_DISCOVERY_BACKOFF_UNTIL = 0.0
_KALSHI_DATA_CACHE: dict[str, tuple[float, object]] = {}
_KALSHI_DATA_INFLIGHT: dict[str, asyncio.Task] = {}
_KALSHI_DATA_LOCK = asyncio.Lock()
_KALSHI_NEXT_REQUEST_AT = 0.0


async def _cached_kalshi_data(key: str, ttl: float, loader):
    """Share catalog/event data across distinct game-name lookups."""
    now = time.monotonic()
    async with _KALSHI_DATA_LOCK:
        cached = _KALSHI_DATA_CACHE.get(key)
        if cached and cached[0] > now:
            return cached[1]
        task = _KALSHI_DATA_INFLIGHT.get(key)
        if task is None:
            task = asyncio.create_task(loader())
            _KALSHI_DATA_INFLIGHT[key] = task
    try:
        result = await asyncio.shield(task)
        async with _KALSHI_DATA_LOCK:
            _KALSHI_DATA_CACHE[key] = (time.monotonic() + ttl, result)
        return result
    finally:
        async with _KALSHI_DATA_LOCK:
            if _KALSHI_DATA_INFLIGHT.get(key) is task and task.done():
                _KALSHI_DATA_INFLIGHT.pop(key, None)


async def _kalshi_get(client: httpx.AsyncClient, url: str, params: dict | None = None):
    """Serialize public reads, space requests, and honor shared 429 cooldown."""
    global _DISCOVERY_BACKOFF_UNTIL, _KALSHI_NEXT_REQUEST_AT
    async with _KALSHI_DATA_LOCK:
        now = time.monotonic()
        if _DISCOVERY_BACKOFF_UNTIL > now:
            request = httpx.Request("GET", url)
            response = httpx.Response(429, request=request)
            raise httpx.HTTPStatusError(
                f"Kalshi discovery paused after HTTP 429 for about {max(1, round(_DISCOVERY_BACKOFF_UNTIL - now))}s",
                request=request, response=response)
        await asyncio.sleep(max(0.0, _KALSHI_NEXT_REQUEST_AT - now))
        response = await client.get(url, params=params)
        _KALSHI_NEXT_REQUEST_AT = time.monotonic() + 0.5
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            try:
                cooldown = min(max(float(retry_after), 1.0), 300.0) if retry_after else 30.0
            except ValueError:
                cooldown = 30.0
            _DISCOVERY_BACKOFF_UNTIL = max(_DISCOVERY_BACKOFF_UNTIL, time.monotonic() + cooldown)
            raise httpx.HTTPStatusError(
                f"Kalshi rate limited request; retry paused for {cooldown:g}s",
                request=response.request, response=response)
        return response


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


async def _scan_live_game_outcome_candidates(client: httpx.AsyncClient, registry: dict,
                                             game_name: str) -> tuple[list[dict], list[str]]:
    """Find actual open Yes outcomes for a Twitch game across relevant series.

    Kalshi series metadata narrows event requests to title-specific and Game
    Awards series; only open event markets are inspected. The matcher requires
    an exact normalized Yes-outcome label. Returned rows retain the original
    market, event and series payloads.
    """
    global _DISCOVERY_BACKOFF_UNTIL
    from backend.quant.live_market_matching import match_game_outcomes

    base = registry["api_base"].rstrip("/")
    errors: list[str] = []
    series_rows: list[dict] = []
    game_key = re.sub(r"[^a-z0-9]+", "", game_name.casefold())
    async def load_series_catalog():
        # An unfiltered series request avoids assuming that Kalshi's primary
        # category equals its discovery category. For example, Game Awards is
        # shown under Video Games on the site while its series taxonomy can use
        # Entertainment. Fetching this one catalog costs far less than probing
        # every series' events and then exact-matching each outcome.
        response = await _kalshi_get(client, base + "/series")
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise ValueError("series response was not an object")
        data = body.get("series")
        if not isinstance(data, list):
            api_message = body.get("message") or body.get("details") or body.get("code")
            if api_message:
                raise ValueError(f"Kalshi API response: {str(api_message)[:160]}")
            raise ValueError(
                f"unexpected series field ({type(data).__name__}); response keys: "
                f"{', '.join(sorted(str(key) for key in body)[:12]) or 'none'}"
            )
        return data

    try:
        data = await _cached_kalshi_data(base + "|series-catalog", 1800.0, load_series_catalog)
        for row in data:
            if not isinstance(row, dict) or not isinstance(row.get("ticker"), str):
                continue
            descriptor = " ".join(str(row.get(field) or "") for field in ("ticker", "title", "name"))
            descriptor_key = re.sub(r"[^a-z0-9]+", "", descriptor.casefold())
            is_game_awards = any(token in descriptor_key for token in (
                "gameawards", "videogameawards", "gameoftheyear", "goty"
            ))
            names_requested_game = bool(game_key and game_key in descriptor_key)
            if not (is_game_awards or names_requested_game):
                continue
            labels = {
                str(value).strip().casefold()
                for field in ("categories", "tags")
                for value in (row.get(field) if isinstance(row.get(field), list) else [])
                if isinstance(value, str)
            }
            labels.update(
                str(row.get(field)).strip().casefold()
                for field in ("category",)
                if isinstance(row.get(field), str)
            )
            discovery_category = "esports" if any("esport" in label for label in labels) else "video_games"
            series_rows.append({**row, "_discovery_category": discovery_category})
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as error:
        errors.append(f"Series catalog: {type(error).__name__}: {str(error)[:180]}")

    # Preserve Kalshi's returned series metadata and deduplicate network fetches.
    grouped: dict[str, dict] = {}
    for row in series_rows:
        ticker = row["ticker"]
        if ticker in grouped:
            grouped[ticker].setdefault("_discovery_categories", set()).add(row["_discovery_category"])
        else:
            grouped[ticker] = {**row, "_discovery_categories": {row["_discovery_category"]}}

    semaphore = asyncio.Semaphore(2)
    async def read_series(series: dict) -> list[dict]:
        ticker = series["ticker"]

        async def load_series_events() -> list[dict]:
            async with semaphore:
                output: list[dict] = []
                cursor = ""
                page_count = 0
                while True:
                    params = {"series_ticker": ticker, "status": "open", "with_nested_markets": "true", "limit": 200}
                    if cursor:
                        params["cursor"] = cursor
                    response = await _kalshi_get(client, base + "/events", params=params)
                    response.raise_for_status()
                    body = response.json()
                    if not isinstance(body, dict):
                        raise ValueError(f"events response for {ticker} was not an object")
                    events = body.get("events", [])
                    if not isinstance(events, list):
                        raise ValueError(f"events response for {ticker} omitted its event list")
                    captured_at = utc_now().isoformat()
                    for event in events:
                        if not isinstance(event, dict):
                            continue
                        markets = event.get("markets", [])
                        if not isinstance(markets, list):
                            continue
                        for market in markets:
                            if not isinstance(market, dict):
                                continue
                            output.append({
                                **market,
                                "series_ticker": market.get("series_ticker") or ticker,
                                "event": {**event, "category": next(iter(sorted(series["_discovery_categories"])), "video_games")},
                                "series": series,
                                "_discovery_categories": sorted(series["_discovery_categories"]),
                                "_captured_at": captured_at,
                                "source_ref": str(response.url),
                            })
                    cursor = body.get("cursor") or ""
                    page_count += 1
                    if not cursor:
                        break
                    if page_count >= 25:
                        raise ValueError(f"event pagination limit reached for {ticker}")
                return output

        try:
            return await _cached_kalshi_data(base + "|events|" + ticker, 30.0, load_series_events)
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as error:
            raise RuntimeError(f"{type(error).__name__}: {str(error)[:180]}") from error

    results = await asyncio.gather(*(read_series(row) for row in grouped.values()), return_exceptions=True)
    raw_markets: list[dict] = []
    for series, result in zip(grouped.values(), results):
        if isinstance(result, Exception):
            errors.append(f"{series['ticker']}: {type(result).__name__}: {str(result)[:180]}")
        else:
            raw_markets.extend(result)
    try:
        matches = match_game_outcomes(game_name, raw_markets)
    except ValueError as error:
        errors.append(f"Outcome matching: {error}")
        matches = []
    return matches, errors


async def fetch_live_game_outcome_candidates(client: httpx.AsyncClient, registry: dict,
                                             game_name: str) -> tuple[list[dict], list[str]]:
    """Share an on-demand catalog scan across callers and cache its result.

    Successful/empty scans are cached for five minutes. A scan interrupted by a
    429 or other API error is cached for one minute to prevent refresh loops from
    immediately repeating the same request burst.
    """
    key = registry["api_base"].rstrip("/") + "|" + " ".join(game_name.casefold().split())
    now = time.monotonic()
    async with _DISCOVERY_CACHE_LOCK:
        if _DISCOVERY_BACKOFF_UNTIL > now:
            wait_seconds = max(1, round(_DISCOVERY_BACKOFF_UNTIL - now))
            return [], [f"Kalshi discovery paused after HTTP 429; retry in about {wait_seconds}s"]
        cached = _DISCOVERY_CACHE.get(key)
        if cached and cached[0] > now:
            rows, errors = cached[1]
            return [dict(row) for row in rows], list(errors)
        task = _DISCOVERY_INFLIGHT.get(key)
        if task is None:
            task = asyncio.create_task(_scan_live_game_outcome_candidates(client, registry, game_name))
            _DISCOVERY_INFLIGHT[key] = task
    try:
        rows, errors = await asyncio.shield(task)
        ttl = 60 if errors else 300
        async with _DISCOVERY_CACHE_LOCK:
            _DISCOVERY_CACHE[key] = (time.monotonic() + ttl, (rows, errors))
        return [dict(row) for row in rows], list(errors)
    finally:
        async with _DISCOVERY_CACHE_LOCK:
            if _DISCOVERY_INFLIGHT.get(key) is task and task.done():
                _DISCOVERY_INFLIGHT.pop(key, None)

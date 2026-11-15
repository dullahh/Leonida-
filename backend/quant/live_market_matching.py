"""Exact game-name matching for actual Kalshi Yes-outcome candidates.

This module only finds open markets whose named Yes outcome is the Twitch game.
It does not estimate probabilities, interpret transcript evidence, or make a
paper decision. The market source retains authority over IDs, status, rules,
categories, and prices.
"""
from __future__ import annotations

from copy import deepcopy
import re
import unicodedata
from typing import Any


MATCHER_VERSION = "game-yes-outcome-exact-v1"

# These words identify an edition of the same named game. Strip only a final
# edition suffix; edition-like words elsewhere remain significant.
_EDITION_SUFFIXES = (
    ("game", "of", "the", "year", "edition"),
    ("collector", "s", "edition"),
    ("collectors", "edition"),
    ("definitive", "edition"),
    ("anniversary", "edition"),
    ("standard", "edition"),
    ("deluxe", "edition"),
    ("ultimate", "edition"),
    ("complete", "edition"),
    ("special", "edition"),
    ("edition",),
)

_EVENT_FIELDS = ("event_ticker", "series_ticker", "category", "categories", "tags")
_SERIES_FIELDS = ("series_ticker", "category", "categories", "tags")


def _normalized_label(value: Any) -> str | None:
    """Return a conservative exact-comparison key for a game/outcome label."""
    if not isinstance(value, str):
        return None
    value = unicodedata.normalize("NFKC", value).casefold()
    # Replace punctuation and symbols with spaces while retaining letters and
    # digits. This equates e.g. "DOOM: The Dark Ages" with punctuation variants
    # but never removes meaningful words or converts numeric/roman numerals.
    words = re.findall(r"[^\W_]+", value, flags=re.UNICODE)
    if not words:
        return None
    for suffix in _EDITION_SUFFIXES:
        if len(words) > len(suffix) and tuple(words[-len(suffix):]) == suffix:
            words = words[:-len(suffix)]
            break
    return " ".join(words) or None


def _event_and_series(market: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    event = market.get("event")
    series = market.get("series")
    return (event if isinstance(event, dict) else {},
            series if isinstance(series, dict) else {})


def _with_actual_parent_metadata(market: dict[str, Any]) -> dict[str, Any]:
    """Copy one venue market and fill absent event/series fields from raw parents."""
    candidate = deepcopy(market)
    event, series = _event_and_series(market)
    for field in _EVENT_FIELDS:
        if candidate.get(field) is None and event.get(field) is not None:
            candidate[field] = deepcopy(event[field])
    for field in _SERIES_FIELDS:
        if candidate.get(field) is None and series.get(field) is not None:
            candidate[field] = deepcopy(series[field])
    # Retain complete category metadata when the API provides it at parent
    # level, so Video Games and Esports remain distinguishable in the UI.
    if event:
        candidate.setdefault("event_metadata", deepcopy(event))
    if series:
        candidate.setdefault("series_metadata", deepcopy(series))
    return candidate


def match_game_outcomes(game_name: str, markets: list[dict]) -> list[dict]:
    """Select active markets where an exact game label is the Yes outcome.

    The comparison is case-insensitive, Unicode-normalized, punctuation-
    tolerant, and strips a small set of recognized trailing edition labels.
    No fuzzy similarity, market-title inference, invented alias, or probability
    is produced. Kalshi's actual status and all other source fields are copied
    to the candidate unchanged; `market_is_open` normalizes only `open` and
    Kalshi's observed `active` status as open.

    Duplicate identical ticker rows are collapsed deterministically. Conflicting
    source payloads for one ticker raise ValueError rather than selecting one by
    input order.
    """
    normalized_game = _normalized_label(game_name)
    if normalized_game is None:
        return []

    by_ticker: dict[str, dict[str, Any]] = {}
    for raw in markets:
        if not isinstance(raw, dict):
            continue
        ticker = raw.get("ticker") or raw.get("market_ticker")
        if not isinstance(ticker, str) or not ticker.strip():
            continue
        status = raw.get("status")
        is_open = isinstance(status, str) and status.strip().casefold() in {"open", "active"}
        if not is_open:
            continue
        outcome = raw.get("yes_sub_title")
        normalized_outcome = _normalized_label(outcome)
        if normalized_outcome != normalized_game:
            continue

        candidate = _with_actual_parent_metadata(raw)
        candidate["market_is_open"] = True
        candidate["match_method"] = MATCHER_VERSION
        candidate["matched_game_name"] = game_name
        candidate["matched_yes_outcome"] = outcome
        candidate["match_rationale"] = (
            "Exact normalized match between Twitch game metadata and the actual "
            "Kalshi Yes outcome label; punctuation/case and recognized trailing "
            "edition wording are normalized."
        )

        previous = by_ticker.get(ticker.strip())
        if previous is not None and previous != candidate:
            raise ValueError(f"conflicting Kalshi payloads for market ticker {ticker.strip()}")
        by_ticker[ticker.strip()] = candidate

    # Output order is stable regardless of venue pagination/input order.
    return [by_ticker[ticker] for ticker in sorted(by_ticker)]


__all__ = ["MATCHER_VERSION", "match_game_outcomes"]

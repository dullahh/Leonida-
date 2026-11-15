#!/usr/bin/env python3
"""Capture actual public market responses. Never invent missing quotes/spreads."""
from __future__ import annotations
import concurrent.futures
import json
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    registry = json.loads((ROOT / "config/market_registry.json").read_text())
    captured = datetime.now(timezone.utc)
    def fetch(event):
        url = registry["api_base"] + "/markets?" + urllib.parse.urlencode({
            "event_ticker": event, "limit": 1000,
        })
        pages, receipts = [], []
        while True:
            with urllib.request.urlopen(url, timeout=15) as response:
                payload = json.load(response)
            if not isinstance(payload.get("markets"), list):
                raise ValueError("Malformed venue response: markets list absent")
            pages.append(payload)
            receipts.append({"url": url, "received_at": datetime.now(timezone.utc).isoformat()})
            cursor = payload.get("cursor")
            if not cursor:
                return {"event_ticker": event, "pages": pages, "page_receipts": receipts}
            url = registry["api_base"] + "/markets?" + urllib.parse.urlencode({
                "event_ticker": event, "limit": 1000, "cursor": cursor,
            })
    results, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch, event): event for event in registry["events"]}
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                errors.append({"event_ticker": futures[future], "error": str(exc)})
    if not results:
        print(json.dumps({"saved": False, "errors": errors}, indent=2))
        return 1
    stamp = captured.strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:8]
    path = ROOT / "data/snapshots" / ("kalshi_actual_" + stamp + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    capture = {
        "capture_kind": "actual_public_api_response",
        "captured_at": captured.isoformat(),
        "note": "Historical capture, not a live execution feed. Original responses preserved.",
        "api_base": registry["api_base"],
        "events": sorted(results, key=lambda x: x["event_ticker"]),
        "errors": errors,
    }
    with path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(capture, indent=2) + "\n")
    print(json.dumps({"saved": True, "path": str(path), "events": len(results), "errors": errors}, indent=2))
    return 0 if not errors else 2

if __name__ == "__main__":
    raise SystemExit(main())


# Quote reference and abstention clarity

This display-only fix starts from87c34a2. No classifier, evidence gate, coefficient, broker, scenario, cache or media processing changed.

The scenario Market reference now derives its Yes midpoint from the quote itself, independently of ModelEstimate. Valid14¢/15¢ Yes bid/ask displays **14.50%**, labelled **Synthetic Yes midpoint / quote-derived**. The display checks current replay-time availability, staleness, active/open status, finite two-sided prices, a non-crossed spread within the existing5¢ reference limit and a non-endpoint midpoint. These checks only explain display availability; they do not create or alter an estimate, candidate or order.

When all quality claims abstain, the panel says exactly: “Market quote available; no evidence-adjusted estimate because no supported quality claims exist.” The model label says “No supported quality claims”; correction stays unavailable; paper candidate says “Evidence-adjusted estimate unavailable.” Source cards now say “No attributable quality opinion” and “Qualifying baseline not established” when those reasons are known. Stale/missing quotes display their explicit reason instead of implying missing evidence explains every unavailable value.

## Venue context audit

The running default app on8000 was inspected: `live_quote_polling=false`, venue status `historical`, eight quotes all `cached_stale`/`is_stale=true`, and `effect_on_proxy_estimate=none`. It reads **bundled tracked historical data**, not a network response fetched at default startup:

`data/snapshots/kalshi_actual_20261114T225215082511Z_b34f22a9.json`

File capture-start timestamp: **2026-11-14T22:52:15.082511+00:00**. Each displayed quote uses its page's client receipt time, listed below. VenueContext observed_at is the maximum receipt, **2026-11-14T22:52:16.404539Z**. Verified venue-side quote timestamps are absent/null; the UI does not relabel receipt times as venue timestamps. Current age is relative to the viewer's wall clock, not replay time. Stored market status `active` describes the historical response, not a newly observed status.

| Exact returned ticker | Yes bid/ask | No bid/ask | Page receipt time, UTC2026-11-14 |
|---|---|---|---|
|KXGAMEAWARDS-2026-GTA|84¢/85¢|15¢/16¢|22:52:15.926253|
|KXGAMEAWARDS-BNAR-GRA|73¢/74¢|26¢/27¢|22:52:15.826877|
|KXGAMEAWARDSBGD-2026-GTA6|60¢/64¢|36¢/40¢|22:52:16.404539|
|KXGTAONLINE-GTA6ONLINE-27|17¢/19¢|81¢/83¢|22:52:16.230161|
|KXGTAONLINE-GTA6ONLINE-27B|76¢/77¢|23¢/24¢|22:52:16.230161|
|KXMC-GTA6-95|78¢/79¢|21¢/22¢|22:52:15.905710|
|KXMC-GTA6-96|56¢/57¢|43¢/44¢|22:52:15.905710|
|KXMC-GTA6-97|28¢/29¢|71¢/72¢|22:52:15.905710|

The tab displays the registry-selected market titles, exact tickers, primary resolution rules, side-specific top bid/ask, historical venue status, staleness and capture provenance. It does not display executable depth, actual fees or all markets contained in the original response. Historical capture selection is newest usable bundled file, with fallback to the earlier bundled capture if parsing fails. No current venue-data accuracy or fresh live observation is claimed by this audit.

The UI now exposes each exact receipt timestamp and source path alongside the historical/stale badge and separate-context notice. Synthetic paper prices remain in the scenario panel, in their own namespace; these historical Kalshi quotes do not anchor GTA V proxy estimates or synthetic orders.

## Existing optional live mode

The option already exists. After setup, with8001 free:

```powershell
python scripts/manage.py demo --scenario recordings --live-quotes --db var/optional-live-context.sqlite3 --port 8001
```

This keeps the recordings/synthetic paper path and enables a separate read-only public poller. No credentials are required by the existing adapter. The default release mode still needs no network.

The adapter requests `https://external-api.kalshi.com/trade-api/v2/markets?event_ticker=KXGAMEAWARDS-BNAR&limit=1000`, selects the actual configured `KXGAMEAWARDS-BNAR-GRA` response and, on success, replaces the context with that **one Best Narrative market/quote**, not all eight historical rows. Its timestamp is client receipt time; source_ref becomes the request URL. Raw responses are saved in SQLite venue_captures. Polling uses3s between successful requests and an8s HTTP timeout.

On HTTP/parsing/missing-ticker failure, the preceding context is retained, all its quotes become `cached_stale`, a fetch error is displayed, and retry delay backs off6/12/24/30s. If a fresh quote reaches age10s, an independent wall-clock expiry task marks it stale, regardless of replay speed or pause. Restart begins from bundled historical context; persisted responses never automatically become live. Recorded/synthetic proxy evidence never changes an actual quote. There is no venue order route. This task did not enable polling or make a fresh Kalshi request.

## Verification

Focused browser test `tests/g4/test_quote_clarity.py` uses a labelled abstaining fixture envelope in an isolated app, with no network/provider/media processing. It asserts14.50% from a valid quote, null model/decisions/zero orders, unavailable correction, exact explanatory text, disabled receipt, explicit stale/missing quote reasons, source-card clarity, historical source/timestamps and synthetic-versus-venue distinction. Desktop1440/narrow390 checks and browser error capture are included.

Release checks: `python scripts/manage.py check --gate G3`, `.venv/Scripts/python.exe -B -m unittest discover -s tests/g4 -v`, and `python scripts/manage.py demo-check --scenario all`. No unrelated feature or methodology change is included.

Executed result:15 G3 tests and11 G4/startup/display tests passed with no skips, plus all six scenario operational smoke checks and the frontend typecheck/build. The focused display case also checks a missing single-side ask and both precise source-card labels. No required network request was introduced; optional live polling was audited from existing code and left disabled.

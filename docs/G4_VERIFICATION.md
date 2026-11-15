# G4 verification - 15 November 2026

Base commit: `4e154fa1c76fd0be4f1bc575e6e52231c09c464a` (`G3 reaction telemetry complete`). Working tree was clean at entry. User explicitly required one thread; no agents were spawned, superseding the delegation wording in prompt04. No application/source/configuration changes, new product features, preprocessing, provider calls or G5 work occurred.

## Result

G4 requested acceptance checks passed on this Windows checkout with the five local recordings/cache, installed Playwright and Microsoft Edge. The original15 checks and6 additional G4 checks passed without skips. There were **no confirmed production defects requiring fixes**. The separate `G4 verification fixes` commit contains verification tests and reporting only; G3 was not amended.

| Acceptance | Evidence executed |
|---|---|
| Deterministic replay | Original1x/5x comparison plus new0.5x/2x/5x event-time partition comparison: evidence/reactions, probabilities, fill quantities/fees/timestamps and cash match. Actual browser2x playback also synchronized all5 players within0.7s. Speed tests compare domain time, not identical wall-clock publication sequences. |
| Restart | New tests compare full committed Courtroom and all-five recording payloads after reopening, plus serialized broker state. Original tests restore pending and filled entries without replay fills. Restarts remain paused. |
| Observation/reaction dedup |1651 unique source/reaction IDs; repeated observation commands leave sequence/state/ledger unchanged. Existing focused tests ignore duplicate reaction deliveries and reject conflicting same-ID payloads. |
| Conservative pricing | Existing intense ambiguous/player-skill/poor-recognition tests exclude pricing. Explicit narrative quality claim passes thresholds and moves the estimate; all1651 actual recording observations remain abstained. |
| Quote gates | Exact10s expiry and outage cancellation in original acceptance; new missing-book test cancels pending order, releases reservation and preserves cash. Recorded evidence cannot authorize synthetic fills. |
| Accounting | Courtroom6-contract partial entry followed by4+2 exits, total fees.12, final cash10000.0800 and no position. Independent No-side test buys4 at.86 plus.04 fee (cash9996.52), exits at held No bid.85 plus.04 fee, leaves cash9999.88/PnL-.12 and no position. Repeating execution creates no further fill. |
| Reset/scenario isolation | Original command/reset and scenario tests; browser switches recorded to separate synthetic Courtroom run, rejects old-run controls409, resets to new epoch with0 fills and retains old filled audit. |
| SQLite rollback/recovery | Original late duplicate-command failure rolls back broker, snapshot and audit; new full-payload restart comparisons also pass. |
| REST/WebSocket | Isolated server returns identical committed full envelopes over REST and initial/reconnected WS; browser REST fallback with sockets blocked preserves fill count. |
| Schema/frontend | Serialization/OpenAPI/type drift checks, root TypeScript, frontend TypeScript and Vite build all pass. |
| Five videos/receipts | Browser decodes all5 at1920x1080, plays2x, pauses and seeks. Source filters105/221/303/467/555 match cache. Cached frame200, traversal artifact404, fixture receipt endpoints200 and receipt dialog work. |
| Layout/console |1440px desktop and390px narrow layouts have no horizontal overflow. Browser captures both page exceptions and console errors; final error list empty. |
| Numeric/missingness | Existing baseline tests plus new20-bucket warmup/finite constant-input check and negative absolute sentiment with positive pre-update surprise. Unsupported technical/gameplay routes retain negative diagnostic features and abstain from narrative pricing. |

## Commands actually run

```powershell
python scripts/manage.py check --gate G3
.venv/Scripts/python.exe -B -m unittest discover -s tests/g4 -v
```

The first command passed15 tests and all contract/build checks. The final G4 command passed6 tests in46.521s; no skips. New file: `tests/g4/test_verification.py`. Test databases, run IDs and HTTP port are isolated and temporary; the user's8000 demo was not mutated. Full local G4 output: `var/g4-verification.log` (ignored by Git). The browser test verifies the built frontend served by a temporary app and closes it afterwards. Installed development dependencies already include Playwright; no packages were installed.

The first browser attempt failed to locate Pause within30s under unittest's asyncio debug mode, accompanied by slow-callback logging. Failure was recorded before changing the harness in [G4_FAILURES.md](G4_FAILURES.md). Disabling debug in the test loop matches the standard server environment; the browser-only rerun passed, followed by the complete final G4 suite. No application workaround was applied.

## Remaining limitations

- Windows Proactor logs connection-reset callbacks/resource warnings when media sockets close; Uvicorn also logs its graceful-close timeout during isolated browser teardown. These are server/platform warnings, despite successful browser assertions, socket comparisons and DB cleanup. Server logs are not claimed error-free.
- The recording acceptance test requires this checkout's untracked local videos and immutable combined cache. They are intentionally absent from Git. A source-only checkout can run deterministic fixtures but cannot prove five-video playback without the supplied files/cache.
- Reaction scores are deterministic English text heuristics; they do not measure actual emotion, acoustic arousal or speaker identity. Source OCR/ASR errors and pending manual speaker verification remain. All recorded quality claims still abstain; nothing was relabelled to make a trade.
- Courtroom observations/baselines are supplied synthetic fixtures; quote movement/depth/fees/latency/execution are simulated. The heuristic probability model is uncalibrated. Actual GTA VI definitions/quotes remain separate historical/stale venue context, not current liquidity or an effect of GTA V proxy evidence.
- No live Twitch ingestion, automatic diarization/scenes, actual venue fee/depth execution, broad forecasting calibration or full multi-market constraint solver is demonstrated. Unsupported market routes continue to abstain. No real-money order path exists.
- Browser coverage verifies the listed paths on installed Edge; it is not a cross-browser/device certification. Replay input batching and full snapshots are suitable for these excerpts; long-recording performance remains outside this gate.

## Launch and demo checklist

The existing demo on8000 is retained. To restart after stopping that server:

```powershell
python scripts/manage.py demo --scenario recordings --cache var/evidence-cache/aa20c31e1a27bbf0fe075f2c9136360e7096731d9365cdd247c89ade4afe95b6.json --db var/recordings-reactions.sqlite3
```

A separate fixture instance can run alongside it:

```powershell
python scripts/manage.py demo --scenario courtroom-praise --db var/g4-courtroom-demo.sqlite3 --port 8001
```

1. Open http://127.0.0.1:8000; play at2x, pause and seek near the end. Filter t1–t5 and inspect original source details.
2. Inspect t4's possible frustration and t5's confusion telemetry. Both remain contextual with explicit pricing exclusions and no estimate/order.
3. Load the clearly labelled Courtroom scenario as a separate run; advance past1.25s. Inspect supported-claim/estimate receipt and6/10 partial entry.
4. Advance to310s; inspect4+2 exits, fees.12, flat position and cash10000.08. Synthetic quote movement is authored, not market prediction.
5. Reset, then load venue-outage-reset; advance past10.15s. Confirm stale quote and cancelled entry/no fill. Return to recordings when finished.

Stop after G4. G5 release/rehearsal is not executed.

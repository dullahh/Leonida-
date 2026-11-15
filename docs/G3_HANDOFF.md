# G3 handoff - integrated recordings and synthetic paper replay

Completed 15 November 2026. G3 acceptance passed. Stop here: G4 formal verification/reviewer gate and G5 release were not started.

## Current demo

Open http://127.0.0.1:8000. Root-owned Uvicorn PID **67112** uses `var/g3-recordings.sqlite3`. Active run `run:d6820290b5d69b01b11882bc` is on the real recordings, paused at zero. The earlier G2 process was stopped after confirming its identity; its database and caches remain intact.

```powershell
python scripts/manage.py demo --scenario recordings --db var/g3-recordings.sqlite3
```

That is the restart command; do not start a second process on the occupied port. The app restores its saved active run paused. To use a separate synthetic instance alongside it:

```powershell
python scripts/manage.py demo --scenario courtroom-praise --db var/g3-courtroom.sqlite3 --port 8001
```

No keys or network are required. In the running app, choose **Courtroom praise**, then **Load isolated scenario**. Advance past 1.25 seconds to inspect the partial entry, or to the end to inspect both timed exits. **Return to recordings** creates a separate recorded run. Synthetic accounting only seeks forward; Reset creates a new run for earlier playback. Recording seeks remain bidirectional. Manual paper exits require an open synthetic position and another 250 ms of replay advancement.

## Preservation after the interrupted session

Before any resumed writes, `git status --short` was attempted: this workspace has no `.git` repository. Existing backend/frontend source and configuration were read, Python files parsed, JSON checked, frontend typechecked, and generated-contract drift checked. No truncated application file was found.

Already complete and retained: media decoding/OCR/ASR and cache, semantic attribution, manual grouping, features and pure broker, the G3 runtime/scheduler/storage/API/schema changes, generated types, and the new scenario/ledger/trace UI components. Hash comparisons confirmed the runtime, schema, replay engine, recording pipeline, paper broker and new UI components remained unchanged after that inspection. The intentional unused G1 preprocessor placeholder and diagnostic reference slice were preserved.

Finished after resumption: the missing tester-owned G3 acceptance module; G3 command-runner/operational-inspector support; two small missing frontend safeguards (reject malformed execution arrays and display synthetic quote freshness/age); integrated browser verification; this handoff and current-state documentation. No working backend module was recreated, no dependencies were changed, and no original video, manifest, evidence cache or venue capture was overwritten.

## Recorded evidence remains abstained

The verified cache remains `var/evidence-cache/a6d8a27fa3c4f5c3e34b2b8a411457e6cc2a50b5362341b12bd8904d039343d9.json`, selected by `var/last-recording-cache.txt`.

| Supplied file | OCR | Speech | Unique observations at replay end |
|---|---:|---:|---:|
| t1.mp4 | 89 | 16 | 105 |
| t2.mp4 | 202 | 19 | 221 |
| t3.mp4 | 277 | 26 | 303 |
| Total | 568 | 61 | 629 |

All 629 claims have null quality sentiment and an abstention reason. There are **no features, estimates, candidate decisions, orders or fills** for these clips. Unknown scenes remain unassigned. Six source statuses consist of three configured recordings and three explicitly unavailable slots; no extra observations are invented. Source windows retain the original words, cached observation, hash/cache identity, media/replay/availability times, crop reference, audio reference and extraction metadata. The source filter and artifact links were exercised in the browser.

No preprocessing/provider rerun was needed. These are uncertain OCR lines and ASR segments, not native chat message counts. The prior machine audio cross-check and five t3 ASR warnings remain applicable; direct listening and transcription accuracy are not newly claimed. See [RECORDING_REVIEW.md](RECORDING_REVIEW.md).

## Integrated flow and contracts

Additive schema 2 revision `g3-v1` in `backend/core/schemas.py` adds manual groups, distinct order/fill/position/mark records, execution traces, scenario identity and scheduler cursor. Root regenerated schemas, OpenAPI and TypeScript. Workers remained directly supervised with no delegation; at most two fix workers ran concurrently.

Cached windows -> supported claims/abstentions -> unique/revisioned evidence and manual groups -> feature baselines -> explicit narrative relevance -> bounded market-relative heuristic estimate -> candidate -> synthetic-only risk/broker -> one SQLite transaction -> complete dashboard snapshot.

The scheduler processes bounded batches of 128 source/quote arrivals, event-time ageing and quote expiry, 250 ms order eligibility and 300-second exits. Same-time inputs project once. Quotes change anchor/EV/marks without adding source observations. Publication, reads and reconnect do not create intents. Partial exits retry on a later explicit quote/manual event, not publication ticks. Speed changes wall pacing only.

The single writer atomically commits cursor/projection, source/model audit, broker state, cash, reservations, consumed liquidity, orders/fills and command acknowledgements. Failed commits leave memory unchanged. Restart restores the committed ledger and starts paused; it does not resubmit fills. Reset and scenario selection create isolated new run IDs and retain prior audit history.

HTTP and WebSocket share full snapshots and sequences. Controls and creation are idempotent; changed payloads under an existing command ID return 409. Old-run controls are rejected. `POST /api/runs/{id}/inject` creates a separate synthetic occurrence; it never appends fixture annotations to the recordings cache. Historical decision receipts and complete execution traces remain available under their original run. Trace stages preserve decision-time and eligibility-time quotes, model inputs, source words and IDs, including null estimates when stale.

Only explicitly authorized `supplied_fixture` evidence plus synthetic quote books can fill. Recorded/generated-media evidence remains candidate-only. Actual GTA VI market definitions/quotes are separate venue context with zero effect on the GTA V proxy estimate. This G3 run used historical/stale actual captures and did not verify a fresh live quote session.

## Acceptance results

| Scenario | Observed integrated result |
|---|---|
| Courtroom praise | Separate synthetic annotation raises reference 50% to about 54.4776% at 1s. Yes net EV about $0.03228/contract. At 1.25s, 6/10 fill at .5025 with .06 fee. Timed exits fill 4 at 301.5s and 2 at 304.25s; final cash 10000.0800, no position. This arithmetic follows an authored quote path, not a forecast of profit. |
| Technical failure/laughter | Negative technical feature retained; laughter abstains and repeated source is dependency-capped. No unsupported narrative estimate or order. |
| Skill rage/controls | Skill-only observation excluded from quality; explicit negative gameplay claims retained. No unsupported narrative estimate or order. |
| Mixed/missing facecam | Disagreement and missing modality visible. Pending entry cancels after adverse quote change; zero fills. |
| Duplicate/reconnect | Two unique observations, one partial entry; repeated evidence/quotes/reconnect do not add fills or baseline updates. Stale residual inventory remains explicitly unpriced. |
| Venue outage/reset | Candidate at 9.9s; quote stale exactly at 10s; pending entry cancels at 10.15s. No fill or neutral substitute estimate. Reset creates a new epoch. |

Executed successfully:

```powershell
python scripts/manage.py check --gate G3
python scripts/manage.py demo-check --scenario all
python scripts/manage.py demo-check --scenario recordings
python scripts/manage.py demo-check --scenario foundation
```

The G3 check runs pack/schema/type drift checks, all six scenario validations, imports, React typecheck/build and **9 focused acceptance tests, zero skips**. These cover actual 629-observation abstention, separate fixtures, partial lifecycle, exact expiry, receipts, command idempotency, reset, pending/filled recovery, late transaction rollback, quote-only baseline preservation and equivalent event-time accounting at 1x/5x partitions. The broader G4 suite/reviewer gate is not claimed.

Operational checks launched isolated temporary HTTP/WS servers and databases, compared full snapshots, fetched receipts/traces and shut down cleanly. All six scenario endpoints, real-cache playback and the G1 diagnostic passed. G1 retains p=.12407788254178297, z=-2 and blocked No EV=.00592211745821703.

Installed Edge/Playwright browser checks passed: three decoded 1920x1080 videos; 2x play/pause within .4s synchronization; end seek and 105/221/303 source filters; cached image access; isolated scenario switching; partial-entry and eligibility receipts; both timed exits; manual exit; quote-stale display; reconnect/REST fallback without ledger changes; reset/old-frame rejection; desktop1440 and narrow390 without horizontal overflow. Final scenario pass recorded no page or HTTP errors. Browser manual exit also demonstrated a loss (cash9999.8500), separate from the authored timed-exit example.

Local evidence: `var/g3-review/browser-recordings.json`, `browser-scenarios.json`, `execution-trace.png`, `paper-lifecycle.png`, `recordings-end-desktop.png`, `recordings-mobile.png`, `outage-mobile.png`, `ready-recordings.png`. Worker details are in `handoffs/pipeline.md`, `handoffs/quant.md`, `handoffs/frontend.md`, `handoffs/tester.md`.

## Failures and remaining limits

No unresolved G3 acceptance failure remains. Initial launch failed because the still-running G2 server occupied8000; root stopped that known owned process and relaunched. Initial browser-helper checks selected an image in a closed row and omitted a request base URL; correcting those inspection helpers produced passing runs without application changes.

Heuristic/unvalidated: English lexical attribution, fixture annotations, seeded fixture baselines, relevance/coefficient choices and model probabilities. Simulated: quote movement, available depth, processing latency, fee schedule and execution. Actual venue fees/depth are not implemented. No live Twitch ingestion, automatic scene matching, diarization, calibrated forecasting, real-money routes or predictive GTA VI evidence is claimed. Cache/snapshot replay is suitable for these excerpts; long recordings may require pagination and further performance work. Legacy isolated G2 broker fingerprint experiments should use a new G3 run/database; the real G2 recordings never had executed broker state. G4/G5 remain unexecuted.

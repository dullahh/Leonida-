# G1 handoff — GTA V proxy foundation

14 November 2026. G1 is accepted and work stops here. No G2 implementation workers were started. All application work is in root-owned core/main/config/scripts/contracts/dependencies and generated frontend types.

## Outcome and launch

The working path is one cached, explicitly supplied chat fixture → source window → supported narrative claim → pre-update feature → bounded heuristic scenario estimate → side-specific candidate paper decision → SQLite snapshot → HTTP/WebSocket → visible HTML app. This is actual computation, not a hard-coded response envelope.

```powershell
python scripts/manage.py demo
```

Open http://127.0.0.1:8000/. Default runtime is offline/no-key with historical venue context. Optional separately labelled public GTA VI polling:

```powershell
python scripts/manage.py demo --live-quotes
```

Fresh environment: `python scripts/manage.py setup`. Verification: `python scripts/manage.py check` and `python scripts/manage.py demo-check`. Make aliases exist but make is not installed/required here. Root's verification preview uses a separate DB and is stopped at final handoff; use the commands above to launch your own process.

## Primary demo plan and G1 boundary

The plan now prioritizes 2–6 local screen recordings of Twitch GTA V streams with embedded chat. Frame sampling/OCR, chat-region configuration, overlapping-line tracking and extraction caching are the next pipeline increment. Actual recordings supplied: none. G1 therefore uses an OCR-shaped fixture with `provider=supplied_fixture`, `evidence_mode=synthetic_replay`, null OCR confidence and frame plus reasons. The fixture sentiment annotation is supplied, not inferred by an OCR/LLM provider.

`RecordingManifest` validates 2–6 assets and offset/ROI/version metadata. `RecordingAsset.replay_offset(t)` computes `t - media_start_seconds + timeline_start_seconds` and rejects pre-trim/negative time. Both example slots are unavailable media; only one has a supplied fixture observation. This is not implemented multi-video playback.

Every evidence record retains GTA V and `proxy_demo`. The synthetic estimate cannot target a venue market; schema validation rejects that combination. Actual GTA VI definitions/quotes live in a separate `VenueContext` with effect_on_proxy_estimate=none. Public quote updates change neither proxy features nor its correction. All decisions are candidate-only; no order/fill/broker implementation exists.

## Exact implemented paths and interfaces

| Path | Implemented interface/responsibility |
|---|---|
| `backend/core/schemas.py` | Schema 2 contracts for manifests/cache, raw windows, claims, features, quotes, estimates, decisions, receipts, snapshot/envelope and commands. Nonempty IDs, Decimal money, null reasons and relevant cross-record validation. |
| `backend/core/interfaces.py` | `Clock.now()`, `SnapshotReader.snapshot(run_id=None)`, `RecordedPreprocessor.preprocess(manifest, cache_directory)`. `UnavailableRecordedPreprocessor` raises NotImplementedError; never returns invented OCR. |
| `backend/core/cache.py` | `prepare_fixture_cache(path: Path, directory: Path) -> EvidenceCache`. Only supplied fixtures are supported. Key includes real input bytes + manifest/schema; atomic write, exact reuse, digest/content rejection. |
| `backend/core/clock.py`, `identity.py`, `config.py` | Aware monotonic ReplayClock; canonical stable hashes/IDs; root config loading. |
| `backend/core/reference_slice.py` | `build_snapshot(run_id, cache, fixture, model, limits, venue) -> DashboardSnapshot`. Root-only one-observation seeded-baseline calculation, real logistic estimate and Decimal candidate EV. This is not the general G2 feature engine. |
| `backend/core/storage.py` | `StateStore.load/all_runs/command/commit/capture/close`. One SQLite connection/writer; transactional snapshots, typed records, idempotency receipts, expected sequence, immutable actual raw quote captures. |
| `backend/core/runtime.py` | `snapshot(run_id=None)`, async `start/create_run/control/close`. Constructs/recovers the slice; serializes commands, reset and quote-context updates. Optional public poller plus separate wall-time expiry. |
| `backend/core/projector.py` | `StateProjector.snapshot(run_id=None) -> StreamEnvelope`. Reads current committed full state without recomputation/ingestion. |
| `backend/core/market.py` | Historical captured context parser and async read-only public fetch. Exact returned ticker/rules/prices; fixed-point dollars preferred; missing prices remain null with reasons. |
| `backend/main.py` | `create_app(db_path=None, cache_dir=None, live_quotes=False)` and FastAPI lifespan/routes; localhost Uvicorn launched by manage. |
| `scripts/state_viewer.html/.css/.js` | Root-owned G1 viewer, state decoder, fallback/reconnect/reset, receipt disclosure, source offsets and independent venue panel. No React/Vite implementation yet. |
| `scripts/manage.py` | setup/demo/check/demo-check/export-contracts/refresh-markets commands. |
| `scripts/inspect_demo.py` | Isolated real HTTP/WS operational inspection with awaited in-process ASGI shutdown; no mutation of another run. |
| `scripts/export_contracts.py`, `generate_types.cjs` | Deterministic serialization schemas/example/OpenAPI and generated TypeScript plus drift checks. |
| `scripts/validate_pack.py` | Existing reference validation adapted to archived v1 and scoped folders; no dependency-directory scan or archived artifact writes. |
| `scripts/refresh_market_snapshot.py` | Actual public capture, per-page receipt times, exclusive collision-safe filenames; original capture preserved. |
| `config/foundation_scenario.json` | Explicit fixture text/annotation, two recording slots, offsets, seeded baseline and synthetic quote/fee inputs. |
| `pyproject.toml`, `uv.lock`, root npm manifests, `contracts/tsconfig.json`, `Makefile` | Locked dependencies and Windows-compatible commands. |

`contracts/models.py` re-exports runtime schemas. Original starter artifacts are archived in `contracts/reference-v1/`. Generated files: `contracts/generated/dashboard-envelope.schema.json`, full example, recording/cache schemas, OpenAPI, and `frontend/src/generated/contracts.ts` / `evidence-cache.ts`. No other frontend-owned file was created. Schema 2 is a deliberate version change for identity/proxy/missingness fields; do not silently treat the old reference v1 as compatible.

## HTTP/WebSocket contract

| Endpoint | Implemented behaviour |
|---|---|
| `GET /`, `/assets/...` | Local viewer/assets. |
| `GET /health`, `/ready` | Liveness plus explicit working/unavailable G1 capabilities. Optional venue failure does not make fixture replay unready. |
| `GET /api/state?run_id=...`, `WS /ws?run_id=...` | Same schema-2 full StreamEnvelope and persisted per-run sequence. WS sends at 1Hz; repeated frames keep sequence/values and never ingest evidence. |
| `GET /api/cache` | Validated current fixture EvidenceCache. |
| `GET /api/markets?run_id=...` | Synthetic scenario and separate actual venue context. |
| `POST /api/runs` | `{command_id}` → CommandResult; create scope is process/application-wide, UUID keys recommended. |
| `POST /api/runs/{id}/control` | `{command_id, action: reset|replay_observation}`. Same key/payload returns saved result, conflicting payload 409. Re-delivery is recognized as duplicate; reset creates a new run ID, preserving old audit state. |
| `GET /api/runs/{id}/receipts/{receipt_id}` | Same-run typed receipt; foreign/missing IDs 404. |

There is no inject/speed/playback endpoint or venue order endpoint. Runs are paused single-observation snapshots. Full streaming clocks/deadlines and control types in the longer plan are future design, not implemented G1 capabilities.

## Numerical acceptance

| Input/result | Value |
|---|---|
| Fixture narrative sentiment | -0.4 |
| Seeded prior mean / variance / count | 0 / .04 / 20 |
| Pre-update z / count after unique observation | -2 / 21 |
| Coefficients / correction | .2 absolute + .05 z → -.18 log-odds, bounded by .5 |
| Synthetic Yes bid/ask; No bid/ask | .14/.15; .85/.86 USD per contract |
| Market reference / model | .145 / .12407788254178297 |
| Requested quantity / total simulated fee | 10 / .10 USD |
| No net EV | .00592211745821703 USD per contract |
| Decision | No-side candidate; below .03 entry gate; proxy/G1/depth restrictions also prohibit execution |
| Cash / orders / fills | 10000.00 USD / 0 / 0 |

Negative absolute opinion and negative surprise stay separate. Relevance=1 applies only to the named synthetic scenario; relevance to actual GTA VI contracts is zero. Fee is a named synthetic schedule, not a Kalshi fee claim. No confidence interval/calibrated posterior/forecasting edge is claimed.

## Verification evidence and limits

Executed with successful exit: setup, export-contracts, check and final demo-check (including repeated clean shutdown). The check command includes reference roundtrip/Decimal strings/five invalid-payload checks, runtime artifact drift, generated TypeScript and viewer syntax. JSON Schema validation of serialized runtime state also ran.

Focused inline checks used temporary DBs/run IDs and covered cache reuse/no rewrite, offsets/trim, invalidation, corrupted evidence, arithmetic/provenance/Decimal, quote/proxy validation, duplicate/command conflict, HTTP/WS/timer invariance, reset/foreign receipt/no order route, restart recovery, and wall-clock quote expiry without changing proxy features. This did not create a tester-owned formal suite. A Starlette TestClient deprecation warning was observed, not treated as a failed check.

Actual browser checks used installed Microsoft Edge through Playwright at 1440×1000 and 390×844: receipt, replay, reset, old-run rejection, WS reconnect, rule disclosure persistence, no horizontal document overflow, and no console/HTTP errors in the final check. Local evidence: [desktop](../var/g1-desktop.png), [narrow](../var/g1-mobile.png), [focused checks](../var/g1-focused-checks.json), [expiry checks](../var/g1-expiry-checks.json), [browser checks](../var/g1-browser-checks.json). These ignored artifacts are local review evidence, not portable test source.

Public refresh actually succeeded for five event families, saved in `kalshi_actual_20261114T225215082511Z_b34f22a9.json`. Live read-only polling of returned `KXGAMEAWARDS-BNAR-GRA` was observed; the UI displayed actual prices and capture age independently. No claim is made about raw Twitch access, OCR, venue depth/fees or real-money execution.

Initial installs/public requests needed approved network access. An intermittent Windows smoke teardown lock was fixed by awaiting the isolated server's ASGI shutdown instead of terminating a launcher process tree. The final smoke command exited cleanly twice. A favicon 404 and rule disclosure refresh issue were fixed before the final browser pass.

## Remaining work and next prompt

Actual media decoding/OCR and native OCR message identity are not implemented. Neither are multiple-video playback, general semantic extraction, rolling warmup/group revisions/ageing, six full scenarios, paper fills/exits/ledger accounting, React UI, or the G4 suite. `var/` contains local SQLite/cache and QA artifacts; no Git repository/commit was created.

The user requested stopping at G1, so do not automatically start prompt 02. When G2 is authorized, use the revised P2 packet for 2–6 recordings and OCR/cache, not the old synthetic-primary brief. Root must finalize additional raw OCR/group/execution contracts before worker consumption. Preserve no-key cached fallback, proxy labels, venue separation and paper-only scope.

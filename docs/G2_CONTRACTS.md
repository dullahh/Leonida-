# G2 frozen integration boundary

Schema 2 remains readable for G1; additive revision `g2-v1` adds media reports, observations, nullable warmup/abstentions and playback controls. Root alone exports JSON Schema/OpenAPI and TypeScript. Decimal values remain wire strings.

- `backend.ingestion.recordings.load_manifest(path, repository_root) -> RecordingManifest`
- `MediaPreprocessor(repository_root).preprocess(manifest, cache_directory) -> EvidenceCache`
- `load_cache(path) -> EvidenceCache`: validates hashes and artifact integrity; never starts OCR/ASR.
- `build_windows(cache, run_id, origin) -> list[SourceWindow]`
- `backend.perception.claims.extract(window) -> list[EvidenceClaim]`
- `backend.ingestion.replay.load_scenario(name, cache_directory) -> EvidenceCache`, `scenario_metadata(name)`.
- `backend.quant.evaluate(run_id, windows, claims, quote, as_of, *, seed_baseline=None) -> Evaluation`: features, optional estimate/decision, reasons. No authoritative writes.
- `backend.execution.paper`: pure typed plans/state serialization; runtime media remains candidate-only. Full broker composition is G3.

Runtime owns the only SQLite writer. Playback position, speed and paused/playing state persist in the full envelope atomically with command receipts; restart pauses saved runs. Root clock pacing never ingests a new observation. Seeking rebuilds from cached source records with availability at or before the requested time.

`RunCommand`: `reset`, `replay_observation`, `play`, `pause`, `seek` (position_seconds required), `set_speed` (speed required, 0 < speed <= 5). Fields from other actions are rejected. Full HTTP and WS envelopes are identical for the same revision. Reset creates a new run.

`GET /api/recordings/{asset_id}/media` serves only manifest-approved workspace media with byte ranges. `GET /api/evidence/artifact?ref=...` serves only frame/audio references in the active validated cache. Cache artifact paths are relative to the cache JSON parent. Browser never receives arbitrary filesystem access.

Actual recording files use recorded evidence. Generated test video uses synthetic_replay even though its OCR and ASR providers really run. Every source remains GTA V proxy material, and generated test graphics are explicitly not game footage. Actual GTA VI venue context has no effect on proxy estimates.

`StateStore.commit(..., broker_state=(expected_revision, BrokerState))` atomically persists validated broker state and distinct revisioned orders/fills with an optional envelope/command; `load_broker(run_id)` returns revision and restored typed state. This seam was checked for rollback/recovery; media playback does not invoke it.

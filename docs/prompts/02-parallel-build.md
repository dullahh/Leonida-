Run G2. Read the G1 handoff and frozen contracts/examples. Explicitly spawn three directly supervised workers; workers may not delegate. At most three workers run concurrently.

pipeline_engineer:
- Own backend/ingestion/, backend/perception/, data/scenarios/, data/recordings/ manifests, handoffs/pipeline.md.
- Read PLAN sections 5, 8, 9 and 15 plus frozen signatures.
- Implement six-stream deterministic structured replay first and six required scenarios with source/available_at times.
- Add claim extraction interface and a labelled fixture provider. Real recorded-media/transcription/chat adapters are optional after replay passes.
- Manual scene IDs first; automatic similarity only as candidate confidence.
- Missing facecam/audio remains unavailable. No implicit face valence.
- Verify replay produces stable unique IDs and handles missing/ambiguous observations.

quant_engineer:
- Own backend/quant/, backend/execution/, handoffs/quant.md.
- Read PLAN sections 10–12 and frozen signatures.
- Implement pre-update normalisation, unique feature ledger, bounded source aggregation, nonnegative relevance, market-anchor correction, side-specific EV, fixed paper risk and depth-aware paper accounting.
- No sqrt(N), no viewer-count reliability, no repeated-window compounding, no live orders.
- Verify hand calculations for negative absolute/positive z, duplicate idempotency and the 9.7-cent Yes/86-cent No example.

frontend_engineer:
- Own frontend/ except generated types, handoffs/frontend.md.
- Read PLAN sections 13–15 and frozen snapshot examples.
- Build the terminal UI against frozen mock snapshots first, then transport adapter.
- Separate mode/freshness/calibration badges, aspect scores vs z, market prices/estimate, receipts and paper tape.
- Connect using generated types. No locally invented backend fields.
- Frontend dependency/lockfile owner; coordinate installs. Verify typecheck/build.

Root meanwhile owns main.py/core/config/scripts/generated types and integration preparation. Do not edit worker-owned source while they are active. Handle precise contract requests; update consumers/version coherently.

Each worker must return paths, signatures, actual verification, limitations, blockers and integration actions. Wait for all three. Inspect diffs, run imports/typecheck, update STATE and assign focused fixes before G3.


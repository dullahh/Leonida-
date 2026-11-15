Current checkpoint: **G3 complete; stop before G4**. See [G3_HANDOFF.md](G3_HANDOFF.md) and [STATE.md](STATE.md). The original job packets and earlier status notes below are retained as history. A focused tester-owned tests/g3 acceptance module now exists and passes; it is not the broader V4 suite.

# Current G2 status - 15 November 2026

P2 media/replay, Q2 features/pure paper plans, U2 React transport and R2 media runtime/persistence are implemented. Direct handoffs are `handoffs/pipeline.md`, `handoffs/quant.md` and `handoffs/frontend.md`; none delegated. Root acceptance is `docs/G2_HANDOFF.md`. Original packets below remain design context; the handoff records completed and remaining scope.

The latest user accepts generated media if no recording is supplied. P2 passed with two generated recordings through actual decoding/OCR/ASR. Real Twitch overlay accuracy remains unverified. Audio extraction/transcription is primary G2 scope, superseding optional-speech wording below. G3 full broker scheduling/tape and G4 formal suite remain unexecuted.

# Leonida Alpha: bounded implementation jobs

G1 checkpoint: 14 November 2026. P0 and F1 are complete. The current turn stops after G1; P2/Q2/U2 and all later jobs are unstarted. G1 commands below now exist and were run; later commands remain targets. [G1_HANDOFF.md](G1_HANDOFF.md) defines the implemented subset and checks, and [STATE.md](STATE.md) records current evidence.

## Rules inherited by every packet

Root supervises workers directly. Workers must be told they are not alone in the shared directory, must preserve others' edits, and must never delegate. At most three spawned workers run concurrently; implementation delegation starts only after G1. Unlisted paths are forbidden. Workers do not edit shared schemas/config/generated types, another owner's source, runtime process state or Git state. Root owns servers and the one SQLite writer. Tester alone creates test source; reviewer cannot edit application files.

Every packet consumes the root-frozen DTOs/imports/signatures in implementation-plan sections 3–4. Contract requests name task, exact field/signature, reason, producers/consumers, migration and acceptance impact. Dependency requests name package, purpose, version constraint, alternative and owning manifest. Send requests to root and continue independent work. Root resolves changes and regenerates consumers; no arbitrary dicts or local field renaming bridge interfaces.

Every worker handoff contains changed paths, public interfaces, exact check commands and actual exit/results, limitations/assumptions, blockers/dependency requests and root integration actions. No passing test/live capability claim without execution/observation. No global installs, worker git operations, real-money routes or fabricated provider output. Root updates STATE/DECISIONS at checkpoints.

## P0 — planning and review: complete

- Owner/root writable paths: these four planning docs only. Read AGENTS, README, all PLAN sections, prompt 00 and actual assets/tools.
- Reviewers: directly spawned `review_quant` (quant_engineer) and `review_runtime` (qa_reviewer), writable paths none. Both returned and rechecked the resulting plan; neither delegated or edited files. Role-specific PLAN reading limits were honored.
- Output: architecture, retained stack, module signatures, dependency DAG, gate schedule, decisions and bounded jobs. Final feedback on relevance, group-aware inputs, deadlines, baseline cardinality and delayed-fill pricing was reconciled.
- Actual acceptance: role returns, supported CLI feature inspection, isolated existing pack validation and original-file hash preservation. Application acceptance remains unrun.
- Next: implementation starts with `docs/prompts/01-foundation.md`; stop planning before code.

## F1 — root foundation and freeze (G1): complete

Implemented in root-owned paths only; no implementation workers were spawned. Actual recording/OCR is an explicit unavailable adapter. Cached fixture processing, offsets, calculations, state/receipts, SQLite/idempotency, generated types and the HTML viewer work. Optional live GTA VI quote context was observed and is isolated from proxy calculations. The small G1 contract is frozen at schema 2; the larger proposed G2 interfaces need root finalization before delegation.

Purpose: one real computed observation-to-candidate chain, visible before parallel expansion.

- Owner: root. Read PLAN 1–7, 10–14, 16–18 and prompt 01.
- Writable: `backend/core/**`, `backend/main.py`, `contracts/**`, `config/**`, `scripts/**`, `data/snapshots/**`, `frontend/src/generated/**`, `pyproject.toml`, `uv.lock`, root `package.json`/`package-lock.json`, `Makefile`, `.gitignore`, `requirements-handoff.txt`, `docs/**`. No worker-owned source or test files. No .codex change currently needed.
- Inputs: reference v1, historical capture, model/risk configs, installed Python/uv/npm. Runtime dependencies and frozen application interfaces do not exist yet.
- Outputs: canonical schema 2/protocols, archived reference v1, complete serialization schemas/examples/TypeScript, clock/identity/config/writer/projector, root `reference_slice.py`, `config/foundation_scenario.json`, `scripts/state_viewer.html`, health/ready/state/WS, Windows runner and Make aliases.
- Seed: x=-.4 narrative claim with exact source support; explicitly seeded previous mean 0/variance .04/count 20 gives z=-2 before update. Synthetic Yes .14/.15, No .85/.86 and known size/simulation fees. Existing coefficients give A=-.18 and No net EV≈.005922, below .03: show an honest blocked/candidate decision and no fill. All source/market/receipt references resolve.
- Required behaviours: stable identity, reasoned missingness, separate modes, real calculations, no duplicate baseline updates or publication ingestion; explicit group-aware EvidenceViewDelta; deterministic run clock/deadline protocol; one writer. Archive/generate with pinned Pydantic serialization output, Decimal strings on the wire.
- Non-goals: six scenarios, React UI, broker fills/exits, optional providers, root-authored tests.
- Acceptance targets: `python scripts/manage.py setup`; `python scripts/manage.py check --gate G1`; `python scripts/manage.py demo --scenario foundation`. The G1 check dispatches imports/schema validation and existing checks, not a new root-authored test suite. Root performs focused HTTP/WS/viewer and duplicate-input checks and records exact commands/results.
- Gate: one calculated observation reaches the visible full envelope with evidence/feature/estimate/decision/receipt IDs, heuristic label and correct side EV; REST/WS shapes agree; repeats leave baseline/correction unchanged. Clearly identify later tests/UI as unimplemented.
- Capture refresh, if attempted: actual responses/timing only; record failure and retain historical/synthetic distinction. No-key slice does not depend on success.
- Checkpoint/handoff: STATE/DECISIONS/TASKS and exact frozen imports/signatures/examples. Only after G1 passes release P2/Q2/U2 under prompt 02.

## P2 — primary recorded GTA V OCR and cached evidence (G2): not started

- Purpose/owner: pipeline_engineer preprocesses 2–6 local screen recordings of Twitch GTA V streams with visible chat, then plays cached evidence without external calls. Read AGENTS, role-assigned PLAN 5, 8, 9, 15 and updated implementation-plan section 8. Do not delegate.
- Writable: `backend/ingestion/**`, `backend/perception/**`, `data/scenarios/**`, `data/recordings/**` manifests only, `handoffs/pipeline.md`. All shared/config/generated/test/UI/quant paths and server lifecycle forbidden.
- Depends on F1: RunContext/ReplayEvent, SourceWindow, EvidenceClaim, EvidenceGroup, source status, quote-book DTOs and root identity/Clock/config helpers.
- Interfaces: `ReplaySource.events(context)`, `Extractor.extract(window)`, `Grouper.upsert(claims)`. Root forwards claim/group revisions together as EvidenceViewDelta; group-only changes must not be hidden mutable state.
- Primary inputs: supplied recording paths/hashes/permission notes; per-video trim and timeline offsets, normalized chat ROI, 2s initial frame sample interval, OCR language/engine/preprocessing and semantic versions. Follow the schema-2 RecordingManifest and `RecordedPreprocessor.preprocess(manifest, cache_directory)` seam. G1's adapter raises NotImplementedError for actual preprocessing; replace it through root integration without fabricating media.
- Implement actual frame decoding and crop/OCR with a root-approved dependency/engine. Preserve raw line boxes/confidence/frame refs/media timestamps, distinguish generated OCR IDs from native Twitch IDs, deduplicate overlapping visible lines without erasing genuine later repetitions, and report sampling/visibility gaps. Ask root for any required cache-contract additions before export.
- Freeze raw OCR and derived claims separately in immutable content/version-addressed caches; replay never reruns OCR or a semantic provider. Test trim/alignment with `replay = media - media_start + timeline_start`, changed ROI/version cache invalidation, stationary-chat dedup, uncertain OCR abstention and different recording arrival times. No audio/face sentiment is implied by visible chat.
- Preserve `content_game_id=gta5`, `evidence_scope=proxy_demo`, target `gta6` across receipts/UI. Automatic relevance to actual GTA VI contracts is zero; candidate scenarios use their synthetic namespace. Coordinate with frontend for 2–6 real recording slots and independently fresh venue quotes.
- Deliver manifests/event timelines for `courtroom-praise`, `technical-failure-laughter`, `skill-rage-controls`, `mixed-missing-facecam`, `duplicate-reconnect`, `venue-outage-reset`. Each has six statuses, applicable gaps/offline sources, source/availability offsets, manual scene/phase/build/platform, seed/baseline and explicit synthetic quote books. Claim spans/timestamps must be supported; ambiguous/skill/unrelated targets are preserved honestly.
- Fixture extraction identifies itself as supplied synthetic claims. Deduplicate original/rebroadcast dependency groups; six streams do not imply six independent incidents. Missing modalities remain null. Explicit liquidity replenishment differs from quote republication. Coordinate eligible/blocked fixture cases through root with quant; no guaranteed P&L.
- Non-goals: live Twitch chat/A/V acquisition, automatic scenes, native chat IDs inferred from pixels, fake media or face valence. Speech transcription uses local Whisper; missing models preserve PCM and explicit speech-unavailable reasons.
- Acceptance targets: owned validation CLI `uv run --frozen python -m backend.ingestion.replay --scenario all --validate-only`; focused stable-ID/order summaries at 1x/5x. After V4 exists: `uv run --frozen pytest -q tests/integration/test_replay.py`.
- Gate: actual preprocessing observations from at least two supplied recordings and up to six supported, traceable sampled frames/OCR, offsets and repeatable cached playback; preserve six parseable fallback fixtures with explicit modes/gaps. If no user recording exists, the latest user authorizes generated media through the actual providers; structured fixtures alone do not satisfy this gate.
- Checkpoint/handoff: first scenario through frozen contracts, then six; `handoffs/pipeline.md` includes factories/manifests, actual checks, source limits and integration actions.

## Q2 — feature model and paper plans (G2)

- Purpose/owner: quant_engineer implements correct bounded estimates and paper lifecycle. Read AGENTS and role-assigned PLAN 10–12, 17 plus frozen math/interfaces. No delegation.
- Writable: `backend/quant/**`, `backend/execution/**`, `handoffs/quant.md`. Schema/config/migrations/main/scenarios/tests/frontend/processes forbidden. No independent DB writer.
- Depends on F1: EvidenceView/Delta with claim/group revisions; Clock; market identity/EstimateResult; PortfolioView/LiquidityView/ExecutionPlan/WriteBatch/config. Read P2 fixtures when ready; use focused in-memory calculations independently meanwhile.
- Interfaces: FeatureEngine ingest/rebuild/snapshot, Router, Estimator, FeeAdapter, Risk, PaperBroker.plan, Portfolio.mark. Planning does not mutate authoritative cash/baselines before root commit.
- Behaviours: one baseline observation per stream/aspect/modality/bucket despite multiple scenes; pre-update z/warmup; source/bundle caps; relevance outside source normalization once; explicit freshness; revision rebuild; no viewer/sqrt(N)/face effect; correct defect direction; unsupported/coherence abstentions.
- Execution: fixed requested quantity 10, synthetic known fee/step/latency; reservations; eligibility-time estimate/EV/risk recheck respecting original limit/reservation; IOC partial fills; separate outcome and bid/ask liquidity keys; Decimal cash/fees/marks/exit basis; unpriced residual; labelled 300s time/risk exits exempt from entry EV/cooldown. Stale/unknown/mixed/live cannot silently fill.
- Non-goals: real orders, calibrated posteriors, actual venue fee model, maker queues, Kelly or scalp guarantee.
- Acceptance targets: `uv run --frozen python -c "import backend.quant.features; import backend.execution.broker"`; documented in-memory calculations for negative-absolute/positive-z, duplicate/revision/relevance/ageing, .097 Yes/.86 No example, delayed EV, partial entry/exit and cash. No test source creation. After V4: `uv run --frozen pytest -q tests/quant tests/execution`.
- Gate: hand calculations match; both eligible/blocked cases explained; duplicate publication cannot refill a book; typed execution plans can commit and restore atomically.
- Checkpoint/handoff: feature boundary then broker boundary; `handoffs/quant.md` records signatures, exact config requests/rounding examples/checks and root actions.

## U2 — terminal UI and transport (G2)

- Purpose/owner: frontend_engineer makes evidence/provenance/paper state inspectable. Read AGENTS and role-assigned PLAN 13–15 plus generated examples. No delegation.
- Writable: `frontend/**` except `frontend/src/generated/**`; `handoffs/frontend.md`. Own frontend package/lockfile; backend/config/scripts/generated/test/server paths forbidden.
- Depends on F1: generated serialization types/schema, complete mock envelopes including null/abstention/reset, ReceiptDetail and command DTOs. No invented fields or hand-edited generated types.
- Build React/TypeScript/Vite, one envelope decoder/run-sequence store, REST fallback/WS, old-run and stale-sequence rejection, gap resync and idempotent reset acknowledgement handling.
- Panels: independent evidence/quote/paper/heuristic badges; source grid and absolute/z; market rules/side prices; estimate-reference trace; evidence/scene/disagreement; receipt drawer; paper fills/fees/realised-unrealised/partial marks; six replay controls. Use explicit units and reasoned nulls. No authoritative accounting recalculation in browser.
- Non-goals: fabricated video, elaborate charts, production hosting or backend contract edits.
- Acceptance: `npm.cmd --prefix frontend ci`; `npm.cmd --prefix frontend run typecheck`; `npm.cmd --prefix frontend run build`. Focused interactions use root-started servers; tester alone authors browser source.
- Gate: mock envelopes render/typecheck, no NaN or neutral defaults for missing data, reset clears previous run, visible values/units match contracts. Build ready for root same-origin serving.
- Checkpoint/handoff: mock layout then transport; `handoffs/frontend.md` with actual commands/build output and integration requirements.

## R2 — root runtime preparation in parallel

- Purpose: prepare durable runtime without touching active worker paths.
- Writable: `backend/core/**`, `backend/main.py`, `config/**`, `scripts/**`, `contracts/**`, `frontend/src/generated/**`, `data/snapshots/**`, root manifests/lockfiles, `docs/**`. All worker/test source forbidden.
- Depends on F1 and frozen boundaries; consumes each worker handoff as it arrives.
- Implement writer/migrations, expected-revision atomic batches, command keys/payload conflict, persisted replay cursor/portfolio/liquidity/deadlines, paused restart, root market adapter and bounded projector. Deterministic scheduler processes controls, external inputs, recomputation, exits, pending entries, new intents; quiet intervals advance expiry/eligibility without waiting for observations.
- Future captures use collision-safe immutable writes/per-page availability, preserving old capture. Optional fetch has bounded whitelist/timeouts/backoff and no replay dependency.
- Acceptance: schema/import/readiness checks; focused command retry/conflict, silent-interval deadline, REST/WS and restart probes on disposable run. Formal regression source waits for tester.
- Handoff/checkpoint: STATE records process owner, DB path, migrations/endpoints and actual checks. G2 is incomplete until all three worker handoffs arrive.

## I3 — root integration (G3)

- Read PLAN 13, six scenario invariants and prompt 03. Writable root scope as R2; defects go back to owners. At most two fix workers while root integrates.
- Depends on P2/Q2/U2/R2 handoffs and frozen contracts. Compose windows -> claims/revisions/groups -> features -> routes -> estimate -> risk -> pending/eligible execution plan -> atomic ledger -> receipt -> projection.
- Remove reference_slice from normal runtime selection; any retained diagnostic mode is labelled. Quote updates and deterministic ageing do not add evidence. Restart rebuilds features without re-executing fills. Root owns servers.
- Acceptance targets: `python scripts/manage.py demo --scenario courtroom-praise`; focused six-scenario receipt/accounting/transport checks; isolated reset/reconnect/restart; frontend typecheck/build. No formal G4 claim yet.
- Gate: six statuses/scenario behaviours, side-specific eligible/blocked candidates, partial/no-fill/exit states, stale entry stop, fully linked receipts, old-run rejection and recovery with unchanged ledger.
- Checkpoint/handoff: STATE with actual run/DB/process/commands and ownership defects, then freeze integrated inputs for V4.

## V4 — tester invariants and browser harness (G4)

- Owner: tester. Read AGENTS, role-assigned PLAN 15, 17, 20 and frozen contracts/failures. No delegation.
- Writable: `tests/**`, `handoffs/tester.md` only. Production/config/generated/manifests/server state forbidden. Dependencies requested through root and frontend owner where applicable.
- Depends on I3, scenario fixtures, deterministic quant APIs and isolated run/DB factory. Deterministic tests need no providers/network.
- Planned files: `tests/contracts/test_contracts.py`, `tests/quant/test_features.py`, `tests/quant/test_estimates.py`, `tests/execution/test_broker.py`, `tests/integration/test_replay.py`, `tests/integration/test_transport.py`, `tests/integration/test_recovery.py`, `tests/browser/test_desk.py`; test-only fixtures under tests. None exists today.
- Cover missingness/run/reference integrity; pre-update/warmup/constant inputs; negative absolute/positive z; sign/skill/null/mixed claims; duplicate/revision/group corrections; relevance/ageing/source caps; quote-only correction; threshold/winner constraints; side-specific VWAP/fee/depth/reservation/cash; delayed revaluation; partial marks/exits; stale/mode gates; quiet deadlines; transactional crash/restart; 1x/5x; REST/WS resync/reset; six scenario receipts.
- Root arranges a scoped usable browser runner, preferably Python Playwright plus pytest-playwright dev dependencies if installation succeeds; tester writes source. Installed Selenium alone proves nothing. Record the actual browser session before claiming availability.
- Acceptance targets: `uv run --frozen pytest -q tests/contracts tests/quant tests/execution tests/integration`; `uv run --frozen pytest -q tests/browser --base-url http://127.0.0.1:8000` using the matching runner/plugin. Root manage check/demo-check dispatches these tests, not duplicate assertion scripts.
- Gate: actual passing invariants on isolated temporary DBs/run IDs; failure goes to one owner, affected check reruns after fix, then required suite once. If browser cannot run, browser gate remains open; a manual checklist is not an automated pass.
- Handoff: `handoffs/tester.md` records actual commands/results, skipped/blocked checks and exact reproduction IDs. No arbitrary test-count target.

## B4 — isolated browser review (G4)

- Owner: qa_reviewer. Read AGENTS, role-assigned PLAN 12–15, 17, 20 and prompt 05. Writable `handoffs/reviewer.md` only; no application/tests/manifest edits, delegation or process lifecycle.
- Depends on root-started ready servers and proven browser tool/harness. Use a dedicated synthetic QA run, never another user's run.
- Inspect all six scenarios, modes/freshness/calibration/units, absolute/z, rules/receipts, partial/no-fill/exit accounting, outage and entry pause, reconnect/resync/reset, laptop and narrow layouts. Capture console/network/screenshots and run/scenario IDs.
- Acceptance: actual isolated browser interactions plus V4 harness where usable; distinguish manual inspection from automated results. No browser access leaves browser acceptance outstanding.
- Handoff: severity, expected/observed, reproduction/owner and evidence; root assigns fixes to owners then reruns affected flows.

## D5 — repeatable demo/release (G5)

- Owner/root writable: scripts/docs/root manifests/config/generated artifacts and README for release; worker fixes retain ownership. Read prompt 06 and PLAN 20.
- Depends on G4 with material defects resolved. Stop adding optional scope.
- Output: README setup/mode explanations/limits, one-command no-key demo, actual verification summary, six-scenario rehearsal and capability matrix. Archive locally if Git is still absent; commit only within an established authorized Git workflow.
- Acceptance: `python scripts/manage.py setup`, `python scripts/manage.py check`, `python scripts/manage.py demo-check` from documented clean dependency conditions; repeat the three-minute demonstration on the presentation machine without runtime credentials/internet. Missing gates remain missing, not caveated passes.
- Handoff: final STATE/README/demo evidence, defects and next research work: as-of historical corpus, held-out market comparison, calibration and execution realism.

## Optional jobs after core gates

O-MARKET/root: deeper public venue/depth support beyond the observed G1 read-only context; fills off. Recording/chat OCR is P2 primary scope, not optional. O-SPEECH/pipeline: actual timestamped transcription of supplied commentary. O-CHAT/pipeline: native live message IDs/latency/dedup/recovery. O-AV/pipeline: one authorized live A/V route before scaling. Each stretch job needs a root-issued bounded packet and observations.

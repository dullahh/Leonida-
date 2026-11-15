# Repository state - 15 November 2026

## Local speech upgrade

Single thread, no agents. `small.en` is now the default for future preprocessing
after both comparison and the full local quality pipeline succeeded; `--asr-model tiny.en`
is the explicit fast fallback. No OCR/claim/reaction/pricing/frontend/scenario logic
changed. The ASR-only pass preserves all1,553 original OCR observations exactly,
adds35 accepted small speech observations, and retains10 uncertain/23 rejected
speech segments in audit only. All speakers remain unknown; supported quality
claims, estimates and decisions remain zero. The old1651-observation playback cache,
pointer and running user server remain unchanged.

New quality cache: `var/evidence-cache/c50cb055b472236a68dc526cbca092cdcead3367384dbc8a8437de0bf67ea751.json`.
Independent model caches: `var/asr-cache/local-asr-v2/`. Final side-by-side review:
`var/asr-comparison/v1/d8730e510b079f8502bf1facea19dc7c4701cc19a98f2f219c451e602a448aba/`.
See [audit/commands/results](LOCAL_ASR_UPGRADE.md) and [listening review](ASR_COMPARISON.md).
All intervals need listening review; no reference transcripts or accuracy improvement
are claimed. Both models still loop on t4; strict gates reject that text before
classification. Small took275.033s versus tiny66.851s on273.744s of comparison audio,
including the overlapping2s no-speech control. The downloaded small files total486,098,798 bytes.

G3 passed22 tests plus schema/type/frontend build checks; G4/release suite passed11
tests with the documented Windows socket/shutdown warnings. Six-scenario release
HTTP/WS smoke passed. No deployment/push; stop after the local ASR upgrade.

## Quote and abstention display clarification

Display-only fix from87c34a2: valid14¢/15¢ synthetic quote now displays14.50% market reference even when claims abstain. Model/correction/candidate remain unavailable with precise explanations; source-card absent-value reasons are explicit. Venue context exposes exact receipt time/source and was audited as eight bundled stale historical Kalshi quotes, polling disabled. Existing optional --live-quotes command and failure/expiry behaviour are documented in [QUOTE_CLARITY.md](QUOTE_CLARITY.md). Release checks pass:15 G3 tests,11 G4/startup/display tests, six-scenario smoke and frontend typecheck/build. No classification, pricing gate, coefficient, execution, scenario or media change. Separate commit title: Clarify quote and abstention states. Stop after this fix.

## G5 local release candidate

Final pass began from74d6949, in one thread. Both full local and portable no-key launch modes verified; missing local media/cache selects a clearly labelled portable fixture. Matching saved inputs resume paused; different saved scenarios cannot override the requested mode. No analytical/provider/media/frontend feature changes. Final G3 checks15/15 and G4+release checks10/10 pass, with no skips. Clean source-only offline dependency installation/build, portable/full startup and22.4s control rehearsal pass; desktop/narrow console checks clean. Existing user8000 demo retained; temporary8002/8003 release servers stopped. See [G5_RELEASE_REPORT.md](G5_RELEASE_REPORT.md), [DEMO_SCRIPT.md](DEMO_SCRIPT.md), [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). Final separate commit: G5 demo release. No publication, push or deployment; stop after local release.

## G4 verification checkpoint

Verified from4e154fa in one thread, without agents or application changes. Original15 G3 tests/build/schema checks and6 new G4 tests pass with no skips. Browser verifies all5 videos, telemetry/pricing exclusion, synthetic claim receipts, reset/reconnect/REST fallback and1440/390 layouts without console errors. Initial browser-harness debug-overhead failure and Windows media teardown warnings are recorded in G4_FAILURES.md. Full results, limitations and launch/demo checklist: [G4_VERIFICATION.md](G4_VERIFICATION.md). Separate commit title: G4 verification fixes; G3 is not amended. Existing user demo on8000 is retained. Stop after G4; G5 is unexecuted.

## Current reaction telemetry integration

Reaction telemetry is integrated alongside the unchanged supported-claim classifier. See [REACTION_TELEMETRY.md](REACTION_TELEMETRY.md). All1651 cached observations were used without OCR/ASR/media reprocessing: t1/t2/t3/t4/t5 have8/1/8/6/13 active text cues respectively, but still zero supported quality claims and zero recorded estimates/orders. Text-only emotion/intensity/target scores remain heuristic; pending speaker verification is unchanged.

The five source cards show activity timelines, strongest recent reaction, contextual/supported status and pricing reasons. Attribution>=.90, claim confidence>=.60 and market relevance>=.80 are explicit gates; intensity never enters pricing. The separate synthetic Courtroom fixture still has three included claims and an estimate change. Schema2 additive revision is g3-reactions-v1; generated types/OpenAPI are current.

All15 G3 tests pass (original9 plus6 focused reaction checks), with zero skips; schema/type/build checks, six-scenario HTTP/WS/receipts smoke,1651-observation recording smoke and G1 diagnostic pass. Browser five-panel/contextual/supported fixture and390px checks pass without page errors. No subagents, paid calls or G4 work occurred. Single-thread authorization covered the focused source, frontend and test changes.

Current root-owned server PID93168: http://127.0.0.1:8000, database `var/recordings-reactions.sqlite3`, recordings paused0 after browser reset and restart. The existing combined evidence cache/pointer is unchanged. Exact launch: `python scripts/manage.py demo --scenario recordings --cache var/evidence-cache/aa20c31e1a27bbf0fe075f2c9136360e7096731d9365cdd247c89ade4afe95b6.json --db var/recordings-reactions.sqlite3`. Stop the current server before rebinding8000. Stop after this integration.

## Current t4/t5 recording validation

Added and preprocessed only t4.mp4/t5.mp4, using their own manifest and fitted chat crops. Current app http://127.0.0.1:8000 uses root-owned PID14352, DB `var/recordings-t1-t5.sqlite3`, active run `run:0324ecedd2df934293e0d2ea`, all five recordings paused0. The earlier process67112 was stopped after identity verification; its database remains intact.

Combined cache `var/evidence-cache/aa20c31e1a27bbf0fe075f2c9136360e7096731d9365cdd247c89ade4afe95b6.json` is selected by the pointer. Original629 t1/t2/t3 observations were copied and compared exactly, without reprocessing or relabelling. New t4/t5 observations467/555 all abstain. Individual/new-combined/all-five projections return null estimates and no orders. Total1651 unique observation IDs.

Full transcripts and interval-specific pending manual speaker review records are reviewable. No explicit game-quality sentence was found by tiny.en or the shorter-window base.en text review; no speaker attribution was fabricated from facial reactions. Audio listening remains unavailable, so verification/admission of a supported spoken reaction is incomplete. See [T4_T5_REVIEW.md](T4_T5_REVIEW.md) for exact transcripts, timing limitations, classifier fields, commands, cache composition and browser results. No subagents, G4, UI redesign or classifier change occurred in this task.

Restart (after stopping the existing owned process): `python scripts/manage.py demo --scenario recordings --cache var/evidence-cache/aa20c31e1a27bbf0fe075f2c9136360e7096731d9365cdd247c89ade4afe95b6.json --db var/recordings-t1-t5.sqlite3`.

## Current G3 checkpoint - complete; stop before G4

G3 integration, nine focused acceptance tests and the integrated Edge browser demo passed. See [G3_HANDOFF.md](G3_HANDOFF.md) for exact commands, scenario results, preservation audit and limitations. No G4/G5 gate was started.

App: http://127.0.0.1:8000; root-owned Uvicorn PID **67112**; database `var/g3-recordings.sqlite3`; active run `run:d6820290b5d69b01b11882bc`, **recordings paused at zero**. Keep this requested demo running. The old G2 process78492 was stopped; its database/cache remain intact.

The verified t1/t2/t3 cache below remains unchanged. All629 observations abstain; no estimate, candidate, order or fill is fabricated. Six statuses show three available recordings plus three unavailable slots. A separately selected synthetic courtroom scenario proves estimate change, depth-limited entry, eligibility recheck, partial/final exits and Decimal accounting. Synthetic scenario selection/reset creates a new run and preserves old receipts. Actual GTA VI quotes remain separate historical/stale context.

After the session interruption, git status confirmed no Git repository. Backend/frontend files were inspected before resumed writes; no application truncation was found. Existing valid modules were preserved. Missing G3 acceptance/command coverage and two frontend contract/freshness gaps were finished. No dependency, recording manifest, source video or cache was changed during recovery.

Passed: `check --gate G3` (9 tests, zero skips, schema/type drift, six scenarios, frontend build), `demo-check --scenario all`, `demo-check --scenario recordings`, `demo-check --scenario foundation`; actual browser source playback, scenario lifecycle/receipts/manual exit, stale cancellation, reset/reconnect/REST fallback, 1440/390 layouts. No unresolved G3 failure. Local screenshots/reports: `var/g3-review/`. Restart with `python scripts/manage.py demo --scenario recordings --db var/g3-recordings.sqlite3` after stopping the existing process.

## Earlier supplied-recording follow-up (G2 history)

The user supplied t1.mp4, t2.mp4 and t3.mp4. All three were configured, processed and loaded in the G2 demo at http://127.0.0.1:8000. That checkpoint used PID78492, DB var/recordings-t1-t3.sqlite3 and run:f390c309c62d6b561618648d, paused at0. Its instruction to stop before G3 was superseded by the user's later G3 request.

Final cache: var/evidence-cache/a6d8a27fa3c4f5c3e34b2b8a411457e6cc2a50b5362341b12bd8904d039343d9.json; var/last-recording-cache.txt selects it. Frames 20/27/23 produced OCR 89/202/277 and ASR 16/19/26 observations, totals 105/221/303. All 629 abstain from quality scoring, so estimate/decision/receipt are absent. Speaker identity is unknown and scenes unassigned; actual GTA VI quotes stay separate. Manifest offsets are 0 and hashes remain null until preprocessing.

Actual preprocessing, cached reuse, G2 checks, isolated HTTP/WS smoke and three-video desktop/mobile browser checks passed. OCR was visually checked against native crops. Audio was machine-cross-checked with another model; direct listening is unavailable here, so transcript accuracy remains unverified. Five t3 speech segments are flagged for repetition/high compression. Out-of-audio ASR timestamps now fail validation; old raw OCR can be reused only with verified matching provenance.

Detailed findings, crops, examples, command results and listening artifacts: [RECORDING_REVIEW.md](RECORDING_REVIEW.md). G2 input verification is now based on supplied media. The earlier generated-demo acceptance below is retained as history; its no-user-input/server-stopped statements describe the earlier handoff, not the current state.

## Earlier G2 acceptance history

## Gate and scope

G2 functional acceptance passed with the user-authorized generated-media substitute. Stop after G2. No user recording was present. G1 remains a working fallback; G3 full broker scheduling/tape, G4 formal regression/reviewer gate and G5 release are not claimed complete.

Read G2_HANDOFF.md for acceptance/run instructions, G2_CONTRACTS.md for actual imports and wire boundaries, and IMPLEMENTATION_PLAN.md for the revised plan. The original G1 report is retained as history.

## Delivered ownership

- Root: schema-2 g2-v1 media/playback extensions, generated JSON Schema/TS/OpenAPI, cached media projection, playback/control/recovery, single-writer transactional broker seam, secure media/artifact endpoints, setup/CLI/generated recording helper, dependency locks and documentation.
- Pipeline: backend/ingestion, backend/perception, six data/scenarios, data/recordings manifest/drop instructions; handoffs/pipeline.md.
- Quant: backend/quant, backend/execution pure feature and paper engines; handoffs/quant.md.
- Frontend: React/TypeScript/Vite terminal, dependency lock, synchronized video/transport/receipts/provenance; handoffs/frontend.md.

All three workers were directly supervised and did not delegate. All handoffs arrived. No worker edited root contracts or created tester-owned source. Root performed integration and process lifecycle.

## Actual local inputs and outputs

No user-supplied MP4/MKV/MOV/WebM/audio file existed at initial G2 scan. Generated test recordings now live under var/generated-demo with a manifest, two12-second H.264/AAC videos and SAPI narration. They are explicitly synthetic test graphics/chat/voice, not actual GTA V or Twitch footage.

Actual local FFmpeg + RapidOCR + Whisper tiny.en processing yielded11 sampled frames,10 unique OCR observations and2 speech observations;9 interpretations are attributable. Cache and every artifact hash validate. Current cache:

`var/evidence-cache/46b767d6b708d63c40ae27472ceca90bbc1637ef9a7ddabd30184c723363da9a.json`

The same verified cache exists under var/g2-media-cache. var/last-recording-cache.txt points to the integrated var/evidence-cache copy. Downloads/models/QA outputs are ignored local artifacts. Real source files belong in data/recordings/inbox; edit its sibling manifest, then preprocess.

The final recording snapshot has12 windows,7 unique stream/aspect/modality buckets, null surprise during unseeded warmup, narrative model probability0.14259941588529948 and No EV-0.01259941588529948 USD/contract. It remains candidate-only with zero orders/fills and10000USD cash. Actual GTA VI captures stay separate/stale. No live polling was re-verified during G2.

## Verification actually run

- `python scripts/manage.py setup`: exit0 after final locked installation and frontend build.
- `python scripts/manage.py setup-speech` equivalent helper: approved local-model download succeeded; no key. Runtime has no downloads.
- Generated recording helper and integrated `preprocess --manifest var/generated-demo/manifest.json`: exit0, both reports PCM/speechavailable.
- `export-contracts`: exit0; schemas/types regenerated coherently.
- `check --gate G2`: schema/reference invalid-case checks, generated drift/types, six scenario validation, public imports, frontend typecheck/build passed.
- `demo-check`: G1 isolated HTTP/WS/receipt/page and clean shutdown passed.
- `demo-check --cache <generated cache>`: G2 isolated HTTP/WS equality, calculated estimate/candidate/receipt/page and clean shutdown passed, including final integrated cache run.
- Pipeline inline checks: cache reuse/no rewrite/provider bypass, payload/artifact corruption rejection, ROI+offset reprocessing, chat overlap/reappearance, quality/target abstention, missing tools/models/files/path escape and six1x/5x scenario fingerprints passed.
- Quant inline checks: pre-update negativeabsolute/positivez, warmup/revisions/dedup/ageing/dependency caps, side EV, Decimal reservations/latency/depth/partial entries+exits/stale/recovery passed; exact values in handoff.
- Root inline runtime: offsets/as-of filtering, duplicate command/conflict, same end-state at1x/5x, no OCR during playback, quiet completion, paused restart and reset audit preservation passed.
- Root inline persistence: atomic broker plan+records/command, duplicate-command rollback, four-contractpartialfill/cash9996.52, reopen and no refill passed.
- Root inline HTTP: videoRange206, frame/audio200, arbitrary/escapedreference404, changedmediahash409 passed.
- Frontend actual Edge Playwright: two synchronized decoded videos,2xspeed/pause/seek/reset, rawframes/audio, receipts, oldrunrejection, RESTfallback/reconnect, desktop 1440/narrow 390, nooverflow and no console/HTTPerrors. Final source-aspect/count/duration fixes rechecked.

Evidence files: var/g2-runtime-checks.json, g2-persistence-checks.json, g2-http-checks.json; frontend/.qa/g2-browser.json, g2-final-ui.json and desktop/mobile screenshots. This is G2 verification, not a formal G4 test suite.

## Processes and launch

Root preview PID100364 was stopped and absence verified. Isolated inspectors await shutdown and close their temporary DBs. No shared preview process should remain. No deployment or hosting was performed.

Run `python scripts/manage.py demo` then open http://127.0.0.1:8000. It selects the latest recording cache, falling back to foundation only without a cache pointer. Explicit fallback: `python scripts/manage.py demo --scenario foundation`. A named six-source fixture uses `--scenario courtroom-praise`, etc. Normal runtime DB defaults to var/leonida.sqlite3; QA used separate databases.

## Limitations and next work

Real Twitch overlay accuracy and2-6real-source load need supplied footage. English lexical semantics are conservative/unvalidated; automatic diarization, scene recognition and native live chat/AV are absent. Only narrative has a configured estimate route. Long recordings need excerpts and may need pagination/efficient incremental projection. Original browser codec support varies; H.264/AAC was verified.

Paper components and atomic persistence work, but automatic broker scheduling, detailed orders/fills/positions projection and execution tape remain G3. Media must remain candidate-only until an explicitly authorized later integration. No actual venue fee/depth or calibrated prediction claim. Formal tester-owned tests remain G4. No Git repository/commit was initialized.


## Frontend terminal redesign - 15 November 2026

User scope: one thread, Playwright MCP, frontend and design documentation only, starting with application baseline 1baadb2. HEAD 2935a2e added README only and is retained. No workers, backend/contract/calculation changes, media processing, external runtime dependencies or live venue fetches.

Implemented neutral terminal surfaces, compact command/replay/scenario chrome, three-column synchronized source workspace, sticky market/model rail, source-aligned reaction/claim timeline, evidence tape, paper blotter and right-edge receipt inspectors. Below 700px the market summary precedes an active-source selector; tables scroll within labelled keyboard-focusable regions. Valid synthetic quote midpoint remains visible during model abstention. Existing semantic IDs/value assertions pass.

Verification: G3 15 tests plus contract/type/scenario/build checks; final G4/release 11 tests; all six release scenario smoke checks; frontend build and diff whitespace check passed. Playwright MCP inspected both modes before/after, five decoded videos, Courtroom three supported claims, partial fill/trace/receipt, venue rules/eight historical quotes, stale outage cancellation, source/search controls, drawer focus and Escape. Widths 390/700/768/1024/1440 have no page overflow; final browser errors/external resource requests zero. Existing G4 Windows socket/resource/shutdown warnings remain. See UI_DIRECTION.md and local artifacts in var/ui-redesign.

Isolated recordings/portable QA used ports 8002/8003 and separate var/ui-*.sqlite3 databases. Existing user server on 8000 was not mutated. No publication or push. Stop after the frontend redesign.

## Optional Twitch live audio demo - 15 November 2026

User requested a demo mode with actual streaming video and audio processed by Whisper. Added an optional official Twitch player embed plus explicit user-triggered browser tab-audio capture. The browser sends audio-only independent WebM/Opus chunks (15 seconds, 2 MiB maximum) to a loopback-only FastAPI route. The route serializes processing through one lazily initialized local Whisper instance; the adapter returns `evidence_mode=live`, timestamped accepted segments, source/payload hashes and the existing ASR quality audit. No incoming audio is durably persisted.

Live DTO remains separate from schema-2 `SourceWindow`, which is constrained to recorded/synthetic GTA V proxy evidence. Live capture currently yields transcripts only: speaker/game identity, semantic claims, scene alignment, market routing and paper effects are unavailable. Missing models and rejected speech remain explicit. Twitch's required `parent` value uses the current hostname. See README's optional live demo steps and `handoffs/pipeline.md`/`handoffs/frontend.md` for adapter details.

The frontend typecheck and production build passed. The backend adapter `py_compile` and diff whitespace check passed. No browser test or actual Twitch stream/audio was exercised, so end-to-end capture remains unverified. The adapter writes chunks briefly to a local temporary directory for FFmpeg conversion and removes it after processing; no evidence cache or durable transcript write occurs. Root owns the HTTP composition; pipeline owns `backend/ingestion/live_audio.py`; frontend owns the live panel.

Follow-up: the capture prompt now requests `preferCurrentTab`, includes the current Leonida tab, and excludes system audio. Instructions specify choosing **This Tab** with tab audio enabled so audio from the embedded Twitch player is captured. Browser confirmation remains mandatory and the chooser can still select another surface; this follow-up has not been exercised in a browser.

## Twitch game to Kalshi outcome discovery - 15 November 2026

User requested automatic market candidates from Twitch game metadata and supplied Kalshi's Video Games category, then added Esports. Added generated schema-1 `LiveMarketContext`, Twitch Helix app-token lookup using optional `TWITCH_CLIENT_ID` / `TWITCH_CLIENT_SECRET`, and a read-only Kalshi resolver that discovers series in Video Games and Esports, paginates open events with nested markets, and exact-matches the Twitch game against the actual Yes outcome. The UI presents both categories, actual ticker/event/series, raw market status, nullable bids/asks/depth, capture/source, and expandable rules alongside the live transcript.

The live discovery is intentionally outside the fixed schema-2 GTA V proxy estimation ledger. It exposes actual outcome candidates; game category and transcript do not yet produce claims, probabilities, or paper decisions. Open-market status is normalized only for raw `open` or observed legacy `active`. No ticker or spread is invented. Missing Twitch credentials, offline/category-blank streams, empty match lists, and venue lookup failures remain explicit.

Official site pages were reviewed; Kalshi's Video Games page contains multi-outcome award markets that substantiate exact Yes-outcome matching as a discovery method. API/adapter code compiled and frontend build/type checks ran. No app credentials were supplied; no Twitch API request or Kalshi market API request was made, and no actual browser live discovery was exercised. Thus live API availability and current category filter results are unverified. See generated `contracts/generated/live-market-context.schema.json`, `handoffs/pipeline.md`, `handoffs/quant.md`, and `handoffs/frontend.md`.

## Manual live game lookup and decision review - 15 November 2026

The live demo now accepts a manually entered game name, with or without a Twitch
channel. Manual names bypass Twitch metadata lookup and can query the existing
read-only Kalshi Video Games / Esports discovery. If channel and game are both
entered, the manual value is labeled as the game source and overrides Twitch's
category. Twitch audio capture still requires a channel/player.

Each exact market candidate receives a separate schema-1 `LiveDecisionReview`.
Current live review status is always `abstain`, with explicit reasons: this path
has no outcome-specific model and Whisper chunks are not connected to supported,
attributed features. It is distinct from the GTA V proxy estimator and emits no
probability, trade side, order or fill. This allows inspection of the real market
discovery plus decision-abstention path without implying a live strategy exists.
Generated contracts were regenerated. Runtime Kalshi discovery still requires a
networked local run; no live request was made for this change.

Follow-up from runtime logs: Twitch returned `Grand Theft Auto V`, but Kalshi
series lookups returned a non-list `series` field because the adapter queried the
website child labels (`Video games`, `Esports`) as if they were series API root
categories. The API requests now use the corresponding parent categories
`Culture` and `Sports`, narrowing Sports results to rows labeled Esports and
retaining Culture series for exact game-outcome matching. Unexpected response
shapes report response keys or API messages rather than the misleading
"omitted its series list". This parser adjustment is compiled but still needs a
user-run live API retry.

## Live audio sentiment wiring - 15 November 2026

Accepted segments from user-authorized browser tab audio now pass through the
existing conservative speech classifier. The response includes separate,
versioned `LiveAudioSentimentSignal` records with stable IDs, transcript text,
source timestamps, aspect/target, heuristic sentiment or abstention, and
classifier provenance. The UI displays the newest twenty. Attribution defaults
to unknown; the user may explicitly confirm the chunk's speech is the streamer,
with the control locked during capture. Mixed NPC/background voices must stay
unknown because no diarization runs.

This is candidate sentiment telemetry only. It is not added to replay feature
snapshots, does not compute rolling surprise or market estimates, and does not
create paper orders. The live route and UI contract were generated; backend
syntax checks and frontend typecheck are recorded in this change. No live
Twitch audio was captured, and no tests were run for this integration.

## Kalshi game-name matching correction - 15 November 2026

Discovery compares the requested game name to the actual market `yes_sub_title`
contender, not only to the market/event title. The supplied Big Walk link is
event `KXGAMEAWARDS-BIG`, series `KXGAMEAWARDS`, with individual contender
markets such as `KXGAMEAWARDS-BIG-BIG`; Big Walk is shown as a contender on the
venue page. The previous discovery path filtered series using assumed `Culture`
/ `Sports` labels before checking contenders, so a Game Awards series exposed
under a different primary category could be discarded before matching.

Discovery now fetches the series catalog once without a category filter, keeps
series whose metadata names the requested game or Game Awards, then requests
open nested events and exact-matches the Yes contender. Python compilation and
diff whitespace checks passed. No live Kalshi API call was made; the linked page
confirms the site-side series/event/contender, but the API response still needs a
user-run retry to confirm the actual `yes_sub_title` payload and match.

Follow-up for recurring 429s: the series catalog is now shared for 30 minutes,
open nested events for a series are shared for 30 seconds, and all Kalshi GETs
are serialized with a 500 ms minimum interval. A 429 applies one shared
Retry-After cooldown (30 seconds if absent, capped at five minutes) to both
catalog and event requests. Cached market rows retain their original capture
time; quotes older than ten seconds are labeled stale rather than restamped as
current. Backend syntax compilation and diff whitespace checks passed. No live
Kalshi request or tests were run.

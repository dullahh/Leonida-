# Leonida Alpha: decisions and consequential unknowns

Updated 14 November 2026 after planning reviews and the subsequent user-authorized G1 implementation. AGENTS.md remains in force. The user's recorded GTA V input choice supersedes the earlier synthetic-primary scope; G1 implementation stops before G2 delegation.

## Retained decisions

| ID | Decision | Reason/status |
|---|---|---|
| D01 | Root alone integrates main/core/shared dependencies and owns writer/process lifecycle. | Preserve ownership; workers return typed results/plans. |
| D02 | Replay first; optional live adapters after proof. | Deterministic no-key demonstration. |
| D03 | Separate evidence/quote modes and paper state. | Mixed data must not look like a historical backtest/live signal. |
| D04 | Aspect/target claims precede routing. | Skill/character sentiment/laughter/game quality differ. |
| D05 | Bounded correction recomputed from unique current evidence. | Publishing/quote refresh does not add observations. |
| D06 | No sqrt(N), viewer reliability or face-derived pricing. | No unsupported certainty/independence. |
| D07 | Fixed capped paper size; no default Kelly. | Heuristic estimates do not justify precision-driven sizing. |
| D08 | Standalone roles inherit parent model/effort. | Docs match and two roles ran; no retired pin/max_depth. |
| D09 | Application requires no MCP server. | Replaces overbroad “no active MCP” wording: session connectors exist, but browser/media routes were not established. |
| D10 | Root generates schemas/examples/frontend types. | Prevent drift and pin generation environment. |

## Resolved implementation choices

| ID | Decision | Rationale/consequence |
|---|---|---|
| D11 | Python 3.12/FastAPI/Pydantic v2/SQLite, React/TypeScript/Vite; uv/npm. | No app framework exists to preserve. Lock Python/root tooling at G1 and frontend at G2; no global installs. |
| D12 | `python scripts/manage.py` commands plus Make aliases. | make absent on this Windows machine; scripts are future targets. |
| D13 | Runtime schema 2, canonical core schemas, archived reference v1. | Breaking identity/missingness/control changes; re-export from contracts, generate serialization-mode Decimal strings. |
| D14 | `synthetic:<scenario-version>:<alias>` separate from `kalshi:<returned-ticker>`. | Synthetic execution cannot masquerade under a live ticker; actual ticker may reference captured rules only. |
| D15 | Typed reasons/abstention and complete run/control/receipt DTOs. | Present reference permits contradictions and incomplete trace/UI states. |
| D16 | G1 root reference_slice + scripts viewer, real blocked/candidate EV, no fill requirement. | Prompt 01 permits it; preserves narrow scope/ownership. Reviewer's proposed entry/exit moves to G2/G3. |
| D17 | One baseline observation per run/game/stream/aspect/modality/10s bucket/version, even across scenes. | alpha=1-exp(-10/180); pre-update z; 20 valid buckets or explicit fixture seed; missing skips updates. |
| D18 | Claim/group revisions through EvidenceViewDelta; deterministic baseline rebuild. | Replacement interpretations are not extra votes. Committed fills remain immutable. |
| D19 | Source weights exclude relevance; X=r*M*F with separate freshness. | Common relevance/decay inside a normalized mean cancels. Initial heuristic H: sentiment 300s, defects 3600s; build supersession invalidates obsolete evidence. |
| D20 | Existing coefficients/cap .5; max reference spread .05 USD; unsupported inputs abstain. | Missing/stale/closed/endpoints cannot be fixed into valid anchors. No calibrated posterior claim. |
| D21 | Requested size 10, synthetic step 1, latency 250ms, simulation-linear-v1 fee ceil-cent(.01*executed Q). | Risk fractions alone do not define sizing/fees; synthetic fee only, never asserted as Kalshi's schedule. |
| D22 | IOC paper orders, reservations, durable intents and outcome/bid-ask-specific liquidity keys. | Partial fill cancels residual; quote wrapper cannot replenish liquidity; root commits quant plans atomically. |
| D23 | Revalue estimate/EV at eligibility, preserve original limit/reservation ceiling. | Delayed fill cannot use an obsolete favorable estimate/quote. Risk exits use separate gates, not entry EV/cooldown. |
| D24 | Partial marks expose priced/unpriced quantity; nullable total equity/P&L. | Shallow bid cannot value full inventory; proportional cost/fee allocation with final-lot rounding residual. |
| D25 | One writer, staged commit, durable cursor/commands/ledger/liquidity/deadlines; restart paused. | Prevent memory/DB divergence and historical intent resubmission. |
| D26 | Deterministic scheduler phases and explicit ageing/expiry/eligibility/exit deadlines. | Quiet intervals still process time; 1x/5x equivalent. Publication timer is not evidence. |
| D27 | Full shared REST/WS envelope, persisted per-run sequence, reset creates new run ID. | Gap resync/idempotent reset and old-run rejection avoid state contamination. |
| D28 | Original capture immutable/display-only; improve future timing/collision safety. | Script uses collection-start timestamp and second filenames; stored content lacks fees/depth. |
| D29 | Synthetic/synthetic fills only; other combinations candidate-only. | Public quote access is not implicit mixed-experiment selection. Stale entries prohibited. |
| D30 | Labelled synthetic time/risk exit; cut scalp/Kelly/maker modelling. | Still demonstrate entry/partial/exit accounting without convergence guarantee. |
| D31 | No Git initialization/worktree/commit in planning. | Directory has no .git. Shared ownership works; release can archive. |
| D32 | Tester-only regression source, actual isolated browser evidence required. | Root owns launch/export/health orchestration; installed browsers/Selenium alone do not establish automation. |
| D33 | Primary demo input is 2–6 GTA V Twitch screen recordings with embedded chat. | Sample the configured chat region, retain OCR quality/frame receipts and replay cached evidence. No native chat API assumed. |
| D34 | Freeze per-video trim/alignment and cache provenance at G1; use an explicitly supplied fixture until media arrives. | No videos in the repository; actual decoding/OCR remains unavailable and is the primary P2 job. |
| D35 | GTA V proxy evidence has zero automatic relevance to real GTA VI markets. | Synthetic scenario estimate/candidate and actual live venue context are separate contracts/panels. No cross-game validation claim. |
| D36 | G1 ships a narrow schema-2 interface and root-owned HTML state viewer. | Full multi-stream grouping/scheduler/broker/React design remains future work; exact implemented seams are in G1_HANDOFF. |
| D37 | Cache identity includes original fixture bytes and complete manifest/config versions; corrupt cache fails closed. | Offset/ROI/version changes cannot reuse old evidence silently; no provider runs during replay. Real asset hashing/OCR still needs media. |

The wire example's p=.097 uses its own illustrative model. Current config on its features yields p≈.124078 and No net EV≈.005922 with the example fee, below .03. Do not copy .097 into the configured estimator or weaken gates to force a demo fill. G2 needs coherent explicit eligible/blocked quote timelines.

## Deliberate adaptations

| Adaptation | Reason | Preserved requirement |
|---|---|---|
| Freeze runtime v2 instead of reusing v1 | Breaking shape/identity and existing v1 artifact. | Root-owned explicit version/generation. |
| Python runner with Make aliases | Actual make absence. | One setup/demo/check/demo-check interface. |
| Separate freshness and non-cancelling relevance | Review found normalized-weight cancellation. | Bounded unique-evidence correction/sign once. |
| G1 candidate instead of reviewer's entry/exit | Foundation prompt allows candidate; maintain ownership. | Real calculated vertical slice before parallel build; broker required later. |
| Wider G1/G2 ranges | Observed contract gaps/absent frameworks/tool setup. | Gates decide completion, protect integration/verification time. |

## Consequential unknowns

| ID | Unknown | Owner/evidence needed | Default if unresolved |
|---|---|---|---|
| U01 | Exact dependency locks/download availability | Root F1/frontend U2: actual resolve/install/import/typecheck/build. | G1/G2 cannot pass uninstalled stack; record concrete error. Globals are not a lockfile. |
| U02 | Usable browser automation | Root/tester V4: scoped runner/browser install and one actual session. | Browser gate stays open; manual inspection distinguished from automation. |
| U03 | Current venue status/rules/prices/depth/auth | Root optional market task: official docs plus actual timestamped response. | Historical reference and synthetic quotes keep replay usable; live unverified. |
| U04 | Authorized recording/transcription provider | Pipeline optional task: manifest/hash/asset/observed supported outputs/model versions. | Labelled structured replay; supplied text is not decoded A/V. |
| U05 | Chat access and separate raw A/V route | Pipeline optional tasks: observed message IDs/recovery then decoded segments/latency. | No live capability claim; chat auth does not establish media access. |
| U06 | Real venue fee/tick/replenishment semantics | Root/quant future explicitly selected paper experiment: source/version/observations. | Synthetic policies only; live fills disabled. |
| U07 | Calibration/public-information overlap | Future research: as-of corpus, held-out game/year market-only comparison. | Heuristic labels; no validated edge/uncertainty or source-count accuracy assumption. |
| U08 | Full CLI strict validation/home resolution | Root if diagnostics needed: supported diagnostic path. | Actual role returns plus bounded docs/override checks; no full strict-pass claim. |
| U09 | Future Git workflow | Root with actual implementation-time repository state. | Preserve files; no branches promised; archive a verified release if needed. |

G1 resolution: U01 dependencies were locked/installed, U02 Playwright with installed Edge was exercised, and U03 public market refresh plus live quote polling succeeded. U04 recordings remain unsupplied; actual recorded OCR is primary P2 work. U06 real fees/depth and U07 calibration remain unresolved. Stop after G1; see G1_HANDOFF for actual acceptance. A future G2 request must use the updated P2 recording/OCR scope.



## G2 decisions - 15 November 2026

- User authorized G2 with recordings primary and generated test media if none supplied. Workspace scan found no user videos; two generated MP4s/SAPI narrations use synthetic_replay even when real OCR/ASR runs. No actual Twitch/GTA capture validation is claimed.
- Three directly supervised pipeline/quant/frontend agents followed ownership and did not delegate. Root retained contracts, dependencies, runtime/processes and documentation.
- Installed locked imageio-ffmpeg/RapidOCR/PyAV/Pillow/faster-whisper. Bundled FFmpeg and OCR avoid separate PATH setup. Tiny English Whisper is downloaded explicitly once; preprocessing/playback never auto-download. Windows cache locks required a serialized retry; SAPI required the normal-user context during verification.
- ASR initially failed at the faster-whisper/PyAV boundary. Passing already decoded 16-kHz PCM directly to Whisper fixed it; implementation version v2 invalidates failed caches. Narrow lexical spacing normalization never changes original raw OCR words.
- Additive schema-2 revision g2-v1 adds media reports/observations, nullable warmup/abstention, generated provenance and playback controls. Interfaces: G2_CONTRACTS.md.
- Validated caches are the sole playback evidence source. Availability gates projection; speed changes pacing, not extraction/ingestion. Seek rebuilds views, reset creates a new run, restart pauses. Manifest media and cached frame/audio routes are allowlisted; videos support byte ranges and hash checks.
- Media uses a named synthetic flat quote timeline. Six scenarios retain explicit quote events including stale outage. Actual GTA VI context never changes GTA V proxy correction. No new live quote session is claimed for G2.
- Pure paper plans and root atomic persistence are checked. Media remains candidate-only; automatic broker scheduling, fill/exit tape and formal G4 regression source are later gates.
- Acceptance proves generated-media function and observed browser/calculation/persistence behavior. It does not establish real-overlay accuracy, diarization, broad semantic coverage or calibrated forecasting.


## Supplied recordings follow-up - 15 November 2026

The user supplied t1/t2/t3 MP4s and explicitly requested G2 preprocessing/launch without G3. Pipeline updated only its owned paths and the manifest; frontend corrected unassigned scene counting/explicit abstention. Root integrated warnings, generalized the existing inspector for no-estimate state and real snapshot size, checked the running app and retained server PID 78492 for the user.

Crops were fitted by actual frame inspection; both start offsets stay0, scenes stay manual-unassigned, speakers unknown and editable hashes null. Clip source IDs do not claim verified independent streamer identities. Native OCR retains overlapping UI/emoji errors. Every one of 629 observations abstains from game-quality sentiment; the app must not manufacture a model estimate/candidate for this batch.

Direct audio listening is unsupported in this session. Two local ASR model/settings passes on actual source PCM were compared and found disagreement/loops, so no accuracy claim or model promotion was made. The observed out-of-duration ASR risk prompted strict timestamp validation, preserved rejection audits and repetition/compression warnings. Validated raw OCR reuse avoids repeating expensive decoding/OCR after an ASR-only version change, while preserving immutable provenance.

The current live local demo uses the real cache documented in RECORDING_REVIEW.md; the generated demo and G1 fixture remain available. No G3 broker scheduling, real order path or new live quote claim was introduced.

## G3 integration and interrupted-session recovery - 15 November 2026

- Latest user authorization advances through G3 only and preserves all629 abstentions from the verified t1/t2/t3 recordings. Qualifying evidence is confined to separate labelled synthetic scenario runs, never inserted into their cache.
- Retain schema2 compatibility with additive g3-v1 fields for groups, execution orders/fills/positions/marks, trace stages and scenario/cursor state. Generated contracts are checked against backend/core/schemas.py.
- Root composes deterministic cached arrivals,1s ageing/expiry,250ms eligibility and300s exits; publication/read/reconnect are not new evidence or intents. The cached source queue batches128 entries. Decimal ledger, source/model audit and projection commit atomically through one writer.
- Scenario selection/injection creates a new isolated run. Reset retains old audit and uses a new epoch. Synthetic accounting rejects backward seeks to avoid undoing committed fills; recorded candidate-only playback can still seek both ways. Restart resumes paused without resubmitting historical orders.
- Only explicitly authorized supplied synthetic fixtures with synthetic quote books and simulation-linear-v1 fees may fill. Unknown fees/depth, stale quotes and unsupported evidence block normal entries. PaperDecision remains a candidate; distinct execution records show actual simulated lifecycle outcomes.
- Actual market context stays separate and historical/stale by default. No new live quote fetch, actual venue execution-fee/depth implementation, real-money route or GTA VI predictive validation is claimed.
- After restored credits, inspected git status (no.git repository) and existing backend/frontend before writes. No application truncation was found; valid files and source data were retained. Finished missing G3 acceptance/command wiring and only two identified frontend gaps: malformed execution-array rejection and explicit synthetic freshness display.
- Tester created only the missing focused G3 acceptance module; nine tests passed with no skips. This does not start or satisfy the broader G4 formal suite/reviewer gate. Existing workers were directly supervised without delegation; at most two fix workers ran together.
- Root replaced its verified old G2 process78492 with G3 process67112 on8000 after an occupied-port launch failure. Original database/cache remain unchanged. Browser helpers initially required corrected selectors/request base URL; final real-recording and synthetic lifecycle checks passed, including manual exit, stale cancellation, reconnect/REST fallback and old-frame rejection.
- Current app is recordings paused0; G3_HANDOFF/STATE record exact run/database/process and commands. Stop afterG3.

## Reaction telemetry - 15 November 2026

The user authorized one-thread implementation and focused tests across the necessary contracts/core/UI/test paths, superseding delegation for this task. No workers or G4 were started. Added ReactionSignal as contextual cached-text telemetry, never a substitute for supported claims. Existing classifier, extracted observations, speaker review and media remain unchanged. Explicit attribution .90 / confidence .60 / market relevance .80 gates apply to supported estimate inputs, with no intensity coefficient. Text-only emotion/intensity are heuristic; OCR/ASR warnings remain missing/abstained. Max-per-bin timelines and unique observation IDs prevent delivery/volume amplification. Unsupported aggregate inputs conservatively suppress the estimate while retaining diagnostic features. Derived immutable views are bounded/memoized; no providers run in playback. All15 G3 tests and existing isolated operational checks passed; browser verified recorded context, fixture support and narrow layout. Current PID93168 uses var/recordings-reactions.sqlite3, recordings paused0. Details: REACTION_TELEMETRY.md. Stop after this integration.

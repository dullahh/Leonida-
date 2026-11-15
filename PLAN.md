# Leonida Alpha: build and agent orchestration plan
Version 1.0 · Prepared 14 November 2026 · Durhack · Two-person team

This is a handoff specification and starter contract/configuration pack. It is not an implemented trading application. The target is a multi-stream evidence desk with market-relative scenario estimates and auditable paper decisions.

Read README.md first. Give docs/prompts/00-master.md to your root Codex session. Keep AGENTS.md short; workers read only their assigned sections of this document. All time allocations below are planning ranges, not delivery promises.

## 1. Outcome, scope and explicit cut line

A reviewer should be able to select a game market, see which streamer observations relate to it, inspect the original words and scene, understand normalisation/weighting, compare a model estimate against executable quotes, and inspect a paper decision and fill.

The primary accomplishment is an inspectable evidence-to-decision chain. Historical forecasting superiority is a later research milestone.

MVP must work without keys or internet:
- Six structured replay streams, including missing sources and disagreement.
- Aspect-specific speech/chat claims with source receipts.
- Manual scene identifiers and explicit candidate match confidence.
- Absolute sentiment and per-stream surprise as separate features.
- A current-market anchor plus a bounded, labelled heuristic correction.
- Real captured Kalshi metadata as a historical reference, with synthetic replay quotes in a separate namespace.
- A paper broker with stale-quote rejection, depth/size constraints and accounting.
- A dashboard with full mode provenance and reconnect/reset behaviour.

First useful live increment: fetch current public market definitions and quotes. Next: process one authorised recording through actual transcription/semantic extraction. Next: live chat. Only then attempt live A/V, automatic scene alignment and more streams.

Out of the critical path:
- Live-money ordering, execution credentials and deployed trading automation.
- Reliable inference of emotion, intent or game approval from a webcam alone.
- Claims that the illustrative coefficients are calibrated Bayesian evidence.
- An arbitrage guarantee.
- Historical backtesting across a large game universe.
- Universal automatic mission recognition.
- A distributed microservice deployment.

Call the product “Multi-stream game evidence and prediction-market research desk.” Use “paper strategy” and “model estimate”; reserve “validated edge” for held-out results.

## 2. Corrections to the supplied blueprint

| Original choice | Replace with | Reason |
|---|---|---|
| Root and pipeline both wire main.py | Root exclusively owns runtime integration | Prevents the highest-risk merge collision |
| Multi-agent flags and depth copied blindly | Version-preflight; current standalone role files; no worker delegation | Codex configuration has changed |
| All modalities required/default zero | Nullable values with availability and quality | Missing is different from neutral |
| MediaPipe valence | Optional observable face movement, zero direct pricing weight | Landmarks/blendshapes are not validated game approval |
| Face/chat boosted automatically in cutscenes | Attribution-led evidence with visible missingness | Silence and expressions are ambiguous |
| Viewer-count reliability weights | Equal capped streamer contributions initially | Popularity does not establish predictive reliability |
| Multiply average Z by sqrt(N) | Bounded mean plus separate coverage diagnostics | Streams, chats and modalities are correlated |
| Negative bug route times negative sentiment | Nonnegative relevance; encode direction once | Prevents sign reversal |
| Discard all player-skill segments | Route individual claims by target, allow ambiguity | Control/design criticism can coexist with skill failure |
| pHash distance 8 proves a scene | Candidate retrieval plus context/sequence verification | No universal distance threshold establishes scene identity |
| Require two streams per event | Singletons allowed with lower corroboration | New incidents can appear first in one stream |
| Mean reversion prevents double counting | Stable IDs, unique evidence ledger, idempotent processing | Damping is not deduplication |
| More hours always increases beta | Bounded coverage-based experience; default multiplier 1 | Clock time is not necessarily informed evaluation |
| Realistic fabricated snapshot spreads | Immutable actual capture or labelled synthetic quotes | Preserve provenance |
| Invisible live→cache switch | Stale badge, original timestamp, execution pause | Cached prices are not current liquidity |
| Arbitrary 1.5-cent fee for all orders | Versioned quantity-aware fee adapter | Rounding and market-specific fees affect EV |
| Kelly on an arbitrary probability | Capped fixed paper sizing by default | Sizing should not amplify unvalidated precision |
| A touch guarantees a fill | Available quantity/depth and partial fills | Price and fillability differ |
| 70% convergence guarantees a scalp | Explicit optional exit heuristic at executable bid | Settlement value does not forecast short-horizon convergence |

## 3. Team topology, ownership and coordination

Use one root integrator and at most three implementation workers at once. Tester and reviewer are specialist roles used after the first interfaces work. Roles are not all concurrent processes.

Root coordinates. Workers do not spawn workers. Enforce flat delegation in instructions. Current documented configuration does not expose max_depth as a portable global setting; use it only if the installed version explicitly documents support.

| Owner | Writable paths/resources | Responsibilities |
|---|---|---|
| Root/integrator | AGENTS.md; .codex/; docs/; contracts/; backend/core/; backend/main.py; root manifests/lockfiles; scripts/; config/; data/snapshots/; generated frontend types | Scope, contract freeze, DB/migrations, dependency approvals, composition, lifecycle, final checks |
| Pipeline | backend/ingestion/; backend/perception/; data/scenarios/; data/recordings/ manifests; handoffs/pipeline.md | Replay, chat/media adapters, semantic extraction, scene matching |
| Quant | backend/quant/; backend/execution/; handoffs/quant.md | Feature computation, correction model, market constraints, paper risk/broker |
| Frontend | frontend/ except generated files; handoffs/frontend.md | UI, frontend package/lockfile, mock state viewer, browser-facing integration |
| Tester | tests/; handoffs/tester.md | Small invariant suite, contract examples and integration tests |
| Reviewer | No application edits; handoffs/reviewer.md only when assigned | Code review and isolated browser verification |

Root owns Python dependencies. Frontend owns frontend dependencies. Tester requests additions; it does not edit manifests. Root alone regenerates JSON Schema/OpenAPI/TypeScript contracts. Pipeline owns replay content; tester reads it and may add test-only fixtures under tests/fixtures/.

One runtime SQLite writer, one app process owner, one test-run database per test. Runtime DB files never live in version control. QA uses a separate run ID; it never injects into another active run.

In a shared worktree:
- No worker git commit, git add -A, reset, clean, checkout, rebase or branch switching.
- Inspect your owned paths; other workers' changes may be visible.
- No worker starts/stops shared servers or globally installs dependencies.
- Return a precise handoff. Root inspects combined diffs and owns commits.
- Ownership instructions reduce collisions; they are not filesystem security boundaries.

Alternative when ownership must overlap: root creates separate Git worktrees after a foundation commit; each worker uses a named branch. Root integrates one reviewed commit at a time. This is a separate workflow; do not mix worktree assumptions with shared-file assumptions. For this hackathon, prefer disjoint paths in one checkout.

Job packet required before every delegation:
1. Task ID and user-visible purpose.
2. Exact writable and forbidden paths.
3. Input/output models and function signatures.
4. Dependencies and examples already available.
5. Behaviour requirements and non-goals.
6. Acceptance command and meaningful result.
7. Dependency/contract change request procedure.
8. Handoff format and checkpoint.

Handoff format:
- Changed files.
- Public interfaces.
- Verification commands, exit codes and concise results.
- Assumptions and limitations.
- Blockers / dependency requests.
- Required integration actions.
- No raw transcript dumps unless necessary to reproduce a failure.

Root keeps docs/STATE.md and docs/DECISIONS.md current. Each task should be independently resumable using its job packet and handoff.

## 4. Repository design

Choose FastAPI + Python, SQLite, and React/TypeScript + Vite for a compact client dashboard. If your existing project already uses Next.js, keep it rather than migrating. Use one frontend framework and one package manager.

| Path | Contents |
|---|---|
| contracts/models.py | Reference Python contracts, adopted into backend/core/schemas.py at G1 |
| contracts/generated/ | Generated JSON Schema and examples |
| backend/core/ | Schemas, config, clocks, market adapter, storage, runtime state |
| backend/ingestion/ | Replay, transcript, chat and A/V source adapters |
| backend/perception/ | Aspect extraction, scene candidates, attribution |
| backend/quant/ | Normalisation, unique feature view, routing, estimates |
| backend/execution/ | Decisions, paper orders/fills, positions, risk |
| backend/main.py | FastAPI lifespan and composition only |
| frontend/src/generated/ | Root-generated contract types; no manual edits |
| frontend/src/ | Terminal UI and state transport |
| data/snapshots/ | Immutable market captures with fetched_at and original responses |
| data/scenarios/ | Explicit synthetic event/quote timelines, seeds, manifests |
| data/recordings/ | Optional local media references/manifest; do not bundle unlicensed media |
| var/ | Ignored runtime SQLite, logs and derived caches |
| tests/ | Deterministic contract, maths, broker and integration checks |
| scripts/ | Startup, health, snapshot refresh, schema generation, demo verification |
| handoffs/ | One worker-owned report per role |
| docs/ | Plan, decisions, state, runbook and evaluation notes |

Do not introduce Kafka, Redis, a vector database or Kubernetes for this MVP. An async bounded queue, SQLite and in-process derived state are sufficient.

## 5. Modes, clocks, provenance and event identity

Keep three independent dimensions:
- evidence_mode: live, recorded, synthetic_replay.
- quote_mode: live, cached_stale, synthetic_replay.
- execution_mode: paper.

A valid screen can read “Recorded evidence · Live quotes · Paper · Heuristic model.” Mixed mode is legitimate, but it is not a historical backtest. Synthetic evidence against current quotes must not masquerade as a real market signal; default to candidate decisions, with fully synthetic quotes for simulated fills.

Each event records:
- schema_version, run_id, event/claim/quote ID.
- game ID, stream ID where relevant.
- source event interval and source asset/offset.
- available_at/received_at, distinct from event time.
- producer/model/prompt version, source mode, quality/missingness.
- links to parent IDs and dedup/scene relationships.

Use UTC-aware ISO datetimes on the wire. Preserve replay source offsets. A Clock interface supplies now() and advancement. Tests and replays use a simulation clock; wall-clock sleep does not determine features, decay, cooldowns or broker state.

Stable IDs:
- Source windows: hash of source ID + interval + source revision.
- Claims: hash of source-window ID + extractor version + claim ordinal/content.
- Scene groups: stable IDs with revision numbers; grouping corrections do not silently duplicate observations.
- Commands: client-provided idempotency key scoped to run.
- Paper intents: hash of run + market + side + decision revision.
- Persist dedup keys; a reconnect/restart must not rerun a previously executed intent.

New extraction versions are alternative interpretations, not additional independent observations. Replace the active interpretation through explicit revisions.

## 6. Contract design and freeze protocol

Raw evidence, derived features, quotes, estimates and fills must remain separate models. The included contracts/models.py is a starting reference, not permission for workers to change contracts independently.

Essential models:
1. SourceWindow: source interval, transcript/chat references, language, modality availability, scene candidate.
2. EvidenceClaim: target/aspect, signed sentiment or defect severity, supporting quote, explicitness, attribution, confidence, abstention reason.
3. EvidenceGroup: scene identity/match confidence, claim IDs, source IDs, platform/build, dependency groups.
4. MarketDefinition: actual contract/event ticker, resolution text, deadline, event constraint metadata.
5. MarketQuote: timestamps, status, both side quotes and sizes, provenance and staleness.
6. FeatureSnapshot: absolute sentiment, surprise, counts, coverage, disagreement, effective-source diagnostic.
7. ModelEstimate: market-reference probability, correction, estimate, model/calibration status, inputs, uncertainty status.
8. PaperDecision: side candidate, quantity, all-in EV, blocked/eligible reason.
9. PaperOrder / PaperFill / Position: distinct order lifecycle and accounting.
10. Receipt: input IDs and human-readable explanation.
11. DashboardSnapshot: full consistent UI state.
12. StreamEnvelope: run, schema, sequence, snapshot type and generated_at.

Money: Decimal in Python, decimal strings in JSON, unit explicitly USD per contract. Probabilities/sentiment may be floats; account balances and fees must not be unqualified floats. Do not assume integer cents if the venue supports fractional price increments.

Nullable quote/size is allowed. Missing bid/ask is unavailable, never a zero-price bargain. Validate bounds, bid≤ask where both available, finite numbers, and aware timestamps.

Freeze process:
- G1 root proves a tiny observation→feature→estimate→decision→state path.
- Publish JSON examples and JSON Schema; generate frontend types once.
- Record contracts v1, signatures and known limitations.
- A change request names the field/signature, reason, producers/consumers and migration.
- Root resolves routine design choices, changes version if needed, regenerates types, informs owners.
- Workers wait only on the changed dependency, continuing independent tasks.
- No ad hoc frontend renaming or arbitrary dicts as integration glue.

Minimum service signatures (root finalises exact imports at G1):
- Source.next_window() -> SourceWindow | None.
- Extractor.extract(window) -> list[EvidenceClaim].
- Grouper.upsert(claims) -> list[EvidenceGroup].
- FeatureEngine.ingest(claim) -> bool indicating new evidence.
- FeatureEngine.snapshot(game_id, as_of) -> list[FeatureSnapshot].
- Router.relevance(claim_or_aspect, market_definition) -> relevance plus rationale.
- Estimator.estimate(definition, quote, features, as_of) -> ModelEstimate | abstention.
- Risk.evaluate(estimate, quote, portfolio, quantity) -> PaperDecision.
- PaperBroker.submit(decision, quote/depth) -> orders/fills.
- StateProjector.snapshot(run_id) -> DashboardSnapshot.

## 7. Market adapter and actual contract registry

Use Kalshi's current documented production Trade API base:
https://external-api.kalshi.com/trade-api/v2

The older api.elections.kalshi.com host remains supported, but do not hard-code endpoints from stale examples when the current docs differ.

Known seed event tickers observed in this conversation:
- KXMC-GTA6.
- KXGAMEAWARDS-2026.
- KXGAMEAWARDS-BNAR.
- KXGAMEAWARDSBGD-2026.
- KXGTAONLINE-GTA6ONLINE.

Actual example contract tickers:
- KXMC-GTA6-95 / -96 / -97.
- KXGAMEAWARDS-2026-GTA.
- KXGAMEAWARDS-BNAR-GRA.
- KXGAMEAWARDSBGD-2026-GTA6.
- KXGTAONLINE-GTA6ONLINE-27 / -27B / -28.

The supplied blueprint's KXGAMEAWARDS-2026-BNAR, KXGAMEAWARDS-2026-GOTY and -27JUL strings must not be treated as verified contract IDs. Resolve definitions from returned data. Registry aliases such as gta_best_narrative point to resolved tickers; pricing never targets invented names.

Market discovery:
1. Request known events through GET /markets with event_ticker and status=open.
2. Follow cursors when present. Capture original JSON and fetched_at.
3. Read contract rules, event year, strike and platform/default-score conditions.
4. Match relevance using game identity and explicit rules; an event title alone is insufficient.
5. Record unsupported/missing markets rather than substituting another contract.
6. UI links to the market page and shows settlement criteria.

Network behaviour:
- One shared HTTP client, bounded concurrency and timeouts.
- Poll a small whitelist initially, e.g. every 3 seconds; this is a local design default, not a venue requirement.
- Exponential backoff with jitter on transient failure; respect venue limits.
- Do not overwrite an actual snapshot with synthetic or malformed data.
- Failed request retains last successful quote with its original capture time.
- Quote source/age is surfaced; default no new fills against stale quotes.
- Verify exact current auth requirements separately for quote/depth and WebSocket endpoints.
- A “live capture” has capture time, not necessarily a venue-generated timestamp. Preserve whether source timestamp is unavailable.

Threshold markets must be monotone. One score distribution feeding all thresholds is a future coherent model; until implemented, label independent estimates and suppress incoherent results. Winner markets need jointly consistent probabilities across nominees and any Other/Tie rules. The MVP may focus on GTA versus not-GTA without presenting independently adjusted probabilities for every nominee as a full coherent distribution.

## 8. Stream ingestion and semantic extraction

Implement transport adapters separately:
- StructuredReplaySource: deterministic structured windows/claims, no external services.
- RecordedMediaSource: supplied/authorised clips + chat transcript + timestamps.
- TwitchChatSource: preferred supported EventSub integration, or documented IRC path if already working.
- LiveAVSource: explicit tested A/V route; chat authentication does not supply media frames/audio.

Preflight must prove one real A/V source before planning many. Do not make “pull 1–2 FPS from Twitch” an assumed capability. Multiple recordings or another available game are acceptable demonstrations; do not label unreleased GTA footage as observed gameplay.

Audio:
- Short buffered windows, speech activity detection, timestamped transcription.
- Keep streamer commentary distinct from NPC/dialogue where possible.
- Non-English/low-confidence windows can abstain.
- Degrade to labelled supplied transcript when transcription unavailable.
- Cache transcription/extraction by source hash + provider/model/prompt version.
- Provider timeouts/cost budget must not block the entire runtime.

Chat:
- Preserve message IDs and timestamps; cap per-user and repeated-phrase contribution.
- Align chat reaction windows using an explicit estimated delay; show uncertain alignment.
- Measure emote rates relative to that channel's baseline.
- Laughter is not inherently positive game quality; context determines the aspect.
- Deleted/unavailable messages do not get reconstructed by the model.

Webcam:
- Optional landmark/blendshape or movement signals with availability/quality.
- No default positive/negative game sentiment derived from a smile/frown.
- A supporting visual cue can accompany explicit speech, but is not an independent vote.
- Missing facecam stays null. Never increase its pricing weight merely because a cutscene is playing.

Extractor:
- Use a constrained structured-output schema and evidence quotations.
- Supply transcript, nearby context, scene label and time-aligned chat summary.
- Extract multiple claims rather than one global sentiment.
- Aspects: narrative, gameplay, presentation, technical_quality, online_experience, overall, irrelevant_unclear; optional subaspects.
- Targets: game, scene/mission, streamer_skill, NPC/story_character, chat/streamer, unrelated, ambiguous.
- Sentiment: signed [-1,1] only when attributable; intensity and confidence separate.
- Bugs: positive severity as a separate factual feature, not negative sentiment times negative routing.
- Require support in the source window. Reject unsupported quotes or outside-window timestamps.
- Ambiguous sarcasm/target -> abstain or low-confidence review; do not fabricate certainty.

Examples:
- “The villain is horrible, brilliant writing” -> positive writing; negative attitude to character is not game dislike.
- “This glitch is hilarious” -> amusement plus negative technical observation.
- “I am terrible at aiming” -> streamer_skill, no quality claim.
- “I missed again because the aiming controls lag” -> skill context plus a separate control-performance claim.
- A donation alert or streamer joke -> unrelated unless the game is explicitly evaluated.

Semantic relevance r is nonnegative [0,1]. Relevance decides which market can use evidence. Signed features or learned coefficients decide direction once. Mere semantic similarity does not establish causal influence.

## 9. Scene matching and correlation

MVP scene label comes from fixture/manual entry. A scene may be encountered at different wall-clock times by different players. Group by canonical scene plus approximate scene-relative phase, game/build/platform context—not simply simultaneous stream time.

Automatic stretch:
1. Configurable gameplay ROI and overlay masks per stream.
2. pHash/embedding retrieval of candidate similar frame sequences.
3. OCR mission/objective/subtitle sequence and temporal consistency.
4. Verification score and abstention.
5. Independent scene test set to tune thresholds.

A fixed Hamming threshold is not a universal truth. Centre cropping can remove useful context and retain overlays. Never route confident claims solely from visual similarity.

Dependencies:
- One streamer rebroadcasting another is a shared underlying source.
- Several chat messages are not independent game evaluations.
- Voice/chat/face for one moment share an observation bundle.
- Streamers reacting to the same viral clip do not constitute separate bug incidents.

Allow singleton groups. More corroboration affects reliability/uncertainty, not an automatic sqrt(N) multiplier. Keep dependency_group_id and count unique sources/scenes separately.

## 10. Normalisation, aggregation, coverage and ageing

Keep normaliser state per streamer × aspect × modality × baseline version. Do not let a burst of chat messages change a voice baseline.

For a new, unique, attributable observation x:
- Compute z from the pre-observation mean/variance.
- If the baseline is unready, z=null with warmup status.
- Use a nonzero standard-deviation floor and clip surprise for display/model robustness.
- Then update the baseline exactly once.

Equations:
δ = x - μ_previous
z = clip(δ / max(sqrt(v_previous), s_min), -z_max, z_max)
μ_new = μ_previous + α δ
v_new = (1-α) × (v_previous + α δ²)

For irregular arrivals use α=1-exp(-Δt/T) after aggregation to stable observation windows. A fixed α on regular windows is acceptable for MVP and must be explicit.

Suggested replay defaults, all illustrative:
- 10-second source buckets.
- Warmup: 20 valid buckets per aspect/modality or an explicitly labelled seeded fixture baseline.
- z_max=4; s_min=0.10 for a [-1,1] score.
- No update for missing/abstained measurements.
- Preserve absolute sentiment separately. A positive z can still be negative opinion.

Aggregate to one streamer contribution per scene/aspect/time bucket. Across streams use a bounded weighted mean:
S = Σ(w_i s_i) / Σw_i
Z = Σ(w_i z_i) / Σw_i, over ready values only.

A stream's many comments do not create arbitrary weight. Start with equal capped streamer weights; quality/attribution can reduce them. Do not use viewer count as presumed accuracy.

Weights can incorporate relevance, extraction quality, dependency discount, coverage and evidence-type-specific decay. Avoid applying the same confidence twice under different names.

Recency:
d(age)=2^(-age/H)
H belongs to the evidence class. Momentary hype may decay quickly; a reproducible crash persists until superseded by build/platform information. Event/availability times come from the run clock.

Maturity:
Use relevant progress/mission coverage and explicit overall appraisal, not stream duration alone. Default maturity_multiplier=1 until a relationship is validated. Optional bounded scenario multiplier must be labelled heuristic.

Diagnostic effective count:
N_eff=(Σw)²/Σ(w²)
This is a weight-concentration diagnostic, not proof of independence or an automatic confidence interval.

FeatureSnapshot also includes number of unique streams, scenes, dependency groups, missingness, standard deviation/disagreement, source age, coverage, and absolute vs relative values.

## 11. Market-relative estimate, calibration and repeated evidence

Recommended MVP:
p_market = midpoint of a current valid Yes bid/ask.
L_market = logit(clamp_for_numerics(p_market)).
A = clip(b + Σ β_j X_j, -A_max, A_max).
p_model = sigmoid(L_market + A).

When there is no valid tight reference quote, abstain or show explicitly degraded reference quality. Price endpoints/closed status are not “fixed” by clipping. Logit epsilon exists only for computation, not a forced 0.5%–99.5% economic belief limit.

A is recomputed from the unique current feature view. The publishing loop must never re-add the same feature window to a prior posterior. A timer refresh is not new evidence.

Example: a quote moves while evidence is unchanged. L_market changes; A remains unchanged. This is a market-relative estimate, not another independent observation.

Current-market anchoring creates an overlap issue: the market may already reflect the public stream. Fit any eventual correction model conditional on market price and available information. Mean reversion cannot solve this statistical problem. Exact Bayesian log-odds updating needs conditional log likelihood ratios; β×Z is not one automatically.

MVP coefficient file contains:
- model_version, calibration_status=heuristic.
- per-market feature coefficients.
- bounded correction cap.
- relevant evidence modes.
- numeric settings and rationale.
- no empirically calibrated uncertainty interval unless supported.

If illustrative coefficients are used, UI says “Scenario estimate—uncalibrated.” A sensitivity range across coefficient choices is a sensitivity range, not a confidence interval.

Calibration research:
- Historical games and fixed forecast cutoff relative to release.
- As-of transcripts/quotes/features only; available_at prevents lookahead.
- Separate training, validation and held-out games; awards split by year.
- Compare market-only vs market-plus-features using Brier/log loss and reliability plots.
- Report sample size and bootstrap uncertainty at game/year level, not chat-message level.
- Evaluate transaction costs and executable quotes separately from forecasting quality.
- Distinguish independent forecasting skill from a temporary public-information latency advantage.

Default weak routes:
- Single-player quality/bugs → online release date: no automatic signal.
- Soundtrack praise → which artist appears on album: no automatic signal.
- Popularity/streamer enthusiasm → jury award: indirect proxy.
- Definitive announcement/release access → date market: direct factual evidence if within rules.

## 12. Paper decisions, broker, sizing and exits

The plan authorises a research application and paper simulation, not live-money ordering. The MVP contains no venue order-submission implementation or execution credentials.

For a $1 binary payout, quantity Q:
EV_yes_per_contract = p_model - executable_yes_ask - Fee_yes(Q)/Q.
EV_no_per_contract = (1-p_model) - executable_no_ask - Fee_no(Q)/Q.

Use the average executable price for Q when crossing multiple levels. Do not add spread again if using actual asks. Unknown costs/depth -> candidate or blocked, not a guaranteed fill.

Example:
p_yes=.097, yes bid=.14, yes ask=.15, no bid=.85, no ask=.86.
Buy Yes: -.053 before fees.
Buy No: .903-.86=.043 before fees.
Bearish candidate is BUY_NO, not BUY_YES or an assumed sale at the Yes ask.

Fee adapter:
- Inputs: contract, order type/quantity/price, fee schedule version.
- Outputs: total fee and source/assumption.
- Actual venue fees when implemented; otherwise explicit simulation fee schedule.
- Fees rounded at the order level according to that schedule; Decimal accounting.
- A fixed illustrative fee may exist only in a synthetic scenario configuration.

Risk default is fixed capped paper quantity, not Kelly:
- Simulated bankroll USD 10,000.
- Illustrative max cost per order: 0.5% bankroll.
- Max game-group gross cost: 3%; total gross cost: 5%.
- Cap by cash and displayed executable depth.
- One net position per contract; reject conflicting duplicate entries.
- Cooldown/hysteresis and risk reservations for pending orders.
- Quote-age threshold and active-status gate; no new normal fills from cached_stale.
- Carry no claim that these limits are optimal.
- Record why a decision was blocked, including calibration/mode limitations.

Fully synthetic replay may generate simulated fills from its own synthetic quotes/sizes. Recorded or synthetic evidence against live quotes defaults to candidate-only unless the user explicitly selects a visibly labelled mixed paper experiment.

Paper broker:
- Separate decision, intent/order, fill and position.
- Marketable simulated orders consume available quantity/depth once.
- Partial fills allowed; unavailable depth leaves a candidate/no-fill.
- No maker fills merely because price touched the limit; omit maker simulation without a queue model.
- Orders use the latest quote available after decision/processing latency, never a more favourable earlier quote.
- Unique intent IDs prevent duplicates on replay, retry and reconnect.
- Cash, quantity, fees and realised P&L form one transactional ledger.

MTM:
Use executable bid depth for the held side, consuming levels for the held quantity. If only the top bid quantity is known, mark at most that quantity and report the residual as unpriced; never value an entire oversized position at the best bid. Absent bid -> unavailable liquidation mark.
Unrealised P&L includes entry fee and estimated exit fee.
Realised P&L exists only after a simulated exit fill/settlement.

Optional 70%-of-gap exit:
executable_exit_vwap >= entry_fill_vwap + 0.70 × (entry_fair_side - entry_fill_vwap).
Use actual entry fill VWAP, entry-side fair value and an executable exit VWAP for the quantity; never substitute the original best ask for a swept entry. It is an illustrative strategy rule, not a consequence of EV. Require net cash P&L after both fees, or label an exit as a risk exit rather than profit taking. Include time/risk exits and current remaining EV.

Kelly stretch:
Ignoring fees, bankroll fraction spent for a Yes bet with probability p and cost c:
f* = max(0, (p-c)/(1-c)).
Fractional Kelly multiplies this by a chosen fraction, still capped by risk/depth. Do not enable it by default for a heuristic probability. For No use 1-p and No cost.

Terminology: this is a sentiment-driven directional event-contract strategy. “Delta” can label a displayed price discrepancy, but does not make the system delta hedging or arbitrage.

## 13. Runtime, storage and HTTP/WebSocket design

One FastAPI lifespan creates clients, adapters, queues, clock, feature engine, paper broker and DB writer. Do not instantiate multiple engines in route handlers.

Flow:
SourceWindow → claims → dedup/revisions → scene groups → feature view → market routing → estimate → risk decision → paper broker → transactional storage → dashboard projection.

Separate quote events from evidence events. A quote update can refresh estimate/EV/MTM without modifying evidence baselines.

Storage tables:
- runs; commands; market_definitions; quotes.
- source_windows; claims; groups; group_members; feature_snapshots.
- estimates; decisions; orders; fills; positions; ledger.
- receipt_links; processing_errors; runtime_metrics.
Use run_id and stable unique keys. Persist original payload/versions where needed. Root owns migration SQL and one writer. SQLite WAL and busy timeout are implementation choices to validate; no MCP connection writes the runtime database.

Backpressure:
- Bounded source queues, per-source status and retry.
- Coalesce dashboard snapshots for slow browsers.
- Never silently drop ledger/accounting events.
- If observation capacity is exceeded, log a gap and abstain/mark coverage degraded.
- Provider failures are isolated, not a global blocking await.
- Stop/reset cancels the correct run's tasks, not all processes.

API:
| Method/path | Behaviour |
|---|---|
| GET /health | Process alive |
| GET /ready | Configuration and current runtime readiness |
| GET /api/state?run_id=… | StreamEnvelope containing the complete DashboardSnapshot |
| GET /api/markets | Definitions, quote modes, age and available prices |
| POST /api/runs | Create an isolated replay/recorded/live-observation run |
| POST /api/runs/{id}/control | Start/pause/reset/speed; command_id required |
| POST /api/runs/{id}/inject | Replay-only scenario injection; command_id required |
| GET /api/runs/{id}/receipts/{receipt_id} | Exact evidence/model/order trace |
| WS /ws?run_id=… | Full snapshots at a bounded rate |

For MVP send complete snapshots at ≤4Hz, not arbitrary partial patches. Envelope: schema_version, run_id, sequence, generated_at, type=snapshot, payload.
- Reconnect immediately sends a full snapshot.
- REST fallback returns the same StreamEnvelope as WebSocket, with a shared sequence and one client decoder.
- Client ignores older/duplicate sequence values within a run.
- Reset has a new run ID or explicit epoch; old frames cannot contaminate new state.
- A gap triggers state resync.
- Show connection status and last update time.
- Configure local CORS/dev proxy; do not hard-code production hosts in components.

Metrics: input lag, extraction latency, event-to-UI latency, queue length, provider errors, dedup count, quote age, active sources, blocked decision reasons, realised/unrealised P&L separately.

## 14. UI design brief and receipts

Use an information-dense dark terminal, crisp typography, tabular numbers, restrained accent colours and explicit units. Design for a laptop projector first, with a usable narrow layout.

Top bar:
Game/run selector; evidence/quote/execution mode badges; calibration label; connection/freshness; play/pause/reset/speed.

Main panels:
- Stream grid: transcript excerpt, aspect, absolute sentiment vs surprise, missing modality indicators, scene grouping, source lag.
- Market table: rules link, actual ticker, Yes/No bids/asks, quote age, reference probability, correction, model estimate, candidate side EV and blocked reason.
- Selected market chart: market reference and model estimate, evidence markers, explicit scenario labels.
- Evidence ledger: quotations, scene/target/aspect, disagreement, relevance and source links.
- Paper tape: intent/fill/exit, quantity, fees, executable price, realised/unrealised P&L.
- Coverage view: independent sources/scenes and uncertainty/limitations.

Click a forecast marker or decision to open a receipt:
1. What happened and exact supporting quotes.
2. Which independent streams/scenes support or disagree.
3. Absolute sentiment and normalised deviations.
4. Which market rules make it relevant.
5. Model version, coefficients and correction.
6. Market quote/time and all-in EV.
7. Fill status/size/cost or why no fill.
8. Mode and calibration status.

Empty states are real product states: no relevant evidence, warming up, unsupported market, missing facecam, stale quote, no depth, uncertain attribution. Do not render them as zero or a confident trade.

Scenario controls are clearly demo controls in replay mode. Browser QA may mutate its own replay state while remaining forbidden from editing application files.

## 15. Six required replay scenarios

| Scenario | Required observations | Required invariant |
|---|---|---|
| Courtroom praise | Independent writing/acting praise; different arrival times | Narrative relevance, inspectable claims, bounded correction |
| Technical failure and laughter | One severe bug; chat laughs; another source repeats clip | Technical quality remains negative; no duplicate incident; Online route stays off |
| Skill rage and control critique | One skill-only claim plus explicit control criticism | Skill claim excluded; valid gameplay claim preserved |
| Mixed views/missing facecam | Positive speech, critical chat, absent webcam | Disagreement visible; no fabricated modality |
| Duplicate/reconnect storm | Same IDs, rebroadcast content, socket reconnect | Baseline/correction/order count unchanged by duplicates |
| Venue outage/reset | Quotes stop; cached display; pause/reset/new run | Staleness visible, executions pause, state resets cleanly |

Each fixture has seed, initial states, event-time offsets, available_at offsets, scenario version, source/quote modes and expected qualitative invariants. Fixtures do not promise profits or hard-code a flattering P&L.

Include a separate pure quote-repricing timeline for optional scalp demonstration. It must say synthetic market movement. Never fabricate a live market response to an injected scenario.

A 1x run and a 5x run must have equivalent event-time features, decisions and accounting after normalising run/epoch IDs and derived run-scoped IDs. Stable source-window/content IDs remain equal. Wall-clock display metadata may differ; isolated runs must not be forced to share intent IDs.

## 16. Sprint plan with gates and realistic sequencing

Assume several hours for a credible replay product. The original approximately one-hour all-live schedule is not a dependable commitment. Keep the last 20–25% for integration, defects and rehearsal.

| Gate | Work | Indicative allocation | Exit evidence |
|---|---|---|---|
| G0 preflight | Versions, config, source capability, scope and manifests | 20–40 min | Actual tools/keys/routes recorded; no unresolved assumed A/V access |
| G1 foundation | Contracts plus one end-to-end replay slice | 40–70 min | One observation reaches UI with trace and paper decision |
| G2 parallel | Pipeline, quant, frontend bounded jobs | 60–120 min | Three owned handoffs pass prescribed checks |
| G3 integration | Six streams/scenarios and paper lifecycle | 40–75 min | Consistent snapshots, receipts, restart/reconnect |
| G4 verification | Invariants and isolated browser QA | 30–60 min | Required checks pass; material limitations explicit |
| G5 demo release | One-command replay startup and rehearsal | 20–40 min | No-key demo repeats on presentation machine |

Use outputs/gates to decide progress, not the elapsed estimate. If less time remains, remove features in this order:
1. Facial processing.
2. Automatic scene matching.
3. Multiple live A/V streams.
4. Optional scalp exits/Kelly.
5. Live chat.
6. Complex charts.
Preserve provenance, dedup, correct EV, paper accounting and the no-key replay.

Two-person human split:
- Abdullah: quant design, market rules, root integration decisions.
- Partner: source clips/transcripts, frontend review, scenario narrative and demo.
Do not let both independently run competing root sessions against the same checkout. One root coordinates workers; the other person reviews visible artefacts and queues focused tasks.

## 17. Verification plan

Tester owns test source creation. Implementers run existing checks, local import checks and focused interactive calculations. Tester ownership is organisational, not a reason to skip meaningful verification.

Contract/data:
- Missing vs neutral, aware timestamps, finite bounds, no invented quote price.
- Validated JSON examples and generated TypeScript consumer.
- Exact tickers/rules, provenance and staleness retained.

Normalisation/semantics:
- Pre-update z; finite constant input; warmup; missing values do not update.
- Positive z with negative absolute sentiment.
- Mixed claims and ambiguous attribution.
- Negative technical evidence changes direction once.
- Null-attributed skill evidence has no quality effect.

State/idempotency:
- Duplicate event does not change baseline, estimate correction or fill count.
- Refresh alone never compounds evidence.
- Quote movement changes anchor with constant correction.
- Revision supersedes previous extraction.
- More duplicate/correlated streams do not manufacture sqrt(N) strength.
- Singleton event stays visible.
- Threshold monotonicity and winner-event constraints.

Paper broker:
- Buy No uses No ask, sell/MTM uses held-side bid.
- Quantity-aware fees, rounding, cash reservation and no negative cash.
- Partial fills, no depth/no fill, stale quote gate.
- Cooldown and game-group exposure cap.
- Entry/exit fees and realised accounting.
- Mixed/synthetic mode gates are respected.

Runtime/UI:
- Six required scenarios and 1x/5x event-time equivalence.
- Lost WebSocket/reconnect/state resync.
- Reset rejects old-run messages.
- Provider and venue failure remain visible.
- No browser console/network errors from normal flows.
- Receipts expose evidence, estimate and decision inputs.
- No-key replay, no external side effects.

Do not impose an arbitrary huge test count or maximum count. Prioritise these invariants; avoid duplicate tests that simply mirror implementation lines.

## 18. Codex configuration and practical operation

Current official documentation was checked for this pack. The supplied blueprint mixes older and current configuration. The starter uses:
- [agents] enabled and max_concurrent_threads_per_session.
- Standalone .codex/agents/*.toml with name, description, developer_instructions.
- Parent model/effort inheritance by default; no hard-coded retired model.
- No sandbox_mode in role files: permissions inherit from the parent.
- No worker grandchildren by project/role instruction.

Current docs identify max_threads as a legacy alias. max_depth is not documented as a current portable setting. Do not add legacy feature flags just because a blog used them.

Preflight on the user's machine:
1. Run codex --version and codex --help.
2. Launch Codex in the repo, inspect /model and pick a model available to the account.
3. Read current subagent/config docs; the installed release may differ from this pack.
4. Load the trusted project's config; do not bypass your organisation's controls.
5. Ask root to spawn a tiny read-only reviewer task and return. This proves registration, model access and tooling.
6. Only after that start implementation waves.

The version inspected in this workspace was codex-cli 0.167.0-alpha.4. That does not establish the version on the user's machine. A TOML parse is not proof that a model, plugin or role can actually run.

Operational prompts:
- “Spawn pipeline_engineer, quant_engineer and frontend_engineer for the bounded G2 jobs. No workers may delegate. Wait for all three and integrate.”
- “Send quant_engineer this focused fix; retain its existing context.”
- “Show agent statuses, owned paths, blockers and next acceptance gates.”
- “Stop the frontend worker after it reports its current edit; do not discard changes.”
- “Close finished agent threads after recording their handoffs.”

CLI /subagents inspects/switches agent threads in current docs; IDE background-agent controls depend on client availability. The root can steer/stop agents in natural language. Do not equate a file ownership instruction with a separate read-only sandbox.

Use three simultaneous implementation workers. Do not run six writers simply because six roles exist. Extra agents consume tokens and integration effort.

Optional browser automation:
- Playwright MCP is useful for UI inspection, but not required for market ingestion, SQLite access or maths.
- Default pack has no active MCP servers.
- If needed, add only Playwright after the core app works; resolve and pin a working package version.
- The current setup command in official Playwright docs uses @playwright/mcp@latest. Treat that as setup-time resolution, then pin a validated version before the demo.
- Context7 is optional. Direct official docs are sufficient if it is unavailable.
- SQLite MCP is unnecessary: use app code and read-only diagnostic queries through existing tooling.
- Keep the tool catalog small; do not attach every MCP server to every task by default.

Optional Codex CLI setup:
codex mcp add playwright -- npx -y @playwright/mcp@latest
codex mcp list
Then restart/resume as required by your client and verify it actually opens localhost.

Read-only QA means no application source edits. Browser clicks still change demo state; use an isolated paper replay run.

## 19. Task/state templates and recovery

docs/STATE.md contains:
- Current gate, contract version, selected modes and running process owner.
- Role→task→owned paths→status.
- Exact last passing acceptance commands.
- Blockers and assigned owner.
- Decisions since last checkpoint.
- Next three concrete actions.
- Explicit cut features.

Contract change request:
Task / requested signature / reason / affected consumers / migration / acceptance update.

Dependency request:
Package / purpose / minimum version constraint / optional alternative / owning manifest.

Defect report:
Severity / expected / observed / exact reproduction / run/scenario ID / source files / screenshot or log reference / proposed owner.

If a worker drifts:
- Interrupt/steer that worker only.
- Request a handoff of current edits and checks.
- Reassign its smallest missing task; do not respawn every role.
- Keep completed artefacts and passing checks.

If context becomes long:
- Persist compact decisions/state/handoffs.
- Root resumes from artefacts and current diff.
- Do not paste full logs or every source transcript into the root thread.

If a module blocks integration:
- Root may supply a visibly labelled deterministic stub behind the frozen interface.
- Keep real and stub provider status distinct.
- Do not quietly replace actual analysis with canned outcomes.

## 20. Demo script and release criteria

A three-minute rehearsal:
1. Explain modes: six synthetic/recorded sources, captured/synthetic or live quote mode, paper, heuristic.
2. Select Best Narrative and show its actual contract rules.
3. Inject Courtroom Praise in the replay. Show source claims, scene grouping, absolute score vs z, bounded correction.
4. Open a receipt and inspect why the market is relevant.
5. Inject a bug plus laughing chat; show technical evidence rather than positive game quality.
6. Show skill-only rage abstaining.
7. Show the No-side EV example, partial/no-fill possibility, and fee-aware paper ledger.
8. Simulate quote outage; stale badge appears and entries stop.
9. End with the research validation milestone: does this improve on the market across unseen games?

Release checklist:
- One documented startup command works from a clean dependency install.
- No-key replay always works; optional credentials live in environment only.
- Actual snapshots immutable; scenario prices labelled.
- All required invariants pass; defects triaged.
- UI has no undefined numeric values or silent missingness.
- Server restart/WS reconnect/reset do not duplicate evidence/trades.
- Model remains labelled heuristic unless actual calibration exists.
- No real-money order route exists in the MVP.
- README has mode explanations, limitations, setup, demo and verification.
- Archive/commit stable demo version before adding stretch features.

## 21. Sources and verification scope

Official OpenAI documentation:
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/config-file/config-sample
- https://learn.chatgpt.com/docs/models

Current docs say Spark retired and older Codex model pins may be deprecated for ChatGPT-authenticated sessions. The pack avoids model pins instead of assuming another model is available.

Primary integration sources:
- https://docs.kalshi.com/getting_started/api_environments.md
- https://docs.kalshi.com/api-reference/market/get-markets
- https://docs.kalshi.com/api-reference/market/get-market
- https://docs.kalshi.com/getting_started/quick_start_market_data.md
- https://help.kalshi.com/en/articles/13823828-the-orderbook
- https://help.kalshi.com/en/articles/13823805-fees
- https://dev.twitch.tv/docs/chat/
- https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker
- https://playwright.dev/docs/getting-started-mcp
- https://scikit-learn.org/stable/modules/calibration
- https://thegameawards.com/faq

These sources support specific platform capabilities and constraints, not the arbitrary heuristic model coefficients. Normalisation, feature choices, paper risk defaults, timelines and ownership procedures here are proposed design choices.

This handoff's syntax/contract checks are reported in VALIDATION.md. It does not claim the application was built, the user's account can access a model, a Twitch media route is operational, or the strategy has demonstrated predictive skill.


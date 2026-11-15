# G2 quant handoff

## G3 integration addendum — 15 November 2026

The G3 root requested the following fixes and pure scheduler helpers. Changes remain only in quant/execution-owned modules and this handoff; no shared contracts, runtime processes, tests or persistence code were edited.

- Estimator, entry, eligibility-time execution and liquidation marks now treat quote age **at or after** 10 seconds as stale. A 9.999999-second quote remains eligible; a 10-second quote does not.
- Same-time due orders execute sells before buys, with stable due-time/order-ID ordering thereafter. Root still owns the broader controls/inputs/features/exits/entries phase scheduler and calls at each exact deadline.
- `PaperOrder.decision_quote_at: datetime | None = None` is an additive internal field mirrored by root. New entry/exit plans always populate it. Execution rejects a quote older than the decision quote. Restored legacy pending records without this field may use their original quote ID only; an unverifiable replacement quote cancels instead of guessing.
- Liquidity revision fingerprints now cover market, actual side prices and depth only. Quote IDs, wrapper timestamps, status and stale flags do not replenish liquidity or create false revision conflicts. Reusing a revision with changed prices/depth remains an error. Marks check known revision consistency and subtract consumed bid quantity.
- A final complete close releases the exact remaining Decimal cost basis directly; partial-close rounding residual remains with the open position. A complete liquidation mark uses that same exact remaining basis.
- `exit_deadlines(state: BrokerState, hold_seconds: int = 300) -> tuple[ExitDeadline, ...]` reconstructs stable deadlines from each still-open entry fill. `ExitDeadline` fields: `deadline_id`, `run_id`, `market_id`, `side`, `entry_fill_id`, `due_at`. Partial exits retain the same deadline. An open position without a committed entry fill is invalid.
- `position_marks(state: BrokerState, books: Mapping[str, QuoteBook], as_of: datetime, limits=PaperLimits()) -> tuple[PositionMark, ...]` returns stable market ordering without writes or liquidity consumption. `PositionMark` fields: `market_id`, `side`, nullable `quote_id`, `as_of`, `priced_quantity`, `unpriced_quantity`, nullable `net_liquidation_value`, nullable `unrealized_pnl_priced_quantity`, nullable `reason`. Quantity and money remain Decimal. Missing/stale quotes leave the entire position unpriced with null value/PnL and a reason.

Root consumes each exit deadline once. An overdue residual or blocked exit may retry on a later causal quote event/manual command, with an intent keyed to that event; a publication or ageing tick is not a new retry. Skip a new plan while the market has a pending order. Root must supply the latest available quote/estimate at eligibility and commit each returned state atomically before retaining it. Candidate wire decisions remain `action=candidate`, `eligible_for_fill=false`; broker results are a separate explicitly synthetic paper lifecycle.

The previous G2 internal liquidity fingerprint algorithm included the whole quote. Existing isolated G2 broker-state artifacts containing such fingerprints cannot transparently reinterpret those hashes; start a new G3 run/isolated DB unless root adds an explicit migration. G2 media runs had no scheduled broker state. New G3 state dump/restore preserves the corrected fingerprint semantics and was exercised successfully.

G3 verification actually executed, all exit 0 using `.venv/Scripts/python.exe`:

1. Focused inline expiry/deadline/repricing/mark checks: exact 10-second estimator/entry/execution/mark boundary; deadline reconstruction through restore and partial exit; stale/missing null marks; partial four-contract No exit leaving six with realized PnL `-0.12`; wrapper-only refresh leaves consumed bid depth at zero; an explicit new liquidity revision replenishes; same-revision changed prices reject; an older eligibility quote cancels; newer No ask `.85` reprices the reserved `.86` entry; legacy missing decision timestamp rejects an unverifiable replacement quote.
2. Focused inline scheduler/risk checks: same-time fill order `sell, buy`; complete held-No close realizes `-0.30` after both fees; a new entry during the 60-second entry cooldown is blocked and exactly 60 seconds is accepted; pending reservations count against game and total caps (observed `4.35` and `9.57` respectively under reduced test-only limits); unavailable current estimate cancels entry while risk exit needs no estimate; complete state roundtrip equality.
3. `-m compileall -q backend/quant backend/execution` exited 0.
4. A focused high-precision cost-basis close/mark check exited 0: complete close removes the position and exactly matches `gross - exit_fee - remaining_cost_basis`, including a 28-digit basis.

No blocker remains for new-run G3 scheduler integration. Real recordings/generated media stay candidate-only unless root selects an explicitly authorized fully synthetic scenario. Root owns wire mirrors, transaction composition, deadline persistence/reconstruction and the integrated acceptance check. The older G2 limitation statements below are historical; root may now integrate the scheduler/tape without changing these pure broker APIs.

Implemented 14 November 2026. Ownership stayed within `backend/quant/`, `backend/execution/` and this handoff. No dependencies, test source, runtime process, database or shared contracts were edited. Workers were not delegated.

## Changed files

- `backend/quant/__init__.py`: public evaluation/feature imports.
- `backend/quant/normalization.py`: immutable `Baseline`, `Normalized`, pure pre-update `normalize`.
- `backend/quant/engine.py`: unique/revisioned feature view and candidate-only synthetic scenario evaluation.
- `backend/execution/__init__.py`: paper planning imports.
- `backend/execution/paper.py`: pure Decimal paper state, entry/exit plans, execution proposals and restore hooks.

## Public integration interfaces

```python
from backend.quant import Evaluation, FeatureEngine, evaluate

evaluate(
    run_id: str,
    windows: Sequence[SourceWindow],
    claims: Sequence[EvidenceClaim],
    quote: MarketQuote,
    as_of: datetime,
    *,
    seed_baseline: Mapping | None = None,
    model: Mapping | None = None,
    limits: Mapping | None = None,
    relevance: float = 1.0,
) -> Evaluation
```

`Evaluation` is a frozen internal dataclass with `features: list[FeatureSnapshot]`, `estimate: ModelEstimate | None`, `decision: PaperDecision | None`, `reasons: list[str]`. Root projects these into the frozen dashboard contracts. The routine does not persist anything or submit an order. Use an aware replay clock time and the explicit synthetic quote available at that time. Quotes older than 10 seconds, future quotes, missing/two-sided invalid anchors, endpoints and spreads above USD 0.05 cause estimate abstention. Never relabel an old quote with a new timestamp merely to bypass this gate; supply an explicit synthetic quote timeline.

`FeatureEngine(run_id).add_window(window) -> bool`, `.ingest(claim) -> bool`, and `.snapshot(as_of, seed_baseline=None) -> list[FeatureSnapshot]` provide the ingestion seam. Duplicate immutable IDs return false; conflicting payloads fail. A newer claim revision supersedes the old interpretation, including a new ID carrying a higher window/aspect/modality revision. Snapshot rebuilding replaces history deterministically and does not alter any already committed fills. Source availability and event time both gate inclusion. Claim text must be supported by its source and have matching source identity/mode.

Root approved and implemented nullable surprise/EV and the additional source/aspect/quality/dependency/freshness fields before consumption. No generated file was edited by quant.

## Feature/model behavior

- One baseline update per stream/aspect/modality/10-second bucket, including multiple claims/scenes within it; fixed alpha `1-exp(-10/180)`, std floor 0.1, z clip 4.
- Z uses the previous baseline; unavailable/ambiguous/non-game claims never update it. Actual recording OCR defaults to no seed and requires 20 prior valid buckets. `seed_baseline` must explicitly contain `mean`, `variance`, `count`, `version`; it is labelled `seeded_fixture`.
- Absolute sentiment and surprise stay separate. Features aggregate each aspect across capped dependency groups; explicit rebroadcast dependencies and simultaneous speech/chat cannot manufacture extra source weight. Effective count is a concentration diagnostic only.
- Current evidence is rebuilt from unique observations. Ageing uses the supplied run clock, a 300-second half-life, a displayed decayed mean and a separate freshness factor. Route relevance is nonnegative and applied once outside normalized means. Missing z contributes no z feature; `z_freshness` accounts for its available coverage.
- Current configured estimator is the narrative synthetic scenario, using `.2 * absolute + .05 * z`, current valid Yes midpoint and correction cap 0.5. Other aspect features remain visible but have no automatic estimate route. No severity is inferred from a signed technical-sentiment score and no technical sign is reversed twice.
- Quote changes recompute the anchor; unchanged evidence/as-of yields the same correction. Timer publication is not ingestion. GTA V proxy inputs cannot price actual GTA VI venue contracts.
- Candidate EV uses the correct side's ask and named synthetic fee. A missing ask leaves that side's EV null with a reason. Every result remains candidate-only, including generated media.
- The legacy previous/updated baseline fields on an aggregate feature describe the last deterministically processed source bucket, not an imaginary aggregate baseline. `stream_ids`, aspect, count, freshness and disagreement describe the aggregate. A richer per-source baseline receipt remains future schema work.

## Pure paper simulator

`backend.execution.paper` provides frozen `DepthLevel`, `QuoteBook`, `PaperLimits`, `PaperOrder`, `PaperFill`, `Position`, `Consumption`, `BrokerState`, `BrokerResult`.

- `plan_entry(state, *, intent_id, game_id, side, probability: Decimal, book, as_of, evidence_mode, simulation_authorized=False, requested_quantity=Decimal('10'), limits=PaperLimits()) -> BrokerResult` reserves a bounded fixed-size synthetic IOC entry. Explicit synthetic authorization is required; recorded evidence, live/stale quotes, missing depth, cooldown, duplicate/opposing positions and insufficient capacity block it.
- `execute_due(state, *, books: Mapping[market_id, QuoteBook], probabilities: Mapping[market_id, Decimal | None], as_of, limits=...) -> BrokerResult` proposes one transaction for due orders in stable order. Caller must recompute current available estimates and supply the latest quote. It rechecks age/status, original limit, reservation ceiling, side EV and remaining depth after 250 ms. An unavailable estimate cancels entry. It never performs venue/network I/O.
- `plan_exit(state, *, intent_id, market_id, book, as_of, reason='explicit paper risk exit', limits=...)` schedules a held-side bid exit. Entry thresholds/cooldown do not prevent risk exits. Partial exits release proportional entry cost basis and book both fees into realized PnL.
- `liquidation_mark(state, position, book, as_of, limits=...)` prices only executable held-side bid quantity and reports residual unpriced quantity. Absent/stale marks stay null.
- `dump_state(state) -> str` and `load_state(payload) -> BrokerState` preserve Decimal strings, timestamps, intent history, consumed depth and book revision fingerprints. Same intent/payload reuses its result; conflicting payload fails. Same depth revision cannot be reused with changed quote/depth. Depth is consumed once per revision/market/side/direction/price.
- Fees are `ceil_to_cent(0.01 * executed_quantity)` once per nonempty order sweep. Defaults are bankroll 10,000; all-in order/game/total exposure caps 0.5%/3%/5%; quantity 10; step 1; EV 0.03; cooldown 60 seconds; quote age 10 seconds. These are explicit simulation assumptions.

Root implemented the persistence hook in `StateStore.commit(..., broker_state=(expected_revision, result.state))` and `StateStore.load_broker(run_id) -> (revision, BrokerState) | None`. The single SQLite transaction contains the optimistic broker revision, serialized state, versioned distinct order/fill records and any accompanying envelope/command receipt. The expected revision must come from the same loaded state used to produce the plan. Do not retain an in-memory result if its commit fails. Restore with `load_broker` before further intents. G2 media runtime intentionally does **not** schedule this broker; it shows candidates only. Full paper runtime scheduling and dashboard execution tape integration belong to G3.

Quant read-only review of the root storage implementation found no critical transaction/CAS issue under the single-writer contract: an envelope sequence conflict or duplicate command after a broker write rolls back the entire transaction, run identity is checked, and serialize/restore validation precedes persistence. `execution_records` deliberately stores complete order/fill snapshots per broker revision; those audit rows are not new executions. Root separately reported a successful isolated partial four-contract commit (cash 9996.52), duplicate-command rollback preserving revision 2, and reopen/restore without another fill. Those persistence checks were run by root, not rerun or claimed as quant's own verification.

## Verification actually executed

All used `.venv/Scripts/python.exe`; no new test source was created.

1. `-m compileall -q backend/quant backend/execution` exited 0.
2. Focused inline feature and broker calculation session exited 0. Covered seeded exact G1 arithmetic, warmup/null z, negative absolute with positive pre-update z, duplicate idempotency, future availability, revision replacement, quote-anchor movement with invariant correction, stale reference rejection and null missing-side EV. Broker checks covered side EV, multi-level VWAP, one sweep fee, reservation, 249/250 ms latency, duplicate execution, partial held-side mark, partial exit and realized PnL, serialized restore, recorded/stale blocks and eligibility-time EV cancellation.
3. Further focused inline session exited 0. Covered 21 valid buckets and ready surprise, cross-scene single bucket update, 300-second singleton half-life, ambiguous exclusion, new-ID revision replacement, known dependency collapse, depth-limited partial entry, cash-constrained quantity, duplicate/opposing entry block, stale-at-execution cancellation and conflicting depth revision rejection.

Observed values:

| Check | Actual result |
|---|---|
| Seeded fixture correction / model | -0.18 / 0.12407788254178297 |
| Seeded fixture No net EV | 0.00592211745821703 USD |
| Absolute -0.4, prior mean -0.8 / variance .04 | z +2 before update |
| p=.097, Yes ask .15 / No ask .86, Q10 | Yes EV -.063 / No EV +.033 after .10 fee |
| No sweep 6@.86 + 4@.87 | gross 8.64, fee .10, cash 9991.26 |
| Exit 4 held No contracts @.85 | residual 6; realized PnL -.136 including entry/exit fees |
| Four-contract depth entry | quantity 4, fee .04, partial status |
| Available cash 1.00 | quantity 1, reservation .87 |
| Execution with quote age 11 seconds | zero fills, reservation released |

## Remaining limitations and integration actions

No calibrated model, real venue fees/depth, automatic profit/time exit scheduler, threshold/complete-awards constraint solver, runtime execution scheduling/UI tape or formal tester-owned regression suite is claimed. The root SQLite broker persistence seam is implemented and separately verified. The current estimate route is narrative only. Normalization settings are the explicit fixed G2 defaults above, not a general user-editable normalization engine.

Root should call `evaluate` with cached available sources and actual replay time, use no seed for media, retain reasons and proxy labels, and expose distinct actual venue context unchanged. Use the pipeline's explicit synthetic timeline to exercise broker plans separately. No dependency or contract blocker remains.

## Live Twitch game-to-market candidate matching

Added `backend/quant/live_market_matching.py` with `match_game_outcomes(game_name: str, markets: list[dict]) -> list[dict]`. It retains each actual market payload and category metadata, and adds `matched_game_name`, the actual `matched_yes_outcome`, versioned `match_method`, a rationale, and `market_is_open=True`. The matcher only accepts exact normalized Yes-outcome names; normalization folds case/Unicode, tolerates punctuation, and strips a small set of explicit trailing edition labels. It does not fuzzy-match titles, invent tickers, compute probabilities, inspect transcript sentiment, or create decisions. Markets with non-open status are ignored; observed Kalshi `active` and literal `open` are accepted as open states while their source status is preserved verbatim.

Input rows may include nested `event` and `series` metadata. Fields absent at the market level are copied from those raw parent objects, preserving category/categories/tags so Video Games and Esports remain distinguishable. Candidates sort by actual market ticker; identical repeated rows deduplicate, while conflicting payloads for the same ticker fail closed.

Changed paths: `backend/quant/live_market_matching.py`, `handoffs/quant.md`. No tests were added. Verification: Python compilation and focused inline matching checks were run; no network calls or live market requests were made. Root owns the Kalshi discovery adapter/API/schema and frontend integration. Root should pass market rows enriched with actual event/series metadata, rules, outcome subtitles, raw status, and current quote fields, then serialize candidates through the additive live-market response contract. Candidates are for market discovery only; do not feed them to the GTA V proxy estimator or paper broker without a separate calibrated/approved live evidence route.

## Manual live-game input and decision-flow feasibility

Root asked whether the manual game input + live Whisper transcript + matched Kalshi markets can safely produce a paper decision. No quant code change is appropriate until the live evidence and decision contracts are separated from the replay proxy contracts.

- `LiveAudioTranscriber` produces standalone live transcript windows and accepted ASR segments, not `SourceWindow`/`EvidenceClaim` records. The current speech classifier abstains unless the speaker is verified as the streamer; the capture path has no speaker attribution. A transcript therefore cannot be treated as streamer opinion by default.
- The current `EvidenceClaim`, `FeatureSnapshot`, `ModelEstimate` and `Receipt` are statically scoped to `content_game_id="gta5"`, `evidence_scope="proxy_demo"`, and recorded/synthetic evidence. `ModelEstimate` rejects market IDs outside `synthetic:`. The quant `evaluate()` function explicitly requires a synthetic quote and says GTA V proxy evidence cannot price venue contracts.
- Kalshi matching is an identity lookup: it returns open markets whose actual Yes outcome exactly matches the game name. This does not establish that game-quality speech predicts the market's settlement outcome. PLAN §11 explicitly identifies game-quality-to-award routes as weak/indirect and says they do not get an automatic signal.
- The existing `PaperDecision` requires a valid estimate ID, quote ID, side and calculated EV; it is not an abstention/review record. The actual live-market response currently has no source-window references or model decision payload.

**Required integration contract:** add a root-owned, versioned live decision-review model separate from `ModelEstimate`/`PaperDecision`. It should have stable review and market IDs, cited source-window/claim IDs, status `abstain|candidate`, nullable probability/side/EV, explicit reasons, model/calibration identity, actual quote ID/timestamp/mode, and paper execution mode. Root should expose the review with live market candidates. Current review should explicitly abstain because speaker attribution and an outcome-specific model/rule-valid evidence route are absent. Do not emit a trade-shaped candidate by copying the GTA V scenario coefficients or treating a game-quality score as an awards/esports win probability.

**Changed paths:** only this handoff. No helper was added because the existing frozen contract cannot represent the required live abstention without conflating a market candidate with an estimate/decision. No checks were run for this assessment; it uses source/contract inspection only. **Root integration action:** create the additive live review contract and project explicit abstention reasons beside manual-game market matches. A subsequent independent task can add a genuine outcome-specific live model after its evidence and attribution rules are defined and validated.

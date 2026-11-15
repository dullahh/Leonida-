"""Schema 2, additive G2 contracts. Provenance and missingness are explicit."""
from __future__ import annotations

import math
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "2"
ID = Annotated[str, Field(min_length=1, max_length=240)]
Finite = Annotated[float, Field(allow_inf_nan=False)]
Nonnegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Score = Annotated[float, Field(ge=-1, le=1, allow_inf_nan=False)]
Aspect = Literal["narrative", "overall", "technical", "gameplay", "audio"]
Target = Literal["game", "player_skill", "streamer", "unrelated", "ambiguous"]
Amount = Annotated[Decimal, Field(allow_inf_nan=False)]
Money = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
Price = Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RunRecord(Contract):
    schema_version: Literal["2"] = "2"
    run_id: ID


class ChatRegion(Contract):
    x: Probability
    y: Probability
    width: Annotated[float, Field(gt=0, le=1)]
    height: Annotated[float, Field(gt=0, le=1)]

    @model_validator(mode="after")
    def fits_frame(self):
        if self.x + self.width > 1.000001 or self.y + self.height > 1.000001:
            raise ValueError("chat region extends outside the frame")
        return self


class RecordingAsset(Contract):
    asset_id: ID
    stream_id: ID
    label: ID
    local_path: str | None
    asset_sha256: str | None
    availability_reason: str | None
    content_game_id: Literal["gta5"] = "gta5"
    target_game_id: Literal["gta6"] = "gta6"
    evidence_scope: Literal["proxy_demo"] = "proxy_demo"
    media_start_seconds: Nonnegative = 0
    timeline_start_seconds: Finite = 0
    chat_region: ChatRegion
    sample_interval_seconds: Annotated[float, Field(gt=0, le=60)] = 2
    language: str = "eng"
    source_url: str | None = None
    permission_note: str
    evidence_mode: Literal["recorded", "synthetic_replay"] = "recorded"
    media_end_seconds: Nonnegative | None = None
    scene_id: ID = "manual-unassigned"
    audio_transcription: Literal["disabled", "faster_whisper"] = "disabled"
    speech_model_path: str | None = None
    speaker_role: Literal["streamer", "unknown"] = "unknown"

    @model_validator(mode="after")
    def availability(self):
        if self.media_end_seconds is not None and self.media_end_seconds <= self.media_start_seconds:
            raise ValueError("media end must follow trim start")
        if (self.local_path is None or self.asset_sha256 is None) and not self.availability_reason:
            raise ValueError("missing recording needs an availability reason")
        if self.asset_sha256 is not None and (len(self.asset_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.asset_sha256)):
            raise ValueError("asset_sha256 must be a lowercase SHA-256")
        return self

    def replay_offset(self, media_seconds: float) -> float:
        if not math.isfinite(media_seconds) or media_seconds < self.media_start_seconds:
            raise ValueError("frame precedes trim start or has a nonfinite time")
        offset = media_seconds - self.media_start_seconds + self.timeline_start_seconds
        if offset < 0:
            raise ValueError("frame is before the replay timeline")
        return offset


class RecordingManifest(Contract):
    schema_version: Literal["2"] = "2"
    manifest_version: ID
    recordings: list[RecordingAsset] = Field(min_length=2, max_length=6)
    ocr_version: ID
    preprocessing_version: ID
    semantic_version: ID

    @model_validator(mode="after")
    def unique_sources(self):
        for field in ("asset_id", "stream_id"):
            if len({getattr(r, field) for r in self.recordings}) != len(self.recordings):
                raise ValueError(f"duplicate {field}")
        return self


class CachedObservation(Contract):
    observation_id: ID
    asset_id: ID
    stream_id: ID
    content_game_id: Literal["gta5"] = "gta5"
    evidence_scope: Literal["proxy_demo"] = "proxy_demo"
    evidence_mode: Literal["recorded", "synthetic_replay"]
    provider: Literal["supplied_fixture", "sampled_frame_ocr", "recorded_asr"]
    media_seconds: Nonnegative
    replay_seconds: Nonnegative
    raw_text: ID
    supporting_quote: ID
    sentiment: Score | None
    abstention_reason: str | None = None
    ocr_confidence: Probability | None
    confidence_reason: str | None = None
    frame_ref: str | None
    frame_reason: str | None
    aspect: Aspect = "narrative"
    target: Target = "game"
    source_modality: Literal["chat", "speech"] = "chat"
    semantic_confidence: Probability | None = None
    media_end_seconds: Nonnegative | None = None
    replay_end_seconds: Nonnegative | None = None
    available_replay_seconds: Nonnegative | None = None
    ocr_boxes: list[list[Finite]] = Field(default_factory=list)
    track_id: str | None = None
    dependency_group: str | None = None
    audio_ref: str | None = None
    scene_id: ID
    extractor_version: ID

    @model_validator(mode="after")
    def support(self):
        if self.supporting_quote not in self.raw_text:
            raise ValueError("claim quotation is not supported by raw text")
        if self.sentiment is None and not self.abstention_reason:
            raise ValueError("null sentiment requires abstention reason")
        if self.frame_ref is None and not self.frame_reason:
            raise ValueError("absent frame needs a reason")
        if self.ocr_confidence is None and not self.confidence_reason:
            raise ValueError("absent OCR confidence needs a reason")
        if self.provider == "supplied_fixture" and self.evidence_mode != "synthetic_replay":
            raise ValueError("supplied fixture must be synthetic")
        return self


class MediaAssetReport(Contract):
    asset_id: ID
    available: bool
    reason: str | None = None
    duration_seconds: Nonnegative | None = None
    frame_count: int = Field(default=0, ge=0)
    audio_available: bool = False
    audio_reason: str | None = None
    audio_ref: str | None = None
    speech_available: bool = False
    speech_reason: str | None = None


class EvidenceCache(Contract):
    schema_version: Literal["2"] = "2"
    cache_key: ID
    input_sha256: ID
    payload_sha256: ID
    manifest: RecordingManifest
    observations: list[CachedObservation]
    asset_reports: list[MediaAssetReport] = Field(default_factory=list)
    extraction_metadata: dict[str, str] = Field(default_factory=dict)


class ModalityAvailability(Contract):
    modality: Literal["chat", "speech", "facecam"]
    available: bool
    reason: str | None = None

    @model_validator(mode="after")
    def missing(self):
        if not self.available and not self.reason:
            raise ValueError("unavailable modality needs reason")
        return self


class SourceWindow(RunRecord):
    window_id: ID
    stream_id: ID
    asset_id: ID
    content_game_id: Literal["gta5"] = "gta5"
    evidence_scope: Literal["proxy_demo"] = "proxy_demo"
    evidence_mode: Literal["recorded", "synthetic_replay"]
    event_at: AwareDatetime
    available_at: AwareDatetime
    source_media_seconds: Nonnegative
    replay_seconds: Nonnegative
    raw_text: ID
    cache_key: ID
    observation_id: ID
    provider: str
    frame_ref: str | None
    frame_reason: str | None
    modalities: list[ModalityAvailability]
    source_modality: Literal["chat", "speech"] = "chat"
    ocr_confidence: Probability | None = None
    confidence_reason: str | None = None
    audio_ref: str | None = None
    observation: CachedObservation | None = None


class EvidenceClaim(RunRecord):
    claim_id: ID
    window_id: ID
    stream_id: ID
    content_game_id: Literal["gta5"] = "gta5"
    evidence_scope: Literal["proxy_demo"] = "proxy_demo"
    evidence_mode: Literal["recorded", "synthetic_replay"]
    aspect: Aspect = "narrative"
    source_modality: Literal["chat", "speech"] = "chat"
    target: Target = "game"
    sentiment: Score | None
    abstention_reason: str | None = None
    semantic_confidence: Probability | None = None
    quality: Probability = 1
    dependency_group: str | None = None
    supporting_quote: ID
    scene_id: ID
    extractor_version: ID
    revision: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def missing_sentiment(self):
        if self.sentiment is None and not self.abstention_reason:
            raise ValueError("null claim sentiment needs an abstention reason")
        return self


class FeatureSnapshot(RunRecord):
    feature_id: ID
    claim_ids: list[ID] = Field(min_length=1)
    content_game_id: Literal["gta5"] = "gta5"
    evidence_scope: Literal["proxy_demo"] = "proxy_demo"
    absolute_sentiment: Score
    mean_z: Finite | None
    baseline_status: Literal["seeded_fixture", "warming_up", "ready"] = "seeded_fixture"
    aspect: Aspect = "narrative"
    source_modality: Literal["chat", "speech", "mixed"] = "chat"
    stream_ids: list[str] = Field(default_factory=list)
    freshness: Probability = 1
    z_freshness: Probability = 1
    z_reason: str | None = None
    disagreement: Nonnegative = 0
    unique_stream_count: int = Field(default=1, ge=1)
    baseline_version: ID
    previous_mean: Finite
    previous_variance: Nonnegative
    updated_mean: Finite
    updated_variance: Nonnegative
    baseline_count: int = Field(ge=1)
    unique_observation_count: int = Field(ge=1)
    effective_source_diagnostic: Nonnegative
    as_of: AwareDatetime


class MarketDefinition(Contract):
    market_id: ID
    market_namespace: Literal["synthetic", "venue"]
    title: ID
    target_game_id: Literal["gta6"] = "gta6"
    venue_ticker: str | None
    reference_venue_ticker: str | None
    rules_primary: str
    definition_version: ID

    @model_validator(mode="after")
    def namespace(self):
        prefix = "synthetic:" if self.market_namespace == "synthetic" else "kalshi:"
        if not self.market_id.startswith(prefix):
            raise ValueError("market ID and namespace disagree")
        if self.market_namespace == "synthetic" and self.venue_ticker is not None:
            raise ValueError("synthetic market cannot execute under a venue ticker")
        if self.market_namespace == "venue" and not self.venue_ticker:
            raise ValueError("venue market requires a returned ticker")
        return self


class MarketQuote(Contract):
    quote_id: ID
    market_id: ID
    quote_mode: Literal["synthetic_replay", "live", "cached_stale"]
    captured_at: AwareDatetime
    venue_timestamp: AwareDatetime | None = None
    venue_timestamp_reason: str | None = "No verified venue quote timestamp"
    venue_status: str
    is_stale: bool
    yes_bid: Price | None
    yes_ask: Price | None
    no_bid: Price | None
    no_ask: Price | None
    missing_reasons: dict[str, str] = Field(default_factory=dict)
    source_ref: ID

    @model_validator(mode="after")
    def quote_integrity(self):
        for side in ("yes", "no"):
            bid, ask = getattr(self, f"{side}_bid"), getattr(self, f"{side}_ask")
            if bid is not None and ask is not None and bid > ask:
                raise ValueError("crossed quote")
            for field in (f"{side}_bid", f"{side}_ask"):
                if getattr(self, field) is None and not self.missing_reasons.get(field):
                    raise ValueError(f"missing {field} needs a reason")
        if self.quote_mode == "cached_stale" and not self.is_stale:
            raise ValueError("cached_stale must be stale")
        if self.quote_mode == "synthetic_replay" and not self.market_id.startswith("synthetic:"):
            raise ValueError("synthetic quote needs synthetic market identity")
        if self.quote_mode != "synthetic_replay" and not self.market_id.startswith("kalshi:"):
            raise ValueError("venue quote needs venue market identity")
        return self


class ModelEstimate(RunRecord):
    estimate_id: ID
    market_id: ID
    quote_id: ID
    feature_ids: list[ID] = Field(min_length=1)
    market_reference_probability: Probability
    correction_log_odds: Finite
    model_probability: Probability
    relevance: Probability
    model_version: ID
    calibration_status: Literal["heuristic"] = "heuristic"
    uncertainty_status: Literal["not_estimated"] = "not_estimated"
    evidence_scope: Literal["proxy_demo"] = "proxy_demo"
    coefficients: dict[str, Finite]

    @model_validator(mode="after")
    def arithmetic(self):
        p = self.market_reference_probability
        if not 0 < p < 1:
            raise ValueError("endpoint quote cannot anchor G1 estimate")
        expected = 1 / (1 + math.exp(-(math.log(p / (1 - p)) + self.correction_log_odds)))
        if not math.isclose(expected, self.model_probability, abs_tol=1e-12):
            raise ValueError("inconsistent estimate arithmetic")
        if not self.market_id.startswith("synthetic:"):
            raise ValueError("GTA V proxy evidence cannot price a live GTA VI contract")
        return self


class PaperDecision(RunRecord):
    decision_id: ID
    estimate_id: ID
    quote_id: ID
    market_id: ID
    execution_mode: Literal["paper"] = "paper"
    action: Literal["candidate"] = "candidate"
    side: Literal["yes", "no"]
    quantity: Money
    yes_ev_per_contract: Amount | None
    no_ev_per_contract: Amount | None
    ev_missing_reasons: dict[str, str] = Field(default_factory=dict)
    estimated_total_fee: Money
    fee_schedule_version: ID
    eligible_for_fill: Literal[False] = False
    reasons: list[str] = Field(min_length=1)


class Receipt(RunRecord):
    receipt_id: ID
    window_ids: list[ID]
    claim_ids: list[ID]
    feature_ids: list[ID]
    estimate_id: ID
    decision_id: ID
    quote_id: ID
    evidence_scope: Literal["proxy_demo"] = "proxy_demo"
    explanation: list[str]
    limitations: list[str]


class VenueContext(Contract):
    status: Literal["historical", "live", "unavailable", "error"]
    observed_at: AwareDatetime | None
    error: str | None
    markets: list[MarketDefinition]
    quotes: list[MarketQuote]
    effect_on_proxy_estimate: Literal["none"] = "none"


class SourceStatus(Contract):
    stream_id: ID
    label: ID
    state: Literal["fixture_ready", "recording_missing", "recording_ready", "error"]
    reason: str


class PlaybackState(Contract):
    position_seconds: Nonnegative = 0
    duration_seconds: Nonnegative = 0
    speed: Annotated[float, Field(gt=0, le=5)] = 1
    playing: bool = False


class EvidenceGroup(RunRecord):
    group_id: ID
    scene_id: ID
    claim_ids: list[ID]
    identity_source: Literal["manual"] = "manual"
    match_confidence: None = None


class ReactionSignal(RunRecord):
    reaction_id: ID
    observation_id: ID
    window_id: ID
    stream_id: ID
    asset_id: ID
    evidence_mode: Literal["recorded", "synthetic_replay"]
    evidence_scope: Literal["proxy_demo"] = "proxy_demo"
    media_seconds: Nonnegative
    media_end_seconds: Nonnegative | None = None
    replay_seconds: Nonnegative
    available_replay_seconds: Nonnegative
    valence: Literal["negative", "neutral", "positive", "uncertain"]
    intensity: Probability | None
    intensity_basis: Literal["text_only"] = "text_only"
    emotion: Literal["excitement", "frustration", "surprise", "amusement", "confusion"] | None
    target_certainty: Probability
    likely_target: Literal["game_quality", "in_game_event", "player_skill", "another_player", "role_play", "unknown"]
    source_modality: Literal["chat", "speech"]
    confidence: Probability | None
    supporting_text: ID
    abstention_reason: str | None
    exclusion_reason: str | None
    supported_claim_id: ID | None
    market_relevance: Probability
    pricing_eligible: bool
    included_in_estimate: bool = False
    classifier_version: ID
    policy_version: ID

    @model_validator(mode="after")
    def conservative_reaction(self):
        if self.pricing_eligible and (self.supported_claim_id is None or self.likely_target != "game_quality"):
            raise ValueError("reaction pricing requires a supported game-quality claim")
        if self.included_in_estimate and not self.pricing_eligible:
            raise ValueError("excluded reaction cannot enter an estimate")
        if not self.pricing_eligible and not self.exclusion_reason:
            raise ValueError("contextual telemetry needs an exclusion reason")
        return self


class OrderRecord(RunRecord):
    order_id: ID
    intent_id: ID
    request_digest: ID
    market_id: ID
    game_id: ID
    side: Literal["yes", "no"]
    direction: Literal["buy", "sell"]
    status: Literal["pending", "filled", "partial", "cancelled"]
    requested_quantity: Money
    quantity: Money
    filled_quantity: Money
    limit_price: Money
    reserved_cash: Money
    decision_probability: Money | None
    eligible_probability: Money | None
    decision_quote_id: ID
    execution_quote_id: ID | None
    created_at: AwareDatetime
    eligible_at: AwareDatetime
    completed_at: AwareDatetime | None
    reasons: list[str]
    decision_quote_at: AwareDatetime | None = None


class FillRecord(Contract):
    fill_id: ID
    order_id: ID
    quote_id: ID
    book_revision: ID
    market_id: ID
    side: Literal["yes", "no"]
    direction: Literal["buy", "sell"]
    quantity: Money
    gross_value: Money
    fee: Money
    vwap: Money
    at: AwareDatetime


class PositionRecord(Contract):
    market_id: ID
    game_id: ID
    side: Literal["yes", "no"]
    quantity: Money
    cost_basis: Money
    entry_fair_side: Money


class PositionMark(Contract):
    market_id: ID
    side: Literal["yes", "no"]
    quote_id: ID | None
    as_of: AwareDatetime
    priced_quantity: Money
    unpriced_quantity: Money
    net_liquidation_value: Amount | None
    unrealized_pnl_priced_quantity: Amount | None
    reason: str | None


class ExecutionTrace(RunRecord):
    trace_id: ID
    order_id: ID
    stage: Literal["entry_plan", "exit_plan", "eligibility"]
    at: AwareDatetime
    windows: list[SourceWindow]
    claims: list[EvidenceClaim]
    features: list[FeatureSnapshot]
    quote: MarketQuote
    estimate: ModelEstimate | None
    decision: PaperDecision | None
    receipt: Receipt | None
    reasons: list[str]


class ExecutionState(Contract):
    enabled: bool = False
    reason: str = "Candidate-only input; no synthetic execution authorization."
    fee_schedule_version: ID = "simulation-linear-v1"
    orders: list[OrderRecord] = Field(default_factory=list)
    fills: list[FillRecord] = Field(default_factory=list)
    positions: list[PositionRecord] = Field(default_factory=list)
    marks: list[PositionMark] = Field(default_factory=list)
    traces: list[ExecutionTrace] = Field(default_factory=list)
    reserved_cash: Money = Decimal("0")
    realized_pnl: Amount = Decimal("0")
    latest_reasons: list[str] = Field(default_factory=list)


class DashboardSnapshot(RunRecord):
    gate: Literal["G1", "G2", "G3"] = "G1"
    contract_revision: Literal["g2-v1", "g3-v1", "g3-reactions-v1"] = "g3-reactions-v1"
    reactions: list[ReactionSignal] = Field(default_factory=list)
    reaction_recent_window_seconds: Nonnegative = 30
    scenario_name: str = "foundation"
    groups: list[EvidenceGroup] = Field(default_factory=list)
    execution: ExecutionState = Field(default_factory=ExecutionState)
    scheduler_cursor: Nonnegative = 0
    source_queue_capacity: int = Field(default=128, ge=1)
    run_status: Literal["paused", "playing", "completed"] = "paused"
    playback: PlaybackState = Field(default_factory=PlaybackState)
    replay_time: AwareDatetime
    evidence_mode: Literal["recorded", "synthetic_replay"] = "synthetic_replay"
    content_game_id: Literal["gta5"] = "gta5"
    target_game_id: Literal["gta6"] = "gta6"
    evidence_scope: Literal["proxy_demo"] = "proxy_demo"
    execution_mode: Literal["paper"] = "paper"
    calibration_status: Literal["heuristic"] = "heuristic"
    cache_key: ID
    configuration_fingerprint: ID
    recording_manifest: RecordingManifest
    streams: list[SourceStatus]
    windows: list[SourceWindow]
    claims: list[EvidenceClaim]
    features: list[FeatureSnapshot]
    markets: list[MarketDefinition]
    quotes: list[MarketQuote]
    estimates: list[ModelEstimate]
    decisions: list[PaperDecision]
    receipts: list[Receipt]
    cash_usd: Money
    order_count: int = Field(default=0, ge=0)
    fill_count: int = Field(default=0, ge=0)
    warnings: list[str]
    venue_context: VenueContext


class StreamEnvelope(RunRecord):
    sequence: int = Field(ge=1)
    generated_at: AwareDatetime
    type: Literal["snapshot"] = "snapshot"
    payload: DashboardSnapshot

    @model_validator(mode="after")
    def consistent_references(self):
        p = self.payload
        if p.run_id != self.run_id:
            raise ValueError("wrong payload run")
        if p.order_count != len(p.execution.orders) or p.fill_count != len(p.execution.fills):
            raise ValueError("execution counts disagree")
        if any(o.run_id != self.run_id for o in p.execution.orders) or any(t.run_id != self.run_id for t in p.execution.traces):
            raise ValueError("foreign execution run")
        order_ids = {o.order_id for o in p.execution.orders}
        if len(order_ids) != p.order_count or len({f.fill_id for f in p.execution.fills}) != p.fill_count:
            raise ValueError("duplicate execution records")
        if any(f.order_id not in order_ids for f in p.execution.fills) or any(t.order_id not in order_ids for t in p.execution.traces):
            raise ValueError("unresolved execution order")
        for field in ("windows", "claims", "features", "estimates", "decisions", "receipts"):
            if any(r.run_id != self.run_id for r in getattr(p, field)):
                raise ValueError(f"foreign run in {field}")
        windows = {w.window_id: w for w in p.windows}
        claims = {c.claim_id: c for c in p.claims}
        reaction_ids = set()
        reaction_observations = set()
        for reaction in p.reactions:
            if reaction.run_id != self.run_id or reaction.window_id not in windows:
                raise ValueError("foreign or unresolved reaction")
            window = windows[reaction.window_id]
            if reaction.observation_id != window.observation_id or reaction.stream_id != window.stream_id or reaction.supporting_text not in window.raw_text:
                raise ValueError("unsupported reaction provenance")
            if reaction.reaction_id in reaction_ids or reaction.observation_id in reaction_observations:
                raise ValueError("duplicate reaction")
            reaction_ids.add(reaction.reaction_id)
            reaction_observations.add(reaction.observation_id)
            if reaction.supported_claim_id:
                claim = claims.get(reaction.supported_claim_id)
                if claim is None or claim.window_id != reaction.window_id or claim.sentiment is None or claim.target != "game":
                    raise ValueError("reaction references an unsupported quality claim")
        features = {f.feature_id: f for f in p.features}
        markets = {m.market_id for m in p.markets}
        quotes = {q.quote_id: q for q in p.quotes}
        estimates = {e.estimate_id: e for e in p.estimates}
        decisions = {d.decision_id: d for d in p.decisions}
        streams = {s.stream_id for s in p.streams}
        for field, key in (("windows", "window_id"), ("claims", "claim_id"), ("features", "feature_id"), ("quotes", "quote_id"), ("estimates", "estimate_id"), ("decisions", "decision_id"), ("receipts", "receipt_id")):
            records = getattr(p, field)
            if len({getattr(r, key) for r in records}) != len(records):
                raise ValueError(f"duplicate IDs in {field}")
        for w in p.windows:
            if w.stream_id not in streams:
                raise ValueError("unresolved window stream")
        for q in p.quotes:
            if q.market_id not in markets:
                raise ValueError("unresolved quote market")
        for c in p.claims:
            if c.window_id not in windows or c.stream_id not in streams or c.supporting_quote not in windows[c.window_id].raw_text:
                raise ValueError("unresolved or unsupported claim")
        for f in p.features:
            if len(set(f.claim_ids)) != len(f.claim_ids) or not set(f.claim_ids) <= claims.keys():
                raise ValueError("invalid feature references")
        for e in p.estimates:
            if e.market_id not in markets or e.quote_id not in quotes or not set(e.feature_ids) <= features.keys() or quotes[e.quote_id].market_id != e.market_id:
                raise ValueError("unresolved estimate")
        for d in p.decisions:
            if d.estimate_id not in estimates or d.quote_id not in quotes or d.market_id != estimates[d.estimate_id].market_id:
                raise ValueError("unresolved decision")
        for r in p.receipts:
            if not set(r.window_ids) <= windows.keys() or not set(r.claim_ids) <= claims.keys() or not set(r.feature_ids) <= features.keys() or r.estimate_id not in estimates or r.decision_id not in decisions or r.quote_id not in quotes:
                raise ValueError("unresolved receipt")
        return self


class RunCommand(Contract):
    command_id: ID
    action: Literal["reset", "replay_observation", "play", "pause", "seek", "set_speed", "exit"]
    position_seconds: Nonnegative | None = None
    speed: Annotated[float, Field(gt=0, le=5)] | None = None

    @model_validator(mode="after")
    def fields_for_action(self):
        if (self.action == "seek") != (self.position_seconds is not None):
            raise ValueError("position_seconds is required only for seek")
        if (self.action == "set_speed") != (self.speed is not None):
            raise ValueError("speed is required only for set_speed")
        return self


class CreateRunRequest(Contract):
    command_id: ID
    scenario: Literal["foundation", "recordings", "courtroom-praise", "technical-failure-laughter", "skill-rage-controls", "mixed-missing-facecam", "duplicate-reconnect", "venue-outage-reset"] | None = None


class ScenarioRequest(Contract):
    command_id: ID
    scenario: Literal["courtroom-praise", "technical-failure-laughter", "skill-rage-controls", "mixed-missing-facecam", "duplicate-reconnect", "venue-outage-reset"]


class CommandResult(Contract):
    command_id: ID
    run_id: ID
    previous_run_id: ID | None = None
    duplicate_observation: bool = False


class TwitchGameContext(Contract):
    status: Literal["live", "offline", "unavailable", "user_provided"]
    channel_login: ID | None = None
    game_id: ID | None = None
    game_name: str | None = None
    source: Literal["twitch_helix", "manual"] = "twitch_helix"
    observed_at: AwareDatetime
    reason: str | None = None


class LiveAudioSentimentSignal(Contract):
    """Live speech interpretation, separate from recorded proxy claims and pricing."""
    schema_version: Literal["1"] = "1"
    signal_id: ID
    source_window_id: ID
    stream_id: ID
    evidence_mode: Literal["live"] = "live"
    start_seconds: Nonnegative
    end_seconds: Nonnegative
    event_start_at: AwareDatetime
    event_end_at: AwareDatetime
    text: Annotated[str, Field(min_length=1, max_length=2000)]
    aspect: Aspect
    target: Target
    sentiment: Score | None
    abstention_reason: str | None = None
    semantic_confidence: Probability | None = None
    classifier_name: ID
    classifier_version: ID
    speaker_role: Literal["unknown", "streamer"] = "unknown"
    status: Literal["candidate", "abstain"]

    @model_validator(mode="after")
    def signal_state(self):
        if self.end_seconds <= self.start_seconds or self.event_end_at <= self.event_start_at:
            raise ValueError("live sentiment signal interval must have positive duration")
        if self.sentiment is None and not self.abstention_reason:
            raise ValueError("null live sentiment requires an abstention reason")
        if (self.sentiment is None) != (self.status == "abstain"):
            raise ValueError("live sentiment status must match sentiment availability")
        if self.sentiment is not None and self.speaker_role != "streamer":
            raise ValueError("only explicitly attributed streamer speech can carry sentiment")
        return self


class LiveMarketCandidate(Contract):
    market_id: ID
    ticker: ID
    event_ticker: ID
    series_ticker: ID
    category: Literal["video_games", "esports"]
    event_title: ID
    market_title: ID
    outcome_name: ID
    matched_game_name: ID
    match_method: Literal["game-yes-outcome-exact-v1"]
    match_rationale: ID
    market_status: ID
    market_is_open: bool = True
    rules_primary: str | None = None
    rules_secondary: str | None = None
    yes_bid: Price | None = None
    yes_ask: Price | None = None
    no_bid: Price | None = None
    no_ask: Price | None = None
    yes_bid_size: Nonnegative | None = None
    yes_ask_size: Nonnegative | None = None
    no_bid_size: Nonnegative | None = None
    no_ask_size: Nonnegative | None = None
    quote_mode: Literal["live", "cached_stale"]
    is_stale: bool
    captured_at: AwareDatetime
    source_ref: ID
    missing_reasons: dict[str, str] = Field(default_factory=dict)


class LiveDecisionReview(Contract):
    """Explicit live-route abstention; distinct from proxy estimates and paper orders."""
    review_id: ID
    market_id: ID
    status: Literal["abstain"] = "abstain"
    model_version: ID = "live-outcome-router-v1"
    calibration_status: Literal["not_estimated"] = "not_estimated"
    execution_mode: Literal["paper"] = "paper"
    reasons: list[ID]


class LiveMarketContext(Contract):
    schema_version: Literal["1"] = "1"
    discovery_id: ID
    observed_at: AwareDatetime
    discovery_status: Literal["matched", "stream_offline", "twitch_unavailable", "no_game_category", "no_matching_markets", "kalshi_unavailable"]
    twitch: TwitchGameContext
    game_source: Literal["twitch_helix", "manual"] = "twitch_helix"
    market_source: Literal["kalshi_public_api"] = "kalshi_public_api"
    market_error: str | None = None
    candidates: list[LiveMarketCandidate] = Field(default_factory=list)
    decision_reviews: list[LiveDecisionReview] = Field(default_factory=list)

"""Reference Pydantic v2 contracts for G1 adoption, not an application runtime."""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1"
Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
SignedScore = Annotated[float, Field(ge=-1, le=1, allow_inf_nan=False)]
Finite = Annotated[float, Field(allow_inf_nan=False)]
Price = Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)]
Money = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
Quantity = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
EvidenceMode = Literal["live", "recorded", "synthetic_replay"]
QuoteMode = Literal["live", "cached_stale", "synthetic_replay"]
Aspect = Literal[
    "narrative", "gameplay", "presentation", "technical_quality",
    "online_experience", "overall", "irrelevant_unclear"
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class RunRecord(Contract):
    schema_version: Literal["1"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)


class ModalityAvailability(Contract):
    modality: Literal["speech", "chat", "emotes", "visual_context"]
    available: bool
    quality: Probability | None = None
    reason: str | None = None


class SourceWindow(RunRecord):
    window_id: str
    stream_id: str
    game_id: str
    evidence_mode: EvidenceMode
    event_start: AwareDatetime
    event_end: AwareDatetime
    available_at: AwareDatetime
    source_ref: str
    source_offset_seconds: Finite | None = None
    transcript: str | None = None
    language: str | None = None
    modalities: list[ModalityAvailability] = Field(default_factory=list)
    scene_candidate: str | None = None
    scene_confidence: Probability | None = None
    platform: str | None = None
    game_build: str | None = None

    @model_validator(mode="after")
    def ordered_interval(self):
        if self.event_end < self.event_start:
            raise ValueError("event_end precedes event_start")
        return self


class EvidenceClaim(RunRecord):
    claim_id: str
    revision: int = Field(default=1, ge=1)
    supersedes_claim_id: str | None = None
    window_id: str
    stream_id: str
    game_id: str
    evidence_mode: EvidenceMode
    event_at: AwareDatetime
    available_at: AwareDatetime
    source_modality: Literal["speech", "chat", "emotes", "visual_context"]
    aspect: Aspect
    subaspect: str | None = None
    target: Literal[
        "game", "scene", "streamer_skill", "story_character",
        "streamer_or_chat", "unrelated", "ambiguous"
    ]
    sentiment: SignedScore | None = None
    defect_severity: Probability | None = None
    explicitness: Literal["explicit", "contextual", "unclear"]
    extraction_confidence: Probability
    attribution_confidence: Probability
    supporting_quote: str | None = None
    abstention_reason: str | None = None
    scene_id: str | None = None
    dependency_group_id: str | None = None
    extractor_version: str


class EvidenceGroup(RunRecord):
    group_id: str
    revision: int = Field(default=1, ge=1)
    game_id: str
    scene_id: str | None
    match_confidence: Probability
    claim_ids: list[str]
    stream_ids: list[str]
    dependency_group_ids: list[str] = Field(default_factory=list)
    platform: str | None = None
    game_build: str | None = None


class MarketDefinition(Contract):
    ticker: str
    event_ticker: str
    title: str
    game_id: str
    rules_primary: str
    rules_secondary: str | None = None
    rules_url: str | None = None
    market_url: str | None = None
    closes_at: AwareDatetime | None = None
    outcome_group: str | None = None
    constraint: Literal["binary", "threshold", "exclusive_winner"] = "binary"
    threshold: Finite | None = None
    definition_version: str


class QuoteLevel(Contract):
    price: Price
    quantity: Quantity


class MarketQuote(RunRecord):
    quote_id: str
    ticker: str
    quote_mode: QuoteMode
    captured_at: AwareDatetime
    available_at: AwareDatetime
    venue_timestamp: AwareDatetime | None = None
    venue_status: str
    is_stale: bool
    yes_bid: Price | None = None
    yes_ask: Price | None = None
    no_bid: Price | None = None
    no_ask: Price | None = None
    yes_ask_quantity: Quantity | None = None
    no_ask_quantity: Quantity | None = None
    yes_bid_quantity: Quantity | None = None
    no_bid_quantity: Quantity | None = None
    yes_ask_depth: list[QuoteLevel] = Field(default_factory=list)
    no_ask_depth: list[QuoteLevel] = Field(default_factory=list)
    yes_bid_depth: list[QuoteLevel] = Field(default_factory=list)
    no_bid_depth: list[QuoteLevel] = Field(default_factory=list)
    source_ref: str

    @model_validator(mode="after")
    def valid_spreads(self):
        for side in ("yes", "no"):
            bid, ask = getattr(self, side + "_bid"), getattr(self, side + "_ask")
            if bid is not None and ask is not None and bid > ask:
                raise ValueError(side + " bid exceeds ask")
        return self


class FeatureSnapshot(RunRecord):
    feature_id: str
    game_id: str
    aspect: Aspect
    as_of: AwareDatetime
    claim_ids: list[str]
    absolute_sentiment: SignedScore | None = None
    mean_z: Finite | None = None
    defect_severity: Probability | None = None
    baseline_ready: bool
    valid_stream_count: int = Field(ge=0)
    independent_group_count: int = Field(ge=0)
    scene_count: int = Field(ge=0)
    effective_source_diagnostic: Finite | None = None
    disagreement: Finite | None = None
    coverage_note: str | None = None
    baseline_version: str
    evidence_modes: list[EvidenceMode]
    features: dict[str, Finite | None] = Field(default_factory=dict)


class ModelEstimate(RunRecord):
    estimate_id: str
    ticker: str
    quote_id: str
    feature_ids: list[str]
    as_of: AwareDatetime
    market_reference_probability: Probability
    correction_log_odds: Finite
    model_probability: Probability
    model_version: str
    calibration_status: Literal["heuristic", "validated"]
    uncertainty_status: Literal["not_estimated", "sensitivity_only", "validated"]
    uncertainty_note: str | None = None
    receipt_id: str


class PaperDecision(RunRecord):
    decision_id: str
    estimate_id: str
    quote_id: str
    ticker: str
    as_of: AwareDatetime
    execution_mode: Literal["paper"] = "paper"
    side: Literal["yes", "no"] | None
    action: Literal["candidate", "buy", "exit", "hold", "blocked"]
    quantity: Quantity
    estimated_ev_per_contract: Decimal | None = None
    estimated_total_fee: Money | None = None
    reason: str
    receipt_id: str


class PaperOrder(RunRecord):
    order_id: str
    intent_id: str
    decision_id: str
    ticker: str
    side: Literal["yes", "no"]
    action: Literal["buy", "sell"]
    quantity: Quantity
    limit_price: Price | None
    created_at: AwareDatetime
    status: Literal["pending", "partial", "filled", "cancelled", "rejected"]
    execution_mode: Literal["paper"] = "paper"


class PaperFill(RunRecord):
    fill_id: str
    order_id: str
    quote_id: str
    filled_at: AwareDatetime
    quantity: Quantity
    price: Price
    fee: Money
    quote_mode: QuoteMode
    fee_schedule_version: str


class Position(RunRecord):
    ticker: str
    side: Literal["yes", "no"]
    quantity: Quantity
    average_entry_price: Price
    entry_fees: Money
    liquidation_bid: Price | None
    estimated_exit_fee: Money | None
    unrealised_pnl: Decimal | None
    realised_pnl: Decimal


class Receipt(RunRecord):
    receipt_id: str
    created_at: AwareDatetime
    summary: str
    claim_ids: list[str]
    feature_ids: list[str]
    quote_ids: list[str]
    estimate_id: str | None
    decision_id: str | None
    order_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SourceStatus(Contract):
    stream_id: str
    evidence_mode: EvidenceMode
    state: Literal["ready", "warming_up", "degraded", "offline", "paused"]
    last_available_at: AwareDatetime | None = None
    note: str | None = None


class DashboardSnapshot(RunRecord):
    generated_at: AwareDatetime
    evidence_modes: list[EvidenceMode]
    quote_modes: list[QuoteMode]
    execution_mode: Literal["paper"] = "paper"
    calibration_status: Literal["heuristic", "validated"]
    streams: list[SourceStatus] = Field(default_factory=list)
    markets: list[MarketDefinition] = Field(default_factory=list)
    quotes: list[MarketQuote] = Field(default_factory=list)
    claims: list[EvidenceClaim] = Field(default_factory=list)
    features: list[FeatureSnapshot] = Field(default_factory=list)
    estimates: list[ModelEstimate] = Field(default_factory=list)
    decisions: list[PaperDecision] = Field(default_factory=list)
    orders: list[PaperOrder] = Field(default_factory=list)
    fills: list[PaperFill] = Field(default_factory=list)
    positions: list[Position] = Field(default_factory=list)
    receipts: list[Receipt] = Field(default_factory=list)
    cash_usd: Money
    equity_usd: Decimal | None
    warnings: list[str] = Field(default_factory=list)


class StreamEnvelope(RunRecord):
    sequence: int = Field(ge=0)
    generated_at: AwareDatetime
    type: Literal["snapshot"] = "snapshot"
    payload: DashboardSnapshot

    @model_validator(mode="after")
    def consistent_run(self):
        if self.payload.run_id != self.run_id:
            raise ValueError("envelope and payload run_id differ")
        for name in (
            "quotes", "claims", "features", "estimates", "decisions",
            "orders", "fills", "positions", "receipts"
        ):
            if any(item.run_id != self.run_id for item in getattr(self.payload, name)):
                raise ValueError(name + " contains another run")
        return self


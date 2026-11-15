"""Small, real G1 calculation over one cached fixture; not the G2 feature engine/broker."""
import math
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING

from .clock import ReplayClock
from .identity import digest, stable_id
from .schemas import (
    DashboardSnapshot, EvidenceCache, EvidenceClaim, FeatureSnapshot, MarketDefinition,
    MarketQuote, ModelEstimate, ModalityAvailability, PaperDecision, Receipt,
    SourceStatus, SourceWindow, VenueContext,
)


def build_snapshot(run_id: str, cache: EvidenceCache, fixture: dict,
                   model: dict, limits: dict, venue: VenueContext) -> DashboardSnapshot:
    observation = cache.observations[0]
    if observation.sentiment is None:
        raise ValueError("G1 fixture must contain an attributable annotation; no neutral substitution")
    origin = datetime.fromisoformat(fixture["replay_origin"].replace("Z", "+00:00"))
    clock = ReplayClock(origin)
    clock.advance_to(origin + timedelta(seconds=observation.replay_seconds))
    now = clock.now()
    window = SourceWindow(
        run_id=run_id, window_id=stable_id("window", observation.observation_id),
        stream_id=observation.stream_id, asset_id=observation.asset_id,
        evidence_mode=observation.evidence_mode, event_at=now, available_at=now,
        source_media_seconds=observation.media_seconds, replay_seconds=observation.replay_seconds,
        raw_text=observation.raw_text, cache_key=cache.cache_key,
        observation_id=observation.observation_id, provider=observation.provider,
        frame_ref=observation.frame_ref, frame_reason=observation.frame_reason,
        modalities=[
            ModalityAvailability(modality="chat", available=True, reason="Supplied fixture text, not observed OCR"),
            ModalityAvailability(modality="speech", available=False, reason="No transcription supplied or run"),
            ModalityAvailability(modality="facecam", available=False, reason="No video supplied; no face-derived pricing"),
        ],
    )
    claim = EvidenceClaim(
        run_id=run_id, claim_id=stable_id("claim", window.window_id, observation.extractor_version),
        window_id=window.window_id, stream_id=window.stream_id,
        evidence_mode=window.evidence_mode, sentiment=observation.sentiment,
        supporting_quote=observation.supporting_quote, scene_id=observation.scene_id,
        extractor_version=observation.extractor_version,
    )
    seed, settings = fixture["baseline"], model["normalization"]
    if seed["count"] < settings["warmup_valid_buckets"]:
        raise ValueError("G1 seeded baseline is unready; warmup must not fabricate z")
    delta = claim.sentiment - seed["mean"]
    z = max(-settings["z_clip"], min(settings["z_clip"], delta / max(math.sqrt(seed["variance"]), settings["std_floor"])))
    alpha = 1 - math.exp(-settings["bucket_seconds"] / settings["ewma_time_constant_seconds"])
    feature = FeatureSnapshot(
        run_id=run_id, feature_id=stable_id("feature", run_id, claim.claim_id, model["model_version"], seed),
        claim_ids=[claim.claim_id], absolute_sentiment=claim.sentiment, mean_z=z,
        baseline_version=seed["version"], previous_mean=seed["mean"], previous_variance=seed["variance"],
        updated_mean=seed["mean"] + alpha * delta,
        updated_variance=(1 - alpha) * (seed["variance"] + alpha * delta * delta),
        baseline_count=seed["count"] + 1, unique_observation_count=1,
        effective_source_diagnostic=1, as_of=now,
    )
    market = MarketDefinition(
        market_id=f"synthetic:{fixture['scenario_version']}:narrative", market_namespace="synthetic",
        title="Narrative scenario · GTA V proxy", venue_ticker=None,
        reference_venue_ticker=None,
        rules_primary="Synthetic $1 binary-payout scenario. GTA V proxy evidence is for demonstration only. No venue settlement or GTA VI forecasting claim.",
        definition_version="proxy-scenario-v1",
    )
    quote = MarketQuote(
        quote_id=stable_id("quote", market.market_id, fixture["quote"]), market_id=market.market_id,
        quote_mode="synthetic_replay", captured_at=now, venue_status="active", is_stale=False,
        source_ref="config/foundation_scenario.json#quote", **fixture["quote"],
    )
    midpoint = float((quote.yes_bid + quote.yes_ask) / Decimal(2))
    if not 0 < midpoint < 1 or quote.yes_ask - quote.yes_bid > Decimal("0.05"):
        raise ValueError("invalid synthetic anchor; no estimate fabricated")
    coefficients = model["illustrative_coefficients"]["gta_narrative_2026"]
    correction = coefficients["narrative_absolute"] * feature.absolute_sentiment + coefficients["narrative_z"] * feature.mean_z
    correction = max(-model["correction_cap_log_odds"], min(model["correction_cap_log_odds"], correction))
    probability = 1 / (1 + math.exp(-(math.log(midpoint / (1 - midpoint)) + correction)))
    estimate = ModelEstimate(
        run_id=run_id, estimate_id=stable_id("estimate", run_id, feature.feature_id, quote.quote_id, coefficients),
        market_id=market.market_id, quote_id=quote.quote_id, feature_ids=[feature.feature_id],
        market_reference_probability=midpoint, correction_log_odds=correction,
        model_probability=probability, relevance=1.0, model_version=model["model_version"], coefficients=coefficients,
    )
    quantity = Decimal(fixture["requested_quantity"])
    if quantity <= 0:
        raise ValueError("candidate quantity must be positive")
    fee = (quantity * Decimal(fixture["simulation_fee_per_contract"])).quantize(Decimal("0.01"), rounding=ROUND_CEILING)
    fair = Decimal(str(probability))
    yes_ev = fair - quote.yes_ask - fee / quantity
    no_ev = Decimal(1) - fair - quote.no_ask - fee / quantity
    side = "yes" if yes_ev > no_ev else "no"
    reasons = ["G1 candidate only; paper broker is not implemented.", "GTA V proxy demo is not evidence about GTA VI.", "Quote, fee and baseline are synthetic scenario inputs; executable depth is not modelled."]
    if max(yes_ev, no_ev) < Decimal(limits["min_net_ev_per_contract"]):
        reasons.append(f"Net EV below ${limits['min_net_ev_per_contract']} per-contract entry threshold.")
    decision = PaperDecision(
        run_id=run_id, decision_id=stable_id("decision", run_id, estimate.estimate_id, limits["version"]),
        estimate_id=estimate.estimate_id, quote_id=quote.quote_id, market_id=market.market_id,
        side=side, quantity=quantity, yes_ev_per_contract=yes_ev, no_ev_per_contract=no_ev,
        estimated_total_fee=fee, fee_schedule_version="simulation-linear-v1", reasons=reasons,
    )
    receipt = Receipt(
        run_id=run_id, receipt_id=stable_id("receipt", run_id, decision.decision_id),
        window_ids=[window.window_id], claim_ids=[claim.claim_id], feature_ids=[feature.feature_id],
        estimate_id=estimate.estimate_id, decision_id=decision.decision_id, quote_id=quote.quote_id,
        explanation=[
            f"Source: supplied GTA V proxy chat fixture at media {window.source_media_seconds:g}s; aligned replay {window.replay_seconds:g}s.",
            f"Absolute sentiment {feature.absolute_sentiment:g}; pre-update z {z:g}; seeded baseline count {seed['count']} -> {feature.baseline_count}.",
            f"Scenario-only relevance 1; relevance to actual GTA VI contracts is 0. Correction = .2×absolute + .05×z = {correction:.6f}, capped at ±.5.",
            f"Synthetic Yes midpoint {midpoint:.6f}; sigmoid(logit(midpoint) + correction) = {probability:.9f}.",
            f"No EV = 1 - p - No ask - total fee/Q = {no_ev}; Decimal money, no additional spread charge.",
            "The venue-context quotes never enter this computation. Replaying the same ID does not update the baseline.",
        ], limitations=["OCR and semantic annotation are fixture supplied.", "One observation; no corroboration or calibrated uncertainty.", "No orders, fills or accounting broker at G1."],
    )
    return DashboardSnapshot(
        run_id=run_id, replay_time=now, cache_key=cache.cache_key, configuration_fingerprint=digest((cache.cache_key, model, limits)), recording_manifest=cache.manifest,
        streams=[SourceStatus(stream_id=a.stream_id, label=a.label,
            state="fixture_ready" if a.stream_id == window.stream_id else "recording_missing",
            reason=a.availability_reason or "Local recording configured") for a in cache.manifest.recordings],
        windows=[window], claims=[claim], features=[feature], markets=[market], quotes=[quote],
        estimates=[estimate], decisions=[decision], receipts=[receipt], cash_usd=limits["bankroll"],
        warnings=["GTA V proxy demo evidence — not GTA VI gameplay.", "No recordings supplied: one cached synthetic chat fixture.", "Candidate-only G1 slice; actual OCR, 2–6 video playback and paper broker remain future work."],
        venue_context=venue,
    )

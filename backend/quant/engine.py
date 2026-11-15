"""Rebuildable unique evidence view and bounded synthetic scenario estimates.

This module does not own a clock, database or publishing task. Every projection
uses its caller's aware ``as_of`` time and available source records.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_CEILING
import math
from typing import Mapping, Sequence

from backend.core.config import read_config
from backend.core.identity import stable_id
from backend.core.schemas import EvidenceClaim, FeatureSnapshot, MarketQuote, ModelEstimate, PaperDecision, SourceWindow
from .normalization import Baseline, Normalized, normalize


@dataclass(frozen=True)
class Evaluation:
    features: list[FeatureSnapshot]
    estimate: ModelEstimate | None
    decision: PaperDecision | None
    reasons: list[str]


@dataclass(frozen=True)
class _Bucket:
    key: tuple
    claims: tuple[EvidenceClaim, ...]
    event_at: datetime
    available_at: datetime
    quality: float
    dependency_group: str
    normalized: Normalized


class FeatureEngine:
    """In-memory ingestion seam; restore by ingesting immutable root records.

    A claim ID is immutable at a revision. Higher revisions replace it; when
    extractors mint new claim IDs the latest revision of a source window and
    aspect/modality replaces the old interpretation when projecting.
    """

    def __init__(self, run_id: str):
        self.run_id = run_id
        self._windows: dict[str, SourceWindow] = {}
        self._claims: dict[str, EvidenceClaim] = {}

    def add_window(self, window: SourceWindow) -> bool:
        if window.run_id != self.run_id:
            raise ValueError("foreign run source window")
        existing = self._windows.get(window.window_id)
        if existing is not None and existing != window:
            raise ValueError("source window ID reused with changed payload")
        self._windows[window.window_id] = window
        return existing is None

    def ingest(self, claim: EvidenceClaim) -> bool:
        if claim.run_id != self.run_id:
            raise ValueError("foreign run claim")
        if claim.window_id not in self._windows:
            raise ValueError("claim source window is missing")
        source = self._windows[claim.window_id]
        if claim.stream_id != source.stream_id or claim.evidence_mode != source.evidence_mode:
            raise ValueError("claim source identity/provenance disagrees with its window")
        if claim.supporting_quote not in source.raw_text:
            raise ValueError("claim quote is not supported by its source text")
        existing = self._claims.get(claim.claim_id)
        if existing is not None:
            if existing.revision > claim.revision:
                return False
            if existing.revision == claim.revision:
                if existing != claim:
                    raise ValueError("claim ID and revision reused with changed payload")
                return False
        self._claims[claim.claim_id] = claim
        return True

    def snapshot(self, as_of: datetime, *, seed_baseline: Mapping | None = None) -> list[FeatureSnapshot]:
        return _features(self.run_id, list(self._windows.values()), list(self._claims.values()), as_of, seed_baseline)


def _aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")


def _weighted(values: Sequence[tuple[float, float]]) -> float:
    denominator = sum(weight for _, weight in values)
    if denominator <= 0:
        raise ValueError("no positive feature weights")
    return sum(value * weight for value, weight in values) / denominator


def _features(run_id: str, windows: Sequence[SourceWindow], claims: Sequence[EvidenceClaim], as_of: datetime, seed: Mapping | None) -> list[FeatureSnapshot]:
    _aware(as_of)
    # Canonical ingestion rejects ID conflicts instead of silently taking the
    # last item in an input list. No caller iteration order influences results.
    engine = FeatureEngine(run_id)
    for window in windows:
        engine.add_window(window)
    for claim in claims:
        engine.ingest(claim)
    eligible = []
    for claim in engine._claims.values():
        source = engine._windows[claim.window_id]
        if source.available_at <= as_of and source.event_at <= as_of:
            eligible.append(claim)
    latest: dict[tuple, int] = {}
    for claim in eligible:
        key = (claim.window_id, claim.aspect, claim.source_modality)
        latest[key] = max(latest.get(key, 0), claim.revision)
    groups: dict[tuple, list[EvidenceClaim]] = defaultdict(list)
    for claim in eligible:
        if claim.revision != latest[(claim.window_id, claim.aspect, claim.source_modality)]:
            continue
        if claim.target != "game" or claim.sentiment is None or claim.quality <= 0:
            continue
        source = engine._windows[claim.window_id]
        key = (claim.stream_id, claim.aspect, claim.source_modality, int(source.replay_seconds // 10))
        groups[key].append(claim)
    ordered = sorted(groups.items(), key=lambda item: (
        max(engine._windows[c.window_id].available_at for c in item[1]),
        max(engine._windows[c.window_id].event_at for c in item[1]),
        item[0],
    ))
    initial = Baseline(**{**dict(seed), "seeded": True}) if seed is not None else Baseline()
    baselines: dict[tuple, Baseline] = {}
    buckets: list[_Bucket] = []
    for key, members in ordered:
        members = sorted(members, key=lambda c: c.claim_id)
        # All claims in a stream/aspect/modality/10s bucket cause one update,
        # including when the source bucket crosses multiple manual scenes.
        value = _weighted([(c.sentiment, c.quality) for c in members])
        baseline_key = key[:3]
        norm = normalize(value, baselines.get(baseline_key, initial))
        baselines[baseline_key] = norm.updated
        dep_groups = {c.dependency_group or c.stream_id for c in members}
        dependency = next(iter(dep_groups)) if len(dep_groups) == 1 else key[0]
        buckets.append(_Bucket(
            key, tuple(members), max(engine._windows[c.window_id].event_at for c in members),
            max(engine._windows[c.window_id].available_at for c in members),
            sum(c.quality for c in members) / len(members), dependency, norm,
        ))
    by_aspect: dict[str, list[_Bucket]] = defaultdict(list)
    for bucket in buckets:
        by_aspect[bucket.key[1]].append(bucket)
    features = []
    for aspect, members in sorted(by_aspect.items()):
        # Collapse explicitly linked rebroadcasts and speech/chat into one
        # dependency contribution. Raw message/source count never multiplies
        # the cap, and no sqrt(N) term is used.
        dependencies: dict[str, list[_Bucket]] = defaultdict(list)
        for bucket in members:
            dependencies[bucket.dependency_group].append(bucket)
        contributions = []
        z_contributions = []
        for dep, source_buckets in sorted(dependencies.items()):
            weighted = [(b, b.quality, 2 ** (-max(0, (as_of - b.event_at).total_seconds()) / 300)) for b in source_buckets]
            denom = sum(w for _, w, _ in weighted)
            decayed = sum(w * age for _, w, age in weighted)
            if decayed <= 0 or denom <= 0:
                continue
            mean = sum(b.normalized.absolute * w * age for b, w, age in weighted) / decayed
            freshness = decayed / denom
            cap = min(1.0, denom / len(source_buckets))
            contributions.append((mean, freshness, cap))
            ready = [(b, w, age) for b, w, age in weighted if b.normalized.z is not None]
            if ready:
                z_weight = sum(w * age for _, w, age in ready)
                if z_weight > 0:
                    z_mean = sum(b.normalized.z * w * age for b, w, age in ready) / z_weight
                    # Warmup coverage attenuates z; missing z is never zero.
                    z_contributions.append((z_mean, z_weight / denom, cap))
        if not contributions:
            continue
        base_weight = sum(w for _, _, w in contributions)
        decayed_weight = sum(f * w for _, f, w in contributions)
        absolute = sum(m * f * w for m, f, w in contributions) / decayed_weight
        freshness = decayed_weight / base_weight
        z_den = sum(f * w for _, f, w in z_contributions)
        z = sum(m * f * w for m, f, w in z_contributions) / z_den if z_den > 0 else None
        z_freshness = z_den / base_weight if z is not None else 0.0
        last = members[-1].normalized
        claim_ids = sorted({c.claim_id for b in members for c in b.claims})
        stream_ids = sorted({b.key[0] for b in members})
        status = "seeded_fixture" if initial.seeded else "ready" if all(b.normalized.z is not None for b in members) else "warming_up"
        # Status describes the latest source baselines, not historic warmup
        # records that remain legitimately in the decayed evidence view.
        if not initial.seeded:
            status = "ready" if all(v.count > 20 for k, v in baselines.items() if k[1] == aspect) else "warming_up"
        feature_fields = dict(
            run_id=run_id, feature_id=stable_id("feature", run_id, aspect, initial, [(c.claim_id, c.revision) for b in members for c in b.claims], as_of.isoformat()),
            claim_ids=claim_ids, absolute_sentiment=absolute, mean_z=z, baseline_status=status,
            baseline_version=initial.version, previous_mean=last.previous.mean, previous_variance=last.previous.variance,
            updated_mean=last.updated.mean, updated_variance=last.updated.variance,
            baseline_count=last.updated.count, unique_observation_count=len(members),
            effective_source_diagnostic=base_weight ** 2 / sum(w * w for _, _, w in contributions),
            as_of=as_of, aspect=aspect,
            source_modality=members[0].key[2] if len({b.key[2] for b in members}) == 1 else "mixed",
            stream_ids=stream_ids, freshness=freshness,
            z_reason="Fewer than 20 prior valid buckets in every contributing baseline; no seed supplied." if z is None else None,
        )
        additions = dict(z_freshness=z_freshness, disagreement=math.sqrt(sum(w * (m - absolute) ** 2 for m, _, w in contributions) / base_weight), unique_stream_count=len(stream_ids))
        feature_fields.update({k: v for k, v in additions.items() if k in FeatureSnapshot.model_fields})
        features.append(FeatureSnapshot(**feature_fields))
    return features


def evaluate(
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
) -> Evaluation:
    """Project candidate-only GTA V proxy evidence against synthetic quotes.

    ``relevance`` applies once outside normalized means. Coefficients remain
    scenario assumptions. This API never submits a paper or venue order.
    """
    features = _features(run_id, windows, claims, as_of, seed_baseline)
    reasons: list[str] = []
    if not math.isfinite(relevance) or not 0 <= relevance <= 1:
        raise ValueError("relevance must be nonnegative and at most one")
    model = dict(model or read_config("scenario_model.json"))
    limits = dict(limits or read_config("paper_limits.json"))
    age = (as_of - quote.captured_at).total_seconds()
    if not quote.market_id.startswith("synthetic:") or quote.quote_mode != "synthetic_replay":
        reasons.append("GTA V proxy evidence cannot price actual GTA VI venue contracts.")
    if quote.is_stale or quote.venue_status not in {"active", "open"} or age < 0 or age >= float(limits["max_quote_age_seconds"]):
        reasons.append("Reference quote is stale, inactive, or not yet available.")
    if quote.yes_bid is None or quote.yes_ask is None:
        reasons.append("A two-sided Yes quote is unavailable.")
    elif quote.yes_ask - quote.yes_bid > Decimal("0.05"):
        reasons.append("Reference Yes spread exceeds the synthetic 0.05 USD limit.")
    elif not 0 < (quote.yes_bid + quote.yes_ask) / 2 < 1:
        reasons.append("An endpoint quote cannot anchor a log-odds estimate.")
    coefficients = dict(model["illustrative_coefficients"]["gta_narrative_2026"])
    inputs: list[tuple[FeatureSnapshot, float]] = []
    for feature in features:
        absolute_name = f"{feature.aspect}_absolute"
        z_name = f"{feature.aspect}_z"
        correction = 0.0
        supported = False
        if absolute_name in coefficients:
            correction += float(coefficients[absolute_name]) * feature.absolute_sentiment * feature.freshness * relevance
            supported = True
        if feature.mean_z is not None and z_name in coefficients:
            correction += float(coefficients[z_name]) * feature.mean_z * getattr(feature, "z_freshness", feature.freshness) * relevance
            supported = True
        if supported and relevance > 0:
            inputs.append((feature, correction))
    if not inputs:
        reasons.append("No attributable configured aspect input with nonzero relevance is available.")
    if reasons:
        return Evaluation(features, None, None, reasons)
    anchor = float((quote.yes_bid + quote.yes_ask) / 2)
    cap = float(model["correction_cap_log_odds"])
    correction = max(-cap, min(cap, sum(value for _, value in inputs)))
    probability = 1 / (1 + math.exp(-(math.log(anchor / (1 - anchor)) + correction)))
    feature_ids = [feature.feature_id for feature, _ in inputs]
    estimate = ModelEstimate(
        run_id=run_id, estimate_id=stable_id("estimate", run_id, quote.quote_id, feature_ids, correction, model["model_version"]),
        market_id=quote.market_id, quote_id=quote.quote_id, feature_ids=feature_ids,
        market_reference_probability=anchor, correction_log_odds=correction, model_probability=probability,
        relevance=relevance, model_version=model["model_version"], coefficients=coefficients,
    )
    quantity = Decimal("10")
    fee = (Decimal("0.01") * quantity).quantize(Decimal("0.01"), rounding=ROUND_CEILING)
    fair = Decimal(str(probability))
    ev_yes = fair - quote.yes_ask - fee / quantity if quote.yes_ask is not None else None
    ev_no = 1 - fair - quote.no_ask - fee / quantity if quote.no_ask is not None else None
    options = [(side, value) for side, value in (("yes", ev_yes), ("no", ev_no)) if value is not None]
    if not options:
        return Evaluation(features, estimate, None, ["Both executable asks are unavailable; no paper candidate."])
    side, ev = max(options, key=lambda item: item[1])
    decision_reasons = ["GTA V proxy recording/fixture evaluation is candidate-only.", "Displayed top asks have no verified executable depth in this evaluation.", "Fee is the explicit simulation-linear-v1 assumption, not a venue fee."]
    if ev < Decimal(limits["min_net_ev_per_contract"]):
        decision_reasons.append("Best side is below the configured minimum net entry EV.")
    missing = {name: "Executable ask unavailable." for name, value in (("yes_ev_per_contract", ev_yes), ("no_ev_per_contract", ev_no)) if value is None}
    decision = PaperDecision(
        run_id=run_id, decision_id=stable_id("decision", run_id, estimate.estimate_id, quote.quote_id, side),
        estimate_id=estimate.estimate_id, quote_id=quote.quote_id, market_id=quote.market_id,
        side=side, quantity=quantity, yes_ev_per_contract=ev_yes, no_ev_per_contract=ev_no,
        estimated_total_fee=fee, fee_schedule_version="simulation-linear-v1", reasons=decision_reasons,
        ev_missing_reasons=missing,
    )
    return Evaluation(features, estimate, decision, ["Heuristic coefficients; scenario results are uncalibrated."])

"""Cached G2 evidence projection. No media/model work occurs during playback."""
from datetime import datetime, timedelta
from decimal import Decimal
from collections import OrderedDict
from .identity import stable_id
from .schemas import DashboardSnapshot, EvidenceGroup, MarketDefinition, MarketQuote, PlaybackState, Receipt, SourceStatus

_source_views = OrderedDict()


def source_view(run_id, cache, origin, config_key, policy):
    """Memoize immutable cached inputs; publication does not reclassify text.

    Retain the cache object in each bounded entry so object IDs cannot be reused
    while an entry exists. Distinct diagnostic cache copies remain independent.
    """
    from backend.ingestion.recordings import build_windows
    from backend.perception.claims import extract
    from .identity import digest
    from .reactions import build_reactions
    key = (run_id, id(cache), origin, config_key, digest(policy))
    if key not in _source_views:
        windows = build_windows(cache, run_id, origin)
        claims = [c for w in windows for c in extract(w)]
        reactions = build_reactions(windows, claims, policy)
        _source_views[key] = (cache, windows, claims, reactions)
        if len(_source_views) > 16:
            _source_views.popitem(last=False)
    _source_views.move_to_end(key)
    return _source_views[key][1:]


def duration(cache, metadata=None):
    assets = {a.asset_id: a for a in cache.manifest.recordings}
    values = [0.0, (metadata or {}).get("duration_seconds", 0)]
    for report in cache.asset_reports:
        asset = assets[report.asset_id]
        if report.available and report.duration_seconds is not None:
            end = min(report.duration_seconds, asset.media_end_seconds or report.duration_seconds)
            values.append(max(0, end - asset.media_start_seconds + asset.timeline_start_seconds))
    values.extend(o.available_replay_seconds if o.available_replay_seconds is not None else o.replay_seconds for o in cache.observations)
    return max(values)


def quote_row(metadata, position):
    eligible = [q for q in metadata.get("quote_timeline", []) if q["available_replay_seconds"] <= position and q["event_seconds"] <= position]
    return max(eligible, key=lambda q: (q["available_replay_seconds"], q["event_seconds"], q["event_id"])) if eligible else None


def project(run_id, cache, position, speed, playing, config_key, venue, metadata=None):
    from backend.quant import evaluate
    metadata = metadata or {}
    origin = datetime.fromisoformat(metadata.get("origin", "2026-11-14T20:30:00+00:00").replace("Z", "+00:00"))
    now = origin + timedelta(seconds=position)
    from .reactions import reaction_policy
    policy = reaction_policy()
    all_windows, all_claims, all_reactions = source_view(run_id, cache, origin, config_key, policy)
    windows = [w for w in all_windows if w.available_at <= now and w.event_at <= now]
    available = {w.window_id for w in windows}
    claims = [c for c in all_claims if c.window_id in available]
    reactions = [r for r in all_reactions if r.window_id in available]
    market = MarketDefinition(market_id=f"synthetic:{metadata.get('scenario_version', 'gta5-recording-demo')}:narrative", market_namespace="synthetic",
        title="Narrative scenario / GTA V proxy", venue_ticker=None, reference_venue_ticker=None,
        rules_primary="Synthetic $1 binary-payout demonstration. Recorded GTA V material is proxy evidence only; it does not price an actual GTA VI market.", definition_version="recording-demo-v1")
    # Media demos use a declared flat synthetic timeline. Structured scenarios
    # consume their own explicit events, including the outage fixture.
    if "quote_timeline" in metadata:
        row = quote_row(metadata, position)
        quote_tick = row["event_seconds"] if row else 0
        values = {name: Decimal(row[name]) if row and row.get(name) is not None else None for name in ("yes_bid", "yes_ask", "no_bid", "no_ask")}
        stale = row is None or position - quote_tick >= 10
        source = row["event_id"] if row else "synthetic-quote-unavailable"
    else:
        quote_tick = int(position // 5) * 5
        values = dict(yes_bid=Decimal("0.14"), yes_ask=Decimal("0.15"), no_bid=Decimal("0.85"), no_ask=Decimal("0.86"))
        stale, source = False, "synthetic-flat-5s-timeline-v1"
    quote = MarketQuote(quote_id=stable_id("quote", cache.cache_key, source, quote_tick, stale), market_id=market.market_id,
        quote_mode="synthetic_replay", captured_at=origin + timedelta(seconds=quote_tick),
        venue_status=(row.get("venue_status", "active") if row else "active") if "quote_timeline" in metadata else "active", is_stale=stale, **values,
        missing_reasons={name: "No available synthetic timeline quote" for name, value in values.items() if value is None}, source_ref=source)
    result = evaluate(run_id, windows, claims, quote, now, seed_baseline=metadata.get("baseline"))
    # Keep all original feature diagnostics. An estimate can only reference
    # supported claims that also pass the independent attribution/relevance gate.
    eligible_ids = {r.supported_claim_id for r in reactions if r.pricing_eligible}
    if result.estimate:
        model_claim_ids = {cid for f in result.features if f.feature_id in result.estimate.feature_ids for cid in f.claim_ids}
        if not model_claim_ids <= eligible_ids:
            result = type(result)(result.features, None, None, [*result.reasons, "Reaction attribution/relevance policy excludes one or more model inputs."])
    used_claim_ids = {cid for f in result.features for cid in f.claim_ids} if result.estimate else set()
    reactions = [r.model_copy(update={"included_in_estimate": r.pricing_eligible and r.supported_claim_id in used_claim_ids,
        "exclusion_reason": "Eligible supported claim; current estimate unavailable (inspect quote/model reasons)." if r.pricing_eligible and r.supported_claim_id not in used_claim_ids else r.exclusion_reason}) for r in reactions]
    receipts = []
    if result.estimate is not None and result.decision is not None:
        ids = {c for f in result.features for c in f.claim_ids}
        used = [c for c in claims if c.claim_id in ids]
        receipts = [Receipt(run_id=run_id, receipt_id=stable_id("receipt", result.decision.decision_id),
            window_ids=sorted({c.window_id for c in used}), claim_ids=sorted(ids),
            feature_ids=[f.feature_id for f in result.features], estimate_id=result.estimate.estimate_id,
            decision_id=result.decision.decision_id, quote_id=quote.quote_id,
            explanation=["Cached source text -> conservative heuristic attribution -> unique source buckets -> market-relative scenario estimate.",
                "Absolute sentiment and pre-update rolling surprise are separate; unseeded sources need 20 valid buckets for surprise.",
                f"Anchor={result.estimate.market_reference_probability:.6f}; correction={result.estimate.correction_log_odds:.6f}; scenario={result.estimate.model_probability:.6f}.",
                *dict.fromkeys(w.confidence_reason for w in windows if w.source_modality == "speech" and w.window_id in {c.window_id for c in used} and w.confidence_reason),
                *result.decision.reasons],
            limitations=["GTA V proxy demonstration; no predictive validation for GTA VI.", "OCR and speech recognition may make errors. Inspect source frames and original words.",
                "Conservative English keyword attribution is heuristic; no calibrated posterior.", "Only separately authorized fully synthetic scenarios can simulate paper fills; media remains candidate-only."])]
    reports = {r.asset_id: r for r in cache.asset_reports}
    streams = []
    for asset in cache.manifest.recordings:
        report = reports.get(asset.asset_id)
        if report and report.available:
            state, reason = "recording_ready", "Cached decoded media; " + ("speech transcribed" if report.speech_available else report.speech_reason or "speech unavailable")
        elif any(o.asset_id == asset.asset_id for o in cache.observations):
            state, reason = "fixture_ready", "Labelled supplied synthetic fixture; no recording"
        else:
            state, reason = "recording_missing", (report.reason if report else asset.availability_reason) or "No available recording"
        streams.append(SourceStatus(stream_id=asset.stream_id, label=asset.label, state=state, reason=reason))
    for index in range(len(streams), 6):
        streams.append(SourceStatus(stream_id=f"unconfigured-{index + 1}", label=f"Source slot {index + 1}", state="recording_missing", reason="No recording configured for this slot; no observations are invented."))
    end = duration(cache, metadata)
    mode = "recorded" if any(o.evidence_mode == "recorded" for o in cache.observations) else "synthetic_replay"
    warnings = ["GTA V proxy demo evidence is separate from actual GTA VI quotes.",
        ("Synthetic quotes follow the scenario event timeline; outages do not refresh prices." if metadata else "Synthetic quote timeline: fixed .14/.15 Yes and .85/.86 No, sampled every 5 replay seconds; no venue or depth claim."),
        "No face-derived game approval. Audio speaker attribution is explicit and conservative.", *result.reasons]
    warnings.extend(r.reason for r in cache.asset_reports if r.reason)
    warnings.extend(f"{r.asset_id}: {r.speech_reason}" for r in cache.asset_reports if r.speech_reason)
    from backend.perception.scenes import scene_membership
    groups = [EvidenceGroup(run_id=run_id, group_id=stable_id("group", run_id, scene), scene_id=scene, claim_ids=list(ids)) for scene, ids in scene_membership(claims).items()]
    return DashboardSnapshot(run_id=run_id, gate="G3", groups=groups, scenario_name=metadata.get("scenario_id", "recordings"), run_status="playing" if playing else ("completed" if end and position >= end else "paused"),
        playback=PlaybackState(position_seconds=position, duration_seconds=end, speed=speed, playing=playing),
        replay_time=now, evidence_mode=mode, cache_key=cache.cache_key, configuration_fingerprint=config_key,
        recording_manifest=cache.manifest, streams=streams, windows=windows, claims=claims, reactions=reactions, reaction_recent_window_seconds=policy["recent_window_seconds"], features=result.features,
        markets=[market], quotes=[quote], estimates=[result.estimate] if result.estimate else [],
        decisions=[result.decision] if result.decision else [], receipts=receipts, cash_usd=Decimal("10000.00"),
        warnings=list(dict.fromkeys(warnings)), venue_context=venue)

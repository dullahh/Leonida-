#!/usr/bin/env python3
"""Validate this handoff pack and export reference wire examples, not app tests."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def check_pack():
    count = 0
    for path in (ROOT / ".codex").rglob("*.toml"):
        with path.open("rb") as f:
            data = tomllib.load(f)
        if path.parent.name == "agents":
            for key in ("name", "description", "developer_instructions"):
                assert isinstance(data.get(key), str) and data[key], (path, key)
            assert "sandbox_mode" not in data, path
            assert "model" not in data, "Default pack inherits the parent's model"
        count += 1
    for directory in (ROOT / "config", ROOT / "contracts", ROOT / "data/snapshots"):
        for path in directory.rglob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("leonida_reference_contracts", ROOT / "contracts/reference-v1/models.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    from pydantic import ValidationError
    now = datetime(2026, 11, 14, 20, 30, tzinfo=timezone.utc)
    quote = module.MarketQuote(
        run_id="demo-v1", quote_id="q1", ticker="KXGAMEAWARDS-BNAR-GRA",
        quote_mode="synthetic_replay", captured_at=now, available_at=now,
        venue_status="active", is_stale=False, yes_bid="0.14", yes_ask="0.15",
        no_bid="0.85", no_ask="0.86", no_ask_quantity="10",
        source_ref="scenario:negative-narrative",
    )
    claim = module.EvidenceClaim(
        run_id="demo-v1", claim_id="c1", window_id="w1", stream_id="s1",
        game_id="gta6", evidence_mode="synthetic_replay", event_at=now,
        available_at=now, source_modality="speech", aspect="narrative",
        target="scene", sentiment=-0.4, explicitness="explicit",
        extraction_confidence=0.9, attribution_confidence=0.9,
        supporting_quote="The dialogue in this scene is repetitive.",
        scene_id="courtroom", extractor_version="fixture-v1",
    )
    feature = module.FeatureSnapshot(
        run_id="demo-v1", feature_id="f1", game_id="gta6", aspect="narrative",
        as_of=now, claim_ids=["c1"], absolute_sentiment=-0.4, mean_z=-2.0,
        baseline_ready=True, valid_stream_count=1, independent_group_count=1,
        scene_count=1, baseline_version="seeded-fixture-v1",
        evidence_modes=["synthetic_replay"],
        coverage_note="Illustrative seeded baseline, not inferred from one claim.",
    )
    estimate = module.ModelEstimate(
        run_id="demo-v1", estimate_id="e1", ticker=quote.ticker, quote_id="q1",
        feature_ids=["f1"], as_of=now, market_reference_probability=0.145,
        correction_log_odds=-0.4566438483974167, model_probability=0.097,
        model_version="illustrative-wire-example", calibration_status="heuristic",
        uncertainty_status="not_estimated", receipt_id="r1",
    )
    decision = module.PaperDecision(
        run_id="demo-v1", decision_id="d1", estimate_id="e1", quote_id="q1",
        ticker=quote.ticker, as_of=now, side="no", action="candidate",
        quantity="1", estimated_ev_per_contract="0.033",
        estimated_total_fee="0.01", reason="Illustrative fee; candidate only.",
        receipt_id="r1",
    )
    receipt = module.Receipt(
        run_id="demo-v1", receipt_id="r1", created_at=now,
        summary="Synthetic negative narrative evidence; example No-side candidate.",
        claim_ids=["c1"], feature_ids=["f1"], quote_ids=["q1"],
        estimate_id="e1", decision_id="d1",
        limitations=["All figures are illustrative wire-example values; not a validated forecast."],
    )
    snapshot = module.DashboardSnapshot(
        run_id="demo-v1", generated_at=now,
        evidence_modes=["synthetic_replay"], quote_modes=["synthetic_replay"],
        calibration_status="heuristic", cash_usd="10000.00", equity_usd="10000.00",
        claims=[claim], features=[feature], quotes=[quote], estimates=[estimate],
        decisions=[decision], receipts=[receipt],
        warnings=["This is a reference payload, not an application run."],
    )
    envelope = module.StreamEnvelope(
        run_id="demo-v1", sequence=1, generated_at=now, payload=snapshot,
    )
    # The archived v1 source and examples remain immutable. Validate in memory.
    module.StreamEnvelope.model_json_schema()
    encoded = envelope.model_dump_json(indent=2)
    assert module.StreamEnvelope.model_validate_json(encoded) == envelope
    assert json.loads(encoded)["payload"]["quotes"][0]["yes_ask"] == "0.15"
    logit_reference = math.log(estimate.market_reference_probability / (1 - estimate.market_reference_probability))
    assert math.isclose(1 / (1 + math.exp(-(logit_reference + estimate.correction_log_odds))), estimate.model_probability)
    negative_checks = 0
    for change in (
        {"yes_ask": "1.1"}, {"yes_bid": "0.20"},
        {"captured_at": "2026-11-14T20:30:00"}, {"invented": "field"},
    ):
        values = quote.model_dump()
        values.update(change)
        try:
            module.MarketQuote.model_validate(values)
        except ValidationError:
            negative_checks += 1
        else:
            raise AssertionError("Invalid quote accepted: " + repr(change))
    invalid = envelope.model_dump()
    invalid["run_id"] = "wrong-run"
    try:
        module.StreamEnvelope.model_validate(invalid)
    except ValidationError:
        negative_checks += 1
    else:
        raise AssertionError("Cross-run envelope accepted")
    prompt_files = sorted((ROOT / "docs/prompts").glob("*.md"))
    assert len(prompt_files) == 7, len(prompt_files)
    for path in [ROOT / "README.md", ROOT / "PLAN.md", ROOT / "AGENTS.md", *prompt_files]:
        assert path.stat().st_size > 100, path
    print(json.dumps({
        "toml_files_valid": count,
        "reference_schema_generated_in_memory": True,
        "example_roundtrip": True,
        "money_serializes_as_decimal_string": True,
        "invalid_payloads_rejected": negative_checks,
        "sprint_prompt_files": len(prompt_files),
        "scope": "Handoff pack only; no app, live source, model spawn or strategy performance test."
    }, indent=2))

if __name__ == "__main__":
    check_pack()


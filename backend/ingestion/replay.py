"""Deterministic six-source fallback scenarios; no provider calls or sleeps."""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal
import json
import math
from pathlib import Path
import tempfile

from backend.core.identity import digest, stable_id
from backend.core.schemas import CachedObservation, EvidenceCache, RecordingManifest, SourceWindow
from backend.perception.fixture import FixtureExtractor
from .recordings import build_windows

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIRECTORY = ROOT / "data" / "scenarios"
NAMES = ("courtroom-praise", "technical-failure-laughter", "skill-rage-controls", "mixed-missing-facecam", "duplicate-reconnect", "venue-outage-reset")


def scenario_names() -> tuple[str, ...]:
    return NAMES


def scenario_metadata(name: str) -> dict:
    if name not in NAMES:
        raise ValueError(f"Unknown scenario {name!r}; choose {', '.join(NAMES)}")
    metadata = json.loads((SCENARIO_DIRECTORY / f"{name}.json").read_text(encoding="utf-8"))
    validate_scenario(metadata)
    return metadata


def validate_scenario(metadata: dict) -> None:
    """Validate authored synthetic clocks/books without simulating execution."""
    manifest = RecordingManifest.model_validate(metadata["manifest"])
    if len(manifest.recordings) != 6 or len(metadata["source_statuses"]) != 6:
        raise ValueError("Required synthetic scenarios must declare six source slots/statuses.")
    if {s["stream_id"] for s in metadata["source_statuses"]} != {a.stream_id for a in manifest.recordings}:
        raise ValueError("Scenario source statuses do not match manifest streams.")
    if metadata.get("simulation_authorized") is not True or any(a.evidence_mode != "synthetic_replay" for a in manifest.recordings):
        raise ValueError("Paper simulation authorization applies only to explicit synthetic fixture sources.")
    duration = metadata["duration_seconds"]
    if not isinstance(duration, (float, int)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("Scenario duration must be positive and finite.")
    for observation in metadata["observations"]:
        if observation["provider"] != "supplied_fixture" or observation["evidence_mode"] != "synthetic_replay":
            raise ValueError("Synthetic lifecycle fixtures cannot authorize recorded/provider observations.")
        source = observation["replay_seconds"]
        available = observation.get("available_replay_seconds", source)
        if not all(math.isfinite(t) for t in (source, available)) or not 0 <= source <= available <= duration:
            raise ValueError("Invalid scenario source/availability time.")
    event_ids, liquidity_books = set(), {}
    if not metadata["quote_timeline"]:
        raise ValueError("Synthetic scenario requires its own explicit quote timeline.")
    for row in metadata["quote_timeline"]:
        event, available = row["event_seconds"], row["available_replay_seconds"]
        captured = row["captured_replay_seconds"]
        if not all(math.isfinite(t) for t in (event, available, captured)) or not 0 <= captured <= event <= available <= duration:
            raise ValueError("Invalid synthetic quote capture/event/availability time.")
        if row["event_id"] in event_ids:
            raise ValueError("Duplicate quote timeline event identity.")
        event_ids.add(row["event_id"])
        if row["quote_mode"] != "synthetic_replay" or row["market_id"] != f"synthetic:{metadata['scenario_version']}:narrative":
            raise ValueError("Fixture quote is not in its explicit synthetic namespace.")
        if row["fee_schedule_version"] != "simulation-linear-v1" or Decimal(row["fee_per_contract"]) != Decimal(".01"):
            raise ValueError("Fixture fee schedule must be explicit simulation-linear-v1.")
        prices = {name: Decimal(row[name]) for name in ("yes_bid", "yes_ask", "no_bid", "no_ask")}
        sizes = {name: Decimal(row[name]) for name in ("yes_bid_size", "yes_ask_size", "no_bid_size", "no_ask_size")}
        if any(not p.is_finite() or not 0 <= p <= 1 for p in prices.values()) or any(not s.is_finite() or s < 0 for s in sizes.values()):
            raise ValueError("Synthetic quote prices/sizes must be finite with explicit nonnegative depth.")
        if prices["yes_bid"] > prices["yes_ask"] or prices["no_bid"] > prices["no_ask"]:
            raise ValueError("Synthetic fixture quote is crossed.")
        if prices["yes_bid"] + prices["no_ask"] != 1 or prices["yes_ask"] + prices["no_bid"] != 1:
            raise ValueError("Authored synthetic Yes/No quotes must be coherent complements.")
        identity = row["liquidity_event_id"]
        if not identity:
            raise ValueError("Explicit liquidity identity is required.")
        fingerprint = digest({"market": row["market_id"], "prices": prices, "sizes": sizes})
        previous = liquidity_books.get(identity)
        if previous is not None and previous != fingerprint:
            raise ValueError("Republished liquidity ID cannot change prices or replenish depth.")
        liquidity_books[identity] = fingerprint


def load_scenario(name: str, cache_directory: Path) -> EvidenceCache:
    config = scenario_metadata(name)
    manifest = RecordingManifest.model_validate(config["manifest"])
    observations = []
    for entry in config["observations"]:
        values = dict(entry)
        values["observation_id"] = stable_id("observation", config["scenario_version"], entry)
        observations.append(CachedObservation.model_validate(values))
    observations.sort(key=lambda o: (o.available_replay_seconds if o.available_replay_seconds is not None else o.replay_seconds, o.replay_seconds, o.observation_id))
    input_hash = digest(config)
    key = digest({"schema": "2", "scenario_sha256": input_hash})
    cache = EvidenceCache(cache_key=key, input_sha256=input_hash, payload_sha256=digest([o.model_dump(mode="json") for o in observations]), manifest=manifest, observations=observations, extraction_metadata={"provider": "supplied fixture annotations; no OCR or ASR ran", "scenario_version": config["scenario_version"], "origin": config["origin"]})
    cache_directory.mkdir(parents=True, exist_ok=True)
    destination = cache_directory / f"{key}.json"
    if destination.exists():
        existing = EvidenceCache.model_validate_json(destination.read_text(encoding="utf-8"))
        if existing != cache:
            raise ValueError("Scenario cache content mismatch; refuse corrupt evidence.")
        return existing
    destination.write_text(cache.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return cache


class StructuredReplaySource:
    def __init__(self, cache: EvidenceCache, run_id: str, origin: datetime, *, duplicate_deliveries: bool = False):
        self.windows = build_windows(cache, run_id, origin)
        if duplicate_deliveries:
            self.windows = [window for window in self.windows for _ in range(3)]
        self.cursor = 0

    def next_window(self) -> SourceWindow | None:
        if self.cursor >= len(self.windows):
            return None
        window = self.windows[self.cursor]
        self.cursor += 1
        return window

    def available(self, as_of: datetime) -> list[SourceWindow]:
        ready = []
        while self.cursor < len(self.windows) and self.windows[self.cursor].available_at <= as_of:
            ready.append(self.next_window())
        return ready


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("all", *NAMES), default="all")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--speed", type=float, default=1)
    arguments = parser.parse_args()
    if arguments.speed <= 0:
        parser.error("speed must be positive")
    summaries = []
    with tempfile.TemporaryDirectory(prefix="leonida-replay-") as temporary:
        for name in NAMES if arguments.scenario == "all" else (arguments.scenario,):
            metadata = scenario_metadata(name)
            cache = load_scenario(name, Path(temporary))
            source = StructuredReplaySource(cache, "validation-run", datetime.fromisoformat(metadata["origin"]), duplicate_deliveries=name == "duplicate-reconnect")
            windows = []
            while (window := source.next_window()) is not None:
                windows.append(window)
                if window.available_at < window.event_at:
                    raise ValueError("fixture became available before its source time")
                for claim in FixtureExtractor().extract(window):
                    if claim.supporting_quote not in window.raw_text:
                        raise ValueError("unsupported fixture quotation")
            summaries.append({"scenario": name, "streams": len(cache.manifest.recordings), "unique_observations": len({w.observation_id for w in windows}), "deliveries": len(windows), "abstentions": sum(o.sentiment is None for o in cache.observations), "duration_seconds": metadata["duration_seconds"], "quote_events": len(metadata["quote_timeline"]), "simulation_authorized": metadata["simulation_authorized"], "event_order_sha256": digest([(w.window_id, w.event_at, w.available_at) for w in windows]), "speed": arguments.speed, "status": "validated"})
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()

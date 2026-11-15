"""Focused G3 acceptance checks. No network, preprocessing or shared user DB.

Run from the repository root:
  .venv/Scripts/python.exe -m unittest discover -s tests/g3 -p "test_*.py" -v

These integration checks are the G3 gate, not the broader G4 verification suite.
"""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import sqlite3
import tempfile
import unittest

from backend.core.config import ROOT
from backend.core.identity import digest
from backend.core.runtime import Runtime
from backend.core.schemas import CreateRunRequest, RunCommand, ScenarioRequest, StreamEnvelope
from backend.execution.paper import dump_state
from backend.ingestion.replay import scenario_names

D = Decimal
RECORDING_CACHE = ROOT / "var/evidence-cache/a6d8a27fa3c4f5c3e34b2b8a411457e6cc2a50b5362341b12bd8904d039343d9.json"


class G3Acceptance(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="leonida-g3-acceptance-")
        self.root = Path(self.directory.name)
        self.runtimes = []
        self.serial = 0

    async def asyncTearDown(self):
        for runtime in reversed(self.runtimes):
            await runtime.close()
        self.directory.cleanup()

    def runtime(self, scenario="courtroom-praise", *, path=None, cache=None):
        self.serial += 1
        runtime = Runtime(path or self.root / f"run-{self.serial}.sqlite3",
                          self.root / "cache", scenario=scenario,
                          evidence_cache_path=cache)
        self.runtimes.append(runtime)
        return runtime

    async def close_runtime(self, runtime):
        await runtime.close()
        self.runtimes.remove(runtime)

    async def seek(self, runtime, at, command_id=None):
        await runtime.control(runtime.active_run_id, RunCommand(
            command_id=command_id or f"seek-{at}", action="seek", position_seconds=at))
        snapshot = runtime.snapshot()
        # Validate the wire roundtrip, including its complete reference graph.
        StreamEnvelope.model_validate_json(snapshot.model_dump_json())
        return snapshot.payload

    def assert_trace(self, runtime, trace):
        self.assertEqual(trace.run_id, runtime.active_run_id)
        windows = {w.window_id: w for w in trace.windows}
        claims = {c.claim_id: c for c in trace.claims}
        features = {f.feature_id: f for f in trace.features}
        for claim in trace.claims:
            self.assertIn(claim.supporting_quote, windows[claim.window_id].raw_text)
        for feature in trace.features:
            self.assertTrue(set(feature.claim_ids) <= claims.keys())
        if trace.estimate:
            self.assertEqual(trace.estimate.quote_id, trace.quote.quote_id)
            self.assertTrue(set(trace.estimate.feature_ids) <= features.keys())
        if trace.receipt:
            receipt = trace.receipt
            self.assertTrue(set(receipt.window_ids) <= windows.keys())
            self.assertTrue(set(receipt.claim_ids) <= claims.keys())
            self.assertEqual(receipt.decision_id, trace.decision.decision_id)
            self.assertEqual(receipt.estimate_id, trace.estimate.estimate_id)
            self.assertEqual(receipt.quote_id, trace.quote.quote_id)
            self.assertIsNotNone(runtime.store.record(trace.run_id, "receipts", receipt.receipt_id))
            for kind, identity in (("estimates", receipt.estimate_id),
                                   ("decisions", receipt.decision_id),
                                   ("quotes", receipt.quote_id)):
                self.assertIsNotNone(runtime.store.record(trace.run_id, kind, identity))

    async def test_courtroom_latency_partial_entry_and_two_time_exits(self):
        runtime = self.runtime()
        before = await self.seek(runtime, .999)
        self.assertFalse(before.estimates)
        planned = await self.seek(runtime, 1)
        self.assertEqual(len(planned.streams), 6)
        self.assertEqual(planned.evidence_mode, "synthetic_replay")
        self.assertEqual(planned.estimates[0].market_reference_probability, .5)
        self.assertGreater(planned.estimates[0].model_probability, .5)
        self.assertGreater(planned.decisions[0].yes_ev_per_contract, D(".03"))
        self.assertEqual(planned.execution.orders[0].status, "pending")
        self.assertGreater(planned.execution.reserved_cash, 0)
        self.assertEqual((await self.seek(runtime, 1.249)).fill_count, 0)

        entered = await self.seek(runtime, 1.25)
        order = entered.execution.orders[0]
        self.assertEqual((order.direction, order.status, order.requested_quantity,
                          order.filled_quantity), ("buy", "partial", D(10), D(6)))
        self.assertEqual(entered.cash_usd, D("9996.925"))
        self.assertEqual(entered.execution.reserved_cash, 0)
        self.assertEqual(entered.execution.positions[0].quantity, D(6))
        self.assertEqual(entered.execution.fills[0].fee, D(".06"))

        exiting = await self.seek(runtime, 301.25)
        self.assertEqual(exiting.execution.orders[-1].status, "pending")
        mark = exiting.execution.marks[0]
        self.assertEqual((mark.priced_quantity, mark.unpriced_quantity), (D(4), D(2)))
        partial = await self.seek(runtime, 301.5)
        self.assertEqual(partial.execution.orders[-1].status, "partial")
        self.assertEqual(partial.execution.positions[0].quantity, D(2))

        closed = await self.seek(runtime, 304.25)
        self.assertEqual([(f.direction, f.quantity) for f in closed.execution.fills],
                         [("buy", D(6)), ("sell", D(4)), ("sell", D(2))])
        self.assertFalse(closed.execution.positions)
        self.assertEqual(closed.cash_usd, D("10000.0800"))
        self.assertEqual(closed.execution.realized_pnl, D(".0800"))
        self.assertEqual(sum(f.fee for f in closed.execution.fills), D(".12"))
        self.assertEqual(len(closed.execution.traces), 6)
        for trace in closed.execution.traces:
            self.assert_trace(runtime, trace)

    async def test_other_five_scenarios_keep_their_qualitative_behavior(self):
        observed = {}
        for name in scenario_names():
            if name == "courtroom-praise":
                continue
            with self.subTest(scenario=name):
                runtime = self.runtime(name)
                payload = await self.seek(runtime, 8 if name != "venue-outage-reset" else 17)
                self.assertEqual(len(payload.streams), 6)
                self.assertTrue(all(w.evidence_mode == "synthetic_replay" for w in payload.windows))
                self.assertTrue(all(q.quote_mode == "synthetic_replay" for q in payload.quotes))
                observed[name] = payload
        technical = observed["technical-failure-laughter"]
        self.assertFalse(technical.estimates)
        self.assertFalse(technical.execution.orders)
        self.assertLess(technical.features[0].absolute_sentiment, 0)
        self.assertEqual(technical.features[0].aspect, "technical")
        self.assertAlmostEqual(technical.features[0].effective_source_diagnostic, 1)
        self.assertTrue(any(c.sentiment is None and c.abstention_reason for c in technical.claims))
        controls = observed["skill-rage-controls"]
        self.assertFalse(controls.estimates)
        self.assertFalse(controls.execution.orders)
        skill = next(c for c in controls.claims if c.target == "player_skill")
        self.assertIsNone(skill.sentiment)
        self.assertTrue(all(skill.claim_id not in f.claim_ids for f in controls.features))
        self.assertLess(controls.features[0].absolute_sentiment, 0)
        self.assertEqual(controls.features[0].aspect, "gameplay")
        mixed = observed["mixed-missing-facecam"]
        self.assertGreater(mixed.features[0].disagreement, 0)
        self.assertEqual(mixed.execution.orders[0].status, "cancelled")
        self.assertEqual(mixed.fill_count, 0)
        self.assertTrue(all(not m.available for w in mixed.windows for m in w.modalities if m.modality == "facecam"))
        duplicate = observed["duplicate-reconnect"]
        self.assertEqual(duplicate.fill_count, 1)
        self.assertEqual(len(duplicate.execution.orders), 1)
        self.assertEqual(duplicate.execution.positions[0].quantity, D(6))
        self.assertAlmostEqual(duplicate.features[0].effective_source_diagnostic, 1)
        outage = observed["venue-outage-reset"]
        self.assertTrue(outage.quotes[0].is_stale)
        self.assertFalse(outage.estimates)
        self.assertEqual(outage.execution.orders[0].status, "cancelled")
        self.assertEqual(outage.fill_count, 0)

    async def test_exact_quote_expiry_cancels_pending_entry_without_neutral_estimate(self):
        runtime = self.runtime("venue-outage-reset")
        before = await self.seek(runtime, 9.9)
        self.assertFalse(before.quotes[0].is_stale)
        self.assertTrue(before.estimates)
        self.assertEqual(before.execution.orders[0].status, "pending")
        expired = await self.seek(runtime, 10)
        self.assertTrue(expired.quotes[0].is_stale)
        self.assertFalse(expired.estimates)
        self.assertEqual(expired.fill_count, 0)
        cancelled = await self.seek(runtime, 10.15)
        self.assertEqual(cancelled.execution.orders[0].status, "cancelled")
        self.assertEqual(cancelled.execution.reserved_cash, 0)
        self.assertEqual(cancelled.cash_usd, D("10000"))
        eligibility = cancelled.execution.traces[-1]
        self.assertEqual(eligibility.stage, "eligibility")
        self.assertIsNone(eligibility.estimate)
        self.assertIsNone(eligibility.decision)
        self.assertTrue(eligibility.quote.is_stale)
        self.assertTrue(eligibility.reasons)

    async def test_read_replay_command_reset_and_payload_idempotency(self):
        runtime = self.runtime("duplicate-reconnect")
        run_id = runtime.active_run_id
        request = RunCommand(command_id="one-seek", action="seek", position_seconds=8)
        first = await runtime.control(run_id, request)
        snapshot = runtime.snapshot()
        broker = runtime.store.load_broker(run_id)
        for _ in range(3):
            self.assertEqual(await runtime.control(run_id, request), first)
            self.assertEqual(runtime.snapshot(), snapshot)
            self.assertEqual(runtime.store.load_broker(run_id), broker)
        with self.assertRaisesRegex(ValueError, "different payload"):
            await runtime.control(run_id, RunCommand(command_id="one-seek", action="seek", position_seconds=9))
        for index in range(3):
            await runtime.control(run_id, RunCommand(command_id=f"redeliver-{index}", action="replay_observation"))
        self.assertEqual(runtime.snapshot(), snapshot)
        self.assertEqual(runtime.store.load_broker(run_id), broker)
        reset = RunCommand(command_id="reset-once", action="reset")
        result = await runtime.control(run_id, reset)
        self.assertNotEqual(result.run_id, run_id)
        self.assertEqual(result.previous_run_id, run_id)
        self.assertEqual(runtime.snapshot().payload.fill_count, 0)
        self.assertEqual(runtime.snapshot(run_id).payload.fill_count, 1)
        self.assertEqual(await runtime.control(run_id, reset), result)
        with self.assertRaisesRegex(ValueError, "active run"):
            await runtime.control(run_id, RunCommand(command_id="old-run-write", action="pause"))

    async def test_restart_preserves_pending_then_filled_state_without_reexecution(self):
        path = self.root / "recovery.sqlite3"
        runtime = self.runtime(path=path)
        await self.seek(runtime, 1)
        run_id = runtime.active_run_id
        pending = dump_state(runtime.store.load_broker(run_id)[1])
        await self.close_runtime(runtime)
        restored = self.runtime(path=path)
        await restored.start()
        self.assertEqual(restored.active_run_id, run_id)
        self.assertFalse(restored.snapshot().payload.playback.playing)
        self.assertEqual(dump_state(restored.store.load_broker(run_id)[1]), pending)
        self.assertEqual(restored.snapshot().payload.fill_count, 0)
        await self.seek(restored, 1.25)
        await restored.control(run_id, RunCommand(command_id="start-before-restart", action="play"))
        filled = dump_state(restored.store.load_broker(run_id)[1])
        await self.close_runtime(restored)
        recovered = self.runtime(path=path)
        await recovered.start()
        self.assertFalse(recovered.snapshot().payload.playback.playing)
        self.assertEqual(dump_state(recovered.store.load_broker(run_id)[1]), filled)
        self.assertEqual(recovered.snapshot().payload.fill_count, 1)
        await self.seek(recovered, 8)
        self.assertEqual(recovered.snapshot().payload.fill_count, 1)
        self.assertEqual(recovered.snapshot().payload.execution.positions[0].quantity, D(6))

    async def test_late_transaction_failure_rolls_back_broker_snapshot_and_audit(self):
        runtime = self.runtime()
        await self.seek(runtime, 1, "pending-command")
        run_id = runtime.active_run_id
        before = runtime.snapshot()
        broker_before = runtime.store.load_broker(run_id)
        db_before = list(runtime.store.connection.iterdump())
        staged, broker, audit = runtime._project_playback(before, 1.25, 1, False)
        original = RunCommand(command_id="pending-command", action="seek", position_seconds=1)
        result = runtime.store.command(run_id, original.command_id, digest(original.model_dump()))
        # The duplicate command fails after broker, envelope and audit writes.
        with self.assertRaises(sqlite3.IntegrityError):
            runtime.store.commit(staged, broker_state=broker, audit_snapshots=audit,
                command=(run_id, original.command_id, digest(original.model_dump()), result))
        self.assertEqual(list(runtime.store.connection.iterdump()), db_before)
        self.assertEqual(runtime.store.load_broker(run_id), broker_before)
        self.assertEqual(runtime.snapshot(), before)
        self.assertEqual(runtime.store.load(run_id), before)
        self.assertEqual((await self.seek(runtime, 1.25, "retry-new-command")).fill_count, 1)

    @staticmethod
    def economic_view(payload):
        return {
            "observations": [w.observation_id for w in payload.windows],
            "features": [{k: v for k, v in f.model_dump(mode="json").items()
                          if k not in {"run_id", "feature_id", "claim_ids"}} for f in payload.features],
            "estimates": [(e.market_reference_probability, e.correction_log_odds, e.model_probability)
                          for e in payload.estimates],
            "decisions": [(d.side, d.quantity, d.yes_ev_per_contract, d.no_ev_per_contract) for d in payload.decisions],
            "orders": [(o.direction, o.side, o.status, o.quantity, o.filled_quantity,
                        o.limit_price, o.created_at, o.eligible_at, o.completed_at,
                        o.decision_probability, o.eligible_probability) for o in payload.execution.orders],
            "fills": [(f.direction, f.side, f.quantity, f.gross_value, f.fee, f.vwap, f.at)
                      for f in payload.execution.fills],
            "positions": [p.model_dump(mode="json") for p in payload.execution.positions],
            "cash": payload.cash_usd,
            "realized": payload.execution.realized_pnl,
        }

    async def test_one_and_five_times_pacing_partition_to_same_event_time_state(self):
        finals = []
        for speed in (1, 5):
            runtime = self.runtime()
            await runtime.create_run(CreateRunRequest(command_id=f"isolated-speed-{speed}"))
            await runtime.control(runtime.active_run_id, RunCommand(
                command_id="speed", action="set_speed", speed=speed))
            end = runtime.snapshot().payload.playback.duration_seconds
            # Different wall publication partitions must not skip 250ms
            # eligibility, expiry or 300-second exit events.
            for at in range(7 * speed, int(end), 7 * speed):
                await self.seek(runtime, at)
            finals.append(await self.seek(runtime, end))
        self.assertNotEqual(finals[0].run_id, finals[1].run_id)
        self.assertEqual(self.economic_view(finals[0]), self.economic_view(finals[1]))

    async def test_quote_only_refresh_preserves_source_baseline_and_read_has_no_effect(self):
        runtime = self.runtime()
        before = await self.seek(runtime, 7)
        after = await self.seek(runtime, 8)
        self.assertNotEqual(before.quotes[0].quote_id, after.quotes[0].quote_id)
        self.assertNotEqual(before.estimates[0].market_reference_probability,
                            after.estimates[0].market_reference_probability)
        self.assertEqual([w.observation_id for w in before.windows],
                         [w.observation_id for w in after.windows])
        fields = ("previous_mean", "previous_variance", "updated_mean",
                  "updated_variance", "baseline_count", "unique_observation_count")
        self.assertEqual([{k: getattr(f, k) for k in fields} for f in before.features],
                         [{k: getattr(f, k) for k in fields} for f in after.features])
        sequence = runtime.snapshot().sequence
        broker = runtime.store.load_broker(runtime.active_run_id)
        for _ in range(5):
            StreamEnvelope.model_validate_json(runtime.snapshot().model_dump_json())
        self.assertEqual(runtime.snapshot().sequence, sequence)
        self.assertEqual(runtime.store.load_broker(runtime.active_run_id), broker)

    async def test_supplied_recordings_abstain_and_fixture_occurrence_is_separate(self):
        if not RECORDING_CACHE.exists():
            self.skipTest("Supplied t1/t2/t3 cache is local and not bundled; preprocess it first.")
        runtime = self.runtime(cache=RECORDING_CACHE)
        recorded_run = runtime.active_run_id
        metadata = runtime.context().cache.extraction_metadata
        self.assertTrue(metadata)
        payload = await self.seek(runtime, runtime.snapshot().payload.playback.duration_seconds)
        self.assertEqual(len(payload.streams), 6)
        self.assertEqual(Counter(w.stream_id for w in payload.windows),
                         Counter({"t1": 105, "t2": 221, "t3": 303}))
        self.assertEqual(len({w.observation_id for w in payload.windows}), 629)
        self.assertTrue(all(c.sentiment is None and c.abstention_reason for c in payload.claims))
        self.assertTrue(all(w.evidence_mode == "recorded" and w.evidence_scope == "proxy_demo"
                            for w in payload.windows))
        self.assertFalse(payload.features)
        self.assertFalse(payload.estimates)
        self.assertFalse(payload.decisions)
        self.assertFalse(payload.groups)
        self.assertFalse(payload.execution.enabled)
        self.assertEqual((payload.order_count, payload.fill_count), (0, 0))
        self.assertEqual(payload.venue_context.effect_on_proxy_estimate, "none")
        preserved = runtime.snapshot(recorded_run)
        request = ScenarioRequest(command_id="separate-fixture", scenario="courtroom-praise")
        result = await runtime.inject(recorded_run, request)
        self.assertNotEqual(result.run_id, recorded_run)
        self.assertEqual(runtime.snapshot(recorded_run), preserved)
        self.assertTrue(all(o.provider == "supplied_fixture" and o.evidence_mode == "synthetic_replay"
                            for o in runtime.cache.observations))
        self.assertEqual(await runtime.inject(recorded_run, request), result)
        qualified = await self.seek(runtime, 1.25, "qualifying-after-recordings")
        self.assertEqual(qualified.fill_count, 1)
        self.assertGreater(qualified.estimates[0].model_probability,
                           qualified.estimates[0].market_reference_probability)
        self.assertEqual(runtime.snapshot(recorded_run).payload.fill_count, 0)


if __name__ == "__main__":
    unittest.main()


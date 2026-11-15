"""Focused reaction integration checks; offline, no media or model providers."""
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone

from backend.core.identity import stable_id
from backend.core.market import unavailable
from backend.core.media_projection import project
from backend.core.reactions import build_reactions, pricing_gate, reaction_policy, _text_signal
from backend.ingestion.recordings import build_windows
from backend.ingestion.replay import load_scenario, scenario_metadata
from backend.perception.claims import interpret, extract


class ReactionIntegration(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cache = load_scenario("courtroom-praise", Path(self.directory.name))

    def observation(self, text, **updates):
        meaning = interpret(text)
        return self.cache.observations[0].model_copy(update={
            "observation_id": stable_id("diagnostic", text), "raw_text": text, "supporting_quote": text,
            "replay_seconds": 0, "media_seconds": 0, "available_replay_seconds": 0,
            "aspect": meaning.aspect, "target": meaning.target, "sentiment": meaning.sentiment,
            "abstention_reason": meaning.reason, "semantic_confidence": meaning.confidence, **updates})

    def projection(self, observation):
        cache = self.cache.model_copy(update={"observations": [observation]})
        return project("reaction-test", cache, 1, 1, False, "reaction-test", unavailable("offline"))

    def test_intense_ambiguous_telemetry_does_not_price(self):
        p = self.projection(self.observation("Oh my god! What the hell!"))
        reaction = p.reactions[0]
        self.assertGreaterEqual(reaction.intensity, .7)
        self.assertEqual(reaction.emotion, "surprise")
        self.assertEqual(reaction.valence, "uncertain")
        self.assertFalse(reaction.pricing_eligible)
        self.assertIsNone(reaction.supported_claim_id)
        self.assertFalse(p.estimates)
        self.assertFalse(p.features)

    def test_player_skill_frustration_excluded(self):
        p = self.projection(self.observation("I'm so bad at this game."))
        self.assertEqual(p.reactions[0].likely_target, "player_skill")
        self.assertEqual(p.reactions[0].emotion, "frustration")
        self.assertFalse(p.reactions[0].pricing_eligible)
        self.assertFalse(p.estimates)

    def test_explicit_quality_claim_passes_existing_classifier_and_gates(self):
        p = self.projection(self.observation("The writing in this game is excellent."))
        self.assertEqual(p.claims[0].sentiment, .4)
        self.assertEqual(p.reactions[0].supported_claim_id, p.claims[0].claim_id)
        self.assertTrue(p.reactions[0].pricing_eligible)
        self.assertTrue(p.reactions[0].included_in_estimate)
        self.assertGreater(p.estimates[0].model_probability, p.estimates[0].market_reference_probability)
        claim = p.claims[0]
        policy = reaction_policy()
        self.assertFalse(pricing_gate(claim, "game_quality", .89, 1, policy)[0])
        self.assertFalse(pricing_gate(claim, "game_quality", .95, .79, policy)[0])
        self.assertFalse(pricing_gate(claim.model_copy(update={"quality": .59}), "game_quality", .95, 1, policy)[0])

    def test_duplicate_deliveries_and_cached_classification(self):
        cache = self.cache.model_copy(update={"observations": [self.observation("Oh my god!")]})
        window = build_windows(cache, "reaction-test", datetime(2026, 11, 14, tzinfo=timezone.utc))[0]
        claim = extract(window)[0]
        single = build_reactions([window], [claim])
        duplicate = build_reactions([window] * 5, [claim] * 5)
        self.assertEqual(single, duplicate)
        before = _text_signal.cache_info().hits
        build_reactions([window], [claim])
        self.assertGreater(_text_signal.cache_info().hits, before)
        with self.assertRaises(ValueError):
            build_reactions([window, window.model_copy(update={"raw_text": "changed"})], [claim])

    def test_bad_ocr_asr_and_emphasis_do_not_establish_quality(self):
        p = self.projection(self.observation("OH MY GOD!", ocr_confidence=.4))
        self.assertIsNone(p.reactions[0].intensity)
        self.assertFalse(p.reactions[0].pricing_eligible)
        # Even a stale/incorrect cached quality annotation cannot bypass the
        # telemetry quality gate or admit poor OCR/ASR into an estimate.
        for extra in ({"ocr_confidence": .4}, {"abstention_reason": "High ASR compression ratio; decoding loop"}):
            p = self.projection(self.observation("The writing in this game is excellent.", **extra))
            self.assertFalse(p.reactions[0].pricing_eligible)
            self.assertFalse(p.estimates)
        for text in ("FUCK!", "WOW!", "YAY!"):
            p = self.projection(self.observation(text))
            self.assertFalse(p.reactions[0].pricing_eligible)
            self.assertFalse(p.estimates)

    def test_courtroom_fixture_stays_labelled_and_changes_estimate(self):
        p = project("reaction-test", self.cache, 7, 1, False, "reaction-test", unavailable("offline"), scenario_metadata("courtroom-praise"))
        self.assertEqual(p.evidence_mode, "synthetic_replay")
        self.assertTrue(all(r.evidence_mode == "synthetic_replay" for r in p.reactions))
        self.assertTrue(all(r.included_in_estimate for r in p.reactions))
        self.assertGreater(p.estimates[0].model_probability, .5)

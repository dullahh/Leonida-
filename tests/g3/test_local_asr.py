"""ASR quality boundary/cache invariants; no model, audio service or network."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

from backend.core.identity import digest
from backend.core.market import unavailable
from backend.core.media_projection import project
from backend.core.schemas import RecordingManifest
from backend.ingestion.audio import (asr_cache_identity, cached_transcribe, model_identity,
                                     transcription_settings, validate_segments)
from backend.ingestion.recordings import MediaPreprocessor, build_windows, load_cache
from backend.ingestion.replay import load_scenario


def segment(text="The writing in this game is excellent.", **updates):
    return dict(start_seconds=0., end_seconds=1., text=text, avg_logprob=-.2,
                compression_ratio=1., no_speech_probability=.02, **updates)


class LocalASRQuality(unittest.TestCase):
    def test_severe_loops_rejected_but_short_human_repetition_retained_for_review(self):
        for text in ("No, " * 100, "please help me " * 5, "the writing is excellent " * 4):
            accepted, audit = validate_segments([segment(text)], 2)
            self.assertFalse(accepted)
            self.assertEqual(audit[0]["status"], "rejected")
            self.assertIn("severe_repetition_loop", audit[0]["reasons"])
            self.assertEqual(audit[0]["raw_segment"]["text"], text)
        accepted, audit = validate_segments([segment("No, no, no!")], 2)
        self.assertFalse(accepted)
        self.assertEqual(audit[0]["status"], "uncertain")

    def test_cross_segment_loops_and_excessive_compression(self):
        rows = [segment("Thank you for watching.") for _ in range(3)]
        accepted, audit = validate_segments(rows, 2)
        self.assertEqual(len(accepted), 0)
        self.assertIn("severe_repetition_loop", audit[-1]["reasons"])
        row = segment()
        row["compression_ratio"] = 26.24
        self.assertIn("excessive_compression_ratio", validate_segments([row], 2)[1][0]["reasons"])

    def test_timestamps_are_never_clipped_including_rounding_overflow(self):
        for start, end in ((-0.01, 1), (0, 2.001), (2, 3), (1, 1), (0, float("inf"))):
            row = segment()
            row.update(start_seconds=start, end_seconds=end)
            accepted, audit = validate_segments([row], 2)
            self.assertFalse(accepted)
            self.assertEqual(audit[0]["raw_segment"], row)
            self.assertEqual(audit[0]["status"], "rejected")
        row = segment()
        row.update(end_seconds=2, window_start_seconds=0, window_end_seconds=1.5)
        self.assertIn("timestamp_outside_decode_window", validate_segments([row], 3)[1][0]["reasons"])
        row.update(end_seconds=1.5)
        accepted, _ = validate_segments([row], 3)
        self.assertEqual(accepted[0]["end_seconds"], 1.5)

    def test_silence_bad_diagnostics_and_uncertainty(self):
        silence = segment("")
        silence.update(decoding_status="no_vad_speech", avg_logprob=None, compression_ratio=None, no_speech_probability=None)
        self.assertEqual(validate_segments([silence], 2)[1][0]["reasons"], ["no_vad_speech"])
        for changes, reason in (({"avg_logprob": -1.1}, "low_avg_logprob"),
                                ({"no_speech_probability": .8}, "high_no_speech_probability"),
                                ({"compression_ratio": float("nan")}, "missing_or_nonfinite_diagnostics")):
            row = {**segment(), **changes}
            accepted, audit = validate_segments([row], 2)
            self.assertFalse(accepted)
            self.assertIn(reason, audit[0]["reasons"])
        accepted, audit = validate_segments([{**segment(), "avg_logprob": -.9}], 2)
        self.assertFalse(accepted)
        self.assertEqual(audit[0]["status"], "uncertain")

    def test_every_material_asr_cache_version_separates(self):
        base = asr_cache_identity("media", "pcm", {"name": "tiny.en", "version": "a"}, transcription_settings(), 0, 2)
        for name, value in (("model", {"name": "small.en", "version": "b"}),
                            ("audio_preprocessing_version", "next"), ("media_sha256", "changed"),
                            ("pcm_sha256", "changed"), ("settings", {"beam_size": 1}),
                            ("gate_version", "next"), ("media_start_seconds", 1), ("duration_seconds", 1)):
            self.assertNotEqual(digest(base), digest({**base, name: value}))

    def test_supported_speech_receipt_exposes_model_version_and_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            cache = load_scenario("courtroom-praise", Path(temporary))
            provenance = "ASR faster-whisper-small.en version=test-hash; gates=asr-quality-v2; observation=accepted; quality_gates_passed"
            original = cache.observations[0]
            speech = original.model_copy(update={"source_modality": "speech", "provider": "recorded_asr",
                                                "ocr_confidence": None, "confidence_reason": provenance})
            cache = cache.model_copy(update={"observations": [speech]})
            snapshot = project("asr-receipt-isolated", cache, 2, 1, False, "test", unavailable("offline"))
            self.assertTrue(snapshot.receipts)
            self.assertIn(provenance, snapshot.receipts[0].explanation)

    def test_rejected_and_uncertain_speech_never_reach_classification_or_reactions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            (root / "config/local_asr.json").write_text(json.dumps({"default_model": "small.en"}), encoding="utf-8")
            model_path = root / "var/models/faster-whisper-small.en"
            model_path.mkdir(parents=True)
            for name in ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt"):
                (model_path / name).write_text(name, encoding="utf-8")
            frame = root / "cache/prior/frame.png"
            frame.parent.mkdir(parents=True)
            frame.write_bytes(b"verified-test-fixture")
            ffmpeg = root / "ffmpeg-fixture"
            ffmpeg.write_bytes(b"hash-only-fixture")
            assets = []
            for index in (1, 2):
                media = root / f"t{index}.mp4"
                media.write_bytes(b"local-fixture")
                from backend.ingestion.tools import file_sha256
                assets.append(dict(asset_id=f"t{index}", stream_id=f"t{index}", label="test", local_path=media.name,
                                   asset_sha256=file_sha256(media), availability_reason=None,
                                   chat_region=dict(x=0, y=0, width=1, height=1), permission_note="test fixture",
                                   audio_transcription="faster_whisper", speaker_role="unknown"))
            manifest = RecordingManifest(manifest_version="test", recordings=assets,
                                         ocr_version="test", preprocessing_version="test", semantic_version="test")
            frames = {(a["asset_id"], 0): dict(frame_ref="prior/frame.png", lines=[]) for a in assets}
            raw = [segment(), {**segment("Wow!"), "no_speech_probability": .9},
                   {**segment("Oh my god!"), "avg_logprob": -.9}, segment("No, " * 50)]

            class FakeEngine:
                identity = model_identity(model_path)
                load_seconds = 0
                def transcribe(self, path, language):
                    return raw

            def audio_fixture(source, destination, start, duration):
                with wave.open(str(destination), "wb") as output:
                    output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                    output.writeframes(b"\0\0" * 32000)
                return []

            from backend.ingestion.recordings import interpret
            with patch("backend.ingestion.recordings._reuse_ocr_audit", return_value=(frames, "prior")), \
                 patch("backend.ingestion.recordings.media_info", return_value={"duration_seconds": 2, "audio_available": True}), \
                 patch("backend.ingestion.recordings.ffmpeg_path", return_value=str(ffmpeg)), \
                 patch("backend.ingestion.recordings.extract_audio", side_effect=audio_fixture), \
                 patch("backend.ingestion.audio.LocalASR", return_value=FakeEngine()), \
                 patch("backend.ingestion.recordings.RapidOCRProvider", side_effect=AssertionError("OCR must not run")), \
                 patch("backend.ingestion.recordings.interpret", wraps=interpret) as classifier:
                cache = MediaPreprocessor(root, reuse_ocr_only=True).preprocess(manifest, root / "cache")
            self.assertEqual(classifier.call_count, 2)  # one accepted segment per asset
            self.assertTrue(all(call.kwargs["speaker_role"] == "unknown" for call in classifier.call_args_list))
            self.assertEqual(len(cache.observations), 2)
            self.assertTrue(all(o.sentiment is None for o in cache.observations))
            self.assertTrue(all("version=" in o.confidence_reason and "observation=accepted" in o.confidence_reason for o in cache.observations))
            restored = load_cache(root / "cache" / f"{cache.cache_key}.json")
            windows = build_windows(restored, "asr-isolated", datetime.now(timezone.utc))
            self.assertEqual([w.raw_text for w in windows], [segment()["text"]] * 2)
            projection = project("asr-isolated", restored, 2, 1, False, "test", unavailable("offline"))
            self.assertEqual(len(projection.reactions), 2)
            self.assertFalse(projection.estimates)
            audit_files = list((root / "cache" / cache.cache_key).rglob("transcript-validation.json"))
            self.assertEqual(len(audit_files), 2)
            self.assertEqual([a["status"] for a in json.loads(audit_files[0].read_text(encoding="utf-8"))],
                             ["accepted", "rejected", "uncertain", "rejected"])
            cached = next((root / "var/asr-cache").rglob("*.json"))
            before = cached.read_bytes()
            # A repeated request reads the immutable result and invokes no model.
            audio = next((root / "cache" / cache.cache_key).rglob("audio.wav"))
            with patch("backend.ingestion.audio.LocalASR", side_effect=AssertionError("cache hit must not load model")):
                cached_transcribe(audio, model_path, "eng", root / "var/asr-cache", assets[0]["asset_sha256"], duration_limit=2)
            self.assertEqual(cached.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

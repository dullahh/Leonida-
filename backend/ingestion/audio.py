"""Local-only, versioned PCM/ASR with auditable pre-classification gates."""
from __future__ import annotations

from array import array
import json
import math
from pathlib import Path
import re
import sys
import time
import wave

from backend.core.identity import digest
from .tools import MediaSetupError, file_sha256, package_version, run_ffmpeg

AUDIO_PREPROCESSING_VERSION = "mono-pcm16-16000-v1"
ASR_VERSION = "local-asr-v2"
GATE_VERSION = "asr-quality-v2"
MODEL_NAMES = ("small.en", "tiny.en")
GATES = {"max_compression_ratio": 2.4, "min_avg_logprob": -1.0,
         "max_no_speech_probability": .6, "uncertain_avg_logprob": -.8,
         "uncertain_no_speech_probability": .35,
         "token_loop_repeats": 8, "phrase_loop_repeats": 4}


def transcription_settings(language: str = "eng") -> dict:
    if language not in {"eng", "en"}:
        raise MediaSetupError("English-only ASR modes require language=en or eng; no silent language override.")
    return dict(language="en", task="transcribe", beam_size=5, best_of=1,
                temperature=0, vad_filter=True,
                vad_parameters=dict(threshold=.5, min_speech_duration_ms=250,
                                    min_silence_duration_ms=500, speech_pad_ms=200),
                condition_on_previous_text=False, word_timestamps=False,
                # Own these gates so returned bad text survives in the audit.
                compression_ratio_threshold=None, log_prob_threshold=None,
                no_speech_threshold=None, chunk_length=15)


def pcm_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as source:
        return source.getnframes() / source.getframerate()


def _loop(text: str) -> bool:
    words = re.findall(r"\w+", text.casefold())
    for width in range(1, min(13, len(words) // 4 + 1)):
        repeats = GATES["token_loop_repeats"] if width == 1 else GATES["phrase_loop_repeats"]
        for pos in range(len(words) - width * repeats + 1):
            phrase = words[pos:pos + width]
            if all(words[pos + n * width:pos + (n + 1) * width] == phrase for n in range(1, repeats)):
                return True
    return False


def validate_segments(segments: list[dict], duration: float) -> tuple[list[dict], list[dict]]:
    """No clipping/repair. Only accepted speech may reach semantic consumers.

    Thresholds are conservative heuristics, not calibrated accuracy measures.
    Uncertain and rejected text stays in the audit with original audio times.
    """
    accepted, audit = [], []
    normalized_texts = [" ".join(re.findall(r"\w+", s["text"].casefold())) for s in segments]
    repeated_indices = set()
    for pos in range(len(segments) - 2):
        if normalized_texts[pos] and normalized_texts[pos] == normalized_texts[pos + 1] == normalized_texts[pos + 2]:
            repeated_indices.update((pos, pos + 1, pos + 2))
    for index, original in enumerate(segments):
        start, end = original["start_seconds"], original["end_seconds"]
        reasons, warnings = [], []
        times = (start, end, duration)
        valid_times = all(isinstance(x, (int, float)) and math.isfinite(x) for x in times)
        if not valid_times:
            reasons.append("nonfinite_timestamp")
        elif duration <= 0 or start < 0 or end <= start or start >= duration or end > duration:
            reasons.append("timestamp_outside_audio_duration")
        # Also reject padding past an individual decoding window, even if the
        # generated time happens to fit in the complete media file.
        if "window_start_seconds" in original and valid_times:
            bounds = (original["window_start_seconds"], original.get("window_end_seconds"))
            if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in bounds):
                reasons.append("nonfinite_decode_window")
            elif start < bounds[0] or end > bounds[1]:
                reasons.append("timestamp_outside_decode_window")
        normalized = " ".join(re.findall(r"\w+", original["text"].casefold()))
        if not normalized:
            reasons.append("no_vad_speech" if original.get("decoding_status") == "no_vad_speech" else "empty_transcript")
        elif _loop(original["text"]) or index in repeated_indices:
            reasons.append("severe_repetition_loop")
        elif re.search(r"\b(\w+)(?:\W+\1){2,}\b", original["text"], re.I):
            warnings.append("short_repetition_requires_listening")
        quality = [original.get(k) for k in ("avg_logprob", "compression_ratio", "no_speech_probability")]
        if normalized:
            if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in quality):
                reasons.append("missing_or_nonfinite_diagnostics")
            else:
                logprob, compression, no_speech = quality
                if compression < 0 or not 0 <= no_speech <= 1 or logprob > 0:
                    reasons.append("invalid_diagnostics")
                if compression > GATES["max_compression_ratio"]:
                    reasons.append("excessive_compression_ratio")
                if logprob < GATES["min_avg_logprob"]:
                    reasons.append("low_avg_logprob")
                if no_speech > GATES["max_no_speech_probability"]:
                    reasons.append("high_no_speech_probability")
                if not reasons and (logprob < GATES["uncertain_avg_logprob"] or no_speech > GATES["uncertain_no_speech_probability"]):
                    warnings.append("borderline_speech_diagnostics")
        status = "rejected" if reasons else "uncertain" if warnings else "accepted"
        entry = {"segment_index": index, "status": status, "gate_version": GATE_VERSION,
                 "reasons": reasons or warnings or ["quality_gates_passed"],
                 "raw_segment": dict(original), "start_seconds": start, "end_seconds": end,
                 "pcm_duration_seconds": duration, "requires_listening_review": True}
        audit.append(entry)
        if status == "accepted":
            accepted.append({**original, "asr_status": status, "quality_gate_reasons": entry["reasons"]})
    return accepted, audit


def extract_audio(path: Path, destination: Path, start: float, duration: float) -> list[dict]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(["-y", "-ss", str(start), "-i", str(path), "-t", str(duration), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(destination)], timeout=max(120, int(duration * 3)))
    activity = []
    with wave.open(str(destination), "rb") as source:
        index = 0
        while data := source.readframes(32000):
            values = array("h", data)
            if sys.byteorder != "little":
                values.byteswap()
            rms = math.sqrt(sum(float(x) * x for x in values) / len(values)) / 32768
            activity.append({"start_seconds": start + index * 2, "end_seconds": start + index * 2 + len(values) / 16000, "rms": rms, "audible_activity": rms >= .005, "measurement": "rms-v1; activity does not establish speech or sentiment"})
            index += 1
    return activity


def model_identity(model_path: Path) -> dict:
    # Require tokenizer files too: faster-whisper otherwise may fetch one.
    required = ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt")
    if not all((model_path / name).is_file() for name in required):
        raise MediaSetupError(f"Complete local Whisper model missing at {model_path}. Run setup-speech with --asr-model small.en or tiny.en; no automatic download or fallback.")
    files = {p.name: file_sha256(p) for p in sorted(model_path.glob("*")) if p.is_file() and p.name != "download.json"}
    return {"name": model_path.name, "version": digest(files), "files_sha256": files}


def asr_cache_identity(media_sha256: str, pcm_sha256: str, model: dict, settings: dict,
                       start_seconds: float, duration: float) -> dict:
    return {"asr_version": ASR_VERSION, "audio_preprocessing_version": AUDIO_PREPROCESSING_VERSION,
            "media_sha256": media_sha256, "pcm_sha256": pcm_sha256,
            "media_start_seconds": start_seconds, "duration_seconds": duration,
            "model": model, "settings": settings, "gate_version": GATE_VERSION, "gates": GATES,
            "window_seconds": 15, "overlap_seconds": 0, "device": "cpu", "compute_type": "int8",
            "cpu_threads": 1, "num_workers": 1,
            "packages": {k: package_version(k) for k in ("faster-whisper", "ctranslate2", "onnxruntime", "numpy")}}


class LocalASR:
    """One local model, serial windows; never sends audio or downloads anything."""
    def __init__(self, model_path: Path):
        self.identity = model_identity(model_path)
        self.load_started = time.perf_counter()
        from faster_whisper import WhisperModel
        self.model = WhisperModel(str(model_path), device="cpu", compute_type="int8",
                                  cpu_threads=1, num_workers=1, local_files_only=True)
        self.load_seconds = time.perf_counter() - self.load_started

    def transcribe(self, path: Path, language: str) -> list[dict]:
        import numpy as np
        settings = transcription_settings(language)
        with wave.open(str(path), "rb") as source:
            if source.getnchannels() != 1 or source.getframerate() != 16000 or source.getsampwidth() != 2:
                raise MediaSetupError("ASR expects extracted 16 kHz mono PCM16 audio.")
            audio = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
        output = []
        for offset in range(0, len(audio), 15 * 16000):
            window_started = time.perf_counter()
            first_output = len(output)
            window = audio[offset:offset + 15 * 16000]
            window_start, window_end = offset / 16000, (offset + len(window)) / 16000
            segments, info = self.model.transcribe(window, **settings)
            count = 0
            for s in segments:
                count += 1
                output.append(dict(start_seconds=window_start + float(s.start), end_seconds=window_start + float(s.end),
                                   window_start_seconds=window_start, window_end_seconds=window_end,
                                   original_window_start_seconds=float(s.start), original_window_end_seconds=float(s.end),
                                   text=s.text.strip(), avg_logprob=float(s.avg_logprob),
                                   no_speech_probability=float(s.no_speech_prob), compression_ratio=float(s.compression_ratio)))
            if not count:
                output.append(dict(start_seconds=window_start, end_seconds=window_end, text="",
                                   window_start_seconds=window_start, window_end_seconds=window_end,
                                   avg_logprob=None, no_speech_probability=None, compression_ratio=None,
                                   decoding_status="no_vad_speech" if info.duration_after_vad == 0 else "no_decoded_text",
                                   vad_speech_seconds=info.duration_after_vad))
            elapsed = time.perf_counter() - window_started
            for entry in output[first_output:]:
                entry["window_processing_seconds"] = elapsed
        return output


def cached_transcribe(path: Path, model_path: Path, language: str, cache_directory: Path,
                     media_sha256: str, start_seconds: float = 0,
                     engine: LocalASR | None = None, duration_limit: float | None = None) -> dict:
    duration = pcm_duration(path)
    supported_duration = min(duration, duration_limit) if duration_limit is not None else duration
    identity = asr_cache_identity(media_sha256, file_sha256(path), engine.identity if engine else model_identity(model_path),
                                  transcription_settings(language), start_seconds, supported_duration)
    key = digest(identity)
    destination = cache_directory / ASR_VERSION / f"{key}.json"
    if destination.exists():
        result = json.loads(destination.read_text(encoding="utf-8"))
        content = {k: v for k, v in result.items() if k != "content_sha256"}
        if result.get("identity") != identity or result.get("content_sha256") != digest(content):
            raise ValueError("ASR cache integrity mismatch")
        return result
    started = time.perf_counter()
    try:
        engine = engine or LocalASR(model_path)
        raw = engine.transcribe(path, language)
    except (ImportError, RuntimeError, OSError) as error:
        raise MediaSetupError(f"Local ASR failed for {identity['model']['name']}: {error}; no fallback or download was attempted.") from error
    accepted, audit = validate_segments(raw, supported_duration)
    result = {"cache_key": key, "identity": identity, "raw_segments": raw, "accepted_segments": accepted,
              "audit": audit, "processing_seconds": time.perf_counter() - started,
              "model_load_seconds": engine.load_seconds, "listening_verified": False}
    result["content_sha256"] = digest(result)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Single writer; exclusive create refuses to overwrite immutable results.
    with destination.open("x", encoding="utf-8") as file:
        file.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def transcribe(path: Path, model_path: Path, language: str) -> list[dict]:
    """Compatibility entrypoint; raw results still require validate_segments."""
    return LocalASR(model_path).transcribe(path, language)

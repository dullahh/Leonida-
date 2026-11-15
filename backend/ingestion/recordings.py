"""Offline preprocessing of local recordings into immutable, replayable evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import io
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

from backend.core.identity import digest, stable_id
from backend.core.schemas import CachedObservation, EvidenceCache, MediaAssetReport, ModalityAvailability, RecordingManifest, SourceWindow
from backend.perception.claims import SEMANTIC_VERSION, interpret
from .audio import extract_audio, pcm_duration, transcribe, validate_segments
from .ocr import OCRLine, RapidOCRProvider, VisibleLineTracker
from .tools import MediaSetupError, ffmpeg_path, file_sha256, media_info, package_version, run_ffmpeg

MEDIA_EXTENSIONS = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v"}
PREPROCESSING_VERSION = "local-media-v3-asr-boundaries"
OCR_PROCESSING_ID = "sampled-native-crop-rapidocr-v1"
OCR_VERSION_KEYS = ("rapidocr-onnxruntime", "onnxruntime", "imageio-ffmpeg", "av", "ffmpeg_binary_sha256")


def resolve_local_path(value: str, repository_root: Path, *, media: bool = True) -> Path:
    root = repository_root.resolve()
    candidate = (root / value).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("Recording and model paths must remain within the repository workspace.")
    if media and candidate.suffix.lower() not in MEDIA_EXTENSIONS:
        raise ValueError(f"Unsupported recording extension {candidate.suffix}; use MP4, MKV, MOV, WebM, AVI or M4V.")
    return candidate


def load_manifest(path: Path, repository_root: Path) -> RecordingManifest:
    """Resolve repository-relative paths and verify/fill actual content hashes.

    Manifest paths always resolve from the repository, never the current shell or
    manifest directory. Unavailable slots remain unavailable and produce no text.
    """
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    for asset in raw.get("recordings", []):
        if asset.get("local_path") is None:
            asset["asset_sha256"] = None
            asset["availability_reason"] = asset.get("availability_reason") or "Recording slot has no local file."
            continue
        source = resolve_local_path(asset["local_path"], repository_root)
        if not source.is_file():
            asset["asset_sha256"] = None
            asset["availability_reason"] = f"Recording not found: {asset['local_path']}"
            continue
        actual = file_sha256(source)
        if asset.get("asset_sha256") is not None and asset["asset_sha256"] != actual:
            raise ValueError(f"Recording hash mismatch for {asset['asset_id']}; review the file and update its manifest hash.")
        asset["asset_sha256"] = actual
        asset["availability_reason"] = None
    return RecordingManifest.model_validate(raw)


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_cache(path: Path) -> EvidenceCache:
    cache = EvidenceCache.model_validate_json(path.read_text(encoding="utf-8"))
    if cache.payload_sha256 != digest([o.model_dump(mode="json") for o in cache.observations]):
        raise ValueError("Cached observation digest mismatch; refuse corrupted evidence.")
    envelope_hash = cache.extraction_metadata.get("content_sha256")
    if envelope_hash:
        content = cache.model_dump(mode="json")
        del content["extraction_metadata"]["content_sha256"]
        if digest(content) != envelope_hash:
            raise ValueError("Cached manifest/report/content digest mismatch; refuse corrupted evidence.")
    index_hash = cache.extraction_metadata.get("artifact_index_sha256")
    if index_hash:
        index_path = path.parent / cache.cache_key / "artifacts.json"
        if not index_path.is_file() or file_sha256(index_path) != index_hash:
            raise ValueError("Media artifact index is missing or corrupt; reprocess the recording.")
        index = json.loads(index_path.read_text(encoding="utf-8"))
        for relative, expected_hash in index.items():
            artifact = (path.parent / relative).resolve()
            if not artifact.is_relative_to(path.parent.resolve()) or not artifact.is_file() or file_sha256(artifact) != expected_hash:
                raise ValueError(f"Media artifact is missing or corrupt: {relative}")
    return cache


def _reuse_ocr_audit(cache_directory: Path, manifest: RecordingManifest, versions: dict[str, str]) -> tuple[dict, str | None]:
    """Reuse only verified raw OCR, never old interpretations or ASR output.

    The known v2 implementation used exactly OCR_PROCESSING_ID. Unknown legacy
    preprocessing versions have no verified OCR identity and are not reused.
    """
    fields = {"asset_id", "asset_sha256", "media_start_seconds", "media_end_seconds", "timeline_start_seconds", "chat_region", "sample_interval_seconds", "language"}
    required = [asset.model_dump(mode="json", include=fields) for asset in manifest.recordings]
    for path in sorted(cache_directory.glob("*.json")):
        try:
            candidate = EvidenceCache.model_validate_json(path.read_text(encoding="utf-8"))
            previous = candidate.extraction_metadata
            processing = previous.get("ocr_processing_id")
            if processing is None and previous.get("preprocessor") == "local-media-v2-pcm-asr":
                processing = OCR_PROCESSING_ID
            if processing != OCR_PROCESSING_ID or candidate.manifest.ocr_version != manifest.ocr_version or candidate.manifest.preprocessing_version != manifest.preprocessing_version:
                continue
            if any(not previous.get(key) or previous[key] != versions[key] for key in OCR_VERSION_KEYS):
                continue
            if [asset.model_dump(mode="json", include=fields) for asset in candidate.manifest.recordings] != required:
                continue
            if not previous.get("content_sha256") or not previous.get("artifact_index_sha256"):
                continue
            candidate = load_cache(path)
            audit_path = cache_directory / candidate.cache_key / "ocr-audit.json"
            index_path = cache_directory / candidate.cache_key / "artifacts.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            if audit_path.relative_to(cache_directory).as_posix() not in index:
                continue
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            frames = {}
            assets = {asset.asset_id: asset for asset in manifest.recordings}
            for frame in audit:
                if frame["frame_ref"] not in index:
                    raise ValueError("Raw OCR crop is not in the verified artifact index.")
                asset = assets[frame["asset_id"]]
                if frame["crop"] != asset.chat_region.model_dump(mode="json") or not math.isclose(frame["replay_seconds"], asset.replay_offset(frame["media_seconds"]), abs_tol=1e-8):
                    raise ValueError("Raw OCR crop/alignment disagrees with its input manifest.")
                frames[(frame["asset_id"], frame["media_seconds"])] = frame
            return frames, candidate.cache_key
        except (ValueError, OSError, KeyError, TypeError):
            # A missing/mismatched/corrupt prior cache cannot provide raw input.
            continue
    return {}, None


class MediaPreprocessor:
    def __init__(self, repository_root: Path):
        self.repository_root = repository_root.resolve()

    def preprocess(self, manifest: RecordingManifest, cache_directory: Path) -> EvidenceCache:
        cache_directory = cache_directory.resolve()
        cache_directory.mkdir(parents=True, exist_ok=True)
        asset_inputs = []
        for asset in manifest.recordings:
            if asset.local_path is None or asset.asset_sha256 is None:
                asset_inputs.append({"asset_id": asset.asset_id, "sha256": None})
                continue
            source = resolve_local_path(asset.local_path, self.repository_root)
            if not source.is_file() or file_sha256(source) != asset.asset_sha256:
                raise ValueError(f"Recording changed or disappeared after manifest resolution: {asset.asset_id}")
            asset_inputs.append({"asset_id": asset.asset_id, "sha256": asset.asset_sha256})
        if not any(item["sha256"] for item in asset_inputs):
            raise MediaSetupError("No recording files are available. Put your videos in data/recordings/inbox/, edit data/recordings/manifest.json, then preprocess it. The G1 fixture remains available with the foundation demo command.")
        versions = {"preprocessor": PREPROCESSING_VERSION, "semantic_implementation": SEMANTIC_VERSION, "rapidocr-onnxruntime": package_version("rapidocr-onnxruntime"), "onnxruntime": package_version("onnxruntime"), "imageio-ffmpeg": package_version("imageio-ffmpeg"), "av": package_version("av"), "faster-whisper": package_version("faster-whisper"), "ffmpeg_binary_sha256": file_sha256(Path(ffmpeg_path()))}
        for asset in manifest.recordings:
            if asset.speech_model_path:
                model_path = resolve_local_path(asset.speech_model_path, self.repository_root, media=False)
                versions[f"speech_model:{asset.asset_id}"] = digest({p.name: file_sha256(p) for p in sorted(model_path.glob("*")) if p.is_file()}) if model_path.is_dir() else "missing"
        versions["ocr_processing_id"] = OCR_PROCESSING_ID
        input_hash = digest(asset_inputs)
        key = digest({"schema": "2", "inputs": asset_inputs, "manifest": manifest.model_dump(mode="json"), "versions": versions})
        destination = cache_directory / f"{key}.json"
        if destination.exists():
            return load_cache(destination)
        try:
            from PIL import Image
        except ImportError as error:
            raise MediaSetupError("Pillow image decoding is unavailable. Run python scripts/manage.py setup.") from error
        reusable_frames, reused_from = _reuse_ocr_audit(cache_directory, manifest, versions)
        provider = None
        directory = cache_directory / key
        directory.mkdir(parents=True, exist_ok=True)
        observations, reports, audit = [], [], []
        for asset in manifest.recordings:
            if asset.local_path is None or asset.asset_sha256 is None:
                reports.append(MediaAssetReport(asset_id=asset.asset_id, available=False, reason=asset.availability_reason or "Recording missing", audio_reason="Recording missing", speech_reason="Recording missing"))
                continue
            source = resolve_local_path(asset.local_path, self.repository_root)
            info = media_info(source)
            start = max(asset.media_start_seconds, asset.media_start_seconds - asset.timeline_start_seconds)
            end = min(asset.media_end_seconds or info["duration_seconds"], info["duration_seconds"])
            if start >= end:
                raise ValueError(f"Trim/alignment starts beyond recording duration for {asset.asset_id}.")
            asset_dir = directory / digest(asset.asset_id)[:16]
            frames_dir = asset_dir / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)
            tracker = VisibleLineTracker(digest([asset.asset_sha256, asset.asset_id, asset.chat_region.model_dump()]))
            frame_count = 0
            for index in range(math.ceil((end - start) / asset.sample_interval_seconds)):
                media_seconds = round(start + index * asset.sample_interval_seconds, 6)
                if media_seconds >= end:
                    break
                region = asset.chat_region
                frame_path = frames_dir / f"{index:06d}.png"
                reusable = reusable_frames.get((asset.asset_id, media_seconds))
                if reusable is not None:
                    shutil.copy2(cache_directory / reusable["frame_ref"], frame_path)
                    lines = [OCRLine(text=line["text"], confidence=line["confidence"], box=line["box"]) for line in reusable["lines"]]
                else:
                    result = run_ffmpeg(["-ss", str(media_seconds), "-i", str(source), "-map", "0:v:0", "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "pipe:1"])
                    if not result.stdout:
                        raise MediaSetupError(f"No frame returned at {media_seconds}s for {asset.asset_id}.")
                    frame = Image.open(io.BytesIO(result.stdout)).convert("RGB")
                    crop = frame.crop((int(region.x * frame.width), int(region.y * frame.height), min(frame.width, math.ceil((region.x + region.width) * frame.width)), min(frame.height, math.ceil((region.y + region.height) * frame.height))))
                    crop.save(frame_path)
                    if provider is None:
                        provider = RapidOCRProvider()
                    lines = provider.read(frame_path)
                frame_ref = frame_path.relative_to(cache_directory).as_posix()
                tracked = tracker.update(lines, media_seconds)
                audit.append({"asset_id": asset.asset_id, "media_seconds": media_seconds, "replay_seconds": asset.replay_offset(media_seconds), "frame_ref": frame_ref, "crop": region.model_dump(), "lines": [{"text": line.text, "confidence": line.confidence, "box": line.box, "track_id": track_id, "new_observation": new} for line, track_id, new in tracked]})
                for line, track_id, new in tracked:
                    if not new:
                        continue
                    text = line.text[:240]
                    meaning = interpret(text, confidence=line.confidence)
                    observations.append(CachedObservation(
                        observation_id=stable_id("observation", asset.asset_sha256, track_id, manifest.semantic_version), asset_id=asset.asset_id, stream_id=asset.stream_id,
                        evidence_mode=asset.evidence_mode, provider="sampled_frame_ocr", source_modality="chat", media_seconds=media_seconds, replay_seconds=asset.replay_offset(media_seconds), available_replay_seconds=asset.replay_offset(media_seconds),
                        raw_text=text, supporting_quote=text, sentiment=meaning.sentiment, abstention_reason=meaning.reason, aspect=meaning.aspect, target=meaning.target, semantic_confidence=meaning.confidence,
                        ocr_confidence=line.confidence, frame_ref=frame_ref, frame_reason=None, ocr_boxes=[line.box], track_id=track_id,
                        scene_id=asset.scene_id, extractor_version=manifest.semantic_version,
                    ))
                frame_count += 1
            audio_ref, audio_reason, speech_reason = None, None, None
            audio_available = info["audio_available"]
            speech_available = False
            if audio_available:
                audio_path = asset_dir / "audio.wav"
                activity = extract_audio(source, audio_path, start, end - start)
                audio_ref = audio_path.relative_to(cache_directory).as_posix()
                _write_json(asset_dir / "audio-activity.json", activity)
                if asset.audio_transcription == "faster_whisper":
                    try:
                        if not asset.speech_model_path:
                            raise MediaSetupError("speech_model_path is not configured; supply a local faster-whisper model directory.")
                        segments = transcribe(audio_path, resolve_local_path(asset.speech_model_path, self.repository_root, media=False), asset.language)
                        _write_json(asset_dir / "transcript.json", segments)
                        valid_segments, validation = validate_segments(segments, min(pcm_duration(audio_path), end - start))
                        _write_json(asset_dir / "transcript-validation.json", validation)
                        speech_available = bool(valid_segments)
                        rejected = len(segments) - len(valid_segments)
                        warned = sum(bool(s.get("repetition_warning") or s.get("quality_warning")) for s in valid_segments)
                        speech_reason = f"Rejected {rejected} ASR segment(s) outside valid audio support; {warned} retained segment(s) have quality warnings; see transcript-validation.json." if rejected or warned else (None if valid_segments else "ASR returned no speech segments.")
                        for segment_index, segment in enumerate(valid_segments):
                            media_seconds = start + segment["start_seconds"]
                            segment_end = start + segment["end_seconds"]
                            # Keep supported spans within the wire limit without manufacturing text.
                            text = segment["text"][:240].strip()
                            meaning = interpret(text, modality="speech", speaker_role=asset.speaker_role)
                            if segment["no_speech_probability"] > .6 or segment["avg_logprob"] < -1:
                                meaning = type(meaning)(meaning.aspect, "ambiguous", None, "ASR quality is too low for an attributable evaluation.", None)
                            if segment.get("repetition_warning"):
                                meaning = type(meaning)(meaning.aspect, "ambiguous", None, segment["repetition_warning"], None)
                            if segment.get("quality_warning"):
                                meaning = type(meaning)(meaning.aspect, "ambiguous", None, segment["quality_warning"], None)
                            observations.append(CachedObservation(
                                observation_id=stable_id("observation", asset.asset_sha256, "speech", media_seconds, segment_end, text, manifest.semantic_version), asset_id=asset.asset_id, stream_id=asset.stream_id,
                                evidence_mode=asset.evidence_mode, provider="recorded_asr", source_modality="speech", media_seconds=media_seconds, media_end_seconds=segment_end, replay_seconds=asset.replay_offset(media_seconds), replay_end_seconds=asset.replay_offset(segment_end), available_replay_seconds=asset.replay_offset(segment_end),
                                raw_text=text, supporting_quote=text, sentiment=meaning.sentiment, abstention_reason=meaning.reason, aspect=meaning.aspect, target=meaning.target, semantic_confidence=meaning.confidence,
                                ocr_confidence=None, confidence_reason="Audio ASR is not OCR; segment quality is retained in transcript.json.", frame_ref=None, frame_reason="Speech observation is supported by the extracted audio segment.", audio_ref=audio_ref,
                                scene_id=asset.scene_id, extractor_version=manifest.semantic_version,
                            ))
                    except MediaSetupError as error:
                        speech_reason = str(error)
                else:
                    speech_reason = "Audio decoded to PCM with measured activity; speech transcription disabled in manifest. Set audio_transcription=faster_whisper and a local speech_model_path."
            else:
                audio_reason = "No audio stream in this recording."
                speech_reason = audio_reason
            reports.append(MediaAssetReport(asset_id=asset.asset_id, available=True, duration_seconds=info["duration_seconds"], frame_count=frame_count, audio_available=audio_available, audio_reason=audio_reason, audio_ref=audio_ref, speech_available=speech_available, speech_reason=speech_reason))
        observations.sort(key=lambda o: (o.available_replay_seconds if o.available_replay_seconds is not None else o.replay_seconds, o.replay_seconds, o.observation_id))
        _write_json(directory / "ocr-audit.json", audit)
        artifacts = {p.relative_to(cache_directory).as_posix(): file_sha256(p) for p in sorted(directory.rglob("*")) if p.is_file() and p.name != "artifacts.json"}
        _write_json(directory / "artifacts.json", artifacts)
        versions["artifact_index_sha256"] = file_sha256(directory / "artifacts.json")
        versions["semantics"] = "heuristic lexical attribution; uncalibrated; ambiguous text abstains"
        versions["ocr_identity"] = "adjacent-frame visible-line tracking, not native chat message IDs"
        versions["ocr_reused_from_cache"] = reused_from or "none; decoded and OCR processed normally"
        cache = EvidenceCache(cache_key=key, input_sha256=input_hash, payload_sha256=digest([o.model_dump(mode="json") for o in observations]), manifest=manifest, observations=observations, asset_reports=reports, extraction_metadata=versions)
        versions["content_sha256"] = digest(cache.model_dump(mode="json"))
        cache = cache.model_copy(update={"extraction_metadata": dict(versions)})
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=cache_directory, suffix=".tmp", delete=False) as file:
            temporary = Path(file.name)
            file.write(cache.model_dump_json(indent=2) + "\n")
        os.replace(temporary, destination)
        return cache


def build_windows(cache: EvidenceCache, run_id: str, origin: datetime) -> list[SourceWindow]:
    if origin.tzinfo is None or origin.utcoffset() is None:
        raise ValueError("Replay origin must be timezone aware.")
    reports = {r.asset_id: r for r in cache.asset_reports}
    windows = []
    for observation in cache.observations:
        report = reports.get(observation.asset_id)
        modalities = [
            ModalityAvailability(modality="chat", available=observation.source_modality == "chat", reason=None if observation.source_modality == "chat" else "This source window contains a speech segment, not chat."),
            ModalityAvailability(modality="speech", available=observation.source_modality == "speech", reason=None if observation.source_modality == "speech" else (report.speech_reason if report and report.speech_reason else "No aligned speech segment belongs to this chat window.")),
            ModalityAvailability(modality="facecam", available=False, reason="Facecam is not interpreted; no face-derived approval."),
        ]
        windows.append(SourceWindow(
            run_id=run_id, window_id=stable_id("window", observation.observation_id, cache.cache_key), stream_id=observation.stream_id, asset_id=observation.asset_id,
            evidence_mode=observation.evidence_mode, event_at=origin + timedelta(seconds=observation.replay_seconds), available_at=origin + timedelta(seconds=observation.available_replay_seconds if observation.available_replay_seconds is not None else observation.replay_seconds),
            source_media_seconds=observation.media_seconds, replay_seconds=observation.replay_seconds, raw_text=observation.raw_text, cache_key=cache.cache_key, observation_id=observation.observation_id,
            provider=observation.provider, source_modality=observation.source_modality, frame_ref=observation.frame_ref, frame_reason=observation.frame_reason, ocr_confidence=observation.ocr_confidence, confidence_reason=observation.confidence_reason, audio_ref=observation.audio_ref,
            modalities=modalities, observation=observation,
        ))
    return windows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/recordings/manifest.json"))
    parser.add_argument("--cache-dir", type=Path, default=Path("var/evidence-cache"))
    parser.add_argument("--inspect-cache", type=Path)
    args = parser.parse_args()
    try:
        if args.inspect_cache:
            cache = load_cache(args.inspect_cache)
        else:
            root = Path(__file__).resolve().parents[2]
            manifest = load_manifest(root / args.manifest, root)
            cache = MediaPreprocessor(root).preprocess(manifest, root / args.cache_dir)
        print(json.dumps({"cache_key": cache.cache_key, "cache_path": str(args.inspect_cache or args.cache_dir / f"{cache.cache_key}.json"), "observations": len(cache.observations), "attributable_observations": sum(o.sentiment is not None for o in cache.observations), "providers": sorted({o.provider for o in cache.observations}), "evidence_modes": sorted({o.evidence_mode for o in cache.observations}), "asset_reports": [r.model_dump(mode="json") for r in cache.asset_reports]}, indent=2))
    except (MediaSetupError, ValueError, OSError) as error:
        parser.exit(2, f"Recording preprocessing failed: {error}\n")


if __name__ == "__main__":
    main()

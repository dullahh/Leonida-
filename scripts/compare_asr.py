"""Compare both local ASR models on every t1-t5 interval; never select evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.core.identity import digest
from backend.ingestion.audio import ASR_VERSION, LocalASR, cached_transcribe, pcm_duration
from backend.ingestion.recordings import load_cache
from backend.ingestion.tools import file_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cache", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "var/asr-comparison/v1")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/ASR_COMPARISON.md")
    args = parser.parse_args()
    source = args.source_cache or Path((ROOT / "var/last-recording-cache.txt").read_text(encoding="utf-8").strip())
    cache = load_cache(source)
    assets = {a.asset_id: a for a in cache.manifest.recordings}
    reports = {r.asset_id: r for r in cache.asset_reports}
    jobs = {}
    for asset_id in ("t1", "t2", "t3", "t4", "t5"):
        asset, report = assets[asset_id], reports[asset_id]
        start = max(asset.media_start_seconds, asset.media_start_seconds - asset.timeline_start_seconds)
        jobs[asset_id] = (asset, source.parent / report.audio_ref, start,
                          min(asset.media_end_seconds or report.duration_seconds, report.duration_seconds) - start)
    # Actual source samples, not a generated silence fixture. This quiet lead-in
    # is an overlapping review-only interval and is never extra ingested evidence.
    quiet_key = digest([assets["t1"].asset_sha256, file_sha256(jobs["t1"][1]), jobs["t1"][2], 2])
    quiet = ROOT / "var/asr-comparison/inputs" / quiet_key / "t1-first-2s.wav"
    quiet.parent.mkdir(parents=True, exist_ok=True)
    if not quiet.exists():
        with wave.open(str(jobs["t1"][1]), "rb") as original:
            params, samples = original.getparams(), original.readframes(2 * original.getframerate())
        with wave.open(str(quiet), "wb") as output:
            output.setparams(params)
            output.writeframes(samples)
    jobs["t1-quiet-lead-in"] = (assets["t1"], quiet, jobs["t1"][2], 2)
    results, loads = {}, {}
    for name in ("tiny.en", "small.en"):
        engine = LocalASR(ROOT / f"var/models/faster-whisper-{name}")
        loads[name] = engine.load_seconds
        results[name] = {}
        for asset_id, (asset, audio, start, limit) in jobs.items():
            media = ROOT / asset.local_path
            if file_sha256(media) != asset.asset_sha256:
                raise ValueError("Comparison media hash changed")
            result = cached_transcribe(audio, ROOT / f"var/models/faster-whisper-{name}", asset.language,
                                      ROOT / "var/asr-cache", asset.asset_sha256, start, engine, limit)
            results[name][asset_id] = result
            print(name, asset_id, f"{result['processing_seconds']:.3f}s", dict(Counter(a['status'] for a in result['audit'])), flush=True)
        del engine
    run_key = digest({name: {a: r["cache_key"] for a, r in rows.items()} for name, rows in results.items()})
    destination = args.output / run_key
    destination.mkdir(parents=True, exist_ok=True)
    review = {"comparison_version": "asr-comparison-v1", "source_evidence_cache": cache.cache_key,
              "run_key": run_key, "model_load_seconds_this_run": loads, "results": results,
              "speaker_roles": {name: job[0].speaker_role for name, job in jobs.items()},
              "manual_reference_transcripts": None, "word_accuracy_improvement": "not evaluated",
              "listening_review_required": True}
    lines = ["# Local ASR comparison - listening review required", "",
             f"Comparison `{run_key}`; source immutable cache `{cache.cache_key}`.", "",
             "Both models ran locally, serially, on the identical original PCM for all five complete clips plus the actual t1 0-2s quiet lead-in. "
             "Every 15-second window and final partial window appears below. Times are audio-relative; "
             "add the listed media origin for original video time. No timestamps were clipped or repaired. "
             "All rows require your listening review: no manually verified reference transcript exists, "
             "so no word-accuracy improvement or speaker identity is claimed. Condition labels are review candidates from prior source notes, not new acoustic annotations.", "",
             "Model/configuration and quality thresholds are recorded in each content-addressed JSON. "
             "Processing time includes inference, VAD and gates, excludes shared model load and hash/cache I/O. "
             "Reused results retain the original measured inference time; cache-hit latency is not substituted. "
             "Audio totals include the overlapping 2-second review control. "
             "Segment log probability/no-speech/compression are decoder diagnostics, not calibrated confidence.", "",
             "| Model | Version (content SHA-256) | Model load (s) | Processing (s) | Audio (s) | RTF | Accepted / uncertain / rejected |",
             "|---|---|---:|---:|---:|---:|---|"]
    for name, rows in results.items():
        elapsed = sum(r["processing_seconds"] for r in rows.values())
        duration = sum(r["identity"]["duration_seconds"] for r in rows.values())
        counts = Counter(a["status"] for r in rows.values() for a in r["audit"])
        version = next(iter(rows.values()))["identity"]["model"]["version"]
        load_time = next(iter(rows.values()))["model_load_seconds"]
        lines.append(f"| {name} | `{version}` | {load_time:.3f} | {elapsed:.3f} | {duration:.3f} | {elapsed / duration:.3f} | {counts['accepted']} / {counts['uncertain']} / {counts['rejected']} |")
    lines += ["", "VAD empty windows are recorded as rejected/no_vad_speech with null decoder diagnostics; no text was manufactured. Accepted means the heuristic ASR gates passed, not that the words or speaker were human verified. Uncertain and rejected rows are audit-only and never semantic/reaction inputs.", ""]
    conditions = {"t1": "ordinary conversation / possible streamer-game dialogue overlap",
                  "t2": "ordinary conversation / possible background music",
                  "t3": "speech with prior compression/repetition warnings; tail timestamp regression",
                  "t4": "shouting candidate; historical repeated-no loop at 0-30s; possible overlap",
                  "t5": "multiple-voice role-play / shouting candidates; tail timestamp regression",
                  "t1-quiet-lead-in": "actual quiet lead-in / no-speech control; listening review required"}
    for asset_id in results["tiny.en"]:
        tiny, small = results["tiny.en"][asset_id], results["small.en"][asset_id]
        duration = tiny["identity"]["duration_seconds"]
        lines += [f"## {asset_id}: {conditions[asset_id]}", "",
                  f"Media origin {tiny['identity']['media_start_seconds']:.3f}s; duration {duration:.3f}s; manifest speaker role: {jobs[asset_id][0].speaker_role}. "
                  f"Processing: tiny {tiny['processing_seconds']:.3f}s; small {small['processing_seconds']:.3f}s. **Listening review: required.**", "",
                  "| Audio interval (s) | tiny.en: transcript; diagnostics; decision | small.en: transcript; diagnostics; decision | tiny / small processing (s) |",
                  "|---|---|---|---|"]
        for start in range(0, int(duration) + 1, 15):
            if start >= duration:
                break
            cells, timings = [], []
            for result in (tiny, small):
                parts = []
                window_time = None
                for entry in result["audit"]:
                    s = entry["raw_segment"]
                    if s["window_start_seconds"] != start:
                        continue
                    window_time = s.get("window_processing_seconds")
                    text = s["text"].replace("|", "\\|").replace("\n", " ") or "[no decoded speech]"
                    metrics = "; ".join(f"{k}={s[k]:.3f}" if s.get(k) is not None else f"{k}=null" for k in ("avg_logprob", "no_speech_probability", "compression_ratio"))
                    parts.append(f"{s['start_seconds']:.3f}-{s['end_seconds']:.3f}: {text}<br>{metrics}<br>**{entry['status']}**: {', '.join(entry['reasons'])}")
                cells.append("<br><br>".join(parts) or "[no returned segment]")
                timings.append(f"{window_time:.3f}" if window_time is not None else "not measured")
            lines.append(f"| {start:.3f}-{min(start + 15, duration):.3f} | {cells[0]} | {cells[1]} | {' / '.join(timings)} |")
        lines.append("")
    lines += ["## Historical failure coverage", "", "These old provider outputs are retained unchanged and are not ingested by this comparison:", ""]
    for report in cache.asset_reports:
        if not report.audio_ref:
            continue
        folder = source.parent / report.audio_ref
        raw_path = folder.parent / "transcript.json"
        if not raw_path.exists():
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        duration = pcm_duration(folder)
        for s in raw:
            if s["end_seconds"] > duration or s.get("compression_ratio", 0) > 2.4:
                lines.append(f"- {report.asset_id} old {s['start_seconds']:.3f}-{s['end_seconds']:.3f}s vs PCM {duration:.3f}s; compression={s.get('compression_ratio')}; text excerpt: {s['text'][:160]}")
    lines += ["", "Full raw text, per-segment diagnostics/reasons, original window times and processing receipts: "
              f"`var/asr-comparison/v1/{run_key}/review.json`. Per-model immutable results: `var/asr-cache/{ASR_VERSION}/`. "
              "Playback evidence and its pointer were not changed. Listen against the original source audio at the listed intervals, especially short repetitions, shouting/music/overlap, VAD omissions and final-window rejections.", ""]
    for filename, content in (("review.json", json.dumps(review, indent=2, ensure_ascii=False) + "\n"), ("review.md", "\n".join(lines))):
        path = destination / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    args.report.write_text("\n".join(line.rstrip() for line in (destination / "review.md").read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    print("COMPARISON:", destination, flush=True)


if __name__ == "__main__":
    main()

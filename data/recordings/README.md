# Local recording input

Put authorized Twitch GTA V screen recordings in `data/recordings/inbox/`.
The manifest `data/recordings/manifest.json` is the editable starting point. It
currently references the three supplied files `t1.mp4`, `t2.mp4` and `t3.mp4`;
manifests support two to six slots. Files are local inputs, not uploaded.
All file and model paths resolve from the repository root. Supported containers
are MP4, MKV, MOV, WebM, AVI and M4V. A missing slot remains explicitly unavailable.

For each recording set a unique `asset_id`, `stream_id`, readable `label` and
`local_path`. Leave `asset_sha256` null to compute it from the actual bytes during
preprocessing; a supplied hash is verified, never silently replaced.

- `media_start_seconds` trims the beginning of that file.
- `timeline_start_seconds` places that trimmed beginning on the shared replay.
- `replay_seconds = media_seconds - media_start_seconds + timeline_start_seconds`.
- `media_end_seconds` optionally limits preprocessing to a shorter excerpt.
- `chat_region` is normalized `x`, `y`, `width`, `height` of the visible chat panel.
- `sample_interval_seconds` defaults to 2 seconds. Fast chat may need 1 second.
- `scene_id` is a manual label, not automatically recognized gameplay.

Example: a stream trimmed at media time 120 seconds with timeline start 5 seconds
contributes its frame at media time 130 seconds at replay time 15 seconds.
Negative timeline starts are supported; pre-replay media is skipped.

The supplied `t1`/`t2`/`t3` configuration uses zero trim and timeline offsets, so
each clip starts at replay second zero. This synchronizes playback positions;
it does not establish that the recordings show the same event or independent
streamers. Source channel identities remain unverified, and the IDs are clip
labels. All three use `scene_id=manual-unassigned` and `speaker_role=unknown`.

Their manually inspected crops differ: `t1` uses the separate white chat panel
on the right; `t2` and `t3` use a small upper-right chat overlay. The welcome
banner in `t1` and game UI/watermark overlapping chat in `t2`/`t3` can enter OCR.
Treat such text as OCR contamination, not automatically as chat or game-quality
evidence. Adjust the crop when replacing these files; it is not auto-detected.

From the repository root:

```powershell
python scripts/manage.py setup
python scripts/manage.py setup-speech
python scripts/manage.py preprocess --manifest data/recordings/manifest.json
python scripts/manage.py demo --scenario recordings
```

Preprocessing prints a content-addressed JSON cache path, and the recordings
launcher consumes the most recently prepared cache. Open http://127.0.0.1:8000/.
Cache playback does not run OCR, decoding or model downloads.

## OCR, audio and missing tools

The locked setup includes `imageio-ffmpeg`, its FFmpeg executable, PyAV, Pillow,
RapidOCR with CPU ONNX models and faster-whisper. FFprobe and Tesseract are not
required. An existing FFmpeg can be selected by setting `LEONIDA_FFMPEG` to its
executable. A bad override fails with its path; missing dependencies instruct you
to run setup. OCR errors stop preprocessing rather than supplying invented text.

All audio tracks are decoded to 16 kHz mono PCM. Two-second RMS activity
measurements are cached. Activity is not sentiment and does not prove speech.
Future preprocessing selects its model from `config/local_asr.json` or explicit
`--asr-model small.en` (quality) / `--asr-model tiny.en` (fast fallback). The old
manifest's tiny path remains historical input; the selected model path is recorded
in each new cache's manifest. Run `python scripts/manage.py setup-speech --asr-model small.en`
once to download the local CTranslate2 model; select `tiny.en` to install the fallback.
The provider never downloads models during preprocessing or playback, and never
silently falls back. Missing models or failed ASR stop new preprocessing before
publishing a complete evidence cache. Existing cached playback remains available.
Set `audio_transcription=disabled` explicitly
if only PCM/activity and chat evidence are wanted.

Keep `speaker_role=unknown` unless the segment is known to be streamer commentary.
ASR does not separate NPC dialogue, music vocals or other voices. Unknown-speaker
transcripts remain visible evidence but abstain from game-quality sentiment.
For a mixed recording, trim to a verified commentary excerpt before setting
`speaker_role=streamer`; this is a manual attribution claim, not diarization.
ASR uses serial 15-second windows without overlap, English transcription, local
Silero VAD, CPU int8 and one inference thread. VAD times are restored to original
audio coordinates before strict checks; media/replay offsets are applied separately.
ASR text is model output, not a verified quotation. Out-of-duration/window timestamps,
severe loops, compression above 2.4, average log probability below -1.0 or no-speech
probability above .6 are rejected. Borderline diagnostics and short repetitions
are uncertain. Only accepted segments enter classification/reactions; uncertain
and rejected text stays audit-only. Gate coefficients are heuristic. Every segment
still requires listening for word/speaker verification.
Raw output, statuses/reasons, timing and content-hashed model/settings receipts
remain in `transcript.json`, `transcript-validation.json` and `asr-receipt.json`.
The independent ASR cache lives at `var/asr-cache/local-asr-v2/`.

ASR-only command preserving current playback selection and requiring verified OCR reuse:

```powershell
python scripts/manage.py preprocess --asr-model small.en --reuse-ocr-only --no-select-cache
```

Use `--asr-model tiny.en` for the explicit fast fallback. Omit `--no-select-cache`
only when you want the new evidence cache selected for future demo launches.
Compare both models without changing evidence selection:
`.venv/Scripts/python.exe -B scripts/compare_asr.py`.
See [ASR audit](../../docs/LOCAL_ASR_UPGRADE.md) and [side-by-side review](../../docs/ASR_COMPARISON.md).

## Cached evidence and limitations

The cache key includes actual video hashes, crop, sampling, trim/alignment,
manifest versions, actual installed provider versions, FFmpeg hash and local
speech-model file hashes. Changing them produces a new cache. The immutable cache
contains supported interpretations while its artifact directory retains every
sampled chat crop, raw OCR text/confidence/boxes/track identity, extracted audio,
activity measurements and ASR segments. Loading verifies hashes and refuses
corrupted evidence. Do not edit cache JSON to change semantics; change the version
or input manifest and preprocess again.
For an ASR-only preprocessing update, verified raw OCR crops/audit may be reused
when the media hash, crop, sampling, offsets and OCR processing/provider versions
match exactly. Interpretations are rebuilt; old derived sentiment is not reused
as raw input. Missing or mismatched provenance runs OCR again.

Visible lines are tracked only across adjacent sampled frames. A stationary line
does not count repeatedly, and a line that disappears then returns can become a
new occurrence. Pixels do not expose native Twitch message IDs; identical lines
with indistinguishable timing cannot always be separated. Fast scrolling may
lose lines between samples. OCR boxes are pixel coordinates within the stored
chat crop. OCR confidence below 0.75 abstains. The simple supported-text sentiment
heuristic is uncalibrated; sarcasm, negation, ambiguous targets and mixed wording
abstain. No facecam sentiment or automatic scene recognition is used.

Real recordings use `evidence_mode=recorded`, `content_game_id=gta5` and
`evidence_scope=proxy_demo`. Generated verification videos use
`evidence_mode=synthetic_replay` even though decoding/OCR/ASR actually execute.
Neither kind is GTA VI gameplay evidence, and neither automatically prices an
actual GTA VI venue contract. Actual quote freshness remains separate.

Structured fallback checks need no media or model:

```powershell
.venv/Scripts/python.exe -m backend.ingestion.replay --scenario all --validate-only
```

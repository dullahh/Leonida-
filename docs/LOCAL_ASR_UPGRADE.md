# Local speech transcription upgrade

Scope: one thread, no agents, local CPU transcription only. OCR implementation,
claim semantics, reaction policy, pricing, frontend, supplied media, speaker-review
records and synthetic scenarios are unchanged. Model installation downloads public
weights; inference never sends audio externally and uses no paid API.

## Pipeline audit and resulting behaviour

| Area | Previous primary path | New preprocessing |
|---|---|---|
| Audio | FFmpeg first audio track, mono signed little-endian PCM16 WAV, 16 kHz; no loudness normalization or denoising | Same extraction, `mono-pcm16-16000-v1`; PCM content hash recorded |
| Chunking | Whole extracted clip passed to tiny.en; Whisper internal 30-second feature windows; no application overlap | Explicit consecutive 15-second windows, zero overlap; both models use identical intervals/settings |
| VAD | Disabled; 2-second RMS is activity only | Bundled local Silero VAD, threshold .5, minimum speech 250ms, minimum silence 500ms, padding 200ms; RMS remains unchanged |
| Time | Provider audio-relative segment times plus manifest media/replay offsets; tolerated and clipped up to 50ms at final boundary | Original provider window times retained; VAD restores uncompressed audio coordinates; add window offset once, media offset once, then existing replay mapping; strict media/PCM and window bounds; no clipping/repair |
| Language | `eng` mapped to `en`, other values passed to library | Explicit English-only `eng`/`en`; other values fail rather than silently selecting English |
| Decode | CPU int8, two inference threads, beam1, temperature0, no previous-text conditioning; default library compression/logprob/no-speech thresholds | CPU int8, one inference thread/worker, beam5, best_of1, temperature0, previous-text conditioning off; library quality thresholds disabled so returned bad text survives into our independent audit |
| Repetition | Three adjacent repetitions triggered a warning; compression above2.4 warned; these texts were classified first and then made to abstain | Severe repetition/compression rejected before classification; shorter repetitions uncertain and audit-only |
| Confidence | `avg_logprob < -1` or `no_speech_prob > .6` overwrote interpretation after the classifier ran | Raw `avg_logprob`, `compression_ratio`, `no_speech_probability` retained; all ASR quality gates run first |
| Speaker/uncertainty | Manifest speaker role (all five unknown); warnings/null sentiment | Same explicit speaker role; confidence never infers identity; accepted/uncertain/rejected recognition status is separate from attribution; accepted unknown speech still abstains |
| Cache | Immutable evidence key included media/manifest/provider/model-file hashes and implementation version; transcription settings depended on implementation bump | Independent versioned ASR cache includes media/PCM hashes, audio-preprocessing version, model name and content version, package versions, all explicit decode/VAD settings, window/offset/duration, CPU settings and gate version/thresholds; new evidence interpretation gets a new key |

The installed library's VAD implementation uses one ONNX thread and restores
original audio timestamps. See the primary [faster-whisper source](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py)
and [VAD source](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/vad.py).
The installed implementation was also inspected locally; package versions are in
each ASR receipt. These references describe implementation, not measured accuracy.

## Gates and audit boundary

`asr-quality-v2` rejects any negative/nonfinite/zero-length/out-of-support timestamp,
including a final timestamp just1ms too long. It also rejects times outside their
own decoding window, even if they fit in the complete clip. It never shortens the
timestamp to fit.

Severe loops mean eight consecutive copies of one normalized token, four copies
of a2–12-token phrase, or three consecutive identical segment texts (all three
are rejected). Compression above2.4, average log probability below-1.0, or no-speech
probability above.6 rejects a segment independently. Missing/nonfinite or invalid
diagnostics also reject returned text. Three to seven single-token repetitions,
log probability between-1.0 and-.8, or no-speech probability between.35 and.6 are
uncertain. These thresholds are conservative heuristics, not calibrated confidence.
Natural repeated speech can be withheld and requires listening review.

Only accepted speech becomes a `CachedObservation` and reaches the existing
semantic classifier/reaction pipeline. Uncertain/rejected output remains in
`transcript.json`, `transcript-validation.json`, `asr-receipt.json` and the independent
ASR JSON, with its full unmodified text, timing and reasons. An empty VAD window has
empty text and null decoder diagnostics, never invented silence probabilities.
Recognition acceptance does not verify the words, speaker or game-quality target.

`confidence_reason` exposes model name/content version, gate version, status/counts,
reasons and audit path through existing source details. Supported-speech decision
receipts also carry that provenance in their explanation. No wire-schema or frontend
architecture change was needed. Failure to load/transcribe a configured model stops
new preprocessing; existing cached playback continues without providers.

## Commands and cache selection

```powershell
# Explicit installation only: public model weights, no audio upload.
python scripts/manage.py setup-speech --asr-model small.en

# Evaluation: both complete t1-t5 clips, original verified PCM, separate cache/report.
.venv/Scripts/python.exe -B scripts/compare_asr.py

# Exact ASR-only preprocessing command used for the quality pipeline check.
python scripts/manage.py preprocess --asr-model small.en --reuse-ocr-only --no-select-cache

# Explicit fast fallback, using the same quality gates.
python scripts/manage.py preprocess --asr-model tiny.en --reuse-ocr-only --no-select-cache
```

`--reuse-ocr-only` refuses to invoke OCR when verified raw artifacts cannot be
reused. When a playback pointer exists it verifies that entire immutable source
cache, preserves its original OCR observations/interpretations and artifact paths
exactly, and replaces only speech. This also handles the existing composed cache's
mixed version labels without reclassifying OCR. `--no-select-cache` preserves
`var/last-recording-cache.txt`. Omitting that
flag explicitly selects the newly prepared evidence cache for future launches.
The ASR model switch applies to future preprocessing; loading an old immutable
cache never applies new gates or changes its recorded model/transcript.

Independent ASR results: `var/asr-cache/local-asr-v2/<content-key>.json`.
Comparison reports: `var/asr-comparison/v1/<comparison-key>/review.json` and
`review.md`. [Side-by-side review](ASR_COMPARISON.md) contains every interval,
both full transcripts, segment diagnostics, decisions, reasons and per-window
processing times. All21 full-clip windows plus the actual t1 0–2s quiet lead-in
require listening review. The overlapping lead-in is comparison-only and never
additional ingested evidence. Acoustic condition labels
are candidates from prior source notes; no new listening annotation is claimed.

## Evaluation and verification

Both models completed locally on271.744s of original audio plus the overlapping
2s no-speech control. Every15-second window, final partial window, and control
appears in the side-by-side report, including ordinary-speech candidates, shouting,
music/overlap candidates, the known t4 loop and historical out-of-duration tails.
The acoustic labels still require your listening verification. Neither model has
manually verified reference transcripts; word accuracy/WER was not measured.

| Model | Downloaded model files | Processing including VAD/gates | RTF | Accepted / uncertain / rejected |
|---|---:|---:|---:|---|
| tiny.en | 78,090,594 bytes already local | 66.851s | .244 | 40 / 9 / 52 |
| small.en | 486,098,798 bytes (486.1MB / 463.6MiB) | 275.033s | 1.005 | 35 / 10 / 24 |

Small was4.114x slower in this single serial CPU run. Times exclude model loading
(tiny1.255s, small2.679s), source hashing, extraction and cache I/O; per-window
measurements are in the report. This is a local timing comparison under development
machine load, not a hardware benchmark. Segment counts differ because model
segmentation differs, so acceptance counts are not an accuracy metric. The control
returned no VAD speech under both models, empty text and null decoder diagnostics.

Small's public download was pinned to repository revision
`d1d751a5f8271d482d14ca55d9e2deeebbae577f` from
[Systran/faster-whisper-small.en](https://huggingface.co/Systran/faster-whisper-small.en).
The4 downloaded files total486,098,798 bytes: `model.bin`483,545,366,
`tokenizer.json`2,128,466, `vocabulary.txt`422,309 and `config.json`2,657.
Actual content versions:

- tiny: `ecec04d56f4ea180fdc1316c09d044878c88a89d1c77e9c932bcb13acced3a0a`.
- small: `79ae67d827bfa96ef9029ecc8087e5c88493249855deec43a9e4b00be43faabe`.

Examples are machine output, **not corrected reference transcripts**:

| Interval | Before / tiny output | Small output and gate result |
|---|---|---|
| t4 initial0–30s legacy / current0–15s | Legacy tiny repeated“no” with compression26.235; the new tiny pass still loops | Small also loops in0–15s. Both are rejected for severe repetition and compression; upgrading the model alone did not cure this failure |
| t4 approximately15–18s | Tiny:“Get up, get up, get up, bro, stop doing that, bro.”; rejected because decoder compression exceeds2.4 | Small:“Bro, get up! Get up! Get up, bro! Stop doin' that, bro!”; recognition accepted, speaker remains unknown and quality interpretation abstains |
| t1 tail30s onward | Tiny:“My wife, my car, it's my wife, my wife, my wife, my wife.”; severe repetition rejected | Small produces a30–40.190s segment against38.357s of audio; rejected, never shortened to fit |
| t1 first0–15s | Tiny gates pass:“I didn't tell her you had that opportunity…” | Small's differing“What the hell is going on?”segments have average log probability-1.025 and are rejected; this is a counterexample to claiming universal improvement |
| t5 legacy tail | Legacy64.960–67.560s exceeded actual PCM67.541s by about19ms and could previously be clipped under the50ms tolerance | New gates reject any such overflow; current small tail60–67.490s is within duration but uncertain for no-speech probability.559 |

Final comparison:
`var/asr-comparison/v1/d8730e510b079f8502bf1facea19dc7c4701cc19a98f2f219c451e602a448aba/`.
Final new quality evidence:
`var/evidence-cache/c50cb055b472236a68dc526cbca092cdcead3367384dbc8a8437de0bf67ea751.json`.
It has1,588 observations:1,553 original OCR observations preserved exactly and35
accepted small speech observations. The full speech audit has35 accepted,10 uncertain
and23 rejected segments; the separate quiet control contributes one more rejection
to the comparison only. All speaker roles remain unknown, supported quality claims,
estimates and decisions remain zero. The config default was changed to small only
after this full preprocessing command and strict artifact/recognition checks succeeded.

Original evidence cache `aa20c31e1a27bbf0fe075f2c9136360e7096731d9365cdd247c89ade4afe95b6`
still has SHA-256`ca68a83c22a8ac466866c274ec6fc20fc35f2db3ab54d1bf70c7f9fe31d1e507`.
Its bytes and playback pointer were checked unchanged. Future processing is explicit;
the current running desk and saved runs continue using their original inputs.

## Checks actually run

| Command/check | Result |
|---|---|
| `.venv/Scripts/python.exe -B -m unittest discover -s tests/g3 -p test_local_asr.py -v` | 7 focused tests passed: token/phrase/cross-segment loops, compression, exact timing bounds, silence/null diagnostics, uncertainty, cache-version separation, pre-classifier/reaction exclusion, immutable cache reuse, speaker-role preservation and receipt provenance |
| `python scripts/manage.py check --gate G3` | Exit0; 22 tests passed; serialization/OpenAPI/generated-type drift, six-scenario validation, TypeScript and frontend build passed |
| `.venv/Scripts/python.exe -B -m unittest discover -s tests/g4 -v` | Exit0; all11 existing G4/release/display/browser tests passed in52.831s, no skips |
| `python scripts/manage.py demo-check --scenario all` | Exit0; six isolated fixture HTTP/WS/receipt/trace inspections passed; servers/databases closed |
| `python scripts/manage.py demo-check --scenario recordings --cache var/evidence-cache/c50cb055b472236a68dc526cbca092cdcead3367384dbc8a8437de0bf67ea751.json` | Exit0; 1,588 unique observations, HTTP/WS equality, no supported quality claims/estimates/orders/fills; isolated server/database closed |
| Quality CLI command above | Exit0; all five assets processed;35 accepted speech observations; preserved1,553 OCR objects exactly; strict cache/artifact verification passed |
| `python scripts/manage.py preprocess --reuse-ocr-only --no-select-cache` | Exit0; default selected small and reused the validated c50cb055 quality cache |
| Explicit tiny fallback command above | Exit0; `var/evidence-cache/f265115f5e23b9d6b228b68ab1374975a669ef452af97b992ee1d11000b778fd.json`;40 accepted speech plus the same1,553 OCR observations |

G4 again emitted the previously documented Windows Proactor connection-reset/
unclosed-transport and Uvicorn graceful-shutdown messages during browser teardown;
assertions passed. This change does not address those platform warnings. The first
redirected G3 shell wrapper treated unittest stderr as a PowerShell native-command
error despite the inner checks passing; the direct command was rerun and exited0.
No application change was made for that shell behaviour. Logs are local under
`var/asr-upgrade-*.log`. Only this ASR upgrade is committed; models/media/runtime
caches remain ignored. No deployment, push or existing-server restart occurred.

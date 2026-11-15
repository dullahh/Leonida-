# Leonida Alpha

Reaction telemetry is now available on each recording: activity over time, strongest recent text cue, source/target trace and pricing exclusion. All1651 recorded observations retain zero supported quality claims; contextual reactions do not create estimates. See [reaction integration results and launch command](docs/REACTION_TELEMETRY.md). The current running demo uses `var/recordings-reactions.sqlite3`; earlier process/database notes below describe previous checkpoints.

A local multi-stream evidence and prediction-market research desk. G3 integrates local GTA V recordings, cached chat OCR/audio transcripts, synchronized replay, heuristic scenario estimates and paper decisions. Separate synthetic fixtures demonstrate depth-aware paper entries, exits and accounting.

GTA V is **proxy demo evidence**. Actual GTA VI venue quotes are displayed separately and do not receive a correction from this material. No real-money routes exist. See [G3 acceptance and gaps](docs/G3_HANDOFF.md).

## Launch the verified demo

From `C:\Users\abdul\Desktop\drhck` in PowerShell:

```powershell
python scripts/manage.py demo
```

Open http://127.0.0.1:8000. The default selects the latest preprocessed recording cache; without one, it uses the labelled G1 fixture. Press Play. This checkout now selects the three supplied recordings t1/t2/t3. See [their crop, OCR and speech review](docs/RECORDING_REVIEW.md). All extracted observations currently abstain from game-quality scoring. The earlier generated test cache remains available. Everything after setup/preprocessing works offline.

The current G3 demo is already running on8000 with `var/g3-recordings.sqlite3`, paused at0. Its restart command is `python scripts/manage.py demo --scenario recordings --db var/g3-recordings.sqlite3`; stop the existing server before restarting. Choose **Courtroom praise** then **Load isolated scenario** to see an explicit qualifying fixture change the estimate and simulate a paper fill. It creates a new run, separate from your clips. **Return to recordings** switches back. Synthetic accounting advances forward; Reset starts a fresh run for earlier playback.

## Use your recordings

1. Put videos in `data/recordings/inbox/`, for example `stream-1.mp4` and `stream-2.mp4`.
2. Edit [data/recordings/manifest.json](data/recordings/manifest.json). Set each file path, unique streamer/asset ID, trim start, timeline offset and normalized chat crop. Two to six slots are supported; missing slots remain visibly unavailable. Set `media_end_seconds` for a short initial excerpt.
3. Run:

```powershell
python scripts/manage.py setup-speech
python scripts/manage.py preprocess --manifest data/recordings/manifest.json
python scripts/manage.py demo --scenario recordings
```

`setup-speech` is a one-time network download of the small English local model to `var/models/faster-whisper-tiny.en`; no API key is needed. It is already installed here. Preprocessing prints an immutable cache path and records it in `var/last-recording-cache.txt`. To select a specific previous extraction:

```powershell
python scripts/manage.py demo --scenario recordings --cache var/evidence-cache/YOUR_CACHE_HASH.json
```

Paths in manifests resolve from the repository root. Alignment is `replay = media - media_start_seconds + timeline_start_seconds`. A crop uses fractions of frame width/height, not pixels. Leave `asset_sha256` null to compute it from your actual file. See [recording setup and limitations](data/recordings/README.md).

Audio is decoded to PCM with measured activity. The default manifest also requests local Whisper transcription. Missing models/audio produce explicit availability reasons; they never become neutral sentiment. Keep `speaker_role=unknown` for mixed/NPC commentary. Only a manually verified streamer excerpt should use `streamer`; unknown-speaker transcripts remain visible but abstain from pricing. OCR and speech semantics use a conservative English keyword heuristic, not a calibrated model.

## Fresh setup and generated verification media

Python 3.12, uv, Node and npm are required. This workspace uses Windows-native commands; Make is optional.

```powershell
python scripts/manage.py setup
python scripts/manage.py setup-speech
python scripts/manage.py generate-recording
python scripts/manage.py preprocess --manifest var/generated-demo/manifest.json
python scripts/manage.py demo --scenario recordings
```

Setup installs locked Python dependencies and frontend packages/build. FFmpeg is bundled with imageio-ffmpeg; RapidOCR includes local CPU models. Tesseract and FFprobe are not required. To use another FFmpeg, set `LEONIDA_FFMPEG` to its executable. Missing tools fail with setup instructions. The generated-media helper uses Windows installed speech voices (or `espeak` on other systems).

OCR samples each configured crop, tracks adjacent visible lines and caches raw text, confidence, boxes, frame references and interpretations. Audio/ASR output and tool/model versions are cached too. Cache loading verifies content and artifact hashes. Playback never reruns extraction. Fast scrolling and identical visible messages can remain ambiguous; real recordings need crop/accuracy review.

## Fallbacks and optional quote context

```powershell
python scripts/manage.py demo --scenario foundation
python scripts/manage.py demo --scenario courtroom-praise
python scripts/manage.py demo --scenario recordings --live-quotes
```

The six structured scenarios are `courtroom-praise`, `technical-failure-laughter`, `skill-rage-controls`, `mixed-missing-facecam`, `duplicate-reconnect`, and `venue-outage-reset`. Each has six explicit source statuses. Unsupported aspects and stale quotes abstain. Media demos use a separate, explicitly synthetic flat quote timeline; scenario fixtures use their own quote events. Neither invents venue prices.

The default venue panel uses historical real captures with stale labels. `--live-quotes` enables the existing read-only public quote poller; G3 did not re-verify a new live session. Public network access is optional. Quote updates never add evidence.

## Verification and current boundary

```powershell
python scripts/manage.py check --gate G3
python scripts/manage.py demo-check --scenario all
python scripts/manage.py demo-check --scenario recordings
python scripts/manage.py demo-check --scenario foundation
```

Checks cover schemas, generated types, six scenarios, imports, React typecheck/build and nine focused G3 acceptance tests. Demo-check starts isolated temporary apps/databases, verifies HTTP/WebSocket state and receipts/traces, then closes them. G4 formal verification and G5 release remain unexecuted.

Working: actual decoding/OCR/ASR, content-addressed cache, offsets, playback controls, paused recovery, source receipts, supported claims/abstentions, pre-update features, bounded narrative estimates and candidate EV. Fully synthetic fixtures integrate latency, cash/exposure/depth gates, partial entry/exit, immutable execution traces and atomic accounting into the UI. **Your629 real observations all abstain, with no estimates or orders.** Media remains candidate-only. Semantics/model coefficients are heuristic; synthetic quote books/fees are simulated. Automatic scenes, diarization, native live ingestion, real venue fee/depth integration and calibrated forecasting remain gaps.

Architecture/ownership: [AGENTS.md](AGENTS.md), [implementation plan](docs/IMPLEMENTATION_PLAN.md), [frozen G2 boundaries](docs/G2_CONTRACTS.md), [current state](docs/STATE.md), [decisions](docs/DECISIONS.md). The G1 reference viewer is retained at `/foundation`; use `--scenario foundation` for its original single-observation state.

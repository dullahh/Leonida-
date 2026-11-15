# Leonida Alpha

A multi-stream game evidence and prediction-market research desk, with paper execution. Streams contain plenty of excitement and frustration; only some of it evaluates game quality. The core insight is to keep **reaction activity, supported quality claims and market relevance separate**, with an inspectable path from source words to a paper decision.

## For judges: install and launch

Requires Python3.12, uv, Node22 and npm. From the repository root:

```powershell
python scripts/manage.py setup
python scripts/manage.py demo
```

Open http://127.0.0.1:8000. Default startup uses available local recordings plus their immutable cache; if files/cache are unavailable, it explains the fallback and starts the labelled deterministic Courtroom demo. No extraction or model download occurs at launch. Stop an existing server before reusing its port.

Two supported modes after installation:

```powershell
# Full local demo: five supplied recordings and cached evidence in this checkout.
python scripts/manage.py demo --scenario recordings

# Portable demo: tracked deterministic fixtures, no videos or speech model needed.
python scripts/manage.py demo --scenario portable
```

Both modes run without API credentials or network access after dependencies are installed. No Whisper model setup or media preprocessing is needed for the portable demo.

Default databases are separate: `var/demo-recordings.sqlite3` and `var/demo-portable.sqlite3`. `--db PATH` overrides this; a saved run matching the selected input resumes paused. A different saved scenario cannot override the selected launch mode; old audit is retained. Use Reset for a fresh epoch. `--port 8001` runs a second instance.

## What the desk shows

- **Recorded evidence:** actual supplied GTA V RP screen recordings, cached OCR lines, machine speech transcripts, media times and source artifacts. GTA V is proxy demo evidence, not GTA VI gameplay. The five clips yield 1651 observations; every quality interpretation currently abstains.
- **Reaction telemetry:** deterministic text cues suggest possible excitement, frustration, surprise or confusion. These scores do not measure actual emotion, vocal arousal or speaker identity. Profanity and shouting alone do not establish game quality.
- **Supported claims:** explicit attributed game-quality opinions must pass the existing conservative classifier plus target-certainty, confidence and market-relevance gates. All current real clips remain excluded from pricing. The separate where fixture supplies clearly labelled qualifying annotations.
- **Market-relative probability:** the current valid synthetic quote midpoint anchors a bounded log-odds adjustment from unique relevant evidence. Absolute sentiment and pre-update surprise stay separate; source count and refreshes do not amplify the signal. Coefficients are illustrative and uncalibrated.
- **Paper execution and receipts:** synthetic scenarios demonstrate 250ms processing latency, fees, available depth, partial fills, cash/position accounting and exits. Receipts show source, feature, model, quote and order-stage IDs. No real-money route exists.

Actual historical GTA VI venue captures are shown separately with stale labels; this proxy material does not change their prices. Courtroom observations/baselines are supplied fixtures. Its price timeline, liquidity, fees and fills are synthetic/simulated, not a historical backtest or a promise of profit. The optional Twitch panel is an implementation path; no real stream capture has been verified.

A valid scenario quote displays its midpoint independently of the model:14¢/15¢ shows **14.50% synthetic Yes midpoint** even when claims abstain. The model and candidate remain unavailable with explicit reasons. The Venue context tab defaults to eight bundled historical Kalshi quotes from14 November2026, with exact receipt timestamps and source paths. [Quote/abstention audit and existing optional live-mode command](docs/QUOTE_CLARITY.md) documents the precise data, staleness and failure behaviour; no live network call is required by default.

## Verification and release evidence

```powershell
python scripts/manage.py check --gate G3
.venv/Scripts/python.exe -B -m unittest discover -s tests/g4 -v
python scripts/manage.py demo-check --scenario all
```

See [release checklist](docs/RELEASE_CHECKLIST.md), [final release report](docs/G5_RELEASE_REPORT.md), [G4 verification](docs/G4_VERIFICATION.md), [reaction telemetry](docs/REACTION_TELEMETRY.md) and [source review](docs/T4_T5_REVIEW.md). G4 browser coverage is retained; final release browser work checks startup and the pitch flow on installed Edge, not cross-browser certification.

## Optional local input workflow

Recordings belong in `data/recordings/inbox/`; configure file/asset IDs, offsets and per-video chat crops in `data/recordings/manifest.json`. Original clips, models, evidence caches, databases and screenshots are ignored by Git. Preserve unknown speakers unless an interval has been manually verified. See [recording setup](data/recordings/README.md). Playback uses validated caches and never redoes OCR/ASR.

Local speech preprocessing supports `--asr-model small.en` for quality mode and
`--asr-model tiny.en` for the explicit fast fallback. Future preprocessing defaults
are in `config/local_asr.json`; existing immutable evidence/playback selection stays
unchanged. Install with `python scripts/manage.py setup-speech --asr-model small.en`,
then run `python scripts/manage.py preprocess --asr-model small.en --reuse-ocr-only --no-select-cache`
for an ASR-only pass using verified OCR artifacts. Both models run locally with no
audio upload or paid API. [ASR audit](docs/LOCAL_ASR_UPGRADE.md) and
[side-by-side listening review](docs/ASR_COMPARISON.md) document quality gates,
timings and unresolved transcription/speaker uncertainty.

The six portable scenarios are courtroom-praise, technical-failure-laughter, skill-rage-controls, mixed-missing-facecam, duplicate-reconnect and venue-outage-reset. The original diagnostic is retained as `--scenario foundation`. Optional `--live-quotes` is a separate read-only network mode and is unnecessary for either release demo; no credentials are required for normal replay.

## Optional live Twitch audio demo

The live panel embeds Twitch's official player. Enter a channel and start playback in the panel, then choose **Start tab audio capture**. In the browser prompt, confirm **This Tab** (the current Leonida tab) and enable tab audio; the embedded Twitch player's audio is what gets captured. The app requests that the current tab be prominent in the picker, but the browser still requires your confirmation. It sends audio-only, independently decodable 15-second chunks to the local backend; video is not uploaded. This requires a supported desktop browser and Twitch player access; screen-audio capture support varies by browser.

Install the optional local model once, configure Twitch app credentials in the shell, rebuild the UI and launch the desk. Create an app in the Twitch developer console to get the Client ID and secret; the app token is cached only in memory. Kalshi market-data discovery is public and does not need a Kalshi key.

```powershell
python scripts/manage.py setup-speech --asr-model small.en
$env:TWITCH_CLIENT_ID = "your-client-id"
$env:TWITCH_CLIENT_SECRET = "your-client-secret"
npm --prefix frontend run build
python scripts/manage.py demo --scenario portable
```

Enter a Twitch channel, a manual game name, or both. A channel loads the embedded player; a manual game name searches Kalshi without Twitch API credentials. When both are supplied, the entered game name overrides Twitch's category for market matching. Market candidates and live sentiment remain separate: exact Yes-outcome matches receive an explicit live decision review, which abstains until an outcome-specific probability model exists. The live route shows no probability, side, order or fill. This is separate from the synthetic replay's paper strategy. Twitch embedding uses its official `parent` parameter; see [Twitch's embed documentation](https://dev.twitch.tv/docs/embed/video-and-clips/), [Twitch Get Streams API](https://dev.twitch.tv/docs/api/reference/streams), and [browser screen-audio capture behavior](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia). Kalshi market discovery uses its [series](https://docs.kalshi.com/api-reference/market/get-series-list), [events](https://docs.kalshi.com/api-reference/events/get-events), and [markets](https://docs.kalshi.com/api-reference/market/get-markets) endpoints.

After starting capture, choose the audio attribution. Keep **Unknown speaker** unless you have verified that all recognized speech in the captured audio is the streamer; game/NPC/background voices are not diarized. Accepted transcript segments pass through the existing conservative lexical classifier and appear as timestamped live sentiment candidates or explicit abstentions. The default unknown-speaker setting abstains. These live signals are heuristic, are not added to the recorded GTA V proxy ledger, and do not yet produce rolling surprise, market estimates, sides, orders or fills. Audio chunks are converted in a local temporary directory and removed; they are not added to the evidence cache. If the Whisper model is missing, decoding fails, or quality gates reject the speech, the panel shows that status without invented transcript text.

Next research milestones: an as-of historical game/year dataset, held-out calibration against market-only and competitor models, and execution evaluation using actual venue fee/depth rules. Current limits include uncertain transcripts/attribution, English lexical semantics, manual scenes and long-recording performance. No validated forecasting edge is claimed.

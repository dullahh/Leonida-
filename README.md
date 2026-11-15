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

Both modes run without API credentials or network access after dependencies are installed. First-time dependency installation needs network access or prepopulated uv/npm caches; it cannot create unavailable packages offline. No Whisper model setup or media preprocessing is needed for the portable demo. A clean source-only copy was installed from the existing dependency caches and launched offline during release verification.

Default databases are separate: `var/demo-recordings.sqlite3` and `var/demo-portable.sqlite3`. `--db PATH` overrides this; a saved run matching the selected input resumes paused. A different saved scenario cannot override the selected launch mode; old audit is retained. Use Reset for a fresh epoch. `--port 8001` runs a second instance.

## What the desk shows

- **Recorded evidence:** actual supplied GTA V RP screen recordings, cached OCR lines, machine speech transcripts, media times and source artifacts. GTA V is proxy demo evidence, not GTA VI gameplay. The five clips yield1651 observations; every quality interpretation currently abstains.
- **Reaction telemetry:** deterministic text cues suggest possible excitement, frustration, surprise or confusion. These scores do not measure actual emotion, vocal arousal or speaker identity. Profanity and shouting alone do not establish game quality.
- **Supported claims:** explicit attributed game-quality opinions must pass the existing conservative classifier plus target-certainty, confidence and market-relevance gates. All current real clips remain excluded from pricing. The separate Courtroom fixture supplies clearly labelled qualifying annotations.
- **Market-relative probability:** the current valid synthetic quote midpoint anchors a bounded log-odds adjustment from unique relevant evidence. Absolute sentiment and pre-update surprise stay separate; source count and refreshes do not amplify the signal. Coefficients are illustrative and uncalibrated.
- **Paper execution and receipts:** synthetic scenarios demonstrate250ms processing latency, fees, available depth, partial fills, cash/position accounting and exits. Receipts show source, feature, model, quote and order-stage IDs. No real-money route exists.

Actual historical GTA VI venue captures are shown separately with stale labels; this proxy material does not change their prices. Courtroom observations/baselines are supplied fixtures. Its price timeline, liquidity, fees and fills are synthetic/simulated, not a historical backtest or a promise of profit. No new live-source claim is made by this release.

## Exact three-minute demonstration

| Pitch clock | Action and point |
|---|---|
|0:00–0:30|Play real recordings briefly, pause, then seek to the end. Show t4/t5 reaction activity. In a portable-only checkout, explain the unavailable private footage and start the labelled fixture instead.|
|0:30–0:55|Inspect t4 “I can't bro” or t5 “what happened?”: contextual reaction, uncertain target, explicit pricing exclusion, no estimate/order.|
|0:55–1:25|Load **Courtroom praise** as a separate synthetic run. Seek to2s: supported narrative claim,50% synthetic reference to about54.47% heuristic estimate.|
|1:25–1:50|Open **Inspect full receipt**, then **Inspect trace** / **Eligibility receipt**: source words, attribution, model inputs, quote and6/10 partial fill with.06 fee.|
|1:50–2:20|Close the dialog and seek to the timeline end310s. Show4+2 exits, flat position, total fees.12 and cash10000.08. This is computed from authored synthetic prices.|
|2:20–2:45|Load **Venue outage / reset**, seek to10.2s. Show stale synthetic quote, cancelled pending entry and zero fills.|
|2:45–3:00|State the honest boundary: source-linked research prototype; uncertain OCR/ASR, text heuristics, uncalibrated probability and simulated execution. Return to recordings.|

Detailed cues and all six scenario behaviours: [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## Verification and release evidence

```powershell
python scripts/manage.py check --gate G3
.venv/Scripts/python.exe -B -m unittest discover -s tests/g4 -v
python scripts/manage.py demo-check --scenario all
```

See [release checklist](docs/RELEASE_CHECKLIST.md), [final release report](docs/G5_RELEASE_REPORT.md), [G4 verification](docs/G4_VERIFICATION.md), [reaction telemetry](docs/REACTION_TELEMETRY.md) and [source review](docs/T4_T5_REVIEW.md). G4 browser coverage is retained; final release browser work checks startup and the pitch flow on installed Edge, not cross-browser certification.

## Optional local input workflow

Recordings belong in `data/recordings/inbox/`; configure file/asset IDs, offsets and per-video chat crops in `data/recordings/manifest.json`. Original clips, models, evidence caches, databases and screenshots are ignored by Git. Preserve unknown speakers unless an interval has been manually verified. See [recording setup](data/recordings/README.md). Playback uses validated caches and never redoes OCR/ASR.

The six portable scenarios are courtroom-praise, technical-failure-laughter, skill-rage-controls, mixed-missing-facecam, duplicate-reconnect and venue-outage-reset. The original diagnostic is retained as `--scenario foundation`. Optional `--live-quotes` is a separate read-only network mode and is unnecessary for either release demo; no credentials are required for normal replay.

Next research milestones: an as-of historical game/year dataset, held-out calibration against market-only and competitor models, and execution evaluation using actual venue fee/depth rules. Current limits include uncertain transcripts/attribution, English lexical semantics, manual scenes and long-recording performance. No validated forecasting edge is claimed.

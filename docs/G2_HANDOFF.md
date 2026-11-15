# G2 handoff - local recording desk

Historical handoff. The user subsequently supplied t1/t2/t3; see [RECORDING_REVIEW.md](RECORDING_REVIEW.md). Current G3 integration, process and launch instructions are in [G3_HANDOFF.md](G3_HANDOFF.md). Generated-media/current-process statements below describe the G2 checkpoint only.

Completed 15 November 2026. Stop after G2. Pipeline, quant and frontend were directly supervised in their assigned paths; workers did not delegate. All three handoffs were received and root integrated their outputs.

## Acceptance result

G2 functional acceptance passes with the user-authorized generated-recording substitute. No user-supplied recording was found. Two generated 12-second H.264/AAC screen recordings exercise the actual media providers; they are not Twitch/GTA footage and retain synthetic_replay/proxy labels.

| Gate item | Observed result |
|---|---|
| Drop location and manifest | data/recordings/inbox/; editable manifest with 2-6 slots, file/stream IDs, trim/timeline offsets, chat ROI, version/model metadata. |
| Actual media pipeline | Bundled FFmpeg, RapidOCR CPU and local Whisper executed on two generated recordings. 11 sampled frames, 10 unique OCR observations, 2 ASR observations, 9 attributable interpretations. Both PCM and speech reports available. |
| Offset/cache behavior | Second video media4s maps to replay3s; changed ROI/alignment invalidates cache. Stationary chat does not repeat; disappeared/reappearing lines can become new occurrences. Cache reuse bypasses OCR and does not rewrite; corruption is rejected. |
| Visible end-to-end path | 12 cached windows -> supported claims/abstentions -> 7 unique stream/aspect/modality buckets -> heuristic narrative estimate -> candidate -> receipt -> identical HTTP/WS state -> React terminal. |
| Missingness/math | Unseeded real/generated media has null z during warmup. Final example p=0.14259941588529948, No EV=-0.01259941588529948 USD/contract, no fills. No fake ready baseline. |
| Recorded/GTA VI separation | Every source retains GTA V proxy scope; actual venue definitions/quotes are separate context. Schema/evaluator refuse proxy estimates for actual venue contracts. Generated media is labelled synthetic. |
| Six fallback scenarios | All six validate stable support/IDs/statuses; 1x/5x ordering fingerprints match. Root projected each. Outage scenario reaches stale quotes and estimate abstention; unsupported non-narrative scenarios abstain. |
| Quant/paper components | Pre-update z, revisions/dedup, ageing, source caps, side-specific EV, Decimal fees/reservations/depth/partial entry+exit checked by quant. p=.097 gives No EV .033 after simulated fee. |
| Atomic root persistence | Broker state, versioned orders/fills, optional envelope and command share one SQLite transaction with expected revision. Four-contract partial fill/cash9996.52 restored after reopening; duplicate-command failure rolled back, no repeat fill. |
| Playback/recovery | Play/pause/seek/speed/reset, availability gating, idempotency/conflict, quiet end-of-media deadline, equivalent end-state at 1x/5x, paused restart and old audit preservation passed. |
| Browser | Installed Edge via Playwright: two decoded players, offset synchronization within0.5s, seek/speed/reset, receipts, OCR frame/audio access, old-run rejection, REST fallback/reconnect, 1440/390 layouts; zero console/HTTP errors. |
| HTTP media | Byte range returns206; frame/audio200; unknown/path escape404; changed media hash409. |
| G1 fallback | Original p=.12407788254178297, z=-2, No EV=.00592211745821703 and candidate-only behavior still pass isolated demo-check. |

## Launch and input

```powershell
python scripts/manage.py demo
```

Open http://127.0.0.1:8000. Default uses the last preprocessed recording cache, or G1 when no pointer exists. This checkout's pointer selects the verified generated recordings. Root's QA server is stopped at handoff; launch your own with the command above.

For your files, use `data/recordings/inbox/stream-1.mp4`, `stream-2.mp4`, etc., and edit `data/recordings/manifest.json`. Paths resolve from repository root. One available video plus an unavailable second slot is valid for initial verification; the intended primary demo is 2-6 recordings.

```powershell
python scripts/manage.py setup
python scripts/manage.py setup-speech
python scripts/manage.py preprocess --manifest data/recordings/manifest.json
python scripts/manage.py demo --scenario recordings
```

Setup installs bundled FFmpeg and OCR. Tesseract/FFprobe are unnecessary. Speech setup explicitly downloads tiny.en once to var/models/faster-whisper-tiny.en; both OCR and ASR run locally thereafter. Missing providers/model/audio produce setup errors or explicit per-asset unavailability, never invented output. Unknown-speaker transcripts abstain from game-quality interpretation.

Generated reproduction:

```powershell
python scripts/manage.py generate-recording
python scripts/manage.py preprocess --manifest var/generated-demo/manifest.json
python scripts/manage.py demo --scenario recordings
```

Current verified cache: `var/evidence-cache/46b767d6b708d63c40ae27472ceca90bbc1637ef9a7ddabd30184c723363da9a.json`. The equivalent pipeline-owned verification copy is in var/g2-media-cache. Cache keys may change when media/model/provider bytes or versions change; use the printed path or default pointer.

## Verification commands and evidence

Executed successful commands: dependency setup, speech setup, generated recording helper, integrated preprocess, export-contracts, `check --gate G2`, `demo-check`, and `demo-check --cache` with the generated cache. Frontend install/typecheck/build and all-six scenario validation passed. Root focused checks were inline and isolated; no formal tester-owned source was created. Final command statuses are in STATE.md.

Local evidence: var/g2-runtime-checks.json, var/g2-persistence-checks.json, var/g2-http-checks.json; frontend/.qa/g2-browser.json, g2-final-ui.json, g2-desktop.png, g2-mobile.png. These ignored files are local QA artifacts. Worker detail: handoffs/pipeline.md, handoffs/quant.md, handoffs/frontend.md.

Resolved failures: restricted network required approved dependency/model downloads; Windows package cache lock needed a serialized retry; SAPI was unavailable in the restricted process and succeeded under normal-user execution; initial ASR PyAV keyword mismatch was fixed by passing decoded PCM; frontend empty CSS data import and source-label selection were fixed before final build/browser checks. The initial check targeted planned module names; it now imports the delivered public quant/paper interfaces.

## Interfaces and remaining gaps

Exact ownership and imports are in G2_CONTRACTS.md and worker handoffs. Root owns core schemas/runtime/projection/storage, FastAPI, scripts, locks/generated files and processes. Pipeline owns recordings/perception/scenarios; quant owns features/execution; frontend owns React. Runtime cache loading is separate from preprocessing. Snapshot cursor and commands are durable; live quote freshness remains independent of replay pacing.

Media runtime intentionally produces candidates only: zero orders/fills. The pure broker and atomic persistence seam work, but full automated scheduling, entry/exit projection and detailed execution tape require G3. No real-money route exists.

Real Twitch overlay/OCR accuracy, multilingual semantics, speaker diarization, native Twitch acquisition and automatic scene grouping remain unverified or unimplemented. The current English lexical interpreter is conservative and uncalibrated; only narrative estimates are routed. Long recordings may need trimmed excerpts and future ledger pagination. Browser support depends on source codecs; H.264/AAC was verified. OCR/ASR sample limitations and capped wire text are documented in the pipeline handoff; full raw audit/transcripts remain in cache artifacts.

G4 formal regression suite/reviewer gate and G5 release rehearsal were not executed. No new live venue polling session was claimed for G2; actual historical captures stay stale, with the prior optional read-only polling capability retained. No Git repository, commit, hosting or deployment was created.

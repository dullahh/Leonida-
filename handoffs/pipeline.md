# P2 / G2 pipeline handoff

Completed 14 November 2026. No workers were delegated, no test source was written,
and no root/shared application files or dependencies were edited. Root installed
the providers and generated verification videos/model; this worker implemented
and exercised the owned media/replay pipeline.

## Changed paths

- `backend/ingestion/{__init__,tools,ocr,audio,recordings,replay}.py`.
- `backend/perception/{__init__,claims,fixture,scenes}.py`.
- `data/recordings/manifest.json`, `README.md`, `.gitignore`, `inbox/.gitkeep`.
- `data/scenarios/README.md` and all six named scenario JSON files.
- This handoff.

## Public interfaces

```python
from backend.ingestion.recordings import (
    load_manifest, MediaPreprocessor, load_cache, build_windows,
)
load_manifest(path: Path, repository_root: Path) -> RecordingManifest
MediaPreprocessor(repository_root: Path).preprocess(
    manifest: RecordingManifest, cache_directory: Path,
) -> EvidenceCache
load_cache(path: Path) -> EvidenceCache
build_windows(cache: EvidenceCache, run_id: str, origin: datetime) -> list[SourceWindow]

from backend.perception.claims import extract
extract(window: SourceWindow) -> list[EvidenceClaim]

from backend.ingestion.replay import (
    load_scenario, scenario_names, scenario_metadata, StructuredReplaySource,
)
load_scenario(name: str, cache_directory: Path) -> EvidenceCache
scenario_names() -> tuple[str, ...]
scenario_metadata(name: str) -> dict  # source JSON configuration, not wire state
StructuredReplaySource(cache, run_id, origin, duplicate_deliveries=False)
StructuredReplaySource.next_window() -> SourceWindow | None
StructuredReplaySource.available(as_of: datetime) -> list[SourceWindow]
```

Root schemas are consumed directly. `CachedObservation.semantic_confidence`
maps to `EvidenceClaim.quality`; unavailable semantics have null sentiment and
an abstention reason. `dependency_group` preserves rebroadcast identity.
`SourceWindow.observation` retains the supported interpretation separately from
the generated claim. `scene_membership` offers a manual internal claim-ID view;
no automatic perceptual matching or independent-vote assertion is implemented.

All recording/model paths resolve from the repository root and must stay inside
it. A manifest has 2–6 unique asset/stream slots; absent media remains absent.
The loader computes actual file hashes and rejects supplied-hash mismatches.
`frame_ref`/`audio_ref` are **relative to the cache directory**, e.g.
`<cache-key>/<asset-hash>/frames/000000.png`. Root should serve only references
from the active cache using its allowlisted artifact endpoint.

## Actual generated-media result

No user recording was available. Root supplied two generated 12-second MP4s with
synthetic chat graphics and SAPI narration, plus a local tiny.en Whisper model:
`var/generated-demo/manifest.json`. They are explicitly `synthetic_replay` and
proxy test material, not actual Twitch/GTA V footage. The second video's trim
starts at media second 2 and replay second 1.

Actual command (exit 0):

```powershell
.venv/Scripts/python.exe -m backend.ingestion.recordings --manifest var/generated-demo/manifest.json --cache-dir var/g2-media-cache
```

Final successful cache:
`var/g2-media-cache/46b767d6b708d63c40ae27472ceca90bbc1637ef9a7ddabd30184c723363da9a.json`.

- FFmpeg decoded 11 sampled frames: six from video 1 and five from video 2.
- Actual RapidOCR produced ten unique visible-line observations after tracking
  repeated stationary lines; raw audit includes every sampled-frame result.
- Both audio tracks were decoded to 16 kHz mono PCM with measured RMS activity.
- Actual local faster-whisper produced two timestamped ASR observations.
- The cache has 12 observations: nine attributable heuristic interpretations
  and three explicit abstentions. Both asset reports mark audio and speech
  available. All claims remain GTA V proxy/synthetic provenance.
- First ASR segment actually reads “The story in this game is excellent. The
  dialogue in this game is repetitive.” Its mixed evaluation abstains. The
  trimmed second recording transcribed “The dialogue in this game is repetitive.”
  and yields a supported negative narrative interpretation.

An initial attempt exposed a real faster-whisper/PyAV 19 compatibility problem:
`av.open` no longer accepted `metadata_errors`. The adapter now passes its
already-decoded PCM NumPy array to Whisper, avoiding that filename decoder.
Preprocessing implementation version changed to `local-media-v2-pcm-asr`, so the
earlier failed-speech cache is not reused. Do not select the older
`6cc528d...` cache for the final demonstration.

## Executed verification

The following exited successfully:

- `uv run --frozen --cache-dir .cache/uv python -m backend.ingestion.replay --scenario all --validate-only`.
- The same six-scenario validation at 1x/5x, with an inline comparison proving
  identical event-order fingerprints for every scenario.
- `.venv/Scripts/python.exe -m compileall -q backend/ingestion backend/perception`.
- Actual generated media preprocessing above, followed by `load_cache` and
  `build_windows`/`extract` for every observation.

Focused inline checks (no persistent test source) passed:

- Stationary adjacent OCR lines retain IDs; disappearance and return creates a
  new occurrence; duplicate fixture delivery repeats existing IDs.
- Low-confidence OCR, sarcasm/laughter, player-skill text, negation and unknown
  audio speakers abstain; explicit supported aspect evaluations remain usable.
- Offset equation, exact quotation support, source/availability ordering and
  stable source-window IDs across run IDs.
- Cache equality/no rewrite on repeat preprocessing; patched OCR constructor
  proves a cache hit does not initialize OCR.
- Corrupted observations, changed cached manifest and corrupted frame artifact
  each fail cache loading in isolated temporary copies.
- Actual shortened videos with a changed crop generate a different cache;
  shifting both offsets by one second changes the cache and moves every replay
  time by exactly one second while source text/media times stay equal.
- PCM extraction with transcription explicitly disabled reports that reason.
- Path escape, absent recording, absent local Whisper model and invalid FFmpeg
  executable produce actionable errors rather than invented observations.

Six scenarios have six declared statuses each. Unique observation counts are
3/3/3/4/2/2 in the documented order. The duplicate/reconnect source returns six
deliveries from two unique observations. Scenario JSON includes manual
scene/phase/build/platform, explicit synthetic quote/depth timeline, baseline
seed and expected qualitative invariants. The final metadata addition changes
scenario cache fingerprints; root should load current files.

## Boundaries and remaining limitations

- No actual user recording was tested; generated graphics establish decoder,
  crop/OCR/audio/ASR/cache mechanics, not accuracy on real Twitch overlays.
- OCR is English-oriented RapidOCR CPU. Tesseract/FFprobe are unnecessary.
  Native Twitch message IDs cannot be recovered from pixels; fast scrolling and
  visually identical consecutive messages remain ambiguous.
- The full raw OCR line is retained in the audit. Wire observation text is capped
  at 240 characters; longer ASR segments are similarly capped for interpretation
  while the full segment remains in `transcript.json`.
- Interpretation is a small, uncalibrated lexical heuristic. It normalizes a
  narrow joined aspect/copula OCR pattern, requires explicit aspect language,
  and abstains on mixed polarity/negation. It does not semantically split mixed
  ASR paragraphs or perform LLM extraction.
- ASR is local CPU with a configured downloaded model; disabled/missing/failed
  ASR keeps real PCM available and reports speech unavailability. Speaker
  attribution is manual `speaker_role`, not diarization. No face-derived signal.
- Frames are individually sought/decoded during offline preprocessing; long
  recordings benefit from `media_end_seconds` excerpts. Playback is cache-only.
- Root integrates clocks, synchronized browser video playback, full-state
  transport, venue separation, quant calculations and paper execution plans.
  This handoff does not claim their browser/integration gates passed.
- The six scenario quote/control timelines are authored configuration. Root must
  schedule quote expiry/reset and duplicate delivery to verify their full runtime
  behaviours; standalone replay validation checks source data/support/identity.

## Root integration actions

1. Use the successful cache above for final generated-media verification and
   write its path to the root launch pointer if desired.
2. Serve cache-relative frame/audio references only from active cache allowlists;
   video input paths likewise must be manifest-allowlisted with range support.
3. Call `build_windows` with the run's aware origin, select by `available_at`, and
   call `extract` for each unique window. Quant must ignore abstentions/targets
   other than game. ASR segment availability is its end time.
4. Drive all videos from the same replay position using the documented trim/
   timeline equation; keep generated/supplied/recorded labels distinct.
5. Document root launch/model-download commands. The drop manifest and setup
   details are already in `data/recordings/README.md`.

No remaining dependency blocker for the verified local pipeline.

## Final default-input adjustment — 15 November 2026

The user recording template now enables `audio_transcription=faster_whisper`
for both slots and uses `speech_model_path=var/models/faster-whisper-tiny.en`.
`speaker_role=unknown` is preserved: transcription is visible while attribution
remains explicitly unverified. A missing model still reports speech unavailable
without fabricating output. `data/recordings/README.md` now documents
`python scripts/manage.py setup-speech`, the integrated `preprocess --manifest
data/recordings/manifest.json` command, and `demo --scenario recordings`.
This small configuration/documentation adjustment required no additional tests;
the actual generated-media results and successful cache above are unchanged.

## Supplied-recording G2 follow-up — 15 November 2026

This follow-up supersedes the earlier absence of supplied media. The user supplied
`data/recordings/inbox/t1.mp4`, `t2.mp4`, and `t3.mp4`. All are 1920×1080 with audio;
their durations are 38.366667, 52.9 and 45.866667 seconds. No source channel identity
or independence was established. Clip IDs `t1`/`t2`/`t3` are not verified streamer
identities, and visible platform UI is not proof of a live Twitch connection.

Changed only owned paths: `data/recordings/manifest.json`, its README,
`backend/ingestion/audio.py`, `backend/ingestion/recordings.py`, and this handoff.
Inspection artifacts and actual derived caches are under `var/`. No server was
started/stopped, no dependency installed, and no formal test source added.

### Actual manifest and crops

The manifest now has all three supplied files, `media_start_seconds=0`,
`timeline_start_seconds=0`, `scene_id=manual-unassigned`, null declared hashes
(computed/verified by the loader), `evidence_mode=recorded`, GTA V/proxy provenance,
local tiny.en ASR, and `speaker_role=unknown`. Simultaneous playback starts do not
claim that the clips depict the same scene or wall-clock time.

Root and pipeline independently inspected representative frames. Final pixel
crops are `(x,y,width,height)` relative to 1920×1080:

| Clip | Crop | Observed limitation |
|---|---|---|
| t1 | 1450, 52, 453, 1022 | Separate white right panel; excludes avatars/header/scrollbar but retains the in-panel welcome banner. |
| t2 | 1584, 58, 336, 330 | Small upper-right overlay; BANKING game UI and DISTRICT10 watermark overlap text. |
| t3 | 1584, 58, 336, 330 | Small upper-right overlay; watermark, emoji and moving background reduce fidelity. |

Review samples: `var/local-recordings-review/pipeline-t1-chat-15.00.png`,
`pipeline-t2-chat-15.00.png`, `pipeline-t3-chat-15.00.png`; paired direct OCR results
are `sample-ocr.json`. These crops were visually compared with actual OCR:

- t1 readable “Choose ricky for the next heist” became “Choose ricky for the next
  hcist” at about .959 provider confidence. Two color/emoji-rich lines were
  dropped or badly corrupted. The privacy banner also enters OCR.
- t2 visible BANKING overlap became `BANKIMSKE` at about .818 confidence, while
  `DISTRICT10` was recognized at about .962. These are screen UI contamination,
  not verified chat messages or game-quality evaluations.
- t3 “Does speed like naruto?” became “Does speedMke naruto?” at about .913,
  and emoji were converted to digit-like text. “roblox” was read as “roblax”.

Provider confidence is not measured accuracy; errors occur even above .9. No OCR
accuracy percentage is claimed. Sampling/dedup counts are observations, not exact
Twitch message counts or independent votes.

### Final observed result

The full actual decoding/OCR/audio run completed successfully. Final validated
cache, after the audio-boundary correctness fix:

`var/evidence-cache/a6d8a27fa3c4f5c3e34b2b8a411457e6cc2a50b5362341b12bd8904d039343d9.json`

| Clip | Sampled frames | Unique OCR observations | ASR observations | OCR confidence median | OCR below .75 | Attributable sentiment |
|---|---:|---:|---:|---:|---:|---:|
| t1 | 20 | 89 | 16 | .9635 | 7 | 0 |
| t2 | 27 | 202 | 19 | .9240 | 33 | 0 |
| t3 | 23 | 277 | 26 | .9074 | 27 | 0 |

Total: 70 sampled frames, 568 OCR observations, 61 ASR observations, 629 explicit
abstentions. All assets have decoded audio and actual ASR output. Most OCR text
is chatter, instructions, names, emoji or unrelated/ambiguous text; no supported
game-quality sentiment was found by the conservative heuristic. Unknown audio
speakers also abstain. **Do not fabricate an estimate or paper candidate from this
all-abstaining evidence.** The G1/synthetic fallback remains the numerical
evidence-to-candidate demonstration.

Raw ASR output examples, not independently verified speech quotations:

- t1: `I didn't know you had that opportunity.`; later `He's got my car!`.
- t2: an opening segment includes `we gotta go to the ATM chat do we make one or
  join one`; later `Uh, F2.`.
- t3: an opening segment includes `we're gonna go to this clothing store`; later
  directions, smoke references and repeated `Oh my god.` output.

No direct listening check was performed by this worker. Root's independent
machine transcription comparison is not a verified transcript. In the final
tiny.en run, all segments were within actual PCM: maximum ends 38.32, 52.2 and
45.8 seconds versus PCM durations 38.3573125, 52.8853125 and 45.8666875 seconds.
t3 has five retained quality warnings: three high-compression segments (ratio
4.6043) and two additional repeated-phrase warnings. t1/t2 maximum compression
ratios are 1.3191/1.53125. No tiny.en segments were rejected for timestamp bounds.

Per-clip transcript and validation paths are under the final cache's artifact
directory: `6e14051745f7649a/` (t1), `4ce6e0a412b5c4ad/` (t2), and
`5950e3cb761734f5/` (t3), each containing `audio.wav`, `audio-activity.json`,
`transcript.json`, `transcript-validation.json`, and sampled `frames/`.
Machine-readable counts/confidence/reasons/paths are in
`var/local-recordings-review/pipeline-quality-summary.json`.

### Focused G2 audio/cache correction

Root's separate base-model experiment exposed out-of-media ASR timestamps; that
output was not promoted. `audio.validate_segments` now checks actual decoded PCM
duration, rejects nonfinite/negative/nonpositive/out-of-audio intervals, and never
turns unsupported intervals into point events by clamping them to file end. Only
up to 50 ms final timestamp rounding is tolerated. Raw rejected segments and
reasons remain in the validation audit. Compression ratio above 2.4 and repeated
phrases flag interpretation unreliability and force sentiment abstention.

The production model and decoding parameters remain tiny.en, beam 1, VAD off;
the provider now exports its actual compression ratio. Implementation version
`local-media-v3-asr-boundaries` invalidates earlier full caches. The initial real
cache `fce3164759597b40ab2d7f8eac0606ff88dc75ef91f662346ff93b6ac2275049`
remains immutable. Final preprocessing reused only its fully verified raw OCR
audit/crops after exact input hash, crop, sample/trim/alignment, language and
OCR/ONNX/FFmpeg processing-version checks. The known v2 OCR implementation maps
explicitly to the unchanged OCR processing identity; unknown legacy identity is
not reused. Current line tracking and semantics were recomputed, and audio/ASR
actually ran again. Old derived sentiment was not used as raw input.

### Actual follow-up verification

- Full preprocessing module command exited 0 on all three supplied files.
- Final v3 preprocessing exited 0 with the OCR constructor patched to raise if
  invoked, proving verified raw reuse while actual ASR ran again.
- Cache loading verified its content and all artifact hashes. Building windows
  and claims produced 629 unique IDs with exact quotation support, recorded/GTA V
  provenance, source/availability order and positive in-audio ASR intervals.
- Repeating preprocessing returned the identical final cache without rewrite,
  with both OCR and ASR constructors patched to fail if invoked.
- Focused inline checks passed boundary rejection, nonpositive/NaN handling,
  rounding tolerance, preserved rejection audits, compression/repetition flags,
  and raw-reuse rejection when provider version, source hash or crop differs.
- `compileall` for ingestion/perception exited 0. No new test files were created.

Root owns remaining app/browser verification and the recording launch pointer.
Use the final `a6d8a27...` cache, show ASR/OCR uncertainty and all-abstaining state,
preserve separate actual GTA VI quotes, and stop within G2.

## G3 synthetic-lifecycle follow-up — 15 November 2026

G3 was subsequently authorized. This worker changed only the six files in
`data/scenarios/`, their README, `backend/ingestion/replay.py`,
`backend/perception/scenes.py`, and this handoff. No media provider ran; actual
`t1`/`t2`/`t3` input configuration or cached interpretation was changed.

### Interfaces and metadata delivered

Existing loading interfaces remain unchanged. `scenario_metadata(name)` now
calls `validate_scenario(metadata) -> None` before returning authored config.
Validation covers six declared source/status slots, fully synthetic provenance
and authorization, positive finite duration, source/capture/availability times,
synthetic market namespace, coherent side prices, explicit nonnegative sizes,
`simulation-linear-v1`, and identical prices/depth for a republished liquidity ID.
Missing or invalid lifecycle metadata fails loudly; it does not authorize fills.

Every fixture is now version `*-v3`, explicitly `simulation_authorized=true`, with
`duration_seconds` and `expected_lifecycle` checkpoint metadata. Quotes include
`event_id`, `event_seconds`, `captured_replay_seconds`,
`available_replay_seconds`, `liquidity_event_id`, `book_event`, four side prices/
sizes, fee provenance, and a descriptive synthetic note. The six statuses and
missing-modalities/proxy labels remain present.

`scene_membership(claims: Sequence[EvidenceClaim]) -> dict[str, tuple[str, ...]]`
returns sorted/deduplicated explicit manual scene memberships. It excludes
`manual-unassigned`, `unknown` and `unassigned` labels, rejects mixed runs and
conflicting same-revision claim content, and selects the latest revision of an
existing claim ID. Root supplies the current available claim view and projects
memberships into its shared DTO. Scene membership does not assert independent
sources, infer scene similarity, or multiply signal weight.

### Timeline details

- **Courtroom praise:** all three narrative annotations are +.4; the first source
  event at 0s becomes available at 1s. Seed is mean 0 / variance .04 / count 20,
  producing pre-update z=2. Initial Yes and No bid/ask are .4975/.5025; Yes asks
  have six contracts against a requested ten. Explicit synthetic convergence at
  8s changes Yes prices to .5375/.5425. At 300s a fresh replacement book has four
  Yes bids at .5375; at 304s another has two Yes bids at .5325. Duration is 310s,
  independent of the last source observation. These are authored synthetic quote
  events and cannot alter actual GTA VI quotes.
- **Technical failure/laughter:** negative technical observations share the
  original clip's dependency group; laughter abstains. No narrative estimate is
  manufactured from unsupported routing.
- **Skill/controls:** skill-only claims abstain; control criticism remains a
  negative gameplay feature with no configured narrative route.
- **Mixed/missing facecam:** positive speech arrives at 1s. Critical chat arrives
  at 1.1s alongside a synthetic quote move to Yes .5275/.5325, before eligibility
  at 1.25s. The original .5025 limit and changed evidence prevent the pending
  entry. Facecam remains unavailable.
- **Duplicate/reconnect:** identical source IDs are delivered three times;
  source/rebroadcast dependency stays shared. Quote wrappers at 2s/5s preserve
  the same exact book and liquidity identity, never replenishing consumed asks.
- **Outage/reset:** the first positive source arrives at 9.9s; quote 0 becomes
  stale at 10s before entry eligibility at 10.15s. A later source at 17s does not
  refresh quotes. Duration is 45s. Reset remains a root-owned command/new run.

Other scenario durations are 30s. No fixture stores fills, realized P&L or a
promised return. Root's scheduler controls actual execution and time exits.

### Actual checks and computed outcomes

`uv run --frozen --cache-dir .cache/uv python -m backend.ingestion.replay
--scenario all --validate-only` exited 0 on all six current fixtures. Source order
fingerprints matched at 1x and 5x. `compileall` for ingestion/perception exited 0.

Focused in-memory calls to the actual quant and broker public APIs passed:

- At courtroom time 1s, p=.5447758750781491 and net Yes EV=.0322758750781491;
  the small difference from an unaged .18 correction is the explicit one-second
  evidence decay. Requested ten, actual entry six at 1.25s, cash 9996.925.
- `exit_deadlines(state,300)` yielded 301.25s. Four contracts exited at 301.5s;
  the fresh 304s quote allowed the final two at 304.25s. Computed final inventory
  was empty, cash 10000.0800 and realized P&L .0800. This is a result of the
  authored synthetic quote example, not observed trading performance.
- Mixed-case pending entry cancelled at 1.25s because no depth met its original
  limit; zero fills, cash unchanged and reservation released.
- Outage pending entry cancelled at 10.15s because the current estimate/quote
  was unavailable/stale; zero fills and reservation released.
- Technical/gameplay features remained negative while narrative estimates
  abstained. Repeating duplicate fixture windows/claims three times returned
  identical features/estimate/decision with one effective dependency contribution.
- Manual groups were invariant to ordering and duplicate delivery; latest
  revisions replaced membership; mixed runs and conflicting revisions rejected.
- Invalid recorded authorization, too-short duration, unknown fees and a changed
  book under a reused liquidity ID were rejected.

The first arithmetic probe used exact float equality for .4 and failed on normal
floating-point representation (.39999999999999997); the corrected tolerance-based
probe passed. All monetary comparisons used Decimal equality.

The supplied recording manifest SHA-256 remained
`9473892aee641b04772b666f78af239d488be645b26277799fff13ff1ca470f5` and final
real cache file SHA-256 remained
`d04e5b19b00aef838b8410190fea69f5a84b1c6b2149b665b0a4bdbb0acae8b1`.
Read-only validation confirmed its 629 claims still abstain and produce no manual
scene groups. No recording preprocessor, OCR or ASR provider was invoked.

### Integration actions and limits

Root should honor `duration_seconds`, use current v3 scenario metadata/cache,
schedule source/quote arrivals plus 250ms eligibility, strict 10s quote expiry,
300s post-fill exit deadlines and scenario end. Quote 304s is the causal trigger
for retrying an overdue partial exit; publication timers must not create retries.
Use `simulation_authorized` only with the synthetic fixture/quote checks already
present in the broker. Real recordings remain candidate-only and all-abstaining.

This worker verified fixture data and pure quant/broker compositions. Integrated
scheduler, SQLite atomicity/restart, HTTP/WS and browser gates remain root-owned;
their acceptance is not claimed here. No dependency or contract blocker remains.
# Live audio ingestion handoff

## Changed paths

- `backend/ingestion/live_audio.py`
- This handoff.

## Public interface

```python
from backend.ingestion.live_audio import LiveAudioTranscriber

transcriber = LiveAudioTranscriber(Path("var/models/faster-whisper-small.en"))
window = transcriber.transcribe_chunk(
    stream_id="twitch:<channel-login>",
    payload=audio_bytes,
    content_type="audio/webm;codecs=opus",  # or audio/wav
    source_media_start_seconds=0.0,
    event_at=aware_chunk_start,
    available_at=aware_received_at,
    language="en",
)
wire_value = window.as_dict()
```

The service accepts at most 2 MiB and 15 seconds per chunk. Supported input is
WAV or a standalone WebM/Opus chunk. The browser should use a user-authorized
display/tab-audio capture and submit non-overlapping chunks. It does not access
Twitch media URLs, download stream content, or persist the incoming bytes.

The result has a deterministic `source_window_id`, `evidence_mode: "live"`,
source interval, aware event/availability timestamps, source and derived-payload
hashes, ASR/model/gate versions, accepted segments, and the full quality-gate
audit. Accepted segment offsets are absolute in the source timeline while
`local_start_seconds`/`local_end_seconds` preserve chunk-relative times. An
unavailable local model returns `status: "unavailable"`, a reason, null model
identity/version, and no text. Decode/shape errors raise `ValueError` for a
client error response.

This is deliberately not the frozen `SourceWindow`: that contract only permits
recorded/synthetic GTA V proxy evidence. The DTO has no game ID, target, aspect,
sentiment, scene, market relevance, or claim. Route it only to a separately
labelled live observation surface until game identity and semantic extraction
are explicitly supplied and versioned. Do not put it into existing quote,
estimate, or paper execution state.

## Verification

- `python -m py_compile backend/ingestion/live_audio.py` — exit 0.
- `git diff --check` — exit 0.
- No tests were added or run. No real Twitch stream or browser-captured audio
  was available, so this does not claim an end-to-end live source works.

## Limitations and integration actions

- The producer must ensure chunks are independently decodable; some browser
  MediaRecorder implementations emit later timeslice fragments without a
  standalone WebM header. A short WAV chunk is the portable initial path.
- English is the current local ASR configuration. There is no model download or
  fallback in the service. Install/select a model through the existing setup
  command before enabling capture.
- Root owns HTTP routes and schemas. Instantiate one transcriber in the app
  lifespan, run synchronous conversion/ASR in a worker thread, enforce one
  active capture stream per run, and deduplicate repeated source-window IDs.
- Browser embed support must use Twitch's required `parent` parameter and user
  interaction. This adapter itself does not prove Twitch playback/capture works.

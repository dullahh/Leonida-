# Reaction telemetry integration - 15 November 2026

One thread; no agents, G4, OCR/ASR reruns, paid calls or media changes. Existing `backend/perception/claims.py`, cached observations and speaker-verification records were preserved. Reaction telemetry describes cached text; it does not establish the person's actual emotion or a verified speaker identity.

## Separate contracts and pricing

Schema2 revision `g3-reactions-v1` adds `ReactionSignal` alongside the existing EvidenceClaim contract. A signal retains run/observation/window/stream/asset IDs, evidence mode and proxy scope, media interval and replay/availability time, valence, nullable text intensity, nullable emotion, likely target and certainty, modality, nullable confidence, original supporting text, abstention/exclusion reasons, optional supported-claim ID, market relevance, eligibility/inclusion flags and classifier/policy versions.

`backend/core/reactions.py` implements deterministic `text-reactions-v1`. The supported-claim classifier remains conservative-lexical-v3, unchanged. There is no telemetry-to-claim promotion. An explicit quality sentence must first have a supported claim from the existing classifier or a labelled supplied fixture annotation. Reactions cannot create a model estimate independently.

`config/reaction_policy.json` explicitly requires target certainty>=.90, claim confidence>=.60 and market relevance>=.80. The current route is narrative to the synthetic narrative market only. A known game-quality claim has attribution.95; narrative relevance is1, unsupported aspects have relevance0. These constants are illustrative heuristics, not calibrated probabilities. Source OCR/ASR quality failures still exclude the reaction. If any claim used by an otherwise available model estimate fails this gate, the aggregate estimate abstains conservatively. Original non-routed feature diagnostics remain visible.

Reaction intensity, profanity, exclamation marks, excitement, surprise and laughter have no pricing coefficient. Actual GTA VI quote context remains independent of GTA V proxy evidence. Unknown speakers remain unverified. Reaction confidence describes interpretation of the text cue, not speaker identity, transcription accuracy or forecasting skill.

Source/claim/reaction views are memoized for up to16 immutable run/cache/config combinations, with a separate32768-entry lexical-result cache. Publication, seeks and quote refreshes reuse source interpretations. One reaction is emitted per observation ID; duplicate delivery is ignored and conflicting reused IDs fail. Timeline bars show the maximum intensity in each bin, never a sum that could inflate with chat volume. This does not claim perfect native-message deduplication from OCR pixels. Alternative overlapping ASR review passes remain outside the input cache and are not ingested as additional signals.

Reaction records and full snapshots are saved by the same SQLite writer. HTTP/WS include them in the full envelope. Source links and quote/model receipts retain their existing IDs. Runtime fingerprints include reaction classifier/policy versions; old run audit is retained.

## Existing recordings under both layers

The unchanged combined cache contains1651 observations. A text intensity>=.40 is counted below as an active cue; poor recognition has null intensity and other unevaluative text has a low/uncertain description. Counts are generated OCR-line/ASR observations, not independent people, emotions or native chat messages.

| Clip | Cached observations | Active text cues | Cue categories | Supported quality claims / priced reactions |
|---|---:|---:|---|---|
| t1 |105|8|2 amusement;6 emphasis/uncertain|0 /0|
| t2 |221|1|1 amusement|0 /0|
| t3 |303|8|4 surprise;3 amusement;1 uncertain|0 /0|
| t4 |467|6|1 possible frustration;1 excitement;1 surprise;1 amusement;2 uncertain|0 /0|
| t5 |555|13|11 amusement;1 surprise;1 confusion|0 /0|

All1651 original quality claims remain abstained; all recorded estimates and orders remain absent. Telemetry makes reaction activity visible without manufacturing quality evidence.

Strong speech intervals (machine ASR timing/text, not a new listening verification):

| Clip and interval | Cached text | Telemetry interpretation | Pricing exclusion |
|---|---|---|---|
| t4 47.72–53.26s | Yeah, I can't bro. I can't bro stop, I can't | possible frustration, negative, intensity.80, confidence.55; target unknown, certainty.20 | No supported game-quality claim or known quality target; this could also be a comedic reaction. |
| t4 60.56–62.56s | I got it right! | excitement, positive, intensity.75, confidence.60; likely in-game event, certainty.65 | Event/player outcome does not establish game quality. |
| t4 64.56–66.56s | Oh man! | surprise, uncertain valence, intensity.75, confidence.55; target unknown | No quality attribution. |
| t5 58.56–60.56s | Oh my god, what happened? | confusion, uncertain valence, intensity.65, confidence.55; likely in-game event, certainty.65 | Question about an event, no quality opinion. |

t4's repeated-“no” ASR loop remains a quality exclusion with null reaction intensity. t5's role-play/player conversation is not game-quality criticism. Direct audio listening is still unavailable; neither shouting nor facial appearance was measured or interpreted as approval. Full original source review remains in T4_T5_REVIEW.md and data/recordings/speaker-reviews.json.

## Dashboard

Each recording now has a Reaction activity panel: timeline bars, strongest cue in the last configured30 replay seconds, original words/media interval/modality, emotion/valence/intensity/confidence/target, contextual-versus-supported badge, pricing inclusion/exclusion explanation and expandable source/claim/version trace. Only observations available by the replay cursor appear. Missing reaction cues are not displayed as neutral mood. Changes are limited to this per-recording panel and its transport/contracts; the terminal layout and other components retain their previous function.

The separate **Courtroom praise** fixture retains its Synthetic demo badge and supplied fixture evidence. At7s it shows three supported/included claims; the synthetic anchor.5 becomes approximately.5443664542. At the authored timeline's end its existing partial entry and exits remain intact. No fixture observations were added to recordings.

## Verification

Passed `python scripts/manage.py check --gate G3`:15 tests (the original9 plus6 focused reaction tests), zero skips, schema/OpenAPI/generated-type drift, six-scenario validation and React typecheck/build. Focused tests cover intense ambiguous telemetry without pricing, player skill exclusion, explicit supported quality opinion/estimate, attribution/relevance/confidence thresholds, duplicate/conflicting delivery, cached reuse, poor OCR/ASR exclusion even with an inconsistent cached annotation, emphasis alone, and the labelled Courtroom fixture.

Also passed the existing isolated operational commands:

```powershell
python scripts/manage.py demo-check --scenario all
python scripts/manage.py demo-check --scenario recordings
python scripts/manage.py demo-check --scenario foundation
```

Browser checks in installed Edge: five reaction panels, timelines and source exclusion text; t4/t5 strongest intervals; Courtroom three included quality claims and estimate change;390px no horizontal overflow; zero page errors; returned to recordings paused0. Cached full-recording seek-to-end completed in about3.6s during the check. Local evidence: `var/reaction-review/classification-summary.json`, `browser-checks.json`, `t4-telemetry.png`, `t5-telemetry.png`, `t4-mobile.png`, `courtroom-supported.png`. An early summary-print helper attempted dictionary access on a Pydantic object; correcting the helper allowed the report to finish. No unresolved check failure remains.

## Launch and limits

```powershell
python scripts/manage.py demo --scenario recordings --cache var/evidence-cache/aa20c31e1a27bbf0fe075f2c9136360e7096731d9365cdd247c89ade4afe95b6.json --db var/recordings-reactions.sqlite3
```

Open http://127.0.0.1:8000. Stop the current owned server before restarting on the same port. Press Play, or seek to the end to see t4/t5's recent reactions. Select Courtroom praise / Load isolated scenario to inspect its separate supported quality flow.

All emotion, valence, target and intensity scores are deterministic English text heuristics. Intensity is not acoustic arousal, decibels or facial affect. OCR errors, uncertain transcription, sarcasm, role-play and ambiguous targets remain material limits. There are no new model/provider calls or calibration claims. Stop after reaction integration; G4/G5 remain unexecuted.

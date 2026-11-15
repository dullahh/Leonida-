# t4/t5 recording review

Reviewed 15 November 2026, one thread, no subagents. G4 was not started. The user clarified that all of each snippet should be reviewed, with possible highlights inside it. That clarification establishes scope; it does not verify a particular voice or game-quality sentence.

## Inputs and processing

Actual files: `data/recordings/inbox/t4.mp4` (169319427 bytes,67.10s) and `t5.mp4` (170705941 bytes,67.566667s). Both decode at1920x1080 with audio. Inspected full frames at0,10,25,40,55s and additional candidate-reaction frames. They show GTA V RP gameplay, a webcam inset with the same apparent foreground presenter/overlay, and upper-right chat. File IDs are not independent verified streamer identities.

Appended both to `data/recordings/manifest.json`, retaining zero start offsets, unknown speakers and unassigned scenes. The first three manifest assets were copied without changes. Fitted chat rectangles separately: t4 pixels(1698,60,222,322), t5(1698,60,222,320). The crops exclude the large counter below chat. The DISTRICT10 watermark crosses the chat and cannot be removed by a rectangle without deleting messages. Native crops and sampled OCR were inspected; small text, emoji and usernames remain error-prone.

Only the two new assets were preprocessed, using `data/recordings/new-t4-t5.manifest.json`. The source videos, original t1/t2/t3 cache and all original629 observations were preserved. No classifier code or frontend code was changed in this task.

```powershell
python scripts/manage.py preprocess --manifest data/recordings/new-t4-t5.manifest.json
```

Raw new cache: `var/evidence-cache/d7940cd220de426b1b466f1759c77806f8ae66035726361dfcce8314d6e818b8.json`.

| Clip | Sampled frames | OCR observations | Production speech segments | Total |
|---|---:|---:|---:|---:|
| t4 |34|459|8|467|
| t5 |34|526|29|555|

All1022 new observations abstain. OCR counts are line-track observations with unique generated IDs, not a claim of perfectly recovered unique native chat messages. Adjacent-frame tracking is active. No OCR or speech observation contributes quality weight, so possible extraction duplicates cannot inflate an estimate.

## Speech shown before estimate admission

Full original tiny.en and shorter-window base.en transcripts were extracted and made reviewable before launching the composed cache: [t4-t5-transcript-review.md](../data/recordings/t4-t5-transcript-review.md). Raw JSON, full16kHz audio, alternative passes and representative frames are under `var/new-recordings-review/`. Production raw transcripts are also retained in the new cache's immutable artifact tree; wire text is capped240 characters, raw provider text is not rewritten.

Candidate examples, not established game-quality reactions:

| Clip | Machine-estimated media interval | Original tiny.en transcript |
|---|---|---|
| t4 |47.72–53.26s|Yeah, I can't bro. I can't bro stop, I can't|
| t5 |54.76–58.56s|Okay, John I knocked him out you did yeah, he's not there|

t4's initial0–30s transcript repeats “no” and has compression ratio26.24; it is explicitly flagged. Whole-clip base.en also loops. Shorter8s decoding recovered17 t4 and29 t5 review segments, including role-play instructions, “I slipped,” “I knocked him out” and “Give me the gun.” All46 shorter-window segments still abstain even in a diagnostic assuming a verified streamer speaker. Alternative/overlapping ASR passes are review artifacts only, never additional ingested observations.

Direct audio listening is unavailable in this session. Still frames show a reacting person but cannot establish which of the multiple voices uttered each sentence. Therefore no manual record falsely asserts a verified streamer voice. Exact spoken words and exact human-aligned intervals remain unverified; reported times are ASR estimates, not ground truth. Shouting, facial reactions, gameplay failure and a black gameplay screen were not classified as criticism of game quality.

## Manual review and classifier results

[speaker-reviews.json](../data/recordings/speaker-reviews.json) preserves original segment text/ASR quality, source file/hash, observation/cache IDs, interval, source audio and transcript links, exported review clip, reviewer annotation, user scope clarification and classifier version. Records are interval-specific and explicitly **pending audio verification**, with `verified_speaker_role=unknown` and `allowed_to_affect_estimate=false`. Neither entire file was marked as streamer speech.

For each candidate, conservative-lexical-v3 returns: aspect overall; sentiment null; target ambiguous; causal attribution unverified_speaker; confidence null; supporting span null; relevance0; supported claim false. If speaker attribution were verified, both still return null sentiment/confidence/span and abstain because no explicit supported game aspect is evaluated. There is no basis to force a positive/negative label or claim a causal game-quality reaction.

## Individual and combined estimate checks

Pure recorded-data projection was run for t4 alone, t5 alone, both and all five, at end-of-replay with the existing synthetic quote timeline. Results are in `var/new-recordings-review/individual-and-combined.json`.

| Selection | Observations | Supported claims | Features | Model estimate | Orders/fills |
|---|---:|---:|---:|---|---|
| t4 only |467|0|0|null|0/0|
| t5 only |555|0|0|null|0/0|
| t4+t5 |1022|0|0|null|0/0|
| t1–t5 |1651|0|0|null|0/0|

The synthetic Yes midpoint14.5% is quote context, not a generated model estimate. No individual or combined probability change can be demonstrated from these extracted sentences. The route remains the existing narrative scenario; no new route/coefficient was introduced to manufacture an effect. Actual GTA VI quotes remain separate historical/stale context.

## Composed demo and checks

Combined cache: `var/evidence-cache/aa20c31e1a27bbf0fe075f2c9136360e7096731d9365cdd247c89ade4afe95b6.json`. It references both original immutable artifact trees plus a hashed copy of speaker-review records. Its content/artifact digests were validated,1651 IDs are unique, and the first629 observations compare exactly to the prior cached model dumps. The launch pointer selects this composed cache. Re-running the two-file preprocess command selects the new-only cache; use the explicit combined path below to retain all five in the demo.

```powershell
python scripts/manage.py demo --scenario recordings --cache var/evidence-cache/aa20c31e1a27bbf0fe075f2c9136360e7096731d9365cdd247c89ade4afe95b6.json --db var/recordings-t1-t5.sqlite3
```

The app is already running at http://127.0.0.1:8000, root-owned process14352, paused0 after browser reset. Stop that process before restarting on8000. The previous G3 database remains intact.

Passed: two-file preprocessing; cache/artifact validation; exact preservation of old629 observations; all-speech classifier checks; individual/combined abstention projections; HTTP state1651 unique IDs; t4/t5 byte-range206; browser five decoded1920x1080 videos, filters105/221/303/467/555, visible no-estimate/no-order state and reset to a fresh run. Browser metadata was initially not ready at the immediate assertion; an explicit diagnostic load/wait decoded all five. No frontend fix was made or broad browser/G4 gate claimed. Windows logged a connection-reset callback when the browser closed media connections; subsequent API requests succeeded. Evidence: `var/new-recordings-review/browser-checks.json` and `five-recordings-desktop.png`.

Remaining gap: no verified explicit game-quality reaction was found in the available text, and audio speaker verification could not be completed. The two clips are processed and reviewable, but supported-speech-to-estimate admission is deliberately incomplete rather than fabricated. Human listening with a specific sentence/time is needed to resolve that gap. Stop after this recording validation.

# Supplied recording review - 15 November 2026

Historical G2 input review. Recording/crop/cache findings below remain unchanged. G3 has since been completed; the current process, launch commands and acceptance are in [G3_HANDOFF.md](G3_HANDOFF.md). The old process/stop statements below describe the earlier checkpoint.

This is a G2 input/configuration and correctness follow-up. G3 was not started. The three actual files are `data/recordings/inbox/t1.mp4`, `t2.mp4`, and `t3.mp4`. All are 1920x1080, 30 fps, H.264/AAC with audio. These are user-supplied screen recordings, not the earlier generated test media.

The app is running at http://127.0.0.1:8000 with all three clips. Root-owned server PID 78492 uses `var/recordings-t1-t3.sqlite3`. The user run is paused at 0; press Play. The manifest retains zero media/timeline offsets, null source hashes (preprocessing computes them), `manual-unassigned` scenes and unknown speakers. Clip IDs t1/t2/t3 are source-file labels, not verified identities or three independent streamers. Zero offsets align recording starts; they do not establish a shared in-game event.

## Per-clip output

| File | Duration | Sampled frames | OCR observations | ASR segments | Total |
|---|---:|---:|---:|---:|---:|
| t1.mp4 |38.367s|20|89|16|105|
| t2.mp4 |52.900s|27|202|19|221|
| t3.mp4 |45.867s|23|277|26|303|
| Total | |70|568|61|629|

Counts are deduplicated OCR line tracks and speech segments, not native chat message counts. OCR can split a message or username, misread the same line differently, or capture overlapping UI. All 629 observations have null game-quality sentiment with an abstention reason. The conservative interpreter found no attributable configured quality signal; unknown/mixed speakers also abstain. No model estimate or paper decision is fabricated. Actual GTA VI quotes remain separate historical/stale venue context.

Examples from actual extraction, with errors left intact:

- t1: chat about heist setup, helping Amanda and other conversation; `Choose ricky for the next hcist` contains an OCR error for visible `heist`. ASR includes `I didn't know you had that opportunity.` The shorter phrase `You had that opportunity` also appears in the visible game subtitle near 9.6s; this is limited visual corroboration, not verification of the whole transcript.
- t2: chat includes `MAKEONE`; gameplay instructions and the BANKING notification overlap the chat. ASR includes `recruit we gotta go to the ATM chat do we make one or join one` and `take money out so you can get a phone`.
- t3: chat includes `whichgame is this` and `what typa game isthis?roblox?`; emoji and names are often garbled. ASR starts `Okay, we're gonna go to this clothing store...` and includes `What do you want me to do?`. Five retained speech segments have repetition/high-compression warnings.

Use the app's **Filter by source** control to inspect105/221/303 observations separately. Expand source/extraction details for cached chat crops and extracted audio. Raw provider outputs are not corrected quotations or established game approval.

## Crop inspection

Representative full frames at 0, roughly 10-12s, midpoint and near end were extracted and inspected. Native 15-second trial crops were compared with real OCR. Final cached 16-second crops and their OCR audit were inspected again.

| Clip | Pixel rectangle (x,y,width,height) | Normalized manifest rectangle |
|---|---|---|
| t1 |1450,52,453,1022|0.75520833,0.04814815,0.2359375,0.94629630|
| t2 |1584,58,336,330|0.825,0.05370370,0.175,0.30555556|
| t3 |1584,58,336,330|0.825,0.05370370,0.175,0.30555556|

These replace the initial generic crop. t1 excludes the right-panel header, avatars and scrollbar while retaining chat. Its initial OBS window partly obscures chat; zero start offsets were preserved as requested. Its welcome banner lies inside the scrolling panel and remains possible OCR noise. t2/t3 exclude the large counter below the chat; BANKING notifications and DISTRICT10 watermark overlap the chat itself and cannot be removed by a single rectangle without also deleting messages. Their source text is smaller and lower contrast. Further rectangular tightening would remove visible chat, so the inspected crops were retained.

Observed OCR median provider confidence: t1 .964,t2 .924,t3 .907; counts below .75 are 7, 33, 27. These are provider scores, not measured accuracy: visibly wrong words sometimes exceed .9. Most stable t1 lines were marked `new_observation=false` at 16s, confirming adjacent-frame tracking is active. Raw UI/emoji/partial text is retained with provenance and abstains from pricing.

## Audio review and limits

Actual audio was decoded from every file to 16-kHz mono PCM and transcribed locally with tiny.en. I could not directly listen: this session's audio tool explicitly reports that audio input is unsupported. Therefore this is a machine cross-check, not a completed human listening audit.

A separate base.en pass and a beam5/VAD/word-timestamp variant processed the source audio. They agreed on several ATM/phone/clothing-store phrases but disagreed substantially elsewhere and produced decoding loops; base.en was not promoted to the production manifest. Cross-model text similarity is recorded only as disagreement evidence, never recognition accuracy. Full review audio is preserved as `var/local-recordings-review/t1-review.wav`, `t2-review.wav`, `t3-review.wav` for direct listening.

The review exposed a real timestamp risk: base.en emitted speech after t3's 45.867-second end. The G2 pipeline now rejects nonfinite, negative, nonpositive and out-of-PCM intervals instead of clamping them into false end-of-file events. It retains raw transcripts and `transcript-validation.json`, and flags high-compression/repeated text for abstention. The final tiny.en outputs had no out-of-file segments: last segment ends are 38.32, 52.2 and 45.8 seconds. t3 has 5 quality warnings; all speakers remain unknown. These are uncertain machine transcripts.

## Cache and reproducibility

Final cache: `var/evidence-cache/a6d8a27fa3c4f5c3e34b2b8a411457e6cc2a50b5362341b12bd8904d039343d9.json`. The launch pointer now selects it. Actual hashes were computed from video bytes and stored in the cache while the editable manifest hashes remain null. The initial full raw OCR cache `fce3164759597b40ab2d7f8eac0606ff88dc75ef91f662346ff93b6ac2275049` remains immutable.

For the ASR-only correctness rerun, the pipeline reused validated raw OCR crops/audit after matching hashes, crop, timing and provider identities, reran tracking/current semantics, and reran actual tiny.en ASR. A failing OCR-constructor probe proved OCR was not repeated. A subsequent final-cache load with OCR/ASR disabled reused the cache without rewriting it. Cache provenance and all artifact digests were verified.

```powershell
python scripts/manage.py preprocess --manifest data/recordings/manifest.json
python scripts/manage.py demo --scenario recordings --db var/recordings-t1-t3.sqlite3
```

The server is already running; these are restart/reprocess commands. Stop the existing server before binding the same port again.

## Verification

- Manifest validation: all 3 actual paths, zero offsets, null hashes, unassigned scenes, recorded/proxy modes and unknown speakers.
- Actual preprocessing and cached reuse: successful; 629 unique IDs, 70 frames, speech timing within actual PCM; no neutral substitution.
- `python scripts/manage.py check --gate G2`: passed schema/type drift, six fixtures, imports, frontend typecheck/build.
- G1 fallback demo-check passed after the inspector was generalized for abstention.
- Actual recording demo-check: HTTP/WS equality, 629 observations, no estimates/decisions/receipts, clean isolated shutdown. The inspector's 1 MiB default client limit was too small for the real full snapshot and was raised to 16 MiB; the rerun passed.
- Browser via installed Edge: all 3 videos decoded at 1920x1080; 2x play/pause reached replay 3.436s with video times 3.436/3.436/3.518s; seek-to-end reached 52.9s; source filters showed 105/221/303 rows; abstention and Unknown/Unassigned scenes visible; desktop 1440/narrow 390 had no horizontal overflow, console errors or HTTP failures. User run reset to paused 0 afterwards; server retained.

Local review evidence: `var/local-recordings-review/metadata.json`, `selected-cached-ocr.json`, `pipeline-quality-summary.json`, `transcript-comparison.json`, `*-base-review.json`, `*-base-bounded.json`, `browser-checks.json`, `app-recordings-desktop.png`, `app-recordings-mobile.png`. Worker changes are recorded in pipeline/frontend handoffs. No formal G4 test suite or G3 execution integration was started.

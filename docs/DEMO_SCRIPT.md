# Three-minute judge demonstration

Use a local-only instance. No live quote flag, API credentials, model setup or preprocessing. Full mode: `python scripts/manage.py demo --scenario recordings`. Portable mode: `python scripts/manage.py demo --scenario portable`. Open the printed localhost URL; use `--port 8001` if8000 is occupied. Default startup falls back to the synthetic Courtroom fixture when local media/cache are absent.

Before the pitch, Reset to a fresh run, close dialogs, choose full mode if the five clips/cache are available, and confirm browser audio is muted. Synthetic accounting seeks forward only; Reset is the way to replay earlier points. Drag/release the replay position slider, or focus it and press End to reach the scenario end. Source text and timestamps are machine extraction, not verified verbatim listening.

| Time | Controls | Suggested narration |
|---|---|---|
|0:00–0:30|Play briefly, pause, then focus timeline and press End. Scroll to t4/t5 source cards.|“Streams contain reactions, but not every reaction evaluates the product. These are actual supplied GTA V proxy recordings with cached chat OCR and speech transcripts.”|
|0:30–0:55|Expand **Reaction source and pricing trace** on t4 or t5.|“‘I can't bro’ could be frustration or comedy; ‘what happened?’ is an event reaction. Text heuristics make that context visible. Unknown targets and missing quality claims keep them out of pricing. All five real clips currently abstain.”|
|0:55–1:25|Choose **Courtroom praise**, click **Load isolated scenario**, seek to2 seconds.|“This is a separate, clearly labelled supplied fixture. Explicit narrative praise passes the claim and market-relevance gates. A50% synthetic quote anchor moves to about54.47% under an uncalibrated bounded correction.”|
|1:25–1:50|Open **Inspect full receipt**, close it; scroll to Paper activity and open **Inspect trace**, then **Eligibility receipt**.|“Here are the supporting words, features, coefficient/version and quote IDs. Paper execution rechecks inputs after250ms. It fills6 of10 requested contracts at.5025, charges.06 and cancels the remainder.”|
|1:50–2:20|Close trace. Focus replay slider and press End (310s). Inspect Paper activity.|“Seeking processes every intervening event. The authored synthetic price timeline supplies two exits,4 then2 contracts. Fees total.12; the position is flat and cash is10000.08. This result is arithmetic on simulated prices, not a profit forecast.”|
|2:20–2:45|Choose **Venue outage / reset**, load it, seek to10.2s.|“The quote expires at10s before the pending order's eligibility at10.15s. It is cancelled, cash stays10000 and fills stay zero. Missing or stale prices prevent execution.”|
|2:45–3:00|Return to recordings, or leave the portable fixture labelled.|“The deliverable is an auditable research desk. Actual captures, machine text, heuristic interpretation and paper simulation retain their provenance. Next is held-out calibration and realistic venue execution evaluation.”|

Portable-only pitch: spend the first55 seconds explaining that private recordings are intentionally absent from source control and showing the fixture's clearly labelled input/mode badges. Do not claim actual footage is present. Start the supported-claim sequence at0:55. Source-only mode has no video players; it remains a complete deterministic evidence-to-paper demonstration.

## Six scenario reference

- Courtroom praise: supported narrative claims, bounded upward adjustment, partial entry and timed exits. End310s.
- Technical failure/laughter: negative technical diagnostics; laughter/rebroadcast do not create a positive narrative estimate. End30s.
- Skill rage/controls: exclude player-skill statement; retain explicit negative gameplay feature without inventing a narrative route. End30s.
- Mixed/missing facecam: disagreement, absent facecam and cancelled pending entry after quote movement. Seek1.3s or end30s.
- Duplicate/reconnect: repeated input/quote publication leaves unique evidence and one partial entry; stale residual inventory can remain unpriced. End30s.
- Venue outage/reset: quote stale at10s; cancel at10.15s. Seek10.2s; Reset creates a new run and retains old audit. End45s.

The rehearsal exercised the full control flow in22.4s without narration. Budget the rest for explanation. Installed Edge was checked; no cross-browser certification is claimed. If media is unavailable, use portable mode immediately instead of downloading or preprocessing during a pitch.

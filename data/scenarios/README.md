# Explicitly synthetic fallback scenarios

The six JSON scenarios are authored fixture annotations, not model output or
recorded Twitch observations. Each declares six source slots, source and
availability times, manual scene/dependency identity, an explicit baseline seed,
separate synthetic quote/depth timeline and qualitative invariants. No input
promises profits. Missing sources/modalities have no fabricated observations.

`backend.ingestion.replay.load_scenario` builds stable content-addressed caches;
`StructuredReplaySource` provides ordered windows without sleeps. Its duplicate
delivery mode deliberately repeats identical IDs. Playback speed does not change
event times or IDs. Runtime scheduling and quote expiry remain root-owned.

## G3 lifecycle fixtures (v3)

All six fixtures explicitly set `simulation_authorized=true` and a finite
`duration_seconds`. This authorization applies to their supplied synthetic
annotations and synthetic books only. Real recording manifests/caches are
unchanged. Quote events include source/capture/availability offsets, coherent
Yes/No prices, explicit sizes, a liquidity identity and the illustrative
`simulation-linear-v1` fee schedule.

| Scenario | Timeline exercised |
|---|---|
| Courtroom praise | First +.4 narrative annotation arrives at 1s with seeded z=2 and a .5 quote midpoint. A 10-contract request has six asks available. Labelled synthetic convergence arrives at 8s. Fresh books at 300s/304s supply four then two held-side exit bids. Duration: 310s. |
| Technical failure/laughter | Negative technical evidence and a shared rebroadcast dependency remain visible; laughter abstains and no narrative route is invented. Duration: 30s. |
| Skill rage/controls | Skill-only text abstains while explicit control criticism remains a gameplay feature with no configured narrative route. Duration: 30s. |
| Mixed/missing facecam | Positive speech arrives at 1s. Critical chat and a quote move arrive at 1.1s before the 1.25s pending-entry deadline; the old limit/current EV block execution. Duration: 30s. |
| Duplicate/reconnect | Three deliveries per source observation preserve IDs. Quote wrappers at 2s/5s retain the original liquidity identity and exact book, so they cannot replenish consumed depth. Duration: 30s. |
| Venue outage/reset | Positive evidence at 9.9s can reserve an entry; the last quote expires at 10s before 10.15s eligibility. Later evidence cannot refresh the quote. Duration: 45s; reset is a root runtime command. |

`expected_lifecycle` documents intended checkpoints, not saved orders, fills or
profit. The broker must calculate those results. Courtroom's first time-exit
deadline is 300 seconds after its actual entry fill, rather than 300 seconds
after scenario start. With the normal 250ms latency, the first entry fill is at
1.25s, the exit is due at 301.25s and can execute at 301.5s. A later causal quote
at 304s allows a residual exit; publication timers do not invent retries.

`validate_scenario` checks synthetic authorization, six statuses, source/quote
times, duration, fee provenance and immutable liquidity republication. The CLI
validates fixtures; root's integrated runtime checks scheduling, persistence and
the complete paper lifecycle.

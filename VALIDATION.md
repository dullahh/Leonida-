# Starter-pack validation

Current application checkpoint: G1 was implemented and verified on 14 November 2026. See [G1_HANDOFF.md](docs/G1_HANDOFF.md) and [STATE.md](docs/STATE.md) for actual application commands/results and limits. The original handoff-only report below is retained as historical evidence; it does not describe the current installed CLI/dependencies or imply G2–G5 acceptance.

Validated 14 November 2026.

## Checks actually run
- python scripts/validate_pack.py: passed.
- Six TOML files parsed; all five standalone role files have required name/description/instructions.
- Reference Pydantic schema exported.
- Dashboard example round-tripped through StreamEnvelope.
- Decimal price serialized as a decimal string.
- Five invalid payload cases rejected (bounds, crossed spread, naive time, unknown field, mismatched run).
- Illustrative logit correction numerically matches the 9.7% example.
- Seven planning/build prompt files found.
- Public Kalshi refresh: five seed event families captured, no reported fetch errors.
- Independent quant and architecture reviews completed; corrections applied for transport envelope, ownership, replay ID normalisation, liquidation depth and actual fill VWAP.

## Codex verification limits
- Workspace CLI: codex-cli 0.167.0-alpha.4.
- CLI accepted agents.enabled and agents.max_concurrent_threads_per_session overrides for features inspection.
- The attempted --strict-config features command is unsupported on this CLI. No strict project-config or actual custom-agent spawning test is claimed.
- Role schema/settings were checked against current official documentation.
- User-machine version, trust, model access, custom-role discovery and MCP capability still require the G0 smoke test.
- No user-level Codex configuration was changed.
- No retired model is pinned.

## What was not tested
This is a handoff pack, not an implemented application. No claim is made that FastAPI/frontend code, Twitch A/V, semantic providers, market WebSockets, fee adapters, paper runtime, browser UI, historical calibration or profitable trading have passed tests.

The generated example is synthetic and candidate-only. Actual captured market responses retain their timestamp; they are historical reference, not current execution liquidity.


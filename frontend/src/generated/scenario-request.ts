/* Generated from schema 2 serialization output. Root-owned; do not edit. */

export type CommandId = string;
export type Scenario =
  | "courtroom-praise"
  | "technical-failure-laughter"
  | "skill-rage-controls"
  | "mixed-missing-facecam"
  | "duplicate-reconnect"
  | "venue-outage-reset";

export interface ScenarioRequest {
  command_id: CommandId;
  scenario: Scenario;
}

/* Generated from schema 2 serialization output. Root-owned; do not edit. */

export type CommandId = string;
export type Scenario =
  | (
      | "foundation"
      | "recordings"
      | "courtroom-praise"
      | "technical-failure-laughter"
      | "skill-rage-controls"
      | "mixed-missing-facecam"
      | "duplicate-reconnect"
      | "venue-outage-reset"
    )
  | null;

export interface CreateRunRequest {
  command_id: CommandId;
  scenario?: Scenario;
}

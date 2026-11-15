/* Generated from schema 2 serialization output. Root-owned; do not edit. */

export type CommandId = string;
export type Action = "reset" | "replay_observation" | "play" | "pause" | "seek" | "set_speed" | "exit";
export type PositionSeconds = number | null;
export type Speed = number | null;

export interface RunCommand {
  command_id: CommandId;
  action: Action;
  position_seconds?: PositionSeconds;
  speed?: Speed;
}

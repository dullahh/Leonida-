/* Generated from schema 2 serialization output. Root-owned; do not edit. */

export type SchemaVersion = "1";
export type SignalId = string;
export type SourceWindowId = string;
export type StreamId = string;
export type EvidenceMode = "live";
export type StartSeconds = number;
export type EndSeconds = number;
export type EventStartAt = string;
export type EventEndAt = string;
export type Text = string;
export type Aspect = "narrative" | "overall" | "technical" | "gameplay" | "audio";
export type Target = "game" | "player_skill" | "streamer" | "unrelated" | "ambiguous";
export type Sentiment = number | null;
export type AbstentionReason = string | null;
export type SemanticConfidence = number | null;
export type ClassifierName = string;
export type ClassifierVersion = string;
export type SpeakerRole = "unknown" | "streamer";
export type Status = "candidate" | "abstain";

/**
 * Live speech interpretation, separate from recorded proxy claims and pricing.
 */
export interface LiveAudioSentimentSignal {
  schema_version?: SchemaVersion;
  signal_id: SignalId;
  source_window_id: SourceWindowId;
  stream_id: StreamId;
  evidence_mode?: EvidenceMode;
  start_seconds: StartSeconds;
  end_seconds: EndSeconds;
  event_start_at: EventStartAt;
  event_end_at: EventEndAt;
  text: Text;
  aspect: Aspect;
  target: Target;
  sentiment: Sentiment;
  abstention_reason?: AbstentionReason;
  semantic_confidence?: SemanticConfidence;
  classifier_name: ClassifierName;
  classifier_version: ClassifierVersion;
  speaker_role?: SpeakerRole;
  status: Status;
}

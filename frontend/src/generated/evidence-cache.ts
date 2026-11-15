/* Generated from schema 2 serialization output. Root-owned; do not edit. */

export type SchemaVersion = "2";
export type CacheKey = string;
export type InputSha256 = string;
export type PayloadSha256 = string;
export type SchemaVersion1 = "2";
export type ManifestVersion = string;
/**
 * @minItems 2
 * @maxItems 6
 */
export type Recordings =
  | [RecordingAsset, RecordingAsset]
  | [RecordingAsset, RecordingAsset, RecordingAsset]
  | [RecordingAsset, RecordingAsset, RecordingAsset, RecordingAsset]
  | [RecordingAsset, RecordingAsset, RecordingAsset, RecordingAsset, RecordingAsset]
  | [RecordingAsset, RecordingAsset, RecordingAsset, RecordingAsset, RecordingAsset, RecordingAsset];
export type AssetId = string;
export type StreamId = string;
export type Label = string;
export type LocalPath = string | null;
export type AssetSha256 = string | null;
export type AvailabilityReason = string | null;
export type ContentGameId = "gta5";
export type TargetGameId = "gta6";
export type EvidenceScope = "proxy_demo";
export type MediaStartSeconds = number;
export type TimelineStartSeconds = number;
export type X = number;
export type Y = number;
export type Width = number;
export type Height = number;
export type SampleIntervalSeconds = number;
export type Language = string;
export type SourceUrl = string | null;
export type PermissionNote = string;
export type EvidenceMode = "recorded" | "synthetic_replay";
export type MediaEndSeconds = number | null;
export type SceneId = string;
export type AudioTranscription = "disabled" | "faster_whisper";
export type SpeechModelPath = string | null;
export type SpeakerRole = "streamer" | "unknown";
export type OcrVersion = string;
export type PreprocessingVersion = string;
export type SemanticVersion = string;
export type ObservationId = string;
export type AssetId1 = string;
export type StreamId1 = string;
export type ContentGameId1 = "gta5";
export type EvidenceScope1 = "proxy_demo";
export type EvidenceMode1 = "recorded" | "synthetic_replay";
export type Provider = "supplied_fixture" | "sampled_frame_ocr" | "recorded_asr";
export type MediaSeconds = number;
export type ReplaySeconds = number;
export type RawText = string;
export type SupportingQuote = string;
export type Sentiment = number | null;
export type AbstentionReason = string | null;
export type OcrConfidence = number | null;
export type ConfidenceReason = string | null;
export type FrameRef = string | null;
export type FrameReason = string | null;
export type Aspect = "narrative" | "overall" | "technical" | "gameplay" | "audio";
export type Target = "game" | "player_skill" | "streamer" | "unrelated" | "ambiguous";
export type SourceModality = "chat" | "speech";
export type SemanticConfidence = number | null;
export type MediaEndSeconds1 = number | null;
export type ReplayEndSeconds = number | null;
export type AvailableReplaySeconds = number | null;
export type OcrBoxes = number[][];
export type TrackId = string | null;
export type DependencyGroup = string | null;
export type AudioRef = string | null;
export type SceneId1 = string;
export type ExtractorVersion = string;
export type Observations = CachedObservation[];
export type AssetId2 = string;
export type Available = boolean;
export type Reason = string | null;
export type DurationSeconds = number | null;
export type FrameCount = number;
export type AudioAvailable = boolean;
export type AudioReason = string | null;
export type AudioRef1 = string | null;
export type SpeechAvailable = boolean;
export type SpeechReason = string | null;
export type AssetReports = MediaAssetReport[];

export interface EvidenceCache {
  schema_version?: SchemaVersion;
  cache_key: CacheKey;
  input_sha256: InputSha256;
  payload_sha256: PayloadSha256;
  manifest: RecordingManifest;
  observations: Observations;
  asset_reports?: AssetReports;
  extraction_metadata?: ExtractionMetadata;
}
export interface RecordingManifest {
  schema_version?: SchemaVersion1;
  manifest_version: ManifestVersion;
  recordings: Recordings;
  ocr_version: OcrVersion;
  preprocessing_version: PreprocessingVersion;
  semantic_version: SemanticVersion;
}
export interface RecordingAsset {
  asset_id: AssetId;
  stream_id: StreamId;
  label: Label;
  local_path: LocalPath;
  asset_sha256: AssetSha256;
  availability_reason: AvailabilityReason;
  content_game_id?: ContentGameId;
  target_game_id?: TargetGameId;
  evidence_scope?: EvidenceScope;
  media_start_seconds?: MediaStartSeconds;
  timeline_start_seconds?: TimelineStartSeconds;
  chat_region: ChatRegion;
  sample_interval_seconds?: SampleIntervalSeconds;
  language?: Language;
  source_url?: SourceUrl;
  permission_note: PermissionNote;
  evidence_mode?: EvidenceMode;
  media_end_seconds?: MediaEndSeconds;
  scene_id?: SceneId;
  audio_transcription?: AudioTranscription;
  speech_model_path?: SpeechModelPath;
  speaker_role?: SpeakerRole;
}
export interface ChatRegion {
  x: X;
  y: Y;
  width: Width;
  height: Height;
}
export interface CachedObservation {
  observation_id: ObservationId;
  asset_id: AssetId1;
  stream_id: StreamId1;
  content_game_id?: ContentGameId1;
  evidence_scope?: EvidenceScope1;
  evidence_mode: EvidenceMode1;
  provider: Provider;
  media_seconds: MediaSeconds;
  replay_seconds: ReplaySeconds;
  raw_text: RawText;
  supporting_quote: SupportingQuote;
  sentiment: Sentiment;
  abstention_reason?: AbstentionReason;
  ocr_confidence: OcrConfidence;
  confidence_reason?: ConfidenceReason;
  frame_ref: FrameRef;
  frame_reason: FrameReason;
  aspect?: Aspect;
  target?: Target;
  source_modality?: SourceModality;
  semantic_confidence?: SemanticConfidence;
  media_end_seconds?: MediaEndSeconds1;
  replay_end_seconds?: ReplayEndSeconds;
  available_replay_seconds?: AvailableReplaySeconds;
  ocr_boxes?: OcrBoxes;
  track_id?: TrackId;
  dependency_group?: DependencyGroup;
  audio_ref?: AudioRef;
  scene_id: SceneId1;
  extractor_version: ExtractorVersion;
}
export interface MediaAssetReport {
  asset_id: AssetId2;
  available: Available;
  reason?: Reason;
  duration_seconds?: DurationSeconds;
  frame_count?: FrameCount;
  audio_available?: AudioAvailable;
  audio_reason?: AudioReason;
  audio_ref?: AudioRef1;
  speech_available?: SpeechAvailable;
  speech_reason?: SpeechReason;
}
export interface ExtractionMetadata {
  [k: string]: string;
}

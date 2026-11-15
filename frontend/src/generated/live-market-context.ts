/* Generated from schema 2 serialization output. Root-owned; do not edit. */

export type SchemaVersion = "1";
export type DiscoveryId = string;
export type ObservedAt = string;
export type DiscoveryStatus =
  | "matched"
  | "stream_offline"
  | "twitch_unavailable"
  | "no_game_category"
  | "no_matching_markets"
  | "kalshi_unavailable";
export type Status = "live" | "offline" | "unavailable" | "user_provided";
export type ChannelLogin = string | null;
export type GameId = string | null;
export type GameName = string | null;
export type Source = "twitch_helix" | "manual";
export type ObservedAt1 = string;
export type Reason = string | null;
export type GameSource = "twitch_helix" | "manual";
export type MarketSource = "kalshi_public_api";
export type MarketError = string | null;
export type MarketId = string;
export type Ticker = string;
export type EventTicker = string;
export type SeriesTicker = string;
export type Category = "video_games" | "esports";
export type EventTitle = string;
export type MarketTitle = string;
export type OutcomeName = string;
export type MatchedGameName = string;
export type MatchMethod = "game-yes-outcome-exact-v1";
export type MatchRationale = string;
export type MarketStatus = string;
export type MarketIsOpen = boolean;
export type RulesPrimary = string | null;
export type RulesSecondary = string | null;
export type YesBid = string | null;
export type YesAsk = string | null;
export type NoBid = string | null;
export type NoAsk = string | null;
export type YesBidSize = number | null;
export type YesAskSize = number | null;
export type NoBidSize = number | null;
export type NoAskSize = number | null;
export type QuoteMode = "live" | "cached_stale";
export type IsStale = boolean;
export type CapturedAt = string;
export type SourceRef = string;
export type Candidates = LiveMarketCandidate[];
export type ReviewId = string;
export type MarketId1 = string;
export type Status1 = "abstain";
export type ModelVersion = string;
export type CalibrationStatus = "not_estimated";
export type ExecutionMode = "paper";
export type Reasons = string[];
export type DecisionReviews = LiveDecisionReview[];

export interface LiveMarketContext {
  schema_version?: SchemaVersion;
  discovery_id: DiscoveryId;
  observed_at: ObservedAt;
  discovery_status: DiscoveryStatus;
  twitch: TwitchGameContext;
  game_source?: GameSource;
  market_source?: MarketSource;
  market_error?: MarketError;
  candidates?: Candidates;
  decision_reviews?: DecisionReviews;
}
export interface TwitchGameContext {
  status: Status;
  channel_login?: ChannelLogin;
  game_id?: GameId;
  game_name?: GameName;
  source?: Source;
  observed_at: ObservedAt1;
  reason?: Reason;
}
export interface LiveMarketCandidate {
  market_id: MarketId;
  ticker: Ticker;
  event_ticker: EventTicker;
  series_ticker: SeriesTicker;
  category: Category;
  event_title: EventTitle;
  market_title: MarketTitle;
  outcome_name: OutcomeName;
  matched_game_name: MatchedGameName;
  match_method: MatchMethod;
  match_rationale: MatchRationale;
  market_status: MarketStatus;
  market_is_open?: MarketIsOpen;
  rules_primary?: RulesPrimary;
  rules_secondary?: RulesSecondary;
  yes_bid?: YesBid;
  yes_ask?: YesAsk;
  no_bid?: NoBid;
  no_ask?: NoAsk;
  yes_bid_size?: YesBidSize;
  yes_ask_size?: YesAskSize;
  no_bid_size?: NoBidSize;
  no_ask_size?: NoAskSize;
  quote_mode: QuoteMode;
  is_stale: IsStale;
  captured_at: CapturedAt;
  source_ref: SourceRef;
  missing_reasons?: MissingReasons;
}
export interface MissingReasons {
  [k: string]: string;
}
/**
 * Explicit live-route abstention; distinct from proxy estimates and paper orders.
 */
export interface LiveDecisionReview {
  review_id: ReviewId;
  market_id: MarketId1;
  status?: Status1;
  model_version?: ModelVersion;
  calibration_status?: CalibrationStatus;
  execution_mode?: ExecutionMode;
  reasons: Reasons;
}

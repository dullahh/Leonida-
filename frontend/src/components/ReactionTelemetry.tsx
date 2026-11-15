import type { ReactionSignal } from '../generated/contracts';
import { Badge, duration } from './Primitives';

export function ReactionTelemetry({ reactions, position, end, recentSeconds }: {
  reactions: ReactionSignal[]; position: number; end: number; recentSeconds: number;
}) {
  const observed = reactions.filter(r => r.available_replay_seconds <= position);
  const recent = observed.filter(r => r.available_replay_seconds >= position - recentSeconds && r.intensity != null && r.intensity >= .4);
  const strongest = recent.slice().sort((a, b) => (b.intensity ?? 0) - (a.intensity ?? 0) || b.available_replay_seconds - a.available_replay_seconds)[0];
  const bins = Array.from({ length: 32 }, () => 0);
  for (const reaction of observed) {
    if (reaction.intensity != null && reaction.intensity >= .4) {
      const index = Math.min(31, Math.floor(reaction.available_replay_seconds / Math.max(end, 1) * 32));
      bins[index] = Math.max(bins[index], reaction.intensity);
    }
  }
  return <section className="reaction-telemetry" aria-label="Reaction telemetry">
    <div className="reaction-heading"><span className="eyebrow">Reaction activity</span><Badge tone={strongest?.included_in_estimate ? 'green' : 'muted'}>{strongest?.supported_claim_id ? 'Supported claim' : 'Contextual telemetry'}</Badge></div>
    <svg viewBox="0 0 320 42" role="img" aria-label="Reaction activity over replay time; each bar is the maximum text intensity in its time interval">
      {bins.map((height, index) => <rect key={index} x={index * 10 + 1} y={40 - height * 36} width="7" height={Math.max(1, height * 36)} fill={height ? 'var(--accent, #b9e87b)' : '#344238'}><title>{duration(index / 32 * end)}: {height.toFixed(2)} text intensity</title></rect>)}
    </svg>
    <div className="reaction-axis"><span>00:00</span><span>Text intensity 0–1 · {duration(end)}</span></div>
    {strongest ? <>
      <p className="reaction-summary"><b>{strongest.emotion ?? 'Uncertain emotion'} · {strongest.valence}</b><span>Intensity {strongest.intensity?.toFixed(2)} · confidence {strongest.confidence == null ? 'unavailable' : strongest.confidence.toFixed(2)}</span></p>
      <p className="reaction-quote">“{strongest.supporting_text}”</p>
      <p className="tiny muted">Media {strongest.media_seconds.toFixed(2)}{strongest.media_end_seconds != null ? `–${strongest.media_end_seconds.toFixed(2)}` : ''}s · {strongest.source_modality} · target {strongest.likely_target.replaceAll('_', ' ')} ({strongest.target_certainty.toFixed(2)})</p>
      <p className={`reaction-exclusion ${strongest.included_in_estimate ? 'included' : ''}`}>{strongest.included_in_estimate ? 'Included: supported game-quality claim passes attribution, confidence and market relevance gates.' : strongest.exclusion_reason ?? 'Excluded: no current estimate is available.'}</p>
      <details><summary>Reaction source and pricing trace</summary><p>{strongest.abstention_reason ?? 'Reaction description is heuristic; inspect the original source.'}</p><p>Classifier {strongest.classifier_version} · policy {strongest.policy_version} · relevance {strongest.market_relevance.toFixed(2)}</p><p className="mono">Observation {strongest.observation_id}</p><p className="mono">Claim {strongest.supported_claim_id ?? 'None — contextual telemetry only'}</p><p>Available at replay {strongest.available_replay_seconds.toFixed(2)}s. Strongest reaction in the last {recentSeconds}s.</p></details>
    </> : <p className="tiny muted">No reliable reaction cue in the last {recentSeconds}s. Missing or poor-quality text does not imply a neutral mood.</p>}
    <p className="reaction-note">Text cues only; vocal loudness and facial emotion are not measured. Activity does not establish game quality.</p>
  </section>;
}

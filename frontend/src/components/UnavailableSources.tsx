import type { SourceStatus } from '../generated/contracts';
import { Badge, Icon } from './Primitives';

export function UnavailableSources({ sources }: { sources: SourceStatus[] }) {
  if (!sources.length) return null;
  return <div className="source-status-grid" aria-label="Unassigned source slots">{sources.map(source => <article key={source.stream_id} className="source-status-card"><Icon name="video" size={16} /><div><strong>{source.label}</strong><span className="mono">{source.stream_id}</span><p>{source.reason}</p></div><Badge tone={source.state === 'error' ? 'red' : 'muted'}>{source.state === 'error' ? 'Error' : 'Unavailable'}</Badge></article>)}</div>;
}

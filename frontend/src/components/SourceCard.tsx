import { useEffect, useRef, useState } from 'react';
import type { EvidenceClaim, FeatureSnapshot, PlaybackState, ReactionSignal, RecordingAsset, SourceStatus, SourceWindow } from '../generated/contracts';
import { ReactionTelemetry } from './ReactionTelemetry';
import { Badge, duration, Icon, signed } from './Primitives';

export function SourceCard({ asset, index, status, window, windows, claims, feature, playback, runId, reactions = [], reactionRecentSeconds = 30 }: {
  asset: RecordingAsset; index: number; status?: SourceStatus; window?: SourceWindow;
  runId: string;
  windows: SourceWindow[];
  reactions?: ReactionSignal[];
  reactionRecentSeconds?: number;
  claims: EvidenceClaim[]; feature?: FeatureSnapshot; playback?: PlaybackState;
}) {
  const video = useRef<HTMLVideoElement>(null);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [muted, setMuted] = useState(true);
  const [ready, setReady] = useState(false);
  const [mediaDuration, setMediaDuration] = useState<number | null>(null);
  const hasMedia = Boolean(asset.local_path && asset.asset_sha256 && !asset.availability_reason && status?.state !== 'error' && status?.state !== 'recording_missing');
  const generatedMedia = asset.evidence_mode === 'synthetic_replay';
  const aggregate = (feature?.stream_ids?.length ?? 0) > 1;
  const target = (playback?.position_seconds ?? window?.replay_seconds ?? 0) - (asset.timeline_start_seconds ?? 0) + (asset.media_start_seconds ?? 0);
  const beforeStart = (playback?.position_seconds ?? 0) < (asset.timeline_start_seconds ?? 0);

  useEffect(() => {
    const element = video.current;
    if (!element || !hasMedia || !ready) return;
    element.playbackRate = playback?.speed ?? 1;
    if (!Number.isFinite(target) || target < 0 || beforeStart) { element.pause(); return; }
    const max = Number.isFinite(element.duration) ? Math.max(0, element.duration - 0.01) : target;
    const bounded = Math.min(target, max);
    if (Math.abs(element.currentTime - bounded) > 0.4) element.currentTime = bounded;
    if (playback?.playing && target < element.duration) {
      void element.play().catch(() => setMediaError('Playback was blocked by the browser. Mute the source and try Play again.'));
    } else { element.pause(); }
  }, [playback?.playing, playback?.speed, target, beforeStart, hasMedia, ready]);

  useEffect(() => { setMediaError(null); setReady(false); setMediaDuration(null); }, [asset.asset_id, asset.asset_sha256]);
  const modality = (kind: 'chat' | 'speech' | 'facecam') => windows.flatMap(item => item.modalities).find(item => item.modality === kind && item.available) ?? window?.modalities.find(item => item.modality === kind);
  const supportedCount = claims.filter(item => item.sentiment != null && (item.target ?? 'game') === 'game').length;

  return <article className="source-card">
    <div className="source-heading"><span className="source-number">{String(index + 1).padStart(2, '0')}</span><div><h3>{asset.label}</h3><span className="mono tiny muted">{asset.stream_id}</span></div><Badge tone={hasMedia ? generatedMedia ? 'amber' : 'green' : 'muted'} dot>{hasMedia ? generatedMedia ? 'Generated test' : 'Local recording' : status?.state === 'error' ? 'Source error' : window ? 'Fixture' : 'Missing'}</Badge></div>
    <div className="video-stage">
      {hasMedia ? <>
        <video ref={video} src={`/api/recordings/${encodeURIComponent(asset.asset_id)}/media?run_id=${encodeURIComponent(runId)}`} muted={muted} playsInline preload="metadata" onLoadedMetadata={() => { setReady(true); setMediaDuration(video.current?.duration ?? null); }} onError={() => setMediaError('This recording could not be played. Check its file path and browser-compatible video format.')} aria-label={`${asset.label} synchronized recording`} />
        {beforeStart && <div className="video-overlay"><Icon name="video" size={24} /><span>Starts at replay {duration(asset.timeline_start_seconds ?? 0)}</span></div>}
        <button type="button" className="audio-toggle" onClick={() => setMuted(value => !value)}>{muted ? 'Enable audio' : 'Mute audio'}</button>
      </> : <div className="missing-video"><div className="empty-video-icon"><Icon name="video" size={28} /></div><strong>{window ? 'Cached fixture evidence' : 'Recording not supplied'}</strong><p>{asset.availability_reason ?? status?.reason ?? 'Add a local recording to the manifest.'}</p></div>}
      <div className="video-corner"><span className="live-dot" />{hasMedia && generatedMedia ? 'GENERATED TEST · PROXY DEMO' : 'GTA V · PROXY DEMO'}</div>
      {mediaError && <div className="media-error" role="alert">{mediaError}</div>}
    </div>
    <div className="source-body">
      <div className="source-meta"><span>MEDIA <b className="mono">{!hasMedia ? 'Missing' : beforeStart ? 'Pending' : duration(Math.max(0, Math.min(target, mediaDuration ?? target)))}</b></span><span>TRIM <b className="mono">{duration(asset.media_start_seconds ?? 0)}</b></span><span>OFFSET <b className="mono">{signed(asset.timeline_start_seconds ?? 0, 1)}s</b></span></div>
      <div className="quote-preview">{window ? <><span className="eyebrow">Latest extracted evidence</span><p>“{window.raw_text}”</p><span className="tiny muted">{window.provider.replaceAll('_', ' ')} · replay {duration(window.replay_seconds)}</span></> : <><span className="eyebrow">Waiting for evidence</span><p className="muted">No observation is available at this replay time.</p></>}</div>
      <div className="source-scores"><div><span>{aggregate ? 'Aggregate sentiment' : 'Absolute sentiment'}</span><strong className={!feature ? 'unavailable' : feature.absolute_sentiment < 0 ? 'negative' : ''}>{feature ? signed(feature.absolute_sentiment) : supportedCount === 0 ? 'No attributable quality opinion' : 'Quality feature unavailable'}</strong><small>{feature ? `${feature.aspect ?? 'narrative'} · ${aggregate ? `${feature.stream_ids?.length} sources` : '−1 to +1'}` : 'No attributable opinion'}</small></div><div><span>{aggregate ? 'Aggregate surprise' : 'Rolling surprise'}</span><strong className={feature?.mean_z == null ? 'unavailable' : feature.mean_z < 0 ? 'negative' : ''}>{feature?.mean_z == null ? 'Qualifying baseline not established' : signed(feature.mean_z)}{feature?.mean_z != null && <em> z</em>}</strong><small title={feature?.z_reason ?? undefined}>{feature ? feature.mean_z == null ? feature.z_reason ?? 'Warming up' : feature.baseline_status?.replaceAll('_', ' ') : 'No baseline observation'}</small></div></div>
      <div className="modality-row">{(['chat', 'speech', 'facecam'] as const).map(kind => <span key={kind} className={modality(kind)?.available ? 'available' : ''} title={modality(kind)?.reason ?? 'No observation available'}><i />{kind === 'speech' ? 'Audio speech' : kind === 'chat' ? 'Chat' : 'Facecam'} {modality(kind)?.available ? 'available' : 'unavailable'}</span>)}</div>
      <div className="source-footer"><span>{supportedCount} supported · {claims.length - supportedCount} excluded / abstained</span><span>Sample / {asset.sample_interval_seconds ?? 2}s</span></div>
      <ReactionTelemetry reactions={reactions} position={playback?.position_seconds ?? 0} end={playback?.duration_seconds ?? 0} recentSeconds={reactionRecentSeconds} />
    </div>
  </article>;
}

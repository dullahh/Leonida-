import { useState } from 'react';
import type { SourceWindow } from '../generated/contracts';

export function EvidenceArtifacts({ window }: { window: SourceWindow }) {
  const [frameFailed, setFrameFailed] = useState(false);
  const [audioFailed, setAudioFailed] = useState(false);
  const artifact = (ref: string) => `/api/evidence/artifact?ref=${encodeURIComponent(ref)}&run_id=${encodeURIComponent(window.run_id)}`;
  return <div className="evidence-artifacts">
    {window.frame_ref ? frameFailed ? <p>Cached sample frame is unavailable.</p> : <a href={artifact(window.frame_ref)} target="_blank" rel="noreferrer" title="Open cached sample frame"><img src={artifact(window.frame_ref)} alt={`Cached sampled frame from ${window.stream_id} at media ${window.source_media_seconds} seconds`} loading="lazy" onError={() => setFrameFailed(true)} /><span>Open sampled frame ↗</span></a> : <p>{window.frame_reason ?? 'No video frame is associated with this observation.'}</p>}
    {window.audio_ref && <div><span>Extracted audio · source artifact</span>{audioFailed ? <p>Cached audio is unavailable or unsupported by this browser.</p> : <audio controls preload="none" src={artifact(window.audio_ref)} onError={() => setAudioFailed(true)} aria-label={`Extracted audio from ${window.stream_id}`} />}<a href={artifact(window.audio_ref)} target="_blank" rel="noreferrer">Open audio file ↗</a></div>}
  </div>;
}

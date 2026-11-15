import { useEffect, useRef, useState } from 'react';
import { Badge } from './Primitives';

export type LiveAudioChunk = {
  channel: string;
  chunkId: string;
  chunkIndex: number;
  startedAt: string;
  durationMs: number;
  mediaType: string;
};

export type LiveAudioResult = {
  status?: string;
  transcript?: string;
  reason?: string;
  provenance?: string;
};

export type TwitchLiveCaptureProps = {
  onAudioChunk: (audio: Blob, metadata: LiveAudioChunk) => Promise<LiveAudioResult>;
};

const CHUNK_MS = 15_000;
const MAX_CHUNK_BYTES = 2 * 1024 * 1024;
const recorderTypes = ['audio/webm;codecs=opus', 'audio/webm'];

function formatTime(milliseconds: number) {
  const seconds = Math.floor(milliseconds / 1000);
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
}

/** Twitch's player is only an embed. Audio is captured separately after an explicit browser permission. */
export function TwitchLiveCapture({ onAudioChunk }: TwitchLiveCaptureProps) {
  const [channel, setChannel] = useState('');
  const [submittedChannel, setSubmittedChannel] = useState('');
  const [capturing, setCapturing] = useState(false);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [chunkCount, setChunkCount] = useState(0);
  const [droppedChunks, setDroppedChunks] = useState(0);
  const [status, setStatus] = useState('No live audio captured.');
  const [transcripts, setTranscripts] = useState<string[]>([]);
  const [provenance, setProvenance] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const startedAtRef = useRef(0);
  const segmentStartedAtRef = useRef(0);
  const chunkIndexRef = useRef(0);
  const uploadPendingRef = useRef(false);
  const callbackRef = useRef(onAudioChunk);
  const captureActiveRef = useRef(false);
  const streamIdRef = useRef<MediaStream | null>(null);

  useEffect(() => { callbackRef.current = onAudioChunk; }, [onAudioChunk]);
  useEffect(() => {
    if (!capturing) return;
    const timer = window.setInterval(() => setElapsedMs(Date.now() - startedAtRef.current), 250);
    return () => window.clearInterval(timer);
  }, [capturing]);
  useEffect(() => () => stopCapture(false), []);

  function stopCapture(showStatus = true) {
    const recorder = recorderRef.current;
    recorderRef.current = null;
    if (recorder && recorder.state !== 'inactive') recorder.stop();
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
    streamIdRef.current = null;
    captureActiveRef.current = false;
    setCapturing(false);
    if (showStatus) setStatus('Capture stopped.');
  }

  async function startCapture() {
    setError(null);
    setTranscripts([]);
    setProvenance(null);
    setChunkCount(0);
    setDroppedChunks(0);
    setElapsedMs(0);
    chunkIndexRef.current = 0;
    if (!submittedChannel) { setError('Enter and load a Twitch channel before capturing audio.'); return; }
    if (!navigator.mediaDevices?.getDisplayMedia || typeof MediaRecorder === 'undefined') {
      setError('This browser does not support tab audio capture with MediaRecorder. Try a current desktop Chrome or Edge browser.');
      return;
    }
    if (!recorderTypes.some(type => MediaRecorder.isTypeSupported(type))) {
      setError('This browser does not support the required WebM/Opus audio recording format.');
      return;
    }
    try {
      // The browser prompt is user-initiated and prefers this Leonida tab. Browser UI
      // still requires confirmation and may let the user choose another surface.
      // Video is immediately discarded; only the selected surface's audio is used.
      const displayOptions = {
        video: { displaySurface: 'browser' },
        audio: true,
        preferCurrentTab: true,
        selfBrowserSurface: 'include',
        systemAudio: 'exclude',
      } as unknown as DisplayMediaStreamOptions;
      const display = await navigator.mediaDevices.getDisplayMedia(displayOptions);
      const audioTracks = display.getAudioTracks();
      display.getVideoTracks().forEach(track => track.stop());
      if (!audioTracks.length) {
        display.getTracks().forEach(track => track.stop());
        setError('No tab audio track was provided. In the browser prompt, choose “This Tab” or the current Leonida tab and enable “Share tab audio”; the embedded Twitch player audio is the source.');
        return;
      }
      const audioOnly = new MediaStream(audioTracks);
      streamRef.current = audioOnly;
      streamIdRef.current = audioOnly;
      startedAtRef.current = Date.now();
      captureActiveRef.current = true;
      setCapturing(true);
      setStatus('Capturing shared-tab audio locally; video is not recorded or uploaded.');
      audioTracks[0].addEventListener('ended', () => stopCapture());
      const mimeType = recorderTypes.find(type => MediaRecorder.isTypeSupported(type))!;
      const recordSegment = () => {
        const activeStream = streamIdRef.current;
        if (!captureActiveRef.current || !activeStream || activeStream.getAudioTracks().every(track => track.readyState === 'ended')) return;
        const recorder = new MediaRecorder(activeStream, { mimeType, audioBitsPerSecond: 64_000 });
        recorderRef.current = recorder;
        segmentStartedAtRef.current = Date.now();
        recorder.ondataavailable = async event => {
          if (!event.data.size) return;
          const index = chunkIndexRef.current++;
          if (event.data.size > MAX_CHUNK_BYTES) {
            setDroppedChunks(count => count + 1);
            setStatus(`Chunk ${index + 1} exceeded the 2 MiB upload limit and was discarded.`);
            return;
          }
          if (uploadPendingRef.current) {
            setDroppedChunks(count => count + 1);
            setStatus(`Chunk ${index + 1} skipped because the previous audio upload is still processing.`);
            return;
          }
          uploadPendingRef.current = true;
          const startedAt = new Date(segmentStartedAtRef.current).toISOString();
          const metadata: LiveAudioChunk = {
            channel: submittedChannel,
            chunkId: `${submittedChannel}-${crypto.randomUUID()}`,
            chunkIndex: index,
            startedAt,
            durationMs: Date.now() - segmentStartedAtRef.current,
            mediaType: event.data.type || mimeType,
          };
          try {
            const result = await callbackRef.current(event.data, metadata);
            setChunkCount(count => count + 1);
            if (result.transcript) setTranscripts(current => [...current.slice(-4), result.transcript!]);
            if (result.provenance) setProvenance(result.provenance);
            const outcome = result.status ?? (result.transcript ? 'Audio chunk processed.' : `Chunk ${index + 1}: transcript unavailable`);
            setStatus(result.reason ? `${outcome} · ${result.reason}` : outcome);
          } catch (failure) {
            setStatus(`Audio chunk ${index + 1} failed: ${failure instanceof Error ? failure.message : String(failure)}`);
          } finally {
            uploadPendingRef.current = false;
          }
        };
        recorder.onerror = () => setError('The browser could not record this tab audio stream.');
        recorder.onstop = () => {
          if (recorderRef.current === recorder) recorderRef.current = null;
          recordSegment();
        };
        recorder.start();
        window.setTimeout(() => {
          if (recorder.state === 'recording') recorder.stop();
        }, CHUNK_MS);
      };
      recordSegment();
    } catch (failure) {
      const message = failure instanceof Error ? failure.message : String(failure);
      setError(message.includes('denied') || message.includes('Permission')
        ? 'Tab capture permission was denied. Start again and confirm sharing “This Tab” / the current Leonida tab with tab audio enabled.'
        : `Could not start tab audio capture: ${message}`);
      stopCapture(false);
    }
  }

  function loadChannel(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const clean = channel.trim().replace(/^@/, '').toLowerCase();
    if (!/^[a-z0-9_]{1,25}$/.test(clean)) { setError('Enter a Twitch channel name using letters, numbers or underscores.'); return; }
    if (capturing) stopCapture();
    setError(null);
    setSubmittedChannel(clean);
    setStatus('Player loaded. Start playback, then explicitly start tab audio capture when ready.');
  }

  const parent = window.location.hostname || 'localhost';
  const embedUrl = submittedChannel
    ? `https://player.twitch.tv/?channel=${encodeURIComponent(submittedChannel)}&parent=${encodeURIComponent(parent)}&muted=false&autoplay=false`
    : null;

  return <section className="panel twitch-live-panel" aria-label="Twitch live audio demo">
    <header className="twitch-live-heading"><div><span className="section-index">LIVE</span><h2>Live stream demo</h2><Badge tone={capturing ? 'green' : 'amber'} dot>{capturing ? 'Audio capture active' : 'Browser-authorized'}</Badge></div><span className="tiny muted">Twitch embed · local Whisper pipeline</span></header>
    <div className="twitch-live-layout">
      <div className="twitch-player-column">
        <form className="twitch-channel-form" onSubmit={loadChannel}>
          <label htmlFor="twitch-channel">Twitch channel</label>
          <input id="twitch-channel" value={channel} onChange={event => setChannel(event.target.value)} placeholder="channel_name" autoComplete="off" />
          <button className="button secondary-button" type="submit">Load player</button>
        </form>
        {embedUrl ? <div className="twitch-player-scroll" role="region" aria-label="Twitch player; horizontally scroll when the viewport is narrower than 400 pixels" tabIndex={0}><iframe className="twitch-player" src={embedUrl} title={`Twitch live stream ${submittedChannel}`} allow="autoplay; fullscreen" allowFullScreen /></div>
          : <div className="twitch-player-placeholder">Load a channel to embed its official Twitch player.</div>}
        <p className="twitch-help">Twitch requires a player area at least 400 × 300 pixels; on narrow screens, scroll the player area horizontally. Play the stream first, then confirm “This Tab” / the current Leonida tab in the browser prompt and enable tab audio. The embedded player’s audio is captured. The browser still requires confirmation and cannot be forced to select this tab.</p>
      </div>
      <div className="twitch-capture-column">
        <div className="twitch-capture-controls"><div><span className="eyebrow">AUDIO PIPELINE</span><strong>{formatTime(elapsedMs)} captured</strong></div>
          {capturing ? <button className="button" type="button" onClick={() => stopCapture()}>Stop capture</button>
            : <button className="button" type="button" onClick={() => void startCapture()} disabled={!submittedChannel}>Start tab audio capture</button>}
        </div>
        <p className="twitch-status" role="status">{status}</p>
        {error && <p className="twitch-error" role="alert">{error}</p>}
        <dl className="twitch-capture-stats"><div><dt>Audio chunks processed</dt><dd>{chunkCount}</dd></div><div><dt>Skipped while busy</dt><dd>{droppedChunks}</dd></div><div><dt>Chunk window</dt><dd>15 sec max</dd></div><div><dt>Captured media</dt><dd>Audio only</dd></div></dl>
        <div className="twitch-transcript" aria-live="polite"><span className="eyebrow">TRANSCRIPTION RESULTS</span>
          {provenance && <p className="twitch-provenance">{provenance}</p>}
          {transcripts.length ? transcripts.map((line, index) => <p key={`${index}-${line}`}>{line}</p>) : <p className="muted">No transcript available yet. The panel shows text only when the processing callback returns it.</p>}
        </div>
        <p className="twitch-footnote">Twitch playback is cross-origin. This panel does not extract its video or bypass Twitch access controls. Only browser-shared audio is sent to the configured callback; no market estimate is implied.</p>
      </div>
    </div>
  </section>;
}

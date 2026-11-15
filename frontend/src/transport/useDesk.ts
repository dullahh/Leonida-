import { useCallback, useEffect, useRef, useState } from 'react';
import type { StreamEnvelope } from '../generated/contracts';
import type { RunCommand } from '../generated/commands';
import type { CreateRunRequest } from '../generated/create-run';
import type { ScenarioRequest } from '../generated/scenario-request';
import frozenExample from '../../../contracts/generated/dashboard-envelope.example.json';

export type Connection = 'connecting' | 'streaming' | 'polling' | 'offline' | 'mock';
export type ControlAction = RunCommand['action'];
export type LoadScenario = 'recordings' | ScenarioRequest['scenario'];

/** HTTP and WebSocket share this decoder and the same run/sequence gate. */
export function decodeEnvelope(value: unknown): StreamEnvelope {
  if (!value || typeof value !== 'object') throw new Error('The server returned an invalid snapshot.');
  const frame = value as StreamEnvelope;
  if (frame.schema_version !== '2' || frame.type !== 'snapshot'
      || typeof frame.run_id !== 'string' || !Number.isSafeInteger(frame.sequence) || frame.sequence < 1
      || !frame.payload || frame.payload.run_id !== frame.run_id
      || !Array.isArray(frame.payload.windows) || !Array.isArray(frame.payload.claims)
      || !Array.isArray(frame.payload.features) || !Array.isArray(frame.payload.markets)
      || !Array.isArray(frame.payload.quotes) || !Array.isArray(frame.payload.decisions)
      || !Array.isArray(frame.payload.receipts) || !Array.isArray(frame.payload.streams)
      || !Array.isArray(frame.payload.recording_manifest?.recordings)
      || !Array.isArray(frame.payload.venue_context?.quotes)) {
    throw new Error('The snapshot does not match this terminal. Regenerate contracts and rebuild the frontend.');
  }
  const execution = frame.payload.execution;
  if (frame.payload.reactions !== undefined && !Array.isArray(frame.payload.reactions)) {
    throw new Error('Reaction telemetry must be an array of source-linked records.');
  }
  if (execution !== undefined) {
    const arrayFields = ['orders', 'fills', 'positions', 'marks', 'traces', 'latest_reasons'] as const;
    if (!execution || typeof execution !== 'object' || Array.isArray(execution)
        || arrayFields.some(field => execution[field] !== undefined && !Array.isArray(execution[field]))) {
      throw new Error('The execution snapshot does not match the generated contract. No malformed ledger data was accepted.');
    }
  }
  return frame;
}

const errorText = (error: unknown) => error instanceof Error ? error.message : String(error);
const mockMode = new URLSearchParams(window.location.search).get('mock') === '1';

export function useDesk() {
  const [frame, setFrame] = useState<StreamEnvelope | null>(null);
  const [connection, setConnection] = useState<Connection>(mockMode ? 'mock' : 'connecting');
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [receivedAt, setReceivedAt] = useState<number | null>(null);
  const activeRun = useRef<string | null>(null);
  const sequence = useRef(0);
  const socket = useRef<WebSocket | null>(null);
  const alive = useRef(false);
  const generation = useRef(0);
  const resyncing = useRef(false);
  const mutationBusy = useRef(false);
  const connectRef = useRef<() => void>(() => {});
  const refreshRef = useRef<() => Promise<void>>(async () => {});

  const accept = useCallback((next: StreamEnvelope) => {
    if (!alive.current) return;
    if (activeRun.current && next.run_id !== activeRun.current) return;
    if (activeRun.current && next.sequence <= sequence.current) return;
    const gap = sequence.current > 0 && next.sequence > sequence.current + 1;
    activeRun.current = next.run_id;
    sequence.current = next.sequence;
    setFrame(next);
    setReceivedAt(Date.now());
    setError(null);
    if (gap && !resyncing.current) {
      resyncing.current = true;
      void refreshRef.current().finally(() => { resyncing.current = false; });
    }
  }, []);

  const refresh = useCallback(async () => {
    if (mockMode) return;
    const epoch = generation.current;
    const requestedRun = activeRun.current;
    try {
      const suffix = requestedRun ? `?run_id=${encodeURIComponent(requestedRun)}` : '';
      const response = await fetch(`/api/state${suffix}`, { cache: 'no-store', signal: AbortSignal.timeout(8000) });
      if (!response.ok) throw new Error(`State request failed (${response.status}). Check the backend terminal.`);
      const next = decodeEnvelope(await response.json());
      if (!alive.current || generation.current !== epoch || activeRun.current !== requestedRun) return;
      accept(next);
      setReceivedAt(Date.now());
      setError(null);
      if (socket.current?.readyState !== WebSocket.OPEN) setConnection('polling');
    } catch (failure) {
      if (!alive.current || generation.current !== epoch) return;
      setError(errorText(failure));
      if (socket.current?.readyState !== WebSocket.OPEN) setConnection('offline');
    }
  }, [accept]);
  refreshRef.current = refresh;

  useEffect(() => {
    alive.current = true;
    if (mockMode) {
      accept(decodeEnvelope(frozenExample));
      setConnection('mock');
      return () => { alive.current = false; };
    }
    let retry: ReturnType<typeof setTimeout> | undefined;
    const connect = () => {
      if (!alive.current || !activeRun.current) return;
      if (socket.current?.readyState === WebSocket.OPEN || socket.current?.readyState === WebSocket.CONNECTING) return;
      const epoch = generation.current;
      const ws = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws?run_id=${encodeURIComponent(activeRun.current)}`);
      socket.current = ws;
      ws.onopen = () => { if (alive.current && generation.current === epoch) setConnection('streaming'); };
      ws.onmessage = (event) => {
        if (!alive.current || generation.current !== epoch || socket.current !== ws) return;
        try {
          accept(decodeEnvelope(JSON.parse(event.data)));
          setReceivedAt(Date.now());
          setError(null);
        } catch (failure) { setError(errorText(failure)); }
      };
      ws.onerror = () => ws.close();
      ws.onclose = () => {
        if (!alive.current || socket.current !== ws) return;
        socket.current = null;
        setConnection('polling');
        void refreshRef.current();
        retry = setTimeout(connect, 1500);
      };
    };
    connectRef.current = connect;
    void refresh().then(connect);
    const polling = setInterval(() => {
      if (socket.current?.readyState !== WebSocket.OPEN) void refresh().then(connect);
    }, 3000);
    return () => {
      alive.current = false;
      generation.current += 1;
      clearInterval(polling);
      clearTimeout(retry);
      socket.current?.close();
      socket.current = null;
    };
  }, [accept, refresh]);

  const mutate = useCallback(async (path: string, body: RunCommand | CreateRunRequest | ScenarioRequest, notice: string | null) => {
    if (mockMode || !activeRun.current || mutationBusy.current) return;
    mutationBusy.current = true;
    setBusy(true);
    setNotice(null);
    const run = activeRun.current;
    try {
      const response = await fetch(path, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(15000),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(typeof detail?.detail === 'string' ? detail.detail : `Run command failed (${response.status}).`);
      }
      const result: unknown = await response.json();
      if (!result || typeof result !== 'object' || !('run_id' in result) || typeof result.run_id !== 'string') {
        throw new Error('The server returned an invalid command result.');
      }
      if (result.run_id !== run) {
        generation.current += 1;
        activeRun.current = result.run_id;
        sequence.current = 0;
        setFrame(null);
        socket.current?.close();
        socket.current = null;
      }
      await refreshRef.current();
      connectRef.current();
      setNotice(notice);
    } catch (failure) { setError(errorText(failure)); }
    finally { mutationBusy.current = false; if (alive.current) setBusy(false); }
  }, []);

  const control = useCallback(async (action: ControlAction, options: Pick<RunCommand, 'position_seconds' | 'speed'> = {}) => {
    if (!activeRun.current) return;
    const notice = action === 'reset' ? 'New run created. Previous evidence remains in its audit history.'
      : action === 'replay_observation' ? 'Cached observation replayed. Duplicate evidence is not counted again.'
      : action === 'exit' ? 'Paper exit requested. Play or seek forward to resolve the simulated latency.' : null;
    await mutate(`/api/runs/${encodeURIComponent(activeRun.current)}/control`, { command_id: crypto.randomUUID(), action, ...options } satisfies RunCommand, notice);
  }, [mutate]);

  const loadScenario = useCallback(async (scenario: LoadScenario) => {
    if (!activeRun.current) return;
    const command_id = crypto.randomUUID();
    if (scenario === 'recordings') {
      await mutate('/api/runs', { command_id, scenario } satisfies CreateRunRequest, 'Recordings loaded in a separate run. Synthetic scenario accounting remains in its original run.');
    } else {
      await mutate(`/api/runs/${encodeURIComponent(activeRun.current)}/inject`, { command_id, scenario } satisfies ScenarioRequest, 'Synthetic scenario loaded in a new isolated run. Recorded observations were not mixed into this scenario.');
    }
  }, [mutate]);

  return { frame, connection, error, notice, busy, receivedAt, mockMode, refresh, control, loadScenario };
}

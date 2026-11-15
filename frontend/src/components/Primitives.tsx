import type { ReactNode } from 'react';

export function Icon({ name, size = 18 }: { name: 'play' | 'pause' | 'reset' | 'arrow' | 'document' | 'video' | 'close' | 'signal' | 'folder'; size?: number }) {
  const paths: Record<typeof name, ReactNode> = {
    play: <path d="m8 5 11 7-11 7Z" />,
    pause: <><path d="M8 5v14M16 5v14" /></>,
    reset: <><path d="M4 10a8 8 0 1 1 1 7M4 4v6h6" /></>,
    arrow: <><path d="M5 12h14m-5-5 5 5-5 5" /></>,
    document: <><path d="M14 3H5v18h14V8Zm0 0v5h5M8 12h8M8 16h6" /></>,
    video: <><rect x="3" y="5" width="13" height="14" rx="2" /><path d="m16 10 5-3v10l-5-3" /></>,
    close: <path d="m6 6 12 12M6 18 18 6" />,
    signal: <><path d="M4 18v2M9 13v7M14 8v12M19 3v17" /></>,
    folder: <path d="M3 6h7l2 3h9v11H3Zm0 3V5h7l2 2h8v2" />,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

export function Badge({ children, tone = 'muted', dot = false }: { children: ReactNode; tone?: 'muted' | 'green' | 'amber' | 'blue' | 'red'; dot?: boolean }) {
  return <span className={`badge ${tone}`}>{dot && <i />}{children}</span>;
}

export const percent = (value: number | null | undefined, digits = 1) => value == null || !Number.isFinite(value) ? 'Unavailable' : `${(value * 100).toFixed(digits)}%`;
export const signed = (value: number | null | undefined, digits = 2) => value == null || !Number.isFinite(value) ? 'Unavailable' : `${value > 0 ? '+' : ''}${value.toFixed(digits)}`;
export const cents = (value: string | null | undefined) => value == null ? 'Unavailable' : `${(Number(value) * 100).toLocaleString('en-US', { maximumFractionDigits: 2 })}¢`;
export const dollars = (value: string | null | undefined, digits = 2) => value == null ? 'Unavailable' : Number(value).toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: digits, maximumFractionDigits: digits });
export const duration = (seconds: number) => {
  const safe = Math.max(0, Math.floor(seconds));
  return `${Math.floor(safe / 60).toString().padStart(2, '0')}:${(safe % 60).toString().padStart(2, '0')}`;
};
export function age(timestamp: string | null | undefined, now: number) {
  if (!timestamp) return 'Time unavailable';
  const seconds = Math.max(0, (now - Date.parse(timestamp)) / 1000);
  if (!Number.isFinite(seconds)) return 'Time unavailable';
  if (seconds < 60) return `${Math.floor(seconds)}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

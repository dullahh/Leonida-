import { useEffect, useState } from 'react';
import type { ScenarioRequest } from '../generated/scenario-request';
import type { LoadScenario } from '../transport/useDesk';
import { Badge, Icon } from './Primitives';

const scenarios: { value: ScenarioRequest['scenario']; label: string; purpose: string }[] = [
  { value: 'courtroom-praise', label: 'Courtroom praise', purpose: 'Narrative praise with different evidence arrival times.' },
  { value: 'technical-failure-laughter', label: 'Technical failure & laughter', purpose: 'Technical criticism, ambiguous laughter and rebroadcast deduplication.' },
  { value: 'skill-rage-controls', label: 'Skill rage & control critique', purpose: 'Player-skill attribution separated from game-control criticism.' },
  { value: 'mixed-missing-facecam', label: 'Mixed views & missing facecam', purpose: 'Speech/chat disagreement with explicit missing facecam.' },
  { value: 'duplicate-reconnect', label: 'Duplicate / reconnect storm', purpose: 'Duplicate evidence preserves the unique evidence ledger.' },
  { value: 'venue-outage-reset', label: 'Venue outage / reset', purpose: 'Synthetic quote expiry, blocked execution and fresh-run reset.' },
];

export function ScenarioChooser({ activeScenario, disabled, onLoad }: { activeScenario?: string; disabled: boolean; onLoad: (scenario: LoadScenario) => void }) {
  const [selected, setSelected] = useState<ScenarioRequest['scenario']>('courtroom-praise');
  useEffect(() => { const match = scenarios.find(item => item.value === activeScenario); if (match) setSelected(match.value); }, [activeScenario]);
  const currentLabel = scenarios.find(item => item.value === activeScenario)?.label ?? (activeScenario === 'recordings' ? 'Local recordings' : activeScenario === 'foundation' ? 'Foundation fixture' : activeScenario ?? 'Loaded run');
  return <section className="scenario-chooser" aria-label="Isolated demo scenarios"><div className="scenario-current"><span className="eyebrow">LOADED RUN</span><strong>{currentLabel}</strong><Badge tone={activeScenario === 'recordings' ? 'green' : 'amber'}>{activeScenario === 'recordings' ? 'Recorded proxy evidence' : 'Synthetic demo'}</Badge></div><div className="scenario-selection"><label htmlFor="scenario-selector">Six synthetic replay scenarios</label><div><select id="scenario-selector" value={selected} onChange={event => setSelected(event.target.value as ScenarioRequest['scenario'])} disabled={disabled}>{scenarios.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select><button type="button" className="button secondary-button" onClick={() => onLoad(selected)} disabled={disabled}>Load isolated scenario<Icon name="arrow" size={14} /></button></div><p>{scenarios.find(item => item.value === selected)?.purpose} Each load creates a new run.</p></div><button type="button" className="text-button recording-return" disabled={disabled || activeScenario === 'recordings'} onClick={() => onLoad('recordings')}><Icon name="video" size={16} />Return to recordings</button></section>;
}

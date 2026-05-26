import { useState } from 'react';
import GlobalTopology from '../components/widgets/GlobalTopology';
import { useAppContext } from '../context/AppContext';
import { RefreshCw } from 'lucide-react';

const SELECT_STYLE = {
  background: 'rgba(255,255,255,0.05)',
  color: 'var(--text-primary)',
  border: '1px solid var(--border-glass)',
  padding: '0.5rem',
  borderRadius: '4px',
};

// Maps dropdown label → node type values stored in topology data
const COMPONENT_TYPE_MAP = {
  'Contact Flows': ['CONTACT_FLOW'],
  'Lex Bots':      ['LEX_BOT'],
  'Queues':        ['QUEUE'],
  'Lambdas':       ['LAMBDA'],
};

const Topology = () => {
  const { mode, activeInstance } = useAppContext();
  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState('');
  const [filterRegion, setFilterRegion] = useState('');
  const [filterType, setFilterType] = useState('');

  const runDiscovery = async () => {
    setScanning(true);
    setScanMsg('');
    try {
      const res = await fetch(`/api/topology/scan?mode=${mode}`, { method: 'POST' });
      const data = await res.json();
      setScanMsg(data.message || 'Scan queued.');
    } catch {
      setScanMsg('Failed to trigger scan.');
    } finally {
      setScanning(false);
      setTimeout(() => setScanMsg(''), 6000);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Connect Topology View</h2>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {scanMsg && (
            <span style={{ fontSize: '0.8rem', color: 'var(--status-ok)', padding: '0 0.5rem' }}>{scanMsg}</span>
          )}
          <select
            style={SELECT_STYLE}
            value={filterRegion}
            onChange={e => setFilterRegion(e.target.value)}
          >
            <option value="">All Regions</option>
            <option value="us-east-1">us-east-1</option>
            <option value="us-west-2">us-west-2</option>
            <option value="eu-west-1">eu-west-1</option>
          </select>
          <select
            style={SELECT_STYLE}
            value={filterType}
            onChange={e => setFilterType(e.target.value)}
          >
            <option value="">All Components</option>
            {Object.keys(COMPONENT_TYPE_MAP).map(label => (
              <option key={label} value={label}>{label}</option>
            ))}
          </select>
          <button
            onClick={runDiscovery}
            disabled={scanning}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              background: 'var(--accent-cyan)', color: 'black',
              border: 'none', borderRadius: '4px', padding: '0.5rem 0.9rem',
              fontWeight: 600, fontSize: '0.85rem', cursor: scanning ? 'not-allowed' : 'pointer',
              opacity: scanning ? 0.7 : 1,
            }}
          >
            <RefreshCw size={14} style={{ animation: scanning ? 'spin 1s linear infinite' : 'none' }} />
            {scanning ? 'Scanning…' : 'Run Discovery'}
          </button>
        </div>
      </div>

      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <GlobalTopology
          mode={mode}
          instanceId={activeInstance?.instanceId || ''}
          filterRegion={filterRegion}
          filterTypes={filterType ? COMPONENT_TYPE_MAP[filterType] : null}
        />
      </div>
    </div>
  );
};

export default Topology;

import { useState, useEffect } from 'react';
import { Clock, Eye, Activity } from 'lucide-react';

const Incidents = () => {
  const [incidents, setIncidents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/incidents')
      .then(res => res.json())
      .then(data => {
        setIncidents(data);
        if (data.length > 0) setSelected(data[0]);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch incidents", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div style={{ padding: '2rem' }}>Loading incidents from DynamoDB...</div>;
  if (incidents.length === 0) return <div style={{ padding: '2rem', color: 'var(--status-ok)' }}>No active incidents found!</div>;

  return (
    <div style={{ display: 'flex', gap: '1.5rem', height: '100%', padding: '1rem' }}>
      {/* List Panel */}
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ marginBottom: '1.5rem', fontSize: '1.2rem', fontWeight: 600 }}>Active Incidents</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto' }}>
          {incidents.map(inc => (
            <div 
              key={inc.incidentId} 
              onClick={() => setSelected(inc)}
              style={{ 
                padding: '1rem', 
                borderRadius: '8px', 
                background: selected?.incidentId === inc.incidentId ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${selected?.incidentId === inc.incidentId ? 'var(--accent-cyan)' : 'var(--border-glass)'}`,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ 
                  color: inc.severity === 'SEV1' ? 'var(--status-critical)' : inc.severity === 'SEV2' ? 'var(--status-warn)' : 'var(--accent-blue)',
                  fontWeight: 700,
                  fontSize: '0.8rem'
                }}>{inc.severity} | {inc.incidentId}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{inc.createdAt}</span>
              </div>
              <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>{inc.description}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <span>{inc.source}</span>
                <span style={{ color: 'inherit' }}>{inc.status || "Investigating"}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detail Panel */}
      {selected && (
        <div className="glass-panel" style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
            <div>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 600, marginBottom: '0.5rem' }}>{selected.description}</h2>
              <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                <span>ID: {selected.incidentId}</span>
                <span>Source: {selected.source}</span>
                <span style={{ color: 'var(--status-critical)' }}>Severity: {selected.severity}</span>
              </div>
            </div>
            <button style={{ padding: '0.5rem 1rem', background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
              Trigger ADK Analysis
            </button>
          </div>

          <div style={{ display: 'flex', gap: '1.5rem', flex: 1, minHeight: 0 }}>
            {/* Timeline & Context */}
            <div style={{ flex: 1, overflowY: 'auto', paddingRight: '1rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--accent-cyan)' }}>Raw Metadata</h3>
              <pre style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px' }}>
                {JSON.stringify(selected.metadata || {}, null, 2)}
              </pre>

              <h3 style={{ fontSize: '1rem', marginTop: '1.5rem', marginBottom: '1rem', color: 'var(--accent-cyan)' }}>Automated SRE Analysis</h3>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
                  <Activity size={16} /> <strong>Agent Swarm</strong>: Investigating...
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)' }}>
                  <Clock size={16} /> <strong>Detected At</strong>: {selected.createdAt}
                </div>
              </div>
            </div>

            {/* Action Recommendation */}
            <div style={{ flex: 1, borderLeft: '1px solid var(--border-glass)', paddingLeft: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--status-ok)' }}>Pending Approvals</h3>
              <div style={{ background: 'rgba(0, 255, 128, 0.05)', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(0, 255, 128, 0.2)' }}>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  The Agent Swarm is currently evaluating the root cause. If a safe remediation path is found, it will generate a ticket here for human approval.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Incidents;

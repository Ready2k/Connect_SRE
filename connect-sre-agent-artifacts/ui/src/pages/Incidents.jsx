import { useState } from 'react';
import { Clock, Eye, Activity } from 'lucide-react';

const incidentData = [
  { id: 'INC-2023-01', severity: 'SEV1', component: 'us-west-2/ccp', title: 'High latency in CCP endpoints', time: '10 mins ago', status: 'Investigating' },
  { id: 'INC-2023-02', severity: 'SEV2', component: 'eu-west-1/lex', title: 'Lex fallback rate spike', time: '45 mins ago', status: 'Awaiting Approval' },
  { id: 'INC-2023-03', severity: 'SEV3', component: 'us-east-1/queue', title: 'Queue wait time SLA breach', time: '2 hours ago', status: 'Resolved' }
];

const Incidents = () => {
  const [selected, setSelected] = useState(incidentData[0]);

  return (
    <div style={{ display: 'flex', gap: '1.5rem', height: '100%', padding: '1rem' }}>
      {/* List Panel */}
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ marginBottom: '1.5rem', fontSize: '1.2rem', fontWeight: 600 }}>Active Incidents</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto' }}>
          {incidentData.map(inc => (
            <div 
              key={inc.id} 
              onClick={() => setSelected(inc)}
              style={{ 
                padding: '1rem', 
                borderRadius: '8px', 
                background: selected.id === inc.id ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${selected.id === inc.id ? 'var(--accent-cyan)' : 'var(--border-glass)'}`,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ 
                  color: inc.severity === 'SEV1' ? 'var(--status-critical)' : inc.severity === 'SEV2' ? 'var(--status-warn)' : 'var(--accent-blue)',
                  fontWeight: 700,
                  fontSize: '0.8rem'
                }}>{inc.severity} | {inc.id}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{inc.time}</span>
              </div>
              <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>{inc.title}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <span>{inc.component}</span>
                <span style={{ 
                  color: inc.status === 'Resolved' ? 'var(--status-ok)' : 'inherit' 
                }}>{inc.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detail Panel */}
      <div className="glass-panel" style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 600, marginBottom: '0.5rem' }}>{selected.title}</h2>
            <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              <span>ID: {selected.id}</span>
              <span>Component: {selected.component}</span>
              <span style={{ color: 'var(--status-critical)' }}>Severity: {selected.severity}</span>
            </div>
          </div>
          <button style={{ padding: '0.5rem 1rem', background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
            Take Action
          </button>
        </div>

        <div style={{ display: 'flex', gap: '1.5rem', flex: 1, minHeight: 0 }}>
          {/* Timeline & Context */}
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '1rem' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--accent-cyan)' }}>Incident Context</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1.5rem' }}>
              Anomaly detected in CCP endpoint latency routing through US-West-2. Latency spiked from 24ms to over 800ms within a 2-minute window. 
              Correlated with a recent deploy of the `ContactFlow_v4` module.
            </p>

            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--accent-cyan)' }}>Automated SRE Analysis</h3>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
                <Activity size={16} /> <strong>Blast Radius</strong>: Estimated 15% of active US customer journeys.
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
                <Eye size={16} /> <strong>Evidence</strong>: CloudWatch logs show Lambda timeout on `FetchCustomerProfile`.
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)' }}>
                <Clock size={16} /> <strong>Timeline</strong>: Issue started at 14:02 UTC.
              </div>
            </div>
          </div>

          {/* Action Recommendation */}
          <div style={{ flex: 1, borderLeft: '1px solid var(--border-glass)', paddingLeft: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--status-ok)' }}>Proposed Remediation</h3>
            <div style={{ background: 'rgba(0, 255, 128, 0.05)', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(0, 255, 128, 0.2)' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--status-ok)' }}>Rollback Flow Version</h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Revert `ContactFlow_v4` to `ContactFlow_v3` for the US-West-2 region. This action is safely reversible and has a 95% confidence score of mitigating the latency spike.
              </p>
              <div style={{ background: '#111', padding: '0.75rem', borderRadius: '4px', fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>
                {`> Discard changes: ContactFlow_v4`}
                <br/>
                {`> Apply: ContactFlow_v3`}
              </div>
              <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
                <button style={{ flex: 1, padding: '0.5rem', background: 'var(--status-ok)', color: '#000', border: 'none', borderRadius: '4px', fontWeight: 600, cursor: 'pointer' }}>
                  Approve Remediation
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Incidents;

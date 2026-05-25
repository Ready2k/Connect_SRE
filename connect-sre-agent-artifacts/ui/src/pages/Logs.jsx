import { FileText } from 'lucide-react';

const logData = [
  { time: '14:32:01 UTC', source: 'EventBridge', type: 'Ingest', details: 'Received CW Metric Alarm: us-west-2 ccp-latency-high', status: 'Success' },
  { time: '14:32:05 UTC', source: 'TopologyAgent', type: 'Query', details: 'Walk topology from ContactFlow_v4 to Queue_Sales', status: 'Success' },
  { time: '14:32:10 UTC', source: 'DiagnosticAgent', type: 'Model Call', details: 'Analyze lambda logs for FetchCustomerProfile', status: 'Success' },
  { time: '14:32:45 UTC', source: 'PolicyEngine', type: 'Evaluate', details: 'Check rollback safety for ContactFlow_v4', status: 'Approved' },
  { time: '14:33:00 UTC', source: 'ManagementUI', type: 'Dispatch', details: 'Render Pending Approval INC-2023-01', status: 'Success' }
];

const Logs = () => {
  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <FileText size={24} color="var(--accent-purple)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>System Audit Logs</h2>
      </div>

      <div className="glass-panel" style={{ flex: 1, overflowY: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-glass)' }}>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Timestamp</th>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Source Component</th>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Action Type</th>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Details</th>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {logData.map((log, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s' }}>
                <td style={{ padding: '1rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{log.time}</td>
                <td style={{ padding: '1rem' }}>{log.source}</td>
                <td style={{ padding: '1rem', color: 'var(--accent-cyan)' }}>{log.type}</td>
                <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>{log.details}</td>
                <td style={{ padding: '1rem' }}>
                  <span style={{ 
                    padding: '0.25rem 0.5rem', 
                    borderRadius: '4px', 
                    fontSize: '0.75rem',
                    background: log.status === 'Success' || log.status === 'Approved' ? 'rgba(0, 255, 128, 0.1)' : 'rgba(255, 255, 255, 0.1)',
                    color: log.status === 'Success' || log.status === 'Approved' ? 'var(--status-ok)' : 'var(--text-primary)'
                  }}>
                    {log.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Logs;

import React from 'react';

const approvals = [
  { action: 'Reset CCP Nodes', trigger: 'us-west-2', requestor: 'Sarah Jenkins', type: 'Approve' },
  { action: 'Increase Lex Capacity', trigger: 'CustomerSupport_v2', requestor: 'Sarah Jenkins', type: 'Approve' },
  { action: 'Scale Queue Nodes', trigger: 'Sales', requestor: 'Sarah Queue', type: 'Reject' },
];

const PendingApprovals = () => {
  return (
    <>
      <h3 className="widget-title">Pending Remediation Approvals</h3>
      <div style={{ flex: 1, overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-glass)' }}>
              <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Action</th>
              <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Trigger</th>
              <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Requested By</th>
              <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600, textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {approvals.map((app, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s' }}>
                <td style={{ padding: '0.75rem 0.5rem' }}>{app.action}</td>
                <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-secondary)' }}>{app.trigger}</td>
                <td style={{ padding: '0.75rem 0.5rem' }}>{app.requestor}</td>
                <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>
                  <button style={{ 
                    background: 'transparent',
                    border: `1px solid ${app.type === 'Approve' ? 'var(--status-ok)' : 'var(--status-critical)'}`,
                    color: app.type === 'Approve' ? 'var(--status-ok)' : 'var(--status-critical)',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    fontWeight: 600
                  }}>
                    {app.type}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default PendingApprovals;

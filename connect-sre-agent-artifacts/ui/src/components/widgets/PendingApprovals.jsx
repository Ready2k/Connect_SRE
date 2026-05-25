import { useState, useEffect } from 'react';

const PendingApprovals = () => {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/approvals')
      .then(res => res.json())
      .then(data => {
        setApprovals(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch approvals", err);
        setLoading(false);
      });
  }, []);

  const handleAction = (approvalId, status) => {
    fetch(`/api/approvals/${approvalId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, justification: "Actioned via UI" })
    }).then(() => {
      // Refresh list
      setApprovals(prev => prev.filter(app => app.approvalId !== approvalId));
    });
  };

  return (
    <>
      <h3 className="widget-title">Pending Remediation Approvals</h3>
      <div style={{ flex: 1, overflowX: 'auto' }}>
        {loading ? (
          <div style={{ padding: '1rem', color: 'var(--text-secondary)' }}>Loading...</div>
        ) : approvals.length === 0 ? (
          <div style={{ padding: '1rem', color: 'var(--status-ok)' }}>No pending approvals.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-glass)' }}>
                <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Action</th>
                <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Incident ID</th>
                <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Created</th>
                <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {approvals.filter(a => a.status === 'PENDING').map((app, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s' }}>
                  <td style={{ padding: '0.75rem 0.5rem' }}>{app.actionType}</td>
                  <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-secondary)' }}>{app.incidentId}</td>
                  <td style={{ padding: '0.75rem 0.5rem' }}>{app.createdAt}</td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right', display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                    <button onClick={() => handleAction(app.approvalId, 'APPROVED')} style={{ 
                      background: 'transparent', border: '1px solid var(--status-ok)', color: 'var(--status-ok)',
                      padding: '0.25rem 0.75rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 600
                    }}>Approve</button>
                    <button onClick={() => handleAction(app.approvalId, 'REJECTED')} style={{ 
                      background: 'transparent', border: '1px solid var(--status-critical)', color: 'var(--status-critical)',
                      padding: '0.25rem 0.75rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 600
                    }}>Reject</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
};

export default PendingApprovals;

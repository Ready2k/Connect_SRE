import { useState, useEffect, useRef } from 'react';
import { useAppContext } from '../../context/AppContext';

const OPERATOR_KEY = 'sre_operator_name';

const PendingApprovals = () => {
  const { mode } = useAppContext();
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [operatorName, setOperatorName] = useState(() => localStorage.getItem(OPERATOR_KEY) || '');
  const [editingName, setEditingName] = useState(false);
  const [draftName, setDraftName] = useState('');
  const nameInputRef = useRef(null);

  useEffect(() => {
    fetch(`/api/approvals?mode=${mode}`)
      .then(res => res.json())
      .then(data => { setApprovals(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [mode]);

  useEffect(() => {
    if (editingName && nameInputRef.current) nameInputRef.current.focus();
  }, [editingName]);

  const commitName = () => {
    const trimmed = draftName.trim();
    if (trimmed) {
      setOperatorName(trimmed);
      localStorage.setItem(OPERATOR_KEY, trimmed);
    }
    setEditingName(false);
  };

  const handleAction = (approvalId, status) => {
    const operator = operatorName.trim() || 'unknown';
    fetch(`/api/approvals/${approvalId}/action?mode=${mode}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, operatorId: operator, justification: `${status} by ${operator} via UI` })
    }).then(() => {
      setApprovals(prev => prev.filter(app => app.approvalId !== approvalId));
    });
  };

  const pending = approvals.filter(a => a.status === 'PENDING');

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <h3 className="widget-title" style={{ margin: 0 }}>Pending Remediation Approvals</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
          {editingName ? (
            <>
              <input
                ref={nameInputRef}
                value={draftName}
                onChange={e => setDraftName(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') commitName(); if (e.key === 'Escape') setEditingName(false); }}
                onBlur={commitName}
                placeholder="Your name"
                style={{
                  background: 'var(--bg-glass)', border: '1px solid var(--accent-cyan)',
                  borderRadius: '4px', color: 'var(--text-primary)', padding: '0.15rem 0.4rem',
                  fontSize: '0.78rem', width: '140px', outline: 'none',
                }}
              />
            </>
          ) : (
            <>
              <span>Acting as:</span>
              <button
                onClick={() => { setDraftName(operatorName); setEditingName(true); }}
                style={{
                  background: 'transparent', border: 'none', cursor: 'pointer',
                  color: operatorName ? 'var(--accent-cyan)' : 'var(--status-warning)',
                  fontWeight: 600, fontSize: '0.78rem', padding: 0,
                }}
              >
                {operatorName || '⚠ set name'}
              </button>
              <span style={{ opacity: 0.5, cursor: 'pointer' }} onClick={() => { setDraftName(operatorName); setEditingName(true); }}>✏</span>
            </>
          )}
        </div>
      </div>

      <div style={{ flex: 1, overflowX: 'auto' }}>
        {loading ? (
          <div style={{ padding: '1rem', color: 'var(--text-secondary)' }}>Loading...</div>
        ) : pending.length === 0 ? (
          <div style={{ padding: '1rem', color: 'var(--status-ok)' }}>No pending approvals.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-glass)' }}>
                <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Action</th>
                <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Incident ID</th>
                <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Justification</th>
                <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>Created</th>
                <th style={{ padding: '0.75rem 0.5rem', fontWeight: 600, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((app, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '0.75rem 0.5rem' }}>{app.actionType}</td>
                  <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-secondary)' }}>{app.incidentId}</td>
                  <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-secondary)', maxWidth: '260px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={app.justification}>{app.justification || '—'}</td>
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

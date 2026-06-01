import { useState, useEffect, useRef } from 'react';
import { useAppContext } from '../../context/AppContext';
import ReactMarkdown from 'react-markdown';

const OPERATOR_KEY = 'sre_operator_name';

const PendingApprovals = () => {
  const { mode } = useAppContext();
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [operatorName, setOperatorName] = useState(() => localStorage.getItem(OPERATOR_KEY) || '');
  const [editingName, setEditingName] = useState(false);
  const [draftName, setDraftName] = useState('');
  const nameInputRef = useRef(null);
  const [rejectTarget, setRejectTarget] = useState(null); // { approvalId }
  const [rejectReason, setRejectReason] = useState('');

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

  const submitAction = (approvalId, status, justification) => {
    const operator = operatorName.trim() || 'unknown';
    fetch(`/api/approvals/${approvalId}/action?mode=${mode}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, operatorId: operator, justification })
    }).then(() => {
      setApprovals(prev => prev.filter(app => app.approvalId !== approvalId));
    });
  };

  const handleApprove = (approvalId) => {
    const operator = operatorName.trim() || 'unknown';
    submitAction(approvalId, 'APPROVED', `Approved by ${operator} via UI`);
  };

  const handleRejectClick = (approvalId) => {
    setRejectTarget({ approvalId });
    setRejectReason('');
  };

  const submitReject = () => {
    if (!rejectTarget) return;
    const operator = operatorName.trim() || 'unknown';
    const justification = rejectReason.trim() || `Rejected by ${operator} via UI`;
    submitAction(rejectTarget.approvalId, 'REJECTED', justification);
    setRejectTarget(null);
    setRejectReason('');
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

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {loading ? (
          <div style={{ padding: '1rem', color: 'var(--text-secondary)' }}>Loading...</div>
        ) : pending.length === 0 ? (
          <div style={{ padding: '1rem', color: 'var(--status-ok)' }}>No pending approvals.</div>
        ) : pending.map((app, idx) => {
          const blastCount = app.blastRadius?.impactedCount ?? null;
          const blastColor = blastCount > 15 ? 'var(--status-critical)' : blastCount > 5 ? 'var(--status-warning)' : 'var(--status-ok)';
          const justificationMd = app.justification
            ? app.justification.split(/(?<=\.)\s+/).filter(Boolean).map(s => `- ${s}`).join('\n')
            : null;

          return (
            <div key={idx} style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid var(--border-glass)', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>

              {/* Header row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{app.actionType}</span>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'var(--status-warning)', color: 'black' }}>
                  {app.status}
                </span>
              </div>

              {/* Meta row */}
              <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                <span>Incident: <strong style={{ color: 'var(--text-primary)' }}>{app.incidentId}</strong></span>
                {blastCount !== null && (
                  <span>Blast radius: <strong style={{ color: blastColor }}>{blastCount} node{blastCount !== 1 ? 's' : ''}</strong></span>
                )}
                <span>Created: <strong style={{ color: 'var(--text-primary)' }}>{app.createdAt}</strong></span>
              </div>

              {/* Justification */}
              <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.2)', borderRadius: '6px', padding: '0.75rem 1rem', borderLeft: '3px solid var(--accent-cyan)' }}>
                <strong style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan)' }}>Proposed Remediation</strong>
                {justificationMd ? (
                  <ReactMarkdown
                    components={{
                      ul: ({ children }) => <ul style={{ paddingLeft: '1.2rem', margin: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>{children}</ul>,
                      li: ({ children }) => <li style={{ lineHeight: '1.6' }}>{children}</li>,
                    }}
                  >
                    {justificationMd}
                  </ReactMarkdown>
                ) : <span>—</span>}
              </div>

              {/* Actions */}
              {rejectTarget?.approvalId === app.approvalId ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <textarea
                    autoFocus
                    value={rejectReason}
                    onChange={e => setRejectReason(e.target.value)}
                    placeholder="Reason for rejection (required for agent learning)..."
                    rows={3}
                    style={{
                      background: 'var(--bg-glass)', border: '1px solid var(--status-critical)',
                      borderRadius: '4px', color: 'var(--text-primary)', padding: '0.5rem',
                      fontSize: '0.83rem', resize: 'vertical', outline: 'none', width: '100%',
                    }}
                  />
                  <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                    <button onClick={() => setRejectTarget(null)} style={{ background: 'transparent', border: '1px solid var(--border-glass)', color: 'var(--text-secondary)', padding: '0.3rem 0.75rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.83rem' }}>
                      Cancel
                    </button>
                    <button onClick={submitReject} style={{ background: 'var(--status-critical)', border: 'none', color: 'white', padding: '0.3rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}>
                      Confirm Reject
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                  <button onClick={() => handleApprove(app.approvalId)} style={{ background: 'transparent', border: '1px solid var(--status-ok)', color: 'var(--status-ok)', padding: '0.3rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}>
                    Approve
                  </button>
                  <button onClick={() => handleRejectClick(app.approvalId)} style={{ background: 'transparent', border: '1px solid var(--status-critical)', color: 'var(--status-critical)', padding: '0.3rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}>
                    Reject
                  </button>
                </div>
              )}

            </div>
          );
        })}
      </div>
    </>
  );
};

export default PendingApprovals;

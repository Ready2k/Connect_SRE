import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import { Clock, Activity, ExternalLink } from 'lucide-react';

const Incidents = () => {
  const { mode } = useAppContext();
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [dismissing, setDismissing] = useState(false);
  const [clearingAll, setClearingAll] = useState(false);

  const ACTIVE_STATUSES = new Set(['Investigating', 'Open', 'Pending', 'Triggered', 'Escalated', 'Failed', 'Failed - Rate Limited']);

  const fetchApprovals = () =>
    fetch(`/api/approvals?mode=${mode}`)
      .then(res => res.json())
      .then(data => setApprovals(data))
      .catch(err => console.error("Failed to fetch approvals", err));

  useEffect(() => {
    Promise.all([
      fetch(`/api/incidents?mode=${mode}`).then(res => res.json()),
      fetch(`/api/approvals?mode=${mode}`).then(res => res.json())
    ])
    .then(([incData, appData]) => {
      const active = incData.filter(i => ACTIVE_STATUSES.has(i.status));
      setIncidents(active);
      setApprovals(appData);
      if (active.length > 0) setSelected(active[0]);
      setLoading(false);
    })
      .catch(err => {
        console.error("Failed to fetch incidents", err);
        setLoading(false);
      });
  }, []);

  // Poll approvals every 8s while any selected incident is actively being investigated
  useEffect(() => {
    if (!selected || !ACTIVE_STATUSES.has(selected.status)) return;
    const timer = setInterval(fetchApprovals, 8000);
    return () => clearInterval(timer);
  }, [selected?.incidentId, selected?.status]);

  const handleAction = (approvalId, status) => {
    fetch(`/api/approvals/${approvalId}/action?mode=${mode}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, justification: "Actioned via Incident Page" })
    }).then(() => {
      setApprovals(prev => prev.map(app => 
        app.approvalId === approvalId ? { ...app, status } : app
      ));
    });
  };

  const handleTriggerAgent = (incidentId) => {
    setTriggering(true);
    fetch(`/api/incidents/${incidentId}/trigger?mode=${mode}`, {
      method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'error') {
        alert("Failed to trigger agent: " + data.message);
        setTriggering(false);
        return;
      }
      setIncidents(prev => prev.map(inc => 
        inc.incidentId === incidentId ? { ...inc, status: "Investigating" } : inc
      ));
      if (selected && selected.incidentId === incidentId) {
        setSelected({ ...selected, status: "Investigating" });
      }
      setTimeout(() => setTriggering(false), 1000);
    })
    .catch(err => {
      alert("Network error: " + err);
      setTriggering(false);
    });
  };

  const handleDismiss = (incidentId) => {
    setDismissing(true);
    fetch(`/api/incidents/${incidentId}/status?mode=${mode}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Dismissed' })
    })
    .then(res => res.json())
    .then(() => {
      setIncidents(prev => prev.filter(inc => inc.incidentId !== incidentId));
      setSelected(null);
      setDismissing(false);
    })
    .catch(err => {
      alert("Network error: " + err);
      setDismissing(false);
    });
  };

  const handleClearAll = () => {
    if (!window.confirm(`Clear all ${incidents.length} incident(s)? This marks them all as Dismissed in DynamoDB.`)) return;
    setClearingAll(true);
    fetch(`/api/incidents/dismiss-all?mode=${mode}`, { method: 'POST' })
      .then(res => res.json())
      .then(() => {
        setIncidents([]);
        setSelected(null);
        setClearingAll(false);
      })
      .catch(err => {
        alert("Network error: " + err);
        setClearingAll(false);
      });
  };


  if (loading) return <div style={{ padding: '2rem' }}>Loading incidents from DynamoDB...</div>;
  if (incidents.length === 0) return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: '1rem', color: 'var(--status-ok)' }}>
      <Activity size={48} />
      <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>All Systems Healthy</h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>No active incidents. The Connect platform is operating normally.</p>
    </div>
  );

  const selectedApprovals = approvals.filter(a => a.incidentId === selected?.incidentId);
  return (
    <div style={{ display: 'flex', gap: '1.5rem', height: '100%', padding: '1rem' }}>
      {/* List Panel */}
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Active Incidents</h2>
          {incidents.length > 0 && (
            <button
              onClick={handleClearAll}
              disabled={clearingAll}
              style={{ padding: '0.3rem 0.75rem', background: 'transparent', color: 'var(--status-critical)', border: '1px solid var(--status-critical)', borderRadius: '4px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, opacity: clearingAll ? 0.5 : 1 }}>
              {clearingAll ? "Clearing..." : "Clear All"}
            </button>
          )}
        </div>
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
              <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>{inc.title}</div>
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
              <h2 style={{ fontSize: '1.4rem', fontWeight: 600, marginBottom: '0.5rem' }}>{selected.title}</h2>
              <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                <span>ID: {selected.incidentId}</span>
                <span>Source: {selected.source}</span>
                <span style={{ color: 'var(--status-critical)' }}>Severity: {selected.severity}</span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => handleDismiss(selected.incidentId)}
                disabled={dismissing}
                style={{ padding: '0.5rem 1rem', background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-glass)', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
                {dismissing ? "Dismissing..." : "Dismiss"}
              </button>
              <button
                onClick={() => handleTriggerAgent(selected.incidentId)}
                disabled={triggering}
                style={{ padding: '0.5rem 1rem', background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
                {triggering ? "Triggering..." : "Trigger Agent Triage"}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1.5rem', flex: 1, minHeight: 0 }}>
            {/* Timeline & Context */}
            <div style={{ flex: 1, overflowY: 'auto', paddingRight: '1rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--accent-cyan)' }}>Incident Context</h3>
              
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Connect Instance ID</span>
                  <span style={{ fontWeight: 600, color: 'var(--accent-purple)' }}>{selected.connectInstanceId || 'N/A'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Resource ID</span>
                  <span style={{ fontWeight: 600 }}>{selected.connectResourceId || 'N/A'}</span>
                </div>
                {selected.metadata && selected.metadata.alarmName && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Alarm Name</span>
                    <span style={{ fontWeight: 600 }}>{selected.metadata.alarmName}</span>
                  </div>
                )}
                {selected.metadata && selected.metadata.eventName && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>CloudTrail Event</span>
                    <span style={{ fontWeight: 600 }}>{selected.metadata.eventName}</span>
                  </div>
                )}
              </div>

              <div style={{ marginTop: '1.5rem', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
                  <Activity size={16} /> <strong>Agent Swarm</strong>: {selected.status || "Investigating..."}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
                  <Clock size={16} /> <strong>Detected At</strong>: {selected.createdAt}
                </div>
                <button
                  onClick={() => navigate(`/logs?incidentId=${selected.incidentId}`)}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.45rem 0.9rem', background: 'rgba(0,212,255,0.08)', color: 'var(--accent-cyan)', border: '1px solid var(--accent-cyan)', borderRadius: '4px', cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600 }}
                >
                  <ExternalLink size={14} /> View Investigation Logs
                </button>
              </div>
            </div>

            {/* Action Recommendation */}
            <div style={{ flex: 1, borderLeft: '1px solid var(--border-glass)', paddingLeft: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--status-ok)' }}>Remediation Tickets</h3>
              
              {selectedApprovals.length === 0 ? (
                <div style={{ background: 'rgba(0, 255, 128, 0.05)', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(0, 255, 128, 0.2)' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {selected?.status === 'Investigating'
                      ? 'The Agent Swarm is evaluating the root cause. If a safe remediation path is found, it will generate a ticket here for human approval.'
                      : 'No remediation action required for this incident.'}
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {selectedApprovals.map(app => (
                    <div key={app.approvalId} style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: 600 }}>{app.actionType}</span>
                        <span style={{ 
                          fontSize: '0.75rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px',
                          background: app.status === 'PENDING' ? 'var(--status-warn)' : app.status === 'APPROVED' ? 'var(--status-ok)' : 'var(--status-critical)',
                          color: 'black'
                        }}>
                          {app.status}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                        <strong>Justification:</strong> {app.justification}
                      </p>
                      
                      {app.status === 'PENDING' && (
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                          <button onClick={() => handleAction(app.approvalId, 'APPROVED')} style={{ background: 'transparent', border: '1px solid var(--status-ok)', color: 'var(--status-ok)', padding: '0.25rem 0.75rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
                            Approve
                          </button>
                          <button onClick={() => handleAction(app.approvalId, 'REJECTED')} style={{ background: 'transparent', border: '1px solid var(--status-critical)', color: 'var(--status-critical)', padding: '0.25rem 0.75rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
                            Reject
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Incidents;

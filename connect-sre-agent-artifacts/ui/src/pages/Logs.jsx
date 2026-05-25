import { useState, useEffect, useRef } from 'react';
import { FileText, ArrowLeft, ChevronDown, ChevronRight, Activity } from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';

// ── Agent colour palette ─────────────────────────────────────────────────────
const AGENT_COLOR = {
  SUPERVISOR: 'var(--accent-cyan)',
  ADK:     '#c084fc',   // Gemini tool calls — soft purple
  FLOW:    '#4a9eff',
  MODULE:  '#a855f7',
  QUEUE:   '#f97316',
  LEXA:    '#eab308',
  AIA:     '#22c55e',
  CHANGE:  '#ec4899',
  IMPACT:  '#ef4444',
  RUNBOOK: '#14b8a6',
  RISK:    '#f59e0b',
  VERIFY:  '#84cc16',
};

const TYPE_ICON = {
  start:            '▶',
  specialist_call:  '→',
  specialist_result:'✓',
  tool_call:        '⚡',  // Gemini direct tool invocation
  tool_result:      '↩',  // Gemini tool return
  complete:         '✓✓',
  error:            '✗',
};

const TYPE_LABEL = {
  start:            'STARTED',
  specialist_call:  'DISPATCH',
  specialist_result:'RESULT',
  tool_call:        'TOOL CALL',
  tool_result:      'TOOL RESULT',
  complete:         'COMPLETE',
  error:            'ERROR',
};

function StepRow({ step }) {
  const [expanded, setExpanded] = useState(false);
  const color = AGENT_COLOR[step.agent] || 'var(--text-secondary)';
  const isError = step.type === 'error';
  const isComplete = step.type === 'complete';

  return (
    <div style={{
      display: 'flex',
      gap: '0.75rem',
      position: 'relative',
    }}>
      {/* Timeline spine + dot */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0, width: '28px' }}>
        <div style={{
          width: '28px', height: '28px', borderRadius: '50%',
          background: isError ? 'rgba(239,68,68,0.15)' : isComplete ? 'rgba(0,255,128,0.12)' : 'rgba(255,255,255,0.06)',
          border: `2px solid ${isError ? '#ef4444' : isComplete ? 'var(--status-ok)' : color}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.7rem', color: isError ? '#ef4444' : isComplete ? 'var(--status-ok)' : color,
          fontWeight: 700, flexShrink: 0,
        }}>
          {TYPE_ICON[step.type] || '·'}
        </div>
        <div style={{ flex: 1, width: '2px', background: 'var(--border-glass)', minHeight: '8px' }} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, paddingBottom: '1rem' }}>
        {/* Header row */}
        <div
          onClick={() => step.detail && setExpanded(e => !e)}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            cursor: step.detail ? 'pointer' : 'default',
            marginBottom: expanded ? '0.5rem' : 0,
          }}
        >
          {/* Agent badge */}
          <span style={{
            fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.05em',
            padding: '0.15rem 0.45rem', borderRadius: '3px',
            background: `${color}22`, color, border: `1px solid ${color}55`,
            flexShrink: 0,
          }}>
            {step.agent}
          </span>
          {/* Type tag */}
          <span style={{
            fontSize: '0.65rem', color: 'var(--text-secondary)',
            fontFamily: 'monospace', flexShrink: 0,
          }}>
            {TYPE_LABEL[step.type] || step.type}
          </span>
          {/* Message */}
          <span style={{
            fontSize: '0.85rem', color: isError ? '#ef4444' : isComplete ? 'var(--status-ok)' : 'var(--text-primary)',
            flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {step.message}
          </span>
          {/* Timestamp + expand chevron */}
          <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', flexShrink: 0, fontFamily: 'monospace' }}>
            {new Date(step.ts).toLocaleTimeString()}
          </span>
          {step.detail && (
            <span style={{ color: 'var(--text-secondary)', flexShrink: 0 }}>
              {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </span>
          )}
        </div>

        {/* Expanded detail */}
        {expanded && step.detail && (
          <pre style={{
            margin: 0, padding: '0.75rem', borderRadius: '6px',
            background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-glass)',
            fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.55,
            whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowX: 'auto',
            maxHeight: '400px', overflowY: 'auto',
          }}>
            {step.detail}
          </pre>
        )}
      </div>
    </div>
  );
}

// ── Investigation sequence view ───────────────────────────────────────────────
function SequenceView({ incidentId }) {
  const { mode } = useAppContext();
  const navigate = useNavigate();
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const bottomRef = useRef(null);

  const isLive = steps.length > 0 &&
    !['complete', 'error'].includes(steps[steps.length - 1]?.type);

  useEffect(() => {
    const fetch_ = () =>
      fetch(`/api/incidents/${incidentId}/steps?mode=${mode}`)
        .then(r => r.json())
        .then(data => { setSteps(data); setLoading(false); })
        .catch(() => setLoading(false));

    fetch_();
    const timer = setInterval(() => {
      // Keep polling while the last step is not terminal
      setSteps(prev => {
        const last = prev[prev.length - 1];
        if (last && (last.type === 'complete' || last.type === 'error')) {
          clearInterval(timer);
        }
        return prev;
      });
      fetch_();
    }, 2000);
    return () => clearInterval(timer);
  }, [incidentId, mode]);

  // Auto-scroll to bottom as new steps arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [steps.length]);

  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => navigate('/logs')}
          style={{ background: 'transparent', border: '1px solid var(--border-glass)', color: 'var(--text-secondary)', borderRadius: '4px', padding: '0.3rem 0.6rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.8rem' }}
        >
          <ArrowLeft size={14} /> All Logs
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Activity size={20} color="var(--accent-cyan)" />
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600 }}>
            Investigation Sequence
            <span style={{ marginLeft: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'monospace', fontWeight: 400 }}>{incidentId}</span>
          </h2>
        </div>
        {isLive && (
          <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--status-warn)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--status-warn)', animation: 'pulse 1.5s infinite' }} />
            LIVE — polling every 2s
          </span>
        )}
      </div>

      {/* Step list */}
      <div className="glass-panel" style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
        {loading ? (
          <div style={{ color: 'var(--text-secondary)', textAlign: 'center', paddingTop: '3rem' }}>Loading steps…</div>
        ) : steps.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)', textAlign: 'center', paddingTop: '3rem' }}>
            No steps recorded yet. Trigger an investigation to see the sequence here.
          </div>
        ) : (
          steps.map((step) => <StepRow key={step.seq} step={step} />)
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

// ── Audit log table (default view) ───────────────────────────────────────────
function AuditTable() {
  const { mode } = useAppContext();
  const navigate = useNavigate();
  const [logData, setLogData] = useState([]);
  const [recentRuns, setRecentRuns] = useState([]);

  useEffect(() => {
    fetch(`/api/logs?mode=${mode}`)
      .then(res => res.json())
      .then(data => setLogData(data))
      .catch(err => console.error(err));

    // Load recent incident runs for quick links
    fetch(`/api/incidents?mode=${mode}`)
      .then(r => r.json())
      .then(data => setRecentRuns(data.slice(0, 8)))
      .catch(() => {});
  }, [mode]);

  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <FileText size={24} color="var(--accent-purple)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>System Audit Logs</h2>
      </div>

      {/* Recent investigations quick-links */}
      {recentRuns.length > 0 && (
        <div className="glass-panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '0.75rem' }}>
            Recent Investigations — click to replay
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {recentRuns.map(inc => (
              <button
                key={inc.incidentId}
                onClick={() => navigate(`/logs?incidentId=${inc.incidentId}`)}
                style={{
                  padding: '0.35rem 0.75rem', borderRadius: '4px', cursor: 'pointer',
                  background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-glass)',
                  color: 'var(--text-primary)', fontSize: '0.78rem', textAlign: 'left',
                }}
              >
                <span style={{ color: 'var(--text-secondary)', marginRight: '0.4rem', fontFamily: 'monospace' }}>{inc.incidentId}</span>
                {inc.title?.slice(0, 40)}{inc.title?.length > 40 ? '…' : ''}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Audit table */}
      <div className="glass-panel" style={{ flex: 1, overflowY: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-glass)', position: 'sticky', top: 0 }}>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Timestamp</th>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Source Component</th>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Action Type</th>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Details</th>
              <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {logData.map((log, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '1rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{new Date(log.time).toLocaleTimeString()}</td>
                <td style={{ padding: '1rem' }}>{log.source}</td>
                <td style={{ padding: '1rem', color: 'var(--accent-cyan)' }}>{log.type}</td>
                <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>{log.details}</td>
                <td style={{ padding: '1rem' }}>
                  <span style={{
                    padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem',
                    background: log.status === 'Success' || log.status === 'Approved' ? 'rgba(0, 255, 128, 0.1)' : 'rgba(255, 255, 255, 0.1)',
                    color: log.status === 'Success' || log.status === 'Approved' ? 'var(--status-ok)' : 'var(--text-primary)',
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
}

// ── Root ──────────────────────────────────────────────────────────────────────
const Logs = () => {
  const [searchParams] = useSearchParams();
  const incidentId = searchParams.get('incidentId');
  return incidentId ? <SequenceView incidentId={incidentId} /> : <AuditTable />;
};

export default Logs;

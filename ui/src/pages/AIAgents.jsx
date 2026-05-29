import { useState, useEffect } from 'react';
import { Bot, Zap, AlertTriangle, CheckCircle, Clock, Wrench, RefreshCw, ExternalLink, ChevronDown, ChevronRight } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const STATUS_STYLE = {
  ACTIVE: { color: 'var(--status-ok)', label: 'Active' },
  INACTIVE: { color: 'var(--status-error)', label: 'Inactive' },
  UNKNOWN: { color: 'var(--text-muted)', label: 'Unknown' },
};

const VISIBILITY_STYLE = {
  PUBLISHED: { color: 'var(--accent-cyan)', label: 'Published' },
  SAVED: { color: 'var(--status-warn)', label: 'Draft' },
};

function healthColor(errorRatePct) {
  if (errorRatePct === null || errorRatePct === undefined) return 'var(--text-muted)';
  if (errorRatePct > 10) return 'var(--status-error)';
  if (errorRatePct > 2) return 'var(--status-warn)';
  return 'var(--status-ok)';
}

function Stat({ label, value, color }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
      <span style={{ fontSize: '1.1rem', fontWeight: 700, color: color || 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}

function AgentCard({ agent, health, expanded, onToggle }) {
  const statusStyle = STATUS_STYLE[agent.status] || STATUS_STYLE.UNKNOWN;
  const visStyle = VISIBILITY_STYLE[agent.visibilityStatus] || {};
  const errorRate = health?.bedrockMetrics?.errorRatePct ?? null;
  const invocations = health?.bedrockMetrics?.Invocations ?? null;
  const latency = health?.bedrockMetrics?.InvocationLatency ?? null;
  const lexErrors = health?.lexMetrics?.RuntimeUserErrors ?? null;

  const modelShort = agent.modelId
    ? agent.modelId.replace('us.anthropic.', '').replace('-v1:0', '')
    : 'Unknown model';

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border-glass)',
      borderRadius: '10px',
      overflow: 'hidden',
      transition: 'border-color 0.2s',
    }}>
      {/* Header row */}
      <div
        onClick={onToggle}
        style={{
          padding: '1rem 1.25rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}
      >
        <Bot size={20} style={{ color: 'var(--accent-cyan)', flexShrink: 0 }} />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{agent.name}</span>
            <span style={{
              fontSize: '0.68rem', fontWeight: 600, padding: '2px 7px',
              borderRadius: '4px', background: `${statusStyle.color}22`, color: statusStyle.color,
            }}>{statusStyle.label}</span>
            {visStyle.label && (
              <span style={{
                fontSize: '0.68rem', fontWeight: 600, padding: '2px 7px',
                borderRadius: '4px', background: `${visStyle.color}22`, color: visStyle.color,
              }}>{visStyle.label}</span>
            )}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {agent.type} · {agent.locale || '—'} · {modelShort}
          </div>
        </div>

        {/* Health KPIs */}
        <div style={{ display: 'flex', gap: '1.5rem', flexShrink: 0 }}>
          {invocations !== null && (
            <Stat label="Invocations" value={invocations} />
          )}
          {errorRate !== null && (
            <Stat label="Error %" value={`${errorRate}%`} color={healthColor(errorRate)} />
          )}
          {latency !== null && (
            <Stat label="Latency" value={`${latency}ms`} />
          )}
        </div>

        {expanded ? <ChevronDown size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} /> : <ChevronRight size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />}
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div style={{
          borderTop: '1px solid var(--border-glass)',
          padding: '1rem 1.25rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.25rem',
        }}>
          {/* Tools */}
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Tools</div>
            {agent.tools && agent.tools.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {agent.tools.map(t => (
                  <span key={t} style={{
                    fontSize: '0.72rem', padding: '2px 8px', borderRadius: '4px',
                    background: 'var(--bg-glass)', border: '1px solid var(--border-glass)',
                    display: 'flex', alignItems: 'center', gap: '4px',
                  }}>
                    <Wrench size={10} /> {t}
                  </span>
                ))}
              </div>
            ) : (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No tools configured</span>
            )}
          </div>

          {/* Bedrock metrics */}
          {health?.bedrockMetrics && (
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Bedrock (60 min)</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                <MetricRow icon={<Zap size={12} />} label="Invocations" value={health.bedrockMetrics.Invocations ?? '—'} />
                <MetricRow icon={<AlertTriangle size={12} />} label="Client errors" value={health.bedrockMetrics.InvocationClientErrors ?? '—'} color={healthColor(health.bedrockMetrics.errorRatePct)} />
                <MetricRow icon={<Clock size={12} />} label="Avg latency" value={health.bedrockMetrics.InvocationLatency ? `${health.bedrockMetrics.InvocationLatency} ms` : '—'} />
              </div>
            </div>
          )}

          {/* Lex metrics */}
          {health?.lexMetrics && (
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Lex runtime (60 min)</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                <MetricRow icon={<Zap size={12} />} label="Requests" value={health.lexMetrics.RuntimeRequestCount ?? '—'} />
                <MetricRow
                  icon={<AlertTriangle size={12} />}
                  label="User errors"
                  value={health.lexMetrics.RuntimeUserErrors ?? '—'}
                  color={lexErrors > 0 ? 'var(--status-warn)' : undefined}
                />
              </div>
            </div>
          )}

          {/* Metadata */}
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Config</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', fontSize: '0.78rem' }}>
              <div><span style={{ color: 'var(--text-muted)' }}>Agent ID: </span><span style={{ fontFamily: 'monospace', fontSize: '0.7rem' }}>{agent.aiAgentId}</span></div>
              <div><span style={{ color: 'var(--text-muted)' }}>Model: </span>{agent.modelId || '—'}</div>
              <div><span style={{ color: 'var(--text-muted)' }}>Prompt: </span>{agent.promptStatus || '—'}</div>
              <div><span style={{ color: 'var(--text-muted)' }}>Modified: </span>{agent.modifiedTime ? new Date(agent.modifiedTime).toLocaleString() : '—'}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MetricRow({ icon, label, value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem' }}>
      <span style={{ color: color || 'var(--text-muted)' }}>{icon}</span>
      <span style={{ color: 'var(--text-muted)', flex: 1 }}>{label}</span>
      <span style={{ color: color || 'var(--text-primary)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}

export default function AIAgents() {
  const { mode, activeInstance } = useAppContext();
  const [agents, setAgents] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState({});
  const [refreshing, setRefreshing] = useState(false);

  async function fetchAll(isRefresh = false) {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ mode });
      if (activeInstance) params.set('instanceId', activeInstance);

      const [agentsRes, healthRes] = await Promise.all([
        fetch(`/api/connect/ai-agents?${params}`),
        fetch(`/api/connect/ai-agents/health?${params}`),
      ]);

      if (!agentsRes.ok) throw new Error(`agents: ${agentsRes.status}`);
      if (!healthRes.ok) throw new Error(`health: ${healthRes.status}`);

      const agentsData = await agentsRes.json();
      const healthData = await healthRes.json();

      setAgents(agentsData.agents || []);
      setHealth(healthData);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { fetchAll(); }, [mode, activeInstance]);

  const toggleExpand = (id) => setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

  const activeCount = agents.filter(a => a.status === 'ACTIVE').length;
  const publishedCount = agents.filter(a => a.visibilityStatus === 'PUBLISHED').length;
  const errorRate = health?.bedrockMetrics?.errorRatePct ?? null;

  return (
    <div style={{ padding: '1.5rem', maxWidth: '1100px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.3rem', fontWeight: 700, margin: 0 }}>Connect AI Agents</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: '4px 0 0' }}>
            Amazon Q Connect orchestration agents · assistant {_QCONNECT_ASSISTANT_ID_SHORT}
          </p>
        </div>
        <button
          onClick={() => fetchAll(true)}
          disabled={refreshing}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.45rem 0.9rem', borderRadius: '6px',
            background: 'var(--bg-glass)', border: '1px solid var(--border-glass)',
            color: 'var(--text-primary)', cursor: 'pointer', fontSize: '0.82rem',
          }}
        >
          <RefreshCw size={14} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {/* Summary KPIs */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {[
          { label: 'Total agents', value: agents.length, icon: <Bot size={16} /> },
          { label: 'Active', value: activeCount, icon: <CheckCircle size={16} />, color: 'var(--status-ok)' },
          { label: 'Published', value: publishedCount, icon: <Zap size={16} />, color: 'var(--accent-cyan)' },
          ...(errorRate !== null ? [{ label: 'Bedrock error %', value: `${errorRate}%`, icon: <AlertTriangle size={16} />, color: healthColor(errorRate) }] : []),
        ].map(({ label, value, icon, color }) => (
          <div key={label} style={{
            background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)',
            borderRadius: '8px', padding: '0.75rem 1.1rem',
            display: 'flex', alignItems: 'center', gap: '0.6rem', minWidth: '130px',
          }}>
            <span style={{ color: color || 'var(--text-muted)' }}>{icon}</span>
            <div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: color || 'var(--text-primary)', lineHeight: 1 }}>{value}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Content */}
      {loading && (
        <div style={{ color: 'var(--text-muted)', padding: '2rem', textAlign: 'center' }}>Loading agents…</div>
      )}
      {error && (
        <div style={{ color: 'var(--status-error)', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
          Failed to load: {error}
        </div>
      )}
      {!loading && !error && agents.length === 0 && (
        <div style={{ color: 'var(--text-muted)', padding: '2rem', textAlign: 'center' }}>
          No AI agents found for this assistant.
        </div>
      )}
      {!loading && !error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {agents.map(agent => (
            <AgentCard
              key={agent.aiAgentId}
              agent={agent}
              health={health}
              expanded={!!expanded[agent.aiAgentId]}
              onToggle={() => toggleExpand(agent.aiAgentId)}
            />
          ))}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

const _QCONNECT_ASSISTANT_ID_SHORT = 'de018ffb…';

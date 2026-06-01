import { useState, useEffect } from 'react';
import { useAppContext } from '../context/AppContext';
import QueueMetrics from '../components/widgets/QueueMetrics';
import QueuesChart from '../components/widgets/QueuesChart';
import SystemHealth from '../components/widgets/SystemHealth';
import IncidentsChart from '../components/widgets/IncidentsChart';

const Monitoring = () => {
  const { mode, activeInstance } = useAppContext();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMetrics = () => {
      const params = new URLSearchParams({ mode });
      if (activeInstance?.instanceId) params.set('instanceId', activeInstance.instanceId);
      fetch(`/api/monitoring/metrics?${params}`)
        .then(res => {
          if (!res.ok) {
            return res.json().then(err => { throw new Error(err.detail || "API Error") });
          }
          return res.json();
        })
        .then(data => {
          setMetrics(data);
          setError(null);
          setLoading(false);
        })
        .catch(err => {
          console.error("Failed to fetch monitoring metrics", err);
          setError(err.message);
          setLoading(false);
        });
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, [mode, activeInstance]);

  if (loading && !metrics && !error) {
    return (
      <div style={{ 
        display: 'flex', 
        height: '100%', 
        alignItems: 'center', 
        justifyContent: 'center', 
        color: 'var(--text-secondary)',
        fontSize: '1rem',
        fontWeight: 500
      }}>
        Ingesting live Connect telemetry...
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div style={{ padding: '2rem', color: 'var(--status-critical)' }}>
        <h3>Error loading detailed monitoring</h3>
        <p>{error}</p>
      </div>
    );
  }

  const queues = metrics?.queueHealthMetrics || [];
  const flows = metrics?.systemHealth?.flows || [];

  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Live Operations Monitor</h2>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Auto-refreshes every 5s</span>
      </div>

      {mode === 'live' && !activeInstance && (
        <div style={{ padding: '0.7rem 1rem', borderRadius: '8px', background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.25)', fontSize: '0.82rem', color: '#fbbf24' }}>
          Select a Connect instance from the header to view real-time queue and call metrics.
        </div>
      )}

      {/* Summary stat row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
        {[
          { label: 'Concurrent Calls',  value: metrics.concurrentCalls ?? '—', color: 'var(--accent-cyan)' },
          { label: 'Abandon Rate',      value: metrics.abandonRate != null ? `${metrics.abandonRate}%` : '—', color: metrics.abandonRate > 5 ? 'var(--status-warn)' : 'var(--status-ok)' },
          { label: 'Queues Monitored',  value: queues.length || '—', color: 'var(--text-primary)' },
          { label: 'Active Incidents',  value: metrics.activeIncidents ?? '—', color: metrics.activeIncidents > 0 ? 'var(--status-critical)' : 'var(--status-ok)' },
        ].map(({ label, value, color }) => (
          <div key={label} className="glass-panel" style={{ textAlign: 'center', padding: '1rem' }}>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color }}>{value}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Incident trend + queue volume charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', minHeight: '280px' }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <IncidentsChart data={metrics.incidentsTimeSeries} />
        </div>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <QueuesChart data={metrics.queueVolumes} />
        </div>
      </div>

      {/* Per-queue drill-down table */}
      <div className="glass-panel" style={{ padding: 0 }}>
        <div style={{ padding: '0.85rem 1.25rem', borderBottom: '1px solid var(--border-glass)', fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Queue Health Breakdown
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-glass)' }}>
              {['Queue', 'Contacts Waiting', 'Oldest Wait', 'Agents Available', 'Abandon Rate', 'Status'].map(h => (
                <th key={h} style={{ padding: '0.6rem 1rem', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {queues.length > 0 ? queues.map((q, i) => {
              const isWarn = q.contactsInQueue > 10 || q.oldestContactAge > 120;
              const isCrit = q.contactsInQueue > 25 || q.oldestContactAge > 300;
              const sc = isCrit ? 'var(--status-critical)' : isWarn ? 'var(--status-warn)' : 'var(--status-ok)';
              return (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '0.65rem 1rem', fontWeight: 500 }}>{q.queueName || q.name || `Queue ${i+1}`}</td>
                  <td style={{ padding: '0.65rem 1rem', color: q.contactsInQueue > 0 ? 'var(--status-warn)' : 'var(--text-secondary)' }}>{q.contactsInQueue ?? '—'}</td>
                  <td style={{ padding: '0.65rem 1rem', color: 'var(--text-secondary)' }}>{q.oldestContactAge != null ? `${q.oldestContactAge}s` : '—'}</td>
                  <td style={{ padding: '0.65rem 1rem' }}>{q.agentsAvailable ?? '—'}</td>
                  <td style={{ padding: '0.65rem 1rem', color: q.abandonRate > 5 ? 'var(--status-warn)' : 'var(--text-secondary)' }}>{q.abandonRate != null ? `${q.abandonRate}%` : '—'}</td>
                  <td style={{ padding: '0.65rem 1rem' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: '3px', background: `${sc}22`, color: sc }}>
                      {isCrit ? 'Critical' : isWarn ? 'Degraded' : 'Healthy'}
                    </span>
                  </td>
                </tr>
              );
            }) : (
              <tr>
                <td colSpan={6} style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  Switch to Live mode with an instance selected to see real-time queue data.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* System health + flow health */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <SystemHealth data={metrics.systemHealth} />
        </div>
        <div className="glass-panel" style={{ padding: 0 }}>
          <div style={{ padding: '0.85rem 1.25rem', borderBottom: '1px solid var(--border-glass)', fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Contact Flow Health
          </div>
          {flows.length > 0 ? (
            <div style={{ overflowY: 'auto', maxHeight: '240px' }}>
              {flows.map((f, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.6rem 1.25rem', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: '0.82rem' }}>
                  <span style={{ fontWeight: 500 }}>{f.name || f.flowName}</span>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    {f.errorRate != null && <span style={{ color: f.errorRate > 0 ? 'var(--status-critical)' : 'var(--text-secondary)' }}>{f.errorRate}% errors</span>}
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '3px', background: f.status === 'Healthy' ? 'rgba(0,255,128,0.1)' : 'rgba(239,68,68,0.12)', color: f.status === 'Healthy' ? 'var(--status-ok)' : 'var(--status-critical)' }}>{f.status || 'Unknown'}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Flow health data is populated from CloudWatch alarms and Contact Lens. Run Discovery to populate.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Monitoring;

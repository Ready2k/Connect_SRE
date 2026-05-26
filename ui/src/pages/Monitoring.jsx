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

  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Detailed Monitoring</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem', minHeight: '350px' }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <QueueMetrics 
            data={metrics.queueHealthMetrics} 
            concurrentCalls={metrics.concurrentCalls} 
            abandonRate={metrics.abandonRate} 
          />
        </div>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <IncidentsChart data={metrics.incidentsTimeSeries} />
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', minHeight: '300px' }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <SystemHealth data={metrics.systemHealth} />
        </div>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gridColumn: 'span 2' }}>
          <QueuesChart data={metrics.queueVolumes} />
        </div>
      </div>
    </div>
  );
};

export default Monitoring;

import { useState, useEffect } from 'react';
import { useAppContext } from '../context/AppContext';
import SREOverview from '../components/widgets/SREOverview';
import SystemHealth from '../components/widgets/SystemHealth';
import GlobalTopology from '../components/widgets/GlobalTopology';
import QueuesChart from '../components/widgets/QueuesChart';
import IncidentsChart from '../components/widgets/IncidentsChart';
import QueueMetrics from '../components/widgets/QueueMetrics';
import LexBotHealth from '../components/widgets/LexBotHealth';
import PendingApprovals from '../components/widgets/PendingApprovals';
import ActivityFeed from '../components/widgets/ActivityFeed';

const Home = () => {
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
        <h3>Error loading dashboard metrics</h3>
        <p>{error}</p>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Check your AWS IAM permissions (KMS Decrypt) and backend logs.</p>
      </div>
    );
  }

  return (
    <div className="dashboard-grid">
      <div className="glass-panel widget overview-widget">
        <SREOverview data={metrics.sreOverview} />
      </div>
      <div className="glass-panel widget health-widget">
        <SystemHealth data={metrics.systemHealth} />
      </div>
      <div className="glass-panel widget topology-widget">
        <GlobalTopology mode={mode} instanceId={activeInstance?.instanceId || ''} />
      </div>
      <div className="glass-panel widget queues-widget">
        <QueuesChart data={metrics.queueVolumes} />
      </div>
      <div className="glass-panel widget incidents-widget">
        <IncidentsChart data={metrics.incidentsTimeSeries} />
      </div>
      <div className="glass-panel widget queue-metrics-widget">
        <QueueMetrics 
          data={metrics.queueHealthMetrics} 
          concurrentCalls={metrics.concurrentCalls} 
          abandonRate={metrics.abandonRate} 
        />
      </div>
      <div className="glass-panel widget lex-bot-widget">
        <LexBotHealth data={metrics.lexBots} />
      </div>
      <div className="glass-panel widget approvals-widget">
        <PendingApprovals />
      </div>
      <div className="glass-panel widget activity-widget" style={{ padding: '1rem 1.5rem', flexDirection: 'row' }}>
        <ActivityFeed data={metrics.activityFeed} />
      </div>
    </div>
  );
};

export default Home;

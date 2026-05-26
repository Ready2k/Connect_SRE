import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Server, ArrowRight, AlertTriangle, CheckCircle, Clock, RefreshCw } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const StatusBadge = ({ status }) => {
  const isActive = status === 'ACTIVE';
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.4rem',
      padding: '0.25rem 0.65rem',
      borderRadius: '12px',
      fontSize: '0.72rem',
      fontWeight: 600,
      letterSpacing: '0.04em',
      background: isActive ? 'rgba(34,197,94,0.12)' : 'rgba(251,191,36,0.12)',
      color: isActive ? '#22c55e' : '#fbbf24',
      border: `1px solid ${isActive ? 'rgba(34,197,94,0.3)' : 'rgba(251,191,36,0.3)'}`
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: '50%',
        background: isActive ? '#22c55e' : '#fbbf24',
        boxShadow: isActive ? '0 0 5px #22c55e' : 'none',
        animation: isActive ? 'pulse 1.5s infinite' : 'none'
      }} />
      {status}
    </span>
  );
};

const InstanceCard = ({ instance, onSelect }) => {
  const openIncidents = instance.openIncidents ?? 0;
  const hasCritical = instance.criticalIncidents > 0;

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: `1px solid ${hasCritical ? 'rgba(239,68,68,0.35)' : 'var(--border-glass)'}`,
      borderRadius: '14px',
      padding: '1.5rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      transition: 'border-color 0.2s, transform 0.2s, box-shadow 0.2s',
      cursor: 'pointer',
      position: 'relative',
      overflow: 'hidden'
    }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 8px 32px rgba(0,0,0,0.3)';
        e.currentTarget.style.borderColor = hasCritical ? 'rgba(239,68,68,0.6)' : 'rgba(6,182,212,0.4)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
        e.currentTarget.style.borderColor = hasCritical ? 'rgba(239,68,68,0.35)' : 'var(--border-glass)';
      }}
    >
      {/* Top gradient accent */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
        background: hasCritical
          ? 'linear-gradient(90deg, #ef4444, #f97316)'
          : 'linear-gradient(90deg, var(--accent-cyan), var(--accent-blue))'
      }} />

      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 40, height: 40, borderRadius: '10px',
            background: 'rgba(6,182,212,0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Server size={20} color="var(--accent-cyan)" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              {instance.instanceAlias || 'Unnamed Instance'}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '0.15rem', fontFamily: 'monospace' }}>
              {instance.instanceId}
            </div>
          </div>
        </div>
        <StatusBadge status={instance.instanceStatus} />
      </div>

      {/* Metrics row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
        <div style={{ textAlign: 'center', padding: '0.6rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: hasCritical ? '#ef4444' : 'var(--text-primary)' }}>
            {openIncidents}
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Open Incidents</div>
        </div>
        <div style={{ textAlign: 'center', padding: '0.6rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: instance.criticalIncidents > 0 ? '#ef4444' : 'var(--text-primary)' }}>
            {instance.criticalIncidents ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>SEV1/SEV2</div>
        </div>
        <div style={{ textAlign: 'center', padding: '0.6rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
          <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {instance.region || '—'}
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Region</div>
        </div>
      </div>

      {/* Critical alert banner if needed */}
      {hasCritical && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          background: 'rgba(239,68,68,0.1)',
          border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: '8px',
          padding: '0.5rem 0.75rem',
          fontSize: '0.78rem',
          color: '#ef4444'
        }}>
          <AlertTriangle size={14} />
          {instance.criticalIncidents} critical incident{instance.criticalIncidents > 1 ? 's' : ''} require attention
        </div>
      )}

      {/* View Details button */}
      <button
        id={`view-instance-${instance.instanceId}`}
        onClick={() => onSelect(instance)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
          padding: '0.6rem',
          background: 'rgba(6,182,212,0.1)',
          border: '1px solid rgba(6,182,212,0.25)',
          borderRadius: '8px',
          color: 'var(--accent-cyan)',
          cursor: 'pointer',
          fontSize: '0.82rem',
          fontWeight: 600,
          transition: 'background 0.2s'
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'rgba(6,182,212,0.2)'}
        onMouseLeave={e => e.currentTarget.style.background = 'rgba(6,182,212,0.1)'}
      >
        View Instance Detail <ArrowRight size={14} />
      </button>
    </div>
  );
};

const InstanceOverview = () => {
  const { mode, selectInstance } = useAppContext();
  const navigate = useNavigate();
  const [overview, setOverview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const fetchOverview = () => {
    setLoading(true);
    fetch(`/api/instances/overview?mode=${mode}`)
      .then(res => {
        if (!res.ok) throw new Error(`API returned ${res.status}`);
        return res.json();
      })
      .then(data => {
        setOverview(data.instances || []);
        setLastRefreshed(new Date());
        setError(null);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchOverview();
    const interval = setInterval(fetchOverview, 30000); // Refresh every 30s
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSelectInstance = (instance) => {
    selectInstance(instance);
    navigate('/');
  };

  // Aggregate stats
  const totalOpen = overview.reduce((sum, i) => sum + (i.openIncidents ?? 0), 0);
  const totalCritical = overview.reduce((sum, i) => sum + (i.criticalIncidents ?? 0), 0);
  const activeCount = overview.filter(i => i.instanceStatus === 'ACTIVE').length;

  return (
    <div style={{ padding: '1.5rem', height: '100%', overflowY: 'auto' }}>
      {/* Page header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Connect Instances</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.3rem 0 0' }}>
            Aggregated overview across all Connect instances in this account
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {lastRefreshed && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Clock size={12} /> {lastRefreshed.toLocaleTimeString()}
            </span>
          )}
          <button
            id="refresh-instances-btn"
            onClick={fetchOverview}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.45rem 0.9rem',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-glass)',
              borderRadius: '8px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: '0.8rem'
            }}
          >
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      </div>

      {/* Summary strip */}
      {!loading && overview.length > 0 && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1rem',
          marginBottom: '1.5rem'
        }}>
          {[
            { label: 'Active Instances', value: `${activeCount} / ${overview.length}`, icon: <CheckCircle size={18} color="#22c55e" />, color: '#22c55e' },
            { label: 'Total Open Incidents', value: totalOpen, icon: <AlertTriangle size={18} color="#fbbf24" />, color: '#fbbf24', link: '/incidents' },
            { label: 'Critical (SEV1/SEV2)', value: totalCritical, icon: <AlertTriangle size={18} color={totalCritical > 0 ? '#ef4444' : 'var(--text-secondary)'} />, color: totalCritical > 0 ? '#ef4444' : 'var(--text-secondary)', link: '/incidents' },
          ].map((stat, i) => (
            <div key={i} className="glass-panel" 
                 onClick={stat.link ? () => navigate(stat.link) : undefined}
                 style={{ 
                   padding: '1rem 1.25rem', 
                   display: 'flex', 
                   alignItems: 'center', 
                   gap: '1rem',
                   cursor: stat.link ? 'pointer' : 'default',
                   transition: stat.link ? 'transform 0.1s, box-shadow 0.1s' : 'none'
                 }}
                 onMouseEnter={stat.link ? e => e.currentTarget.style.transform = 'translateY(-2px)' : undefined}
                 onMouseLeave={stat.link ? e => e.currentTarget.style.transform = 'translateY(0)' : undefined}
            >
              {stat.icon}
              <div>
                <div style={{ fontSize: '1.6rem', fontWeight: 700, color: stat.color }}>{stat.value}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{stat.label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.75rem',
          background: 'rgba(251,191,36,0.08)',
          border: '1px solid rgba(251,191,36,0.3)',
          borderRadius: '10px',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          color: '#fbbf24',
          fontSize: '0.85rem'
        }}>
          <AlertTriangle size={18} />
          <div>
            <strong>Could not load instances.</strong> {error}
            <div style={{ fontSize: '0.78rem', marginTop: '0.25rem', opacity: 0.8 }}>
              Ensure the runtime IAM role has <code>connect:ListInstances</code> permission.
            </div>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px', color: 'var(--text-secondary)' }}>
          <RefreshCw size={20} style={{ marginRight: '0.5rem', animation: 'spin 1s linear infinite' }} />
          Discovering Connect instances...
        </div>
      )}

      {/* Instance card grid */}
      {!loading && overview.length > 0 && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
          gap: '1.25rem'
        }}>
          {overview.map(instance => (
            <InstanceCard
              key={instance.instanceId}
              instance={instance}
              onSelect={handleSelectInstance}
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && overview.length === 0 && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          height: '300px', gap: '1rem', color: 'var(--text-secondary)'
        }}>
          <Server size={48} opacity={0.3} />
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontWeight: 600, marginBottom: '0.4rem' }}>No Connect instances found</div>
            <div style={{ fontSize: '0.85rem' }}>Check IAM permissions: <code>connect:ListInstances</code></div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pulse {
          0%, 100% { opacity: 1; box-shadow: 0 0 5px #22c55e; }
          50% { opacity: 0.5; box-shadow: 0 0 10px #22c55e; }
        }
      `}</style>
    </div>
  );
};

export default InstanceOverview;

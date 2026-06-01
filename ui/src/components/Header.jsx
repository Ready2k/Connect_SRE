import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, ChevronDown, Wifi, WifiOff } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const Header = () => {
  const { mode, activeInstance, modeLocked, liveModeLocked, toggleMode, selectInstance, clearInstance } = useAppContext();
  const navigate = useNavigate();
  const [instances, setInstances] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [loadingInstances, setLoadingInstances] = useState(false);

  // Fetch instances list when mode switches to live
  useEffect(() => {
    if (mode === 'live') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoadingInstances(true);
      fetch('/api/connect/instances')
        .then(res => res.json())
        .then(data => {
          setInstances(data.instances || []);
          setLoadingInstances(false);
        })
        .catch(() => {
          setInstances([]);
          setLoadingInstances(false);
        });
    } else {
      setInstances([]);
      setDropdownOpen(false);
    }
  }, [mode]);

  const handleModeToggle = (newMode) => {
    toggleMode(newMode);
    if (newMode === 'live') {
      navigate('/instances');
    } else {
      navigate('/');
    }
  };

  const handleSelectInstance = (instance) => {
    selectInstance(instance);
    setDropdownOpen(false);
    navigate('/');
  };

  const handleClearInstance = () => {
    clearInstance();
    setDropdownOpen(false);
    navigate('/instances');
  };

  const instanceLabel = activeInstance
    ? activeInstance.instanceAlias || activeInstance.instanceId
    : 'All Instances';

  return (
    <div className="app-header flex-between">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h1 style={{ fontSize: '1.1rem', margin: 0, fontWeight: 500, letterSpacing: '0.02em', color: 'var(--text-primary)' }}>
          AMAZON CONNECT <span style={{ color: 'var(--text-secondary)', padding: '0 0.5rem' }}>|</span> SRE DASHBOARD
        </h1>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>

        {/* Demo / Live Toggle — replaced with a badge when locked to a single mode */}
        {modeLocked ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'linear-gradient(135deg, rgba(251,191,36,0.15), rgba(245,158,11,0.08))',
            borderRadius: '20px',
            padding: '0.3rem 0.85rem',
            border: '1px solid rgba(251,191,36,0.3)',
          }}>
            <span style={{
              display: 'inline-block',
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: '#fbbf24',
              boxShadow: '0 0 6px rgba(251,191,36,0.6)',
            }} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', color: '#fbbf24' }}>
              DEMO MODE
            </span>
          </div>
        ) : liveModeLocked ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'linear-gradient(135deg, rgba(34,197,94,0.15), rgba(16,185,129,0.08))',
            borderRadius: '20px',
            padding: '0.3rem 0.85rem',
            border: '1px solid rgba(34,197,94,0.3)',
          }}>
            <span style={{
              display: 'inline-block',
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: '#22c55e',
              boxShadow: '0 0 6px rgba(34,197,94,0.6)',
              animation: 'pulse 1.5s infinite',
            }} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', color: '#22c55e' }}>
              LIVE MODE
            </span>
          </div>
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '20px',
            padding: '3px',
            border: '1px solid var(--border-glass)',
            gap: '2px'
          }}>
            <button
              id="mode-demo-btn"
              onClick={() => handleModeToggle('demo')}
              style={{
                padding: '0.3rem 0.85rem',
                borderRadius: '16px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 600,
                letterSpacing: '0.05em',
                transition: 'all 0.2s',
                background: mode === 'demo'
                  ? 'linear-gradient(135deg, rgba(251,191,36,0.25), rgba(245,158,11,0.15))'
                  : 'transparent',
                color: mode === 'demo' ? '#fbbf24' : 'var(--text-secondary)',
                boxShadow: mode === 'demo' ? '0 0 10px rgba(251,191,36,0.2)' : 'none',
              }}
            >
              DEMO
            </button>
            <button
              id="mode-live-btn"
              onClick={() => handleModeToggle('live')}
              style={{
                padding: '0.3rem 0.85rem',
                borderRadius: '16px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 600,
                letterSpacing: '0.05em',
                transition: 'all 0.2s',
                background: mode === 'live'
                  ? 'linear-gradient(135deg, rgba(34,197,94,0.25), rgba(16,185,129,0.15))'
                  : 'transparent',
                color: mode === 'live' ? '#22c55e' : 'var(--text-secondary)',
                boxShadow: mode === 'live' ? '0 0 10px rgba(34,197,94,0.2)' : 'none',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              {mode === 'live' ? (
                <span style={{
                  display: 'inline-block',
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: '#22c55e',
                  boxShadow: '0 0 6px #22c55e',
                  animation: 'pulse 1.5s infinite'
                }} />
              ) : (
                <span style={{
                  display: 'inline-block',
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: 'var(--text-secondary)',
                  opacity: 0.4
                }} />
              )}
              LIVE
            </button>
          </div>
        )}

        {/* Instance Selector — only when Live */}
        {mode === 'live' && (
          <div style={{ position: 'relative' }}>
            <button
              id="instance-selector-btn"
              onClick={() => setDropdownOpen(o => !o)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border-glass)',
                borderRadius: '8px',
                padding: '0.4rem 0.85rem',
                cursor: 'pointer',
                color: 'var(--text-primary)',
                fontSize: '0.8rem',
                fontWeight: 500,
                minWidth: '180px',
                justifyContent: 'space-between'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {activeInstance
                  ? <Wifi size={14} color="#22c55e" />
                  : <WifiOff size={14} color="var(--text-secondary)" />
                }
                <span style={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {loadingInstances ? 'Loading...' : instanceLabel}
                </span>
              </div>
              <ChevronDown size={14} style={{ transition: 'transform 0.2s', transform: dropdownOpen ? 'rotate(180deg)' : 'none' }} />
            </button>

            {dropdownOpen && (
              <div style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                right: 0,
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-glass)',
                borderRadius: '10px',
                minWidth: '240px',
                zIndex: 100,
                overflow: 'hidden',
                boxShadow: '0 8px 32px rgba(0,0,0,0.4)'
              }}>
                {/* All Instances option */}
                <button
                  id="instance-all-btn"
                  onClick={handleClearInstance}
                  style={{
                    width: '100%',
                    padding: '0.65rem 1rem',
                    textAlign: 'left',
                    background: !activeInstance ? 'rgba(255,255,255,0.07)' : 'transparent',
                    border: 'none',
                    borderBottom: '1px solid var(--border-glass)',
                    color: 'var(--text-primary)',
                    cursor: 'pointer',
                    fontSize: '0.82rem',
                    fontWeight: !activeInstance ? 600 : 400,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}
                >
                  <WifiOff size={13} color="var(--text-secondary)" />
                  All Instances (Overview)
                </button>

                {/* Per-instance options */}
                {instances.length === 0 && !loadingInstances && (
                  <div style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    No instances found — check IAM permissions
                  </div>
                )}
                {instances.map((inst) => (
                  <button
                    key={inst.instanceId}
                    id={`instance-${inst.instanceId}-btn`}
                    onClick={() => handleSelectInstance(inst)}
                    style={{
                      width: '100%',
                      padding: '0.65rem 1rem',
                      textAlign: 'left',
                      background: activeInstance?.instanceId === inst.instanceId ? 'rgba(34,197,94,0.08)' : 'transparent',
                      border: 'none',
                      borderBottom: '1px solid var(--border-glass)',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      fontSize: '0.82rem'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                      <span style={{
                        display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
                        background: inst.instanceStatus === 'ACTIVE' ? '#22c55e' : '#fbbf24'
                      }} />
                      <span style={{ fontWeight: 600 }}>{inst.instanceAlias || 'Unnamed'}</span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.73rem', paddingLeft: '1.1rem' }}>
                      {inst.instanceId.substring(0, 8)}... · {inst.region}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Bell Notification */}
        <div 
          onClick={() => navigate('/incidents')}
          style={{ position: 'relative', cursor: 'pointer' }}
          title="View Incidents"
        >
          <Bell size={20} color="var(--text-secondary)" />
          <div style={{
            position: 'absolute',
            top: -2,
            right: -2,
            width: 8,
            height: 8,
            background: 'var(--status-critical)',
            borderRadius: '50%'
          }}></div>
        </div>

        {/* SRE Service Agent Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(255,255,255,0.05)', padding: '0.5rem 1rem', borderRadius: '20px', border: '1px solid var(--border-glass)' }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, rgba(34,197,94,0.2), rgba(6,182,212,0.2))',
            border: '1px solid rgba(34,197,94,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.7rem',
            fontWeight: 700,
            color: 'var(--accent-cyan)',
            letterSpacing: '0.02em'
          }}>
            AI
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>SRE Agent</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--status-ok)', boxShadow: '0 0 4px var(--status-ok)' }}></div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Active &middot; us-west-2</span>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; box-shadow: 0 0 6px #22c55e; }
          50% { opacity: 0.5; box-shadow: 0 0 12px #22c55e; }
        }
      `}</style>
    </div>
  );
};

export default Header;

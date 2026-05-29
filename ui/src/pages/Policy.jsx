import { useState, useEffect } from 'react';
import { ShieldAlert, Info } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const Toggle = ({ enabled, onChange }) => (
  <div
    onClick={onChange}
    style={{
      width: '44px', height: '26px', borderRadius: '13px',
      background: enabled ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)',
      display: 'flex', alignItems: 'center', cursor: 'pointer',
      padding: '3px', transition: 'background 0.2s', flexShrink: 0,
    }}
  >
    <div style={{
      width: '20px', height: '20px', borderRadius: '50%', background: 'white',
      transform: `translateX(${enabled ? '18px' : '0px'})`,
      transition: 'transform 0.2s',
    }} />
  </div>
);

const RISK_COLORS = {
  High:   { bg: 'rgba(239,68,68,0.12)',   color: 'var(--status-critical)' },
  Medium: { bg: 'rgba(234,179,8,0.12)',   color: 'var(--status-warn)' },
  Low:    { bg: 'rgba(0,255,128,0.10)',   color: 'var(--status-ok)' },
};

const Policy = () => {
  const { mode } = useAppContext();
  const [policies, setPolicies] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/policy?mode=${mode}`)
      .then(res => res.json())
      .then(data => {
        setPolicies(data);
        if (data.length > 0) setSelected(data[0]);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch policies", err);
        setLoading(false);
      });
  }, [mode]);

  const togglePolicy = async (idx) => {
    const updated = policies.map((p, i) => i === idx ? { ...p, enabled: !p.enabled } : p);
    setPolicies(updated);
    // Keep selected in sync
    if (selected && (selected.policyId || selected.id) === (updated[idx].policyId || updated[idx].id)) {
      setSelected(updated[idx]);
    }
    try {
      await fetch(`/api/policy?mode=${mode}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated),
      });
    } catch {
      // Revert on failure
      setPolicies(policies);
    }
  };

  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <ShieldAlert size={24} color="var(--accent-cyan)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Policy Management</h2>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
        Operational guardrails and safety limits for the Agent Swarm.
      </p>

      {loading ? (
        <div style={{ color: 'var(--text-secondary)' }}>Loading policies...</div>
      ) : policies.length === 0 ? (
        <div style={{ color: 'var(--text-secondary)' }}>No policies defined.</div>
      ) : (
        <div style={{ display: 'flex', gap: '1.5rem', flex: 1, minHeight: 0 }}>
          {/* List pane */}
          <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto', gap: '0.5rem' }}>
            {policies.map((policy, idx) => {
              const isSelected = selected?.policyId === policy.policyId || selected?.id === policy.id;
              const name = policy.policyName || policy.name || 'Unnamed Policy';
              return (
                <div
                  key={policy.policyId || idx}
                  onClick={() => setSelected(policy)}
                  style={{
                    padding: '0.85rem 1rem', borderRadius: '8px', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem',
                    background: isSelected ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                    border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-glass)'}`,
                    transition: 'all 0.2s',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', minWidth: 0 }}>
                    <div style={{
                      width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0,
                      background: policy.enabled ? 'var(--status-ok)' : 'rgba(255,255,255,0.2)',
                    }} />
                    <span style={{
                      fontWeight: 500, fontSize: '0.88rem',
                      color: isSelected ? 'white' : 'var(--text-secondary)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>{name}</span>
                  </div>
                  <Toggle enabled={!!policy.enabled} onChange={(e) => { e.stopPropagation(); togglePolicy(idx); }} />
                </div>
              );
            })}
          </div>

          {/* Detail pane */}
          <div className="glass-panel" style={{ flex: 2, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {selected ? (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                  <div style={{ minWidth: 0 }}>
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                      {selected.policyName || selected.name || 'Unnamed Policy'}
                    </h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                      {selected.policyId || selected.id}
                    </span>
                  </div>
                  <Toggle
                    enabled={!!selected.enabled}
                    onChange={() => {
                      const idx = policies.findIndex(p => (p.policyId || p.id) === (selected.policyId || selected.id));
                      if (idx !== -1) togglePolicy(idx);
                    }}
                  />
                </div>

                <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <Info size={13} /> Description
                  </div>
                  <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.6 }}>{selected.description}</p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>Status</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, fontSize: '0.9rem', color: selected.enabled ? 'var(--status-ok)' : 'var(--text-secondary)' }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: selected.enabled ? 'var(--status-ok)' : 'rgba(255,255,255,0.2)' }} />
                      {selected.enabled ? 'Enforced' : 'Disabled'}
                    </div>
                  </div>
                  {selected.riskLevel && (
                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>Risk Level</div>
                      <span style={{
                        fontSize: '0.8rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px',
                        ...(RISK_COLORS[selected.riskLevel] || { bg: 'rgba(255,255,255,0.08)', color: 'var(--text-secondary)' }),
                      }}>{selected.riskLevel}</span>
                    </div>
                  )}
                  {selected.scope && (
                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid var(--border-glass)', gridColumn: selected.riskLevel ? 'auto' : 'span 2' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>Scope</div>
                      <div style={{ fontSize: '0.88rem' }}>{selected.scope}</div>
                    </div>
                  )}
                </div>

                {selected.conditions && (
                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Conditions</div>
                    <pre style={{ margin: 0, fontSize: '0.8rem', color: 'var(--accent-cyan)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {typeof selected.conditions === 'string' ? selected.conditions : JSON.stringify(selected.conditions, null, 2)}
                    </pre>
                  </div>
                )}
              </>
            ) : (
              <div style={{ color: 'var(--text-secondary)', padding: '1rem' }}>Select a policy to view details.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Policy;

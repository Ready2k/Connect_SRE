import { useState, useEffect } from 'react';
import { ShieldAlert, Info } from 'lucide-react';

const Policy = () => {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/policy')
      .then(res => res.json())
      .then(data => {
        setPolicies(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch policies", err);
        setLoading(false);
      });
  }, []);

  const togglePolicy = (index) => {
    const newPolicies = [...policies];
    newPolicies[index].enabled = !newPolicies[index].enabled;
    setPolicies(newPolicies);
    // In a fully wired app, this would PATCH to the backend.
  };

  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <ShieldAlert size={24} color="var(--accent-cyan)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Policy Management</h2>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '2rem' }}>
        Configure operational guardrails and safety limits for the ADK Agent Swarm.
      </p>

      {loading ? (
        <div style={{ color: 'var(--text-secondary)' }}>Loading policies...</div>
      ) : policies.length === 0 ? (
        <div style={{ color: 'var(--text-secondary)' }}>No policies defined in the DynamoDB table.</div>
      ) : (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {policies.map((policy, idx) => (
            <div key={policy.id || idx} className="glass-panel" style={{ display: 'flex', alignItems: 'flex-start', gap: '1.5rem' }}>
              <div 
                onClick={() => togglePolicy(idx)}
                style={{ 
                  width: '40px', height: '24px', borderRadius: '12px', 
                  background: policy.enabled ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)',
                  display: 'flex', alignItems: 'center', cursor: 'pointer',
                  padding: '2px', transition: 'background 0.2s', flexShrink: 0
                }}
              >
                <div style={{ 
                  width: '20px', height: '20px', borderRadius: '50%', background: 'white',
                  transform: `translateX(${policy.enabled ? '16px' : '0px'})`,
                  transition: 'transform 0.2s'
                }} />
              </div>
              
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <h3 style={{ fontSize: '1.1rem', margin: 0, fontWeight: 600 }}>{policy.name}</h3>
                  <Info size={14} color="var(--text-secondary)" />
                </div>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {policy.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Policy;

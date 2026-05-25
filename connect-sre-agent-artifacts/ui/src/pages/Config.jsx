import React, { useState } from 'react';
import { Settings, Shield, Cpu } from 'lucide-react';

const Config = () => {
  const [agentMode, setAgentMode] = useState('recommend_only');
  const [primaryModel, setPrimaryModel] = useState('gemini-1.5-pro');

  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ fontSize: '1.4rem', fontWeight: 600, marginBottom: '1.5rem' }}>Agent Configuration</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Agent Modes */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-cyan)' }}>
            <Shield size={20} />
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Operational Mode</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Determine the autonomy level of the SRE Agent.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1rem', border: `1px solid ${agentMode === 'observe_only' ? 'var(--accent-cyan)' : 'var(--border-glass)'}`, borderRadius: '8px', cursor: 'pointer', background: agentMode === 'observe_only' ? 'rgba(255,255,255,0.05)' : 'transparent' }}>
              <input type="radio" name="mode" value="observe_only" checked={agentMode === 'observe_only'} onChange={(e) => setAgentMode(e.target.value)} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Observe Only</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Agent ingests telemetry but generates no recommendations.</div>
              </div>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1rem', border: `1px solid ${agentMode === 'recommend_only' ? 'var(--accent-cyan)' : 'var(--border-glass)'}`, borderRadius: '8px', cursor: 'pointer', background: agentMode === 'recommend_only' ? 'rgba(255,255,255,0.05)' : 'transparent' }}>
              <input type="radio" name="mode" value="recommend_only" checked={agentMode === 'recommend_only'} onChange={(e) => setAgentMode(e.target.value)} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Recommend Only (Current)</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Agent proposes remediations requiring human approval.</div>
              </div>
            </label>
          </div>
        </div>

        {/* Model Routing */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-blue)' }}>
            <Cpu size={20} />
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Model Routing</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Configure the LLM provider mapping for the ADK deterministic policy engine.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 600 }}>Primary Model</label>
              <select 
                value={primaryModel}
                onChange={(e) => setPrimaryModel(e.target.value)}
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-glass)', color: 'white' }}
              >
                <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                <option value="claude-3-opus">Claude 3 Opus (Bedrock)</option>
              </select>
            </div>
            
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 600 }}>Fallback Model</label>
              <select 
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-glass)', color: 'white' }}
              >
                <option>Claude 3 Sonnet (Bedrock)</option>
                <option>Gemini 1.5 Flash</option>
              </select>
            </div>

            <button style={{ marginTop: 'auto', padding: '0.75rem', background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}>
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Config;

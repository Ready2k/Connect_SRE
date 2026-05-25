import { useState, useEffect } from 'react';
import { Shield, Cpu, Info } from 'lucide-react';

const GEMINI_MODELS = [
  { value: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash (recommended)' },
  { value: 'gemini-2.5-pro',   label: 'Gemini 2.5 Pro' },
  { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
];

const BEDROCK_MODELS = [
  { value: 'us.anthropic.claude-sonnet-4-6', label: 'Claude Sonnet 4.6 — Bedrock (recommended)' },
  { value: 'us.anthropic.claude-opus-4-7',   label: 'Claude Opus 4.7 — Bedrock' },
  { value: 'anthropic.claude-haiku-4-5',     label: 'Claude Haiku 4.5 — Bedrock (fastest)' },
];

const ALL_MODELS = [...GEMINI_MODELS, ...BEDROCK_MODELS];

const isBedrockModel = (id) => id && (id.startsWith('anthropic.') || id.includes('.anthropic.'));

const Config = () => {
  const [agentMode, setAgentMode]       = useState('recommend_only');
  const [primaryModel, setPrimaryModel] = useState('');
  const [fallbackModel, setFallbackModel] = useState('');
  const [activeModel, setActiveModel]   = useState('');  // what's actually running
  const [saveStatus, setSaveStatus]     = useState(null);
  const [loading, setLoading]           = useState(true);

  useEffect(() => {
    fetch('/api/models/config')
      .then(res => res.json())
      .then(data => {
        setAgentMode(data.agentMode || 'recommend_only');
        setPrimaryModel(data.primaryModel || 'gemini-3.5-flash');
        setFallbackModel(data.fallbackModel || '');
        setActiveModel(data.primaryModel || '');
      })
      .catch(() => {
        setPrimaryModel('gemini-3.5-flash');
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = () => {
    setSaveStatus('saving');
    fetch('/api/models/config', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agentMode, primaryModel, fallbackModel }),
    })
      .then(res => res.json())
      .then(() => setSaveStatus('saved'))
      .catch(() => setSaveStatus('error'))
      .finally(() => setTimeout(() => setSaveStatus(null), 3000));
  };

  const activeProvider = isBedrockModel(activeModel) ? 'AWS Bedrock' : 'Google ADK';
  const activeProviderColor = isBedrockModel(activeModel) ? 'var(--accent-orange, #f59e0b)' : 'var(--accent-blue)';

  const modelLabel = (id) => ALL_MODELS.find(m => m.value === id)?.label ?? id;

  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ fontSize: '1.4rem', fontWeight: 600, marginBottom: '1.5rem' }}>Agent Configuration</h2>

      {/* Active provider banner */}
      {!loading && activeModel && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem', marginBottom: '1.5rem', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: `1px solid ${activeProviderColor}` }}>
          <Info size={16} color={activeProviderColor} />
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Active runtime provider: <strong style={{ color: activeProviderColor }}>{activeProvider}</strong>
            {' '}— <span style={{ color: 'var(--text-primary)' }}>{modelLabel(activeModel)}</span>
          </span>
          <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Provider set via MODEL_PROVIDER env var at container start
          </span>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>

        {/* Operational Mode */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-cyan)' }}>
            <Shield size={20} />
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Operational Mode</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Determine the autonomy level of the SRE Agent.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {[
              { value: 'observe_only',   label: 'Observe Only',         desc: 'Agent ingests telemetry but generates no recommendations.' },
              { value: 'recommend_only', label: 'Recommend Only',       desc: 'Agent proposes remediations requiring human approval.' },
            ].map(opt => (
              <label key={opt.value} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1rem', border: `1px solid ${agentMode === opt.value ? 'var(--accent-cyan)' : 'var(--border-glass)'}`, borderRadius: '8px', cursor: 'pointer', background: agentMode === opt.value ? 'rgba(255,255,255,0.05)' : 'transparent' }}>
                <input type="radio" name="mode" value={opt.value} checked={agentMode === opt.value} onChange={e => setAgentMode(e.target.value)} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{opt.label}{opt.value === 'recommend_only' ? ' (Current)' : ''}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{opt.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Model Routing */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-blue)' }}>
            <Cpu size={20} />
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Model Routing</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Configure the preferred model for incident investigations. Changes are saved to the runtime config and take effect on next investigation.
          </p>

          {loading ? (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Loading current config…</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 600 }}>Primary Model</label>
                <select
                  value={primaryModel}
                  onChange={e => setPrimaryModel(e.target.value)}
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-glass)', color: 'white' }}
                >
                  <optgroup label="Google ADK">
                    {GEMINI_MODELS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                  </optgroup>
                  <optgroup label="AWS Bedrock">
                    {BEDROCK_MODELS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                  </optgroup>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 600 }}>Fallback Model</label>
                <select
                  value={fallbackModel}
                  onChange={e => setFallbackModel(e.target.value)}
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-glass)', color: 'white' }}
                >
                  <option value="">— None —</option>
                  <optgroup label="Google ADK">
                    {GEMINI_MODELS.filter(m => m.value !== primaryModel).map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                  </optgroup>
                  <optgroup label="AWS Bedrock">
                    {BEDROCK_MODELS.filter(m => m.value !== primaryModel).map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                  </optgroup>
                </select>
              </div>

              <div style={{ padding: '0.65rem 0.85rem', borderRadius: '6px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                <strong style={{ color: 'var(--text-primary)' }}>Note:</strong> The active inference provider (Google ADK or AWS Bedrock) is determined by the <code>MODEL_PROVIDER</code> env var set when the container starts. To switch provider, restart with <code>./start.sh</code>.
              </div>

              <button
                onClick={handleSave}
                disabled={saveStatus === 'saving'}
                style={{ marginTop: 'auto', padding: '0.75rem', background: saveStatus === 'error' ? 'var(--status-critical)' : 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: saveStatus === 'saving' ? 'not-allowed' : 'pointer', opacity: saveStatus === 'saving' ? 0.7 : 1 }}
              >
                {saveStatus === 'saving' ? 'Saving…' : saveStatus === 'saved' ? 'Saved!' : saveStatus === 'error' ? 'Error — retry' : 'Save Configuration'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Config;

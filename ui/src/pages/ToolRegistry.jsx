import { useState, useEffect } from 'react';
import { Wrench, CheckCircle, Lock, ShieldOff, Info, Tag, Cpu } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const PERM_STYLE = {
  'Read-Only':        { bg: 'rgba(0,255,128,0.1)',  color: 'var(--status-ok)',       icon: <CheckCircle size={12} /> },
  'Requires Approval':{ bg: 'rgba(255,170,0,0.1)',  color: 'var(--status-warn)',     icon: <CheckCircle size={12} /> },
  'Blocked (Policy)': { bg: 'rgba(255,50,50,0.1)',  color: 'var(--status-critical)', icon: <Lock size={12} /> },
  'Write':            { bg: 'rgba(0,180,255,0.1)',  color: 'var(--accent-cyan)',     icon: <CheckCircle size={12} /> },
  'Unknown':          { bg: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)', icon: <Info size={12} /> },
};

function PermBadge({ permission }) {
  const s = PERM_STYLE[permission] || PERM_STYLE['Unknown'];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
      padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600,
      background: s.bg, color: s.color,
    }}>
      {s.icon}{permission || 'Unknown'}
    </span>
  );
}

const ToolRegistry = () => {
  const { mode } = useAppContext();
  const [tools, setTools] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    fetch(`/api/tools?mode=${mode}`)
      .then(res => res.json())
      .then(data => {
        setTools(data);
        if (data.length > 0) setSelected(data[0]);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch tools", err);
        setLoading(false);
      });
  }, [mode]);

  useEffect(() => {
    setNotes(selected?.notes || '');
  }, [selected?.toolId]);

  const toggleStatus = async (tool) => {
    const newStatus = tool.status === 'Active' ? 'Inactive' : 'Active';
    const updated = tools.map(t => (t.toolId || t.id) === (tool.toolId || tool.id) ? { ...t, status: newStatus } : t);
    setTools(updated);
    setSelected(prev => prev && (prev.toolId || prev.id) === (tool.toolId || tool.id) ? { ...prev, status: newStatus } : prev);
    try {
      await fetch(`/api/tools/${tool.toolId || tool.id}?mode=${mode}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
    } catch {
      setTools(tools);
    }
  };

  const saveNotes = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await fetch(`/api/tools/${selected.toolId || selected.id}?mode=${mode}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes }),
      });
      setTools(prev => prev.map(t => (t.toolId || t.id) === (selected.toolId || selected.id) ? { ...t, notes } : t));
      setSelected(prev => prev ? { ...prev, notes } : prev);
    } catch { /* silent */ }
    setSaving(false);
  };

  if (loading) return <div style={{ padding: '2rem', color: 'var(--text-secondary)' }}>Loading tools...</div>;

  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <Wrench size={24} color="var(--accent-cyan)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Tool Registry</h2>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
        Catalog of actions and queries available to the Agent Swarm. Click a tool to view details, configure, or toggle activation.
      </p>

      {tools.length === 0 ? (
        <div style={{ color: 'var(--text-secondary)' }}>No tools registered in the DynamoDB table.</div>
      ) : (
        <div style={{ display: 'flex', gap: '1.5rem', flex: 1, minHeight: 0 }}>
          {/* List pane */}
          <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto', gap: '0.4rem' }}>
            {tools.map((tool) => {
              const id = tool.toolId || tool.id;
              const isSelected = (selected?.toolId || selected?.id) === id;
              const isActive = tool.status !== 'Inactive';
              return (
                <div
                  key={id}
                  onClick={() => setSelected(tool)}
                  style={{
                    padding: '0.75rem 1rem', borderRadius: '8px', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem',
                    background: isSelected ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                    border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-glass)'}`,
                    transition: 'all 0.2s', opacity: isActive ? 1 : 0.5,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: 0 }}>
                    <Wrench size={14} color={isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)'} style={{ flexShrink: 0 }} />
                    <span style={{
                      fontWeight: 500, fontSize: '0.85rem', fontFamily: 'monospace',
                      color: isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>{id}</span>
                  </div>
                  <span style={{
                    fontSize: '0.7rem', fontWeight: 700, flexShrink: 0, padding: '0.1rem 0.4rem',
                    borderRadius: '3px',
                    background: isActive ? 'rgba(0,255,128,0.1)' : 'rgba(255,255,255,0.06)',
                    color: isActive ? 'var(--status-ok)' : 'var(--text-secondary)',
                  }}>{tool.status || 'Active'}</span>
                </div>
              );
            })}
          </div>

          {/* Detail pane */}
          <div className="glass-panel" style={{ flex: 2, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {selected ? (
              <>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                  <div style={{ minWidth: 0 }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.2rem', fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>
                      {selected.toolId || selected.id}
                    </h3>
                    {selected.category && (
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Tag size={11} />{selected.category}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => toggleStatus(selected)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.4rem',
                      padding: '0.4rem 0.9rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600,
                      background: selected.status === 'Inactive' ? 'rgba(0,255,128,0.1)' : 'rgba(255,50,50,0.1)',
                      color: selected.status === 'Inactive' ? 'var(--status-ok)' : 'var(--status-critical)',
                      border: `1px solid ${selected.status === 'Inactive' ? 'var(--status-ok)' : 'var(--status-critical)'}`,
                    }}
                  >
                    {selected.status === 'Inactive' ? <CheckCircle size={14} /> : <ShieldOff size={14} />}
                    {selected.status === 'Inactive' ? 'Activate' : 'Deactivate'}
                  </button>
                </div>

                {/* Description */}
                <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Description</div>
                  <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.6 }}>{selected.description || '—'}</p>
                </div>

                {/* Meta grid */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>Execution Permission</div>
                    <PermBadge permission={selected.permission} />
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>Status</div>
                    <span style={{
                      fontSize: '0.85rem', fontWeight: 600,
                      color: selected.status !== 'Inactive' ? 'var(--status-ok)' : 'var(--text-secondary)',
                    }}>{selected.status || 'Active'}</span>
                  </div>
                  {selected.assignedAgents && (
                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid var(--border-glass)', gridColumn: 'span 2' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Cpu size={11} /> Assigned Agents
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                        {(Array.isArray(selected.assignedAgents) ? selected.assignedAgents : selected.assignedAgents.split(','))
                          .map(a => a.trim()).filter(Boolean).map(a => (
                            <span key={a} style={{ fontSize: '0.72rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: '3px', background: 'rgba(0,212,255,0.1)', color: 'var(--accent-cyan)', border: '1px solid rgba(0,212,255,0.25)' }}>{a}</span>
                          ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Notes */}
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Operator Notes</div>
                  <textarea
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="Add notes about this tool's behaviour, known issues, or configuration details…"
                    rows={4}
                    style={{ width: '100%', boxSizing: 'border-box', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.2)', color: 'var(--text-primary)', fontSize: '0.85rem', resize: 'vertical', fontFamily: 'inherit' }}
                  />
                  <button
                    onClick={saveNotes}
                    disabled={saving}
                    style={{ marginTop: '0.5rem', padding: '0.35rem 0.85rem', background: 'var(--accent-cyan)', color: 'black', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600, fontSize: '0.82rem', opacity: saving ? 0.6 : 1 }}
                  >{saving ? 'Saving…' : 'Save Notes'}</button>
                </div>
              </>
            ) : (
              <div style={{ color: 'var(--text-secondary)', padding: '1rem' }}>Select a tool to view details.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ToolRegistry;

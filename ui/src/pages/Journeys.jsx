import { useState, useEffect } from 'react';
import { Route, CheckCircle, AlertTriangle, PhoneCall, Plus, Pencil, Trash2, X, Save } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const EMPTY_JOURNEY = { name: '', entryPoint: '', owner: '', sla: '', criticality: 'TIER2', status: 'Healthy', flows: [] };

const CRITICALITY_COLOR = {
  TIER1: { bg: 'rgba(239,68,68,0.12)',   color: 'var(--status-critical)' },
  TIER2: { bg: 'rgba(234,179,8,0.12)',   color: 'var(--status-warn)' },
  TIER3: { bg: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)' },
};

const INPUT_STYLE = {
  width: '100%', boxSizing: 'border-box', padding: '0.5rem 0.7rem',
  borderRadius: '4px', border: '1px solid var(--border-glass)',
  background: 'rgba(0,0,0,0.2)', color: 'var(--text-primary)', fontSize: '0.88rem',
};

function JourneyModal({ journey, onClose, onSave }) {
  const [form, setForm] = useState(journey ? { ...journey } : { ...EMPTY_JOURNEY });
  const [flowInput, setFlowInput] = useState('');

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const addFlow = () => {
    const v = flowInput.trim();
    if (!v) return;
    set('flows', [...(form.flows || []), v]);
    setFlowInput('');
  };
  const removeFlow = (i) => set('flows', form.flows.filter((_, idx) => idx !== i));

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '560px', maxHeight: '85vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{journey ? 'Edit Journey' : 'New Journey'}</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}><X size={18} /></button>
        </div>

        {[
          { label: 'Name', key: 'name', placeholder: 'e.g. Customer Authentication' },
          { label: 'Entry Point', key: 'entryPoint', placeholder: 'e.g. +1-800-555-0199' },
          { label: 'Owner', key: 'owner', placeholder: 'e.g. Security-Ops' },
          { label: 'SLA Target', key: 'sla', placeholder: 'e.g. 99.9%' },
        ].map(({ label, key, placeholder }) => (
          <div key={key}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>{label}</label>
            <input value={form[key] || ''} onChange={e => set(key, e.target.value)} placeholder={placeholder} style={INPUT_STYLE} />
          </div>
        ))}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Criticality</label>
            <select value={form.criticality || 'TIER2'} onChange={e => set('criticality', e.target.value)} style={{ ...INPUT_STYLE }}>
              <option value="TIER1">TIER1 — Critical</option>
              <option value="TIER2">TIER2 — Important</option>
              <option value="TIER3">TIER3 — Standard</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Status</label>
            <select value={form.status || 'Healthy'} onChange={e => set('status', e.target.value)} style={{ ...INPUT_STYLE }}>
              <option value="Healthy">Healthy</option>
              <option value="Degraded">Degraded</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Associated Flows</label>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <input
              value={flowInput}
              onChange={e => setFlowInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addFlow()}
              placeholder="Flow name… (Enter to add)"
              style={{ ...INPUT_STYLE, flex: 1 }}
            />
            <button onClick={addFlow} style={{ padding: '0.5rem 0.75rem', background: 'var(--accent-cyan)', color: 'black', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
              <Plus size={14} />
            </button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {(form.flows || []).map((f, i) => (
              <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', background: 'rgba(255,255,255,0.06)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.78rem' }}>
                {f}
                <button onClick={() => removeFlow(i)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: 0, display: 'flex' }}><X size={11} /></button>
              </span>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', paddingTop: '0.5rem', borderTop: '1px solid var(--border-glass)' }}>
          <button onClick={onClose} style={{ padding: '0.45rem 1rem', background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-glass)', borderRadius: '4px', cursor: 'pointer' }}>Cancel</button>
          <button onClick={() => onSave(form)} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.45rem 1rem', background: 'var(--accent-cyan)', color: 'black', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
            <Save size={14} />{journey ? 'Save Changes' : 'Create Journey'}
          </button>
        </div>
      </div>
    </div>
  );
}

const Journeys = () => {
  const { mode } = useAppContext();
  const [journeys, setJourneys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // null | 'create' | journeyObj (edit)
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    fetch(`/api/journeys?mode=${mode}`)
      .then(res => res.json())
      .then(data => { setJourneys(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [mode]);

  const handleSave = async (form) => {
    const isNew = modal === 'create';
    const journeyId = form.journeyId || `journey-${Date.now()}`;
    const body = { ...form, journeyId };

    if (isNew) {
      await fetch(`/api/journeys?mode=${mode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      setJourneys(prev => [body, ...prev]);
    } else {
      await fetch(`/api/journeys/${journeyId}?mode=${mode}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      setJourneys(prev => prev.map(j => (j.journeyId || j.id) === journeyId ? body : j));
    }
    setModal(null);
  };

  const handleDelete = async (journey) => {
    const id = journey.journeyId || journey.id;
    setDeleting(id);
    await fetch(`/api/journeys/${id}?mode=${mode}`, { method: 'DELETE' });
    setJourneys(prev => prev.filter(j => (j.journeyId || j.id) !== id));
    setDeleting(null);
  };

  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Route size={24} color="var(--accent-cyan)" />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Business Journeys</h2>
        </div>
        <button
          onClick={() => setModal('create')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.45rem 0.9rem', background: 'var(--accent-cyan)', color: 'black', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}
        >
          <Plus size={14} /> New Journey
        </button>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
        High-level abstraction of customer contact paths mapping to underlying Connect flows and resources.
      </p>

      {loading ? (
        <div style={{ color: 'var(--text-secondary)' }}>Loading journeys...</div>
      ) : journeys.length === 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, gap: '1rem', color: 'var(--text-secondary)' }}>
          <Route size={40} />
          <span>No journeys defined yet.</span>
          <button onClick={() => setModal('create')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.5rem 1rem', background: 'var(--accent-cyan)', color: 'black', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
            <Plus size={14} /> Create First Journey
          </button>
        </div>
      ) : (
        <div style={{ overflowY: 'auto', flex: 1 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {journeys.map(journey => {
              const id = journey.journeyId || journey.id;
              const crit = CRITICALITY_COLOR[journey.criticality] || CRITICALITY_COLOR.TIER3;
              return (
                <div key={id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <h3 style={{ fontSize: '1rem', margin: 0, fontWeight: 600 }}>{journey.name || 'Unnamed'}</h3>
                        {journey.criticality && (
                          <span style={{ fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.35rem', borderRadius: '3px', ...crit }}>{journey.criticality}</span>
                        )}
                      </div>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{id}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                      <div style={{ color: journey.status === 'Healthy' ? 'var(--status-ok)' : journey.status === 'Critical' ? 'var(--status-critical)' : 'var(--status-warn)' }}>
                        {journey.status === 'Healthy' ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
                      </div>
                    </div>
                  </div>

                  {journey.entryPoint && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', color: 'var(--text-primary)' }}>
                      <PhoneCall size={14} color="var(--text-secondary)" style={{ flexShrink: 0 }} />
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{journey.entryPoint}</span>
                    </div>
                  )}

                  {(journey.flows || []).length > 0 && (
                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.65rem', borderRadius: '4px', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>Associated Flows</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                        {journey.flows.map(flow => (
                          <span key={flow} style={{ background: 'rgba(255,255,255,0.05)', padding: '0.15rem 0.45rem', borderRadius: '3px', fontSize: '0.7rem' }}>{flow}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '0.75rem', borderTop: '1px solid var(--border-glass)' }}>
                    <div style={{ display: 'flex', gap: '1.5rem' }}>
                      {journey.activeContacts !== undefined && (
                        <div>
                          <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>Active</div>
                          <div style={{ fontSize: '1rem', fontWeight: 600 }}>{journey.activeContacts}</div>
                        </div>
                      )}
                      {journey.sla && (
                        <div>
                          <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>SLA</div>
                          <div style={{ fontSize: '1rem', fontWeight: 600, color: journey.status === 'Healthy' ? 'var(--status-ok)' : 'var(--status-warn)' }}>{journey.sla}</div>
                        </div>
                      )}
                      {journey.owner && (
                        <div>
                          <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>Owner</div>
                          <div style={{ fontSize: '0.78rem', fontWeight: 500 }}>{journey.owner}</div>
                        </div>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button onClick={() => setModal(journey)} style={{ background: 'transparent', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'var(--text-secondary)', padding: '0.3rem 0.5rem', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                        <Pencil size={13} />
                      </button>
                      <button
                        onClick={() => { if (window.confirm(`Delete "${journey.name}"?`)) handleDelete(journey); }}
                        disabled={deleting === id}
                        style={{ background: 'transparent', border: '1px solid var(--status-critical)', borderRadius: '4px', color: 'var(--status-critical)', padding: '0.3rem 0.5rem', cursor: 'pointer', display: 'flex', alignItems: 'center', opacity: deleting === id ? 0.5 : 1 }}>
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {modal !== null && (
        <JourneyModal
          journey={modal === 'create' ? null : modal}
          onClose={() => setModal(null)}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

export default Journeys;

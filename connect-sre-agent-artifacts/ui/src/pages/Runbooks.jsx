import { useState, useEffect } from 'react';
import { BookOpen, FileText } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const Runbooks = () => {
  const { mode } = useAppContext();
  const [runbooks, setRunbooks] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/runbooks?mode=${mode}`)
      .then(res => res.json())
      .then(data => {
        setRunbooks(data);
        if (data.length > 0) setSelected(data[0]);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch runbooks", err);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <BookOpen size={24} color="var(--accent-cyan)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>SOP Runbooks</h2>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
        The Ground Truth Standard Operating Procedures (SOPs) that guide the ADK Agent Swarm's decision engine.
      </p>

      {loading ? (
        <div style={{ color: 'var(--text-secondary)' }}>Loading runbooks from S3...</div>
      ) : runbooks.length === 0 ? (
        <div style={{ color: 'var(--text-secondary)' }}>No runbooks found in the S3 bucket.</div>
      ) : (
        <div style={{ display: 'flex', gap: '1.5rem', flex: 1, minHeight: 0 }}>
          {/* List Pane */}
          <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto', gap: '0.5rem' }}>
            {runbooks.map(rb => (
              <div 
                key={rb.id} 
                onClick={() => setSelected(rb)}
                style={{
                  padding: '1rem',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  background: selected?.id === rb.id ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${selected?.id === rb.id ? 'var(--accent-cyan)' : 'var(--border-glass)'}`,
                  transition: 'all 0.2s'
                }}
              >
                <FileText size={16} color={selected?.id === rb.id ? 'var(--accent-cyan)' : 'var(--text-secondary)'} />
                <span style={{ fontWeight: 500, fontSize: '0.9rem', color: selected?.id === rb.id ? 'white' : 'var(--text-secondary)' }}>
                  {rb.title}
                </span>
              </div>
            ))}
          </div>

          {/* Content Pane */}
          <div className="glass-panel" style={{ flex: 2, overflowY: 'auto' }}>
            {selected ? (
              <pre style={{ 
                fontFamily: 'monospace', 
                fontSize: '0.85rem', 
                color: 'var(--text-primary)',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.6
              }}>
                {selected.content}
              </pre>
            ) : (
              <div style={{ color: 'var(--text-secondary)', padding: '1rem' }}>Select a runbook to view its contents.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Runbooks;

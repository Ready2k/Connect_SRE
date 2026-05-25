import { useState, useEffect } from 'react';
import { Route, CheckCircle, AlertTriangle, PhoneCall } from 'lucide-react';

const Journeys = () => {
  const [journeys, setJourneys] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/journeys')
      .then(res => res.json())
      .then(data => {
        // If data is empty from DynamoDB, maybe default to some placeholder or empty state
        setJourneys(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch journeys", err);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <Route size={24} color="var(--accent-cyan)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Business Journeys</h2>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '2rem' }}>
        High-level abstraction of customer contact paths mapping to underlying Connect flows and resources.
      </p>

      {loading ? (
        <div style={{ color: 'var(--text-secondary)' }}>Loading journeys...</div>
      ) : journeys.length === 0 ? (
        <div style={{ color: 'var(--text-secondary)' }}>No journeys found. Add data to the DynamoDB table.</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {journeys.map(journey => (
            <div key={journey.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', margin: '0 0 0.25rem 0' }}>{journey.name || 'Unnamed'}</h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>ID: {journey.id || journey.journeyId}</span>
                </div>
                <div style={{ color: journey.status === 'Healthy' ? 'var(--status-ok)' : 'var(--status-warn)' }}>
                  {journey.status === 'Healthy' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                <PhoneCall size={16} color="var(--text-secondary)" /> {journey.entryPoint || 'N/A'}
              </div>

              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Associated Flows</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {(journey.flows || []).map(flow => (
                    <span key={flow} style={{ background: 'rgba(255,255,255,0.05)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem' }}>
                      {flow}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-glass)' }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Active Contacts</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{journey.activeContacts || 0}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>SLA Attainment</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 600, color: journey.status === 'Healthy' ? 'var(--status-ok)' : 'var(--status-warn)' }}>{journey.sla || 'N/A'}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Journeys;

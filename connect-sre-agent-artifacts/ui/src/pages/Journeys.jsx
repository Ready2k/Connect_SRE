import { useState } from 'react';
import { Route, CheckCircle, AlertTriangle, PhoneCall } from 'lucide-react';

const mockJourneys = [
  { id: 'J-001', name: 'Retail Sales Inbound', entryPoint: '+1 (800) 555-0199', flows: ['Main_Sales_Flow', 'Sales_Queue_Router'], status: 'Healthy', activeContacts: 142, sla: '99.9%' },
  { id: 'J-002', name: 'Fraud Verification', entryPoint: '+1 (800) 555-0200', flows: ['Fraud_Auth_Flow', 'Lex_Verification_Bot'], status: 'Degraded', activeContacts: 58, sla: '82.4%' },
  { id: 'J-003', name: 'General Support', entryPoint: '+1 (800) 555-0100', flows: ['Support_Triage', 'Support_Queue_Router'], status: 'Healthy', activeContacts: 310, sla: '98.5%' }
];

const Journeys = () => {
  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <Route size={24} color="var(--accent-cyan)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Business Journeys</h2>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '2rem' }}>
        High-level abstraction of customer contact paths mapping to underlying Connect flows and resources.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {mockJourneys.map(journey => (
          <div key={journey.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', margin: '0 0 0.25rem 0' }}>{journey.name}</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>ID: {journey.id}</span>
              </div>
              <div style={{ color: journey.status === 'Healthy' ? 'var(--status-ok)' : 'var(--status-warn)' }}>
                {journey.status === 'Healthy' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
              <PhoneCall size={16} color="var(--text-secondary)" /> {journey.entryPoint}
            </div>

            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border-glass)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Associated Flows</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {journey.flows.map(flow => (
                  <span key={flow} style={{ background: 'rgba(255,255,255,0.05)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem' }}>
                    {flow}
                  </span>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-glass)' }}>
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Active Contacts</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{journey.activeContacts}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>SLA Attainment</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: journey.status === 'Healthy' ? 'var(--status-ok)' : 'var(--status-warn)' }}>{journey.sla}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Journeys;

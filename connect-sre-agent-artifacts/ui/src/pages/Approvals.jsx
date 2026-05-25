import React from 'react';
import PendingApprovals from '../components/widgets/PendingApprovals';

const Approvals = () => {
  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%' }}>
      <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Action Approvals</h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Review and approve automated remediation steps proposed by the ADK agent.</p>
      
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <PendingApprovals />
      </div>
    </div>
  );
};

export default Approvals;

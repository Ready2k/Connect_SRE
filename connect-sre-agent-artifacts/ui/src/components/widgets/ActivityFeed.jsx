import React from 'react';
import { AlertTriangle } from 'lucide-react';

const ActivityFeed = () => {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ color: 'var(--status-critical)', display: 'flex', alignItems: 'center' }}>
          <AlertTriangle size={18} />
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          <span style={{ color: 'var(--text-primary)', fontWeight: 600, marginRight: '0.5rem' }}>Activity Feed</span> 
          | System degradation detected in EU-West-1 connection layer. Recommended rollback initiated.
        </div>
      </div>
    </>
  );
};

export default ActivityFeed;

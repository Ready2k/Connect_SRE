import { AlertTriangle, Info } from 'lucide-react';

const ActivityFeed = ({ data }) => {
  if (!data || data.length === 0) return null;

  // Get the most recent activity item
  const latest = data[0];
  const isCritical = latest.severity === 'SEV1' || latest.severity === 'SEV2';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '100%' }}>
      <div style={{ color: isCritical ? 'var(--status-critical)' : 'var(--accent-cyan)', display: 'flex', alignItems: 'center' }}>
        {isCritical ? <AlertTriangle size={18} /> : <Info size={18} />}
      </div>
      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        <span style={{ color: 'var(--text-primary)', fontWeight: 600, marginRight: '0.5rem' }}>Activity Feed</span> 
        | [{latest.severity}] {latest.id} - {latest.title}
      </div>
    </div>
  );
};

export default ActivityFeed;

const SREOverview = ({ data }) => {
  if (!data) return null;

  return (
    <>
      <h3 className="widget-title">SRE Overview</h3>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', paddingBottom: '0.5rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '4px' }}>Status</div>
          <div style={{ 
            color: data.status === 'ACTIVE' ? 'var(--status-ok)' : 'var(--status-critical)', 
            fontSize: '1.5rem', 
            fontWeight: 700, 
            letterSpacing: '0.05em' 
          }}>
            {data.status}
          </div>
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '4px' }}>Latency</div>
          <div style={{ color: 'var(--text-primary)', fontSize: '1.8rem', fontWeight: 600 }}>{data.latency}</div>
        </div>
        <div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '4px' }}>Throughput</div>
          <div style={{ color: 'var(--text-primary)', fontSize: '1.8rem', fontWeight: 600 }}>{data.throughput}</div>
        </div>
      </div>
    </>
  );
};

export default SREOverview;

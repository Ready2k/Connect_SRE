
const SREOverview = () => {
  return (
    <>
      <h3 className="widget-title">SRE Overview</h3>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', paddingBottom: '0.5rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '4px' }}>Status</div>
          <div style={{ color: 'var(--status-ok)', fontSize: '1.5rem', fontWeight: 700, letterSpacing: '0.05em' }}>ACTIVE</div>
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '4px' }}>Latency</div>
          <div style={{ color: 'var(--text-primary)', fontSize: '1.8rem', fontWeight: 600 }}>42ms</div>
        </div>
        <div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '4px' }}>Throughput</div>
          <div style={{ color: 'var(--text-primary)', fontSize: '1.8rem', fontWeight: 600 }}>1.8k TPS</div>
        </div>
      </div>
    </>
  );
};

export default SREOverview;

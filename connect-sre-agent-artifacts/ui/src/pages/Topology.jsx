import GlobalTopology from '../components/widgets/GlobalTopology';

const Topology = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Connect Topology View</h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <select style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid var(--border-glass)', padding: '0.5rem', borderRadius: '4px' }}>
            <option>All Regions</option>
            <option>us-east-1</option>
            <option>us-west-2</option>
            <option>eu-west-1</option>
          </select>
          <select style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid var(--border-glass)', padding: '0.5rem', borderRadius: '4px' }}>
            <option>All Components</option>
            <option>Contact Flows</option>
            <option>Lex Bots</option>
            <option>Queues</option>
            <option>Lambdas</option>
          </select>
        </div>
      </div>
      
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <GlobalTopology />
      </div>
    </div>
  );
};

export default Topology;

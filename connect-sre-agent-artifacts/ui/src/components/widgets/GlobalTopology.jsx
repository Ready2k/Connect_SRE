import ReactFlow, { Background } from 'reactflow';
import 'reactflow/dist/style.css';

const initialNodes = [
  { id: '1', position: { x: 50, y: 50 }, data: { label: 'us-east-1' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '50%', width: 60, height: 60, display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: '0.7rem' } },
  { id: '2', position: { x: 250, y: 50 }, data: { label: 'eu-west-1' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '50%', width: 60, height: 60, display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: '0.7rem' } },
  { id: '3', position: { x: 150, y: 150 }, data: { label: 'Connection' }, style: { background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--status-warn)', borderRadius: '8px', padding: '10px', fontSize: '0.7rem' } },
  { id: '4', position: { x: 50, y: 250 }, data: { label: 'us-west-2' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--accent-blue)', borderRadius: '50%', width: 60, height: 60, display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: '0.7rem' } },
  { id: '5', position: { x: 250, y: 250 }, data: { label: 'Endpoints' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-critical)', borderRadius: '50%', width: 60, height: 60, display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: '0.7rem' } },
];

const initialEdges = [
  { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: 'var(--status-ok)' }, label: '13ms', labelStyle: { fill: 'var(--text-primary)', fontSize: 10 } },
  { id: 'e2-3', source: '2', target: '3', animated: true, style: { stroke: 'var(--status-ok)' }, label: '22ms', labelStyle: { fill: 'var(--text-primary)', fontSize: 10 } },
  { id: 'e3-4', source: '3', target: '4', animated: true, style: { stroke: 'var(--status-ok)' }, label: '20ms', labelStyle: { fill: 'var(--text-primary)', fontSize: 10 } },
  { id: 'e3-5', source: '3', target: '5', animated: true, style: { stroke: 'var(--status-critical)' }, label: '120ms', labelStyle: { fill: 'var(--status-critical)', fontSize: 10 } },
];

const GlobalTopology = () => {
  return (
    <>
      <h3 className="widget-title">Global Network Topology</h3>
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '0.5rem' }}>
        Dynamic, interactive graph of interconnected nodes.<br/>
        <span style={{ color: 'var(--status-ok)' }}>●</span> Connect Instances <span style={{ color: 'var(--status-warn)' }}>●</span> CCPs, LEX Bots <span style={{ color: 'var(--status-critical)' }}>●</span> Endpoints
      </div>
      <div style={{ flex: 1, width: '100%', minHeight: '200px', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-glass)' }}>
        <ReactFlow nodes={initialNodes} edges={initialEdges} fitView attributionPosition="bottom-right" nodesDraggable={false} zoomOnScroll={false}>
          <Background color="var(--border-highlight)" gap={16} />
        </ReactFlow>
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem', fontSize: '0.8rem', fontWeight: 600 }}>
        <span style={{ color: 'var(--status-ok)' }}>Connections: 85 OK</span>
        <span style={{ color: 'var(--status-warn)' }}>3 DEGRADED</span>
      </div>
    </>
  );
};

export default GlobalTopology;

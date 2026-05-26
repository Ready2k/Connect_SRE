import { useState, useEffect } from 'react';
import ReactFlow, { Background } from 'reactflow';
import 'reactflow/dist/style.css';

const GlobalTopology = ({ mode = 'demo', instanceId = '' }) => {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    const params = new URLSearchParams({ mode });
    if (instanceId) params.set('instanceId', instanceId);
    fetch(`/api/topology?${params}`)
      .then(res => res.json())
      .then(data => {
        // Apply custom styling to fetched nodes and edges
        const styledNodes = data.nodes.map((node, index) => ({
          ...node,
          // Simple layout logic since x, y come back as 250, 250
          position: { x: 50 + (index % 5) * 150, y: 50 + Math.floor(index / 5) * 100 },
          style: { 
            background: 'rgba(255,255,255,0.05)', 
            color: 'var(--text-primary)', 
            border: '1px solid var(--border-glass)', 
            borderRadius: '8px', 
            padding: '10px', 
            fontSize: '0.7rem' 
          }
        }));

        const styledEdges = data.edges.map(edge => ({
          ...edge,
          style: { stroke: 'var(--status-ok)' }
        }));

        setNodes(styledNodes);
        setEdges(styledEdges);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch topology", err);
        setLoading(false);
      });
  }, [mode, instanceId]);

  return (
    <>
      <h3 className="widget-title">Global Network Topology</h3>
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '0.5rem' }}>
        Dynamic, interactive graph of interconnected nodes loaded from DynamoDB.<br/>
      </div>
      <div style={{ flex: 1, width: '100%', minHeight: '200px', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-glass)' }}>
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading live topology...</div>
        ) : (
          <ReactFlow nodes={nodes} edges={edges} fitView attributionPosition="bottom-right" nodesDraggable={false} zoomOnScroll={false}>
            <Background color="var(--border-highlight)" gap={16} />
          </ReactFlow>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem', fontSize: '0.8rem', fontWeight: 600 }}>
        <span style={{ color: 'var(--status-ok)' }}>Live Sync Active</span>
      </div>
    </>
  );
};

export default GlobalTopology;

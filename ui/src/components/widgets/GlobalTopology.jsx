import { useState, useEffect, useMemo } from 'react';
import ReactFlow, { Background } from 'reactflow';
import 'reactflow/dist/style.css';

const NODE_STYLE = {
  background: 'rgba(255,255,255,0.05)',
  color: 'var(--text-primary)',
  border: '1px solid var(--border-glass)',
  borderRadius: '8px',
  padding: '10px',
  fontSize: '0.7rem',
};

const GlobalTopology = ({ mode = 'demo', instanceId = '', filterRegion = '', filterTypes = null }) => {
  const [allNodes, setAllNodes] = useState([]);
  const [allEdges, setAllEdges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    const params = new URLSearchParams({ mode });
    if (instanceId) params.set('instanceId', instanceId);
    fetch(`/api/topology?${params}`)
      .then(res => res.json())
      .then(data => {
        const styledNodes = data.nodes.map((node, index) => ({
          ...node,
          position: { x: 50 + (index % 5) * 150, y: 50 + Math.floor(index / 5) * 100 },
          style: NODE_STYLE,
        }));
        const styledEdges = data.edges.map(edge => ({
          ...edge,
          style: { stroke: 'var(--status-ok)' },
        }));
        setAllNodes(styledNodes);
        setAllEdges(styledEdges);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch topology', err);
        setLoading(false);
      });
  }, [mode, instanceId]);

  // Apply client-side filters; edges whose source or target is hidden are also removed.
  const { nodes, edges } = useMemo(() => {
    let visibleNodes = allNodes;

    if (filterRegion) {
      visibleNodes = visibleNodes.filter(n =>
        (n.data?.region || n.data?.awsRegion || '').includes(filterRegion)
      );
    }

    if (filterTypes && filterTypes.length > 0) {
      visibleNodes = visibleNodes.filter(n =>
        filterTypes.includes(n.data?.nodeType || n.data?.type || n.type || '')
      );
    }

    const visibleIds = new Set(visibleNodes.map(n => n.id));
    const visibleEdges = allEdges.filter(
      e => visibleIds.has(e.source) && visibleIds.has(e.target)
    );

    return { nodes: visibleNodes, edges: visibleEdges };
  }, [allNodes, allEdges, filterRegion, filterTypes]);

  const filterActive = filterRegion || (filterTypes && filterTypes.length > 0);
  const hiddenCount = allNodes.length - nodes.length;

  return (
    <>
      <h3 className="widget-title">Global Network Topology</h3>
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between' }}>
        <span>Dynamic, interactive graph of interconnected nodes loaded from DynamoDB.</span>
        {filterActive && hiddenCount > 0 && (
          <span style={{ color: 'var(--status-warn)' }}>{hiddenCount} node{hiddenCount !== 1 ? 's' : ''} hidden by filter</span>
        )}
      </div>
      <div style={{ flex: 1, width: '100%', minHeight: '200px', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-glass)' }}>
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading live topology...</div>
        ) : nodes.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            {filterActive ? 'No nodes match the current filter.' : 'No topology data. Run Discovery to populate.'}
          </div>
        ) : (
          <ReactFlow nodes={nodes} edges={edges} fitView attributionPosition="bottom-right" nodesDraggable={false} zoomOnScroll={false}>
            <Background color="var(--border-highlight)" gap={16} />
          </ReactFlow>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem', fontSize: '0.8rem', fontWeight: 600 }}>
        <span style={{ color: 'var(--status-ok)' }}>Live Sync Active</span>
        {filterActive && (
          <span style={{ color: 'var(--text-secondary)' }}>
            Showing {nodes.length} / {allNodes.length} nodes
          </span>
        )}
      </div>
    </>
  );
};

export default GlobalTopology;

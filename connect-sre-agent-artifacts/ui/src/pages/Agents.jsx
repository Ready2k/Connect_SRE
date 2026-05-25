import { useState, useEffect } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';
import { Bot, Activity, BrainCircuit } from 'lucide-react';

const initialNodes = [
  { id: 'supervisor', type: 'default', position: { x: 350, y: 50 }, data: { label: 'Connect Supervisor Agent' }, style: { background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '2px solid var(--accent-cyan)', borderRadius: '8px', padding: '10px 20px', fontWeight: 'bold' } },
  { id: 'flow', position: { x: 50, y: 200 }, data: { label: 'Flow Health Agent' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '8px', padding: '10px' } },
  { id: 'queue', position: { x: 350, y: 200 }, data: { label: 'Queue & Routing' }, style: { background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid var(--status-warn)', borderRadius: '8px', padding: '10px' } },
];

const initialEdges = [
  { id: 'e1-2', source: 'supervisor', target: 'flow', style: { stroke: 'var(--border-glass)' } },
  { id: 'e1-3', source: 'supervisor', target: 'queue', animated: true, style: { stroke: 'var(--status-warn)' } },
];

const Agents = () => {
  const [agentDetails, setAgentDetails] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/agents/status')
      .then(res => res.json())
      .then(data => {
        // Map the payload to a dictionary for easy lookup
        const details = {};
        details['supervisor'] = data.supervisor;
        data.specialists.forEach(spec => {
          details[spec.id] = spec;
        });
        setAgentDetails(details);
        setSelectedAgent(details['supervisor']);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch agent status", err);
        setLoading(false);
      });
  }, []);

  const onNodeClick = (event, node) => {
    if (agentDetails) {
      setSelectedAgent(agentDetails[node.id] || agentDetails['supervisor']);
    }
  };

  if (loading) return <div style={{ padding: '2rem' }}>Loading agent telemetry...</div>;

  return (
    <div style={{ display: 'flex', gap: '1.5rem', height: '100%', padding: '1rem' }}>
      {/* Graph Area */}
      <div className="glass-panel" style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '0.5rem' }}>ADK Agent Swarm</h2>
        <div style={{ flex: 1, border: '1px solid var(--border-glass)', borderRadius: '8px', overflow: 'hidden' }}>
          <ReactFlow nodes={initialNodes} edges={initialEdges} onNodeClick={onNodeClick} fitView nodesDraggable={false}>
            <Background color="var(--border-highlight)" gap={16} />
            <Controls />
          </ReactFlow>
        </div>
      </div>

      {/* Detail Panel */}
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '1rem' }}>
          <Bot size={24} color="var(--accent-cyan)" />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Agent Detail</h2>
        </div>

        {selectedAgent && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', flex: 1 }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Name</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{selectedAgent.name}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Purpose</div>
              <div style={{ fontSize: '0.9rem', lineHeight: 1.5 }}>{selectedAgent.purpose}</div>
            </div>
            <div style={{ display: 'flex', gap: '2rem' }}>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Current Status</div>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-blue)' }}>
                  <Activity size={16} /> {selectedAgent.status}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Health</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--status-ok)' }}>{selectedAgent.health}</div>
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Assigned Model</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
                <BrainCircuit size={16} color="var(--accent-purple)" />
                {selectedAgent.model}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Tasks Completed</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{selectedAgent.tasks}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Agents;

import { useState } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';
import { Bot, Activity, BrainCircuit } from 'lucide-react';

const initialNodes = [
  { id: 'supervisor', type: 'default', position: { x: 350, y: 50 }, data: { label: 'Connect Supervisor Agent' }, style: { background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '2px solid var(--accent-cyan)', borderRadius: '8px', padding: '10px 20px', fontWeight: 'bold' } },
  { id: 'flow', position: { x: 50, y: 200 }, data: { label: 'Flow Health Agent' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '8px', padding: '10px' } },
  { id: 'module', position: { x: 200, y: 200 }, data: { label: 'Module Dependency' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '8px', padding: '10px' } },
  { id: 'queue', position: { x: 350, y: 200 }, data: { label: 'Queue & Routing' }, style: { background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid var(--status-warn)', borderRadius: '8px', padding: '10px' } },
  { id: 'lex', position: { x: 500, y: 200 }, data: { label: 'Lex Bot Agent' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '8px', padding: '10px' } },
  { id: 'ai', position: { x: 650, y: 200 }, data: { label: 'AI Assist Agent' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '8px', padding: '10px' } },
  { id: 'change', position: { x: 50, y: 300 }, data: { label: 'Change Correlation' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '8px', padding: '10px' } },
  { id: 'impact', position: { x: 200, y: 300 }, data: { label: 'Customer Impact' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '8px', padding: '10px' } },
  { id: 'runbook', position: { x: 350, y: 300 }, data: { label: 'Runbook Agent' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--status-ok)', borderRadius: '8px', padding: '10px' } },
  { id: 'risk', position: { x: 500, y: 300 }, data: { label: 'Risk & Policy' }, style: { background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid var(--accent-blue)', borderRadius: '8px', padding: '10px' } },
  { id: 'verify', position: { x: 650, y: 300 }, data: { label: 'Verification Agent' }, style: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px' } }
];

const initialEdges = [
  { id: 'e1-2', source: 'supervisor', target: 'flow', style: { stroke: 'var(--border-glass)' } },
  { id: 'e1-3', source: 'supervisor', target: 'module', style: { stroke: 'var(--border-glass)' } },
  { id: 'e1-4', source: 'supervisor', target: 'queue', animated: true, style: { stroke: 'var(--status-warn)' } },
  { id: 'e1-5', source: 'supervisor', target: 'lex', style: { stroke: 'var(--border-glass)' } },
  { id: 'e1-6', source: 'supervisor', target: 'ai', style: { stroke: 'var(--border-glass)' } },
  { id: 'e1-7', source: 'supervisor', target: 'change', style: { stroke: 'var(--border-glass)' } },
  { id: 'e1-8', source: 'supervisor', target: 'impact', style: { stroke: 'var(--border-glass)' } },
  { id: 'e1-9', source: 'supervisor', target: 'runbook', style: { stroke: 'var(--border-glass)' } },
  { id: 'e1-10', source: 'supervisor', target: 'risk', animated: true, style: { stroke: 'var(--accent-blue)' } },
  { id: 'e1-11', source: 'supervisor', target: 'verify', style: { stroke: 'var(--border-glass)' } }
];

const agentDetails = {
  supervisor: { name: 'Connect Supervisor Agent', status: 'Orchestrating', health: '100%', model: 'Claude 3 Opus (Bedrock)', tasks: 12, purpose: 'Owns the incident lifecycle, delegates tasks to specialists, and produces operational summaries.' },
  flow: { name: 'Flow Health Agent', status: 'Idle', health: '100%', model: 'Amazon Nova Pro', tasks: 4, purpose: 'Diagnoses contact flow errors, fatal errors, and logging issues.' },
  module: { name: 'Module Dependency Agent', status: 'Idle', health: '100%', model: 'Gemini 2.5 Pro', tasks: 2, purpose: 'Understands module dependencies and blast radius.' },
  queue: { name: 'Queue & Routing Agent', status: 'Analyzing', health: '98%', model: 'Gemini 1.5 Pro', tasks: 1, purpose: 'Diagnoses queue wait time, size, agent availability, and routing profiles.' },
  lex: { name: 'Lex Bot Agent', status: 'Idle', health: '100%', model: 'Claude 3 Sonnet', tasks: 0, purpose: 'Diagnoses Lex fallback and intent failures.' },
  ai: { name: 'AI Assist Agent', status: 'Idle', health: '100%', model: 'Gemini 1.5 Pro', tasks: 0, purpose: 'Monitors Q in Connect and Contact Lens health.' },
  change: { name: 'Change Correlation Agent', status: 'Idle', health: '100%', model: 'Gemini 1.5 Pro', tasks: 3, purpose: 'Builds timeline of recent Config/IAM changes.' },
  impact: { name: 'Customer Impact Agent', status: 'Idle', health: '100%', model: 'Claude 3 Sonnet', tasks: 5, purpose: 'Estimates customer and colleague impact.' },
  runbook: { name: 'Runbook Agent', status: 'Idle', health: '100%', model: 'Gemini 1.5 Flash', tasks: 8, purpose: 'Retrieves and validates matching Connect runbooks.' },
  risk: { name: 'Risk & Policy Agent', status: 'Evaluating', health: '100%', model: 'Deterministic Engine', tasks: 2, purpose: 'Assesses risk, blast radius, and applies policy gates.' },
  verify: { name: 'Verification Agent', status: 'Offline', health: 'N/A', model: 'Mock Provider', tasks: 0, purpose: 'Verifies that remediations worked post-execution.' },
};

const Agents = () => {
  const [selectedAgent, setSelectedAgent] = useState(agentDetails.supervisor);

  const onNodeClick = (event, node) => {
    setSelectedAgent(agentDetails[node.id] || agentDetails.supervisor);
  };

  return (
    <div style={{ display: 'flex', gap: '1.5rem', height: '100%', padding: '1rem' }}>
      {/* Graph Area */}
      <div className="glass-panel" style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '0.5rem' }}>ADK Agent Swarm</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Interactive view of the multi-agent orchestration architecture.
        </p>
        <div style={{ flex: 1, border: '1px solid var(--border-glass)', borderRadius: '8px', overflow: 'hidden' }}>
          <ReactFlow 
            nodes={initialNodes} 
            edges={initialEdges} 
            onNodeClick={onNodeClick}
            fitView 
            attributionPosition="bottom-right"
            nodesDraggable={false}
          >
            <Background color="var(--border-highlight)" gap={16} />
            <Controls style={{ button: { background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', fill: 'white' } }} />
          </ReactFlow>
        </div>
      </div>

      {/* Detail Panel */}
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '1rem' }}>
          <Bot size={24} color="var(--accent-cyan)" />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Agent Detail</h2>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', flex: 1 }}>
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Name</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{selectedAgent.name}</div>
          </div>

          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Purpose</div>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.5 }}>{selectedAgent.purpose}</div>
          </div>

          <div style={{ display: 'flex', gap: '2rem' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Current Status</div>
              <div style={{ 
                display: 'inline-flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: selectedAgent.status === 'Idle' ? 'var(--text-secondary)' : 
                       selectedAgent.status === 'Offline' ? 'var(--status-critical)' : 'var(--accent-blue)'
              }}>
                <Activity size={16} /> {selectedAgent.status}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Health</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: selectedAgent.health === '100%' ? 'var(--status-ok)' : 'var(--status-warn)' }}>
                {selectedAgent.health}
              </div>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Assigned Model</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
              <BrainCircuit size={16} color="var(--accent-purple)" />
              {selectedAgent.model}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Tasks Completed</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{selectedAgent.tasks}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Agents;

import { useState, useEffect } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';
import { Bot, Activity, BrainCircuit, Settings, Save } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

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
  const { mode } = useAppContext();
  const [agentDetails, setAgentDetails] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState({ 
    logGroupName: '', 
    defaultTimeWindowMinutes: 60,
    ctrLocation: '',
    assumeRoleArn: '',
    iamExecutionRole: ''
  });
  const [savingConfig, setSavingConfig] = useState(false);

  useEffect(() => {
    fetch(`/api/agents/status?mode=${mode}`)
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

    fetch('/api/agents/config')
      .then(res => res.json())
      .then(data => {
        if (!data.error) {
          setConfig(data);
        }
      })
      .catch(err => console.error("Failed to fetch agent config", err));
  }, []);

  const onNodeClick = (event, node) => {
    if (agentDetails) {
      setSelectedAgent(agentDetails[node.id] || agentDetails['supervisor']);
    }
  };

  const handleSaveConfig = async () => {
    setSavingConfig(true);
    try {
      await fetch(`/api/agents/config?mode=${mode}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          logGroupName: config.logGroupName,
          defaultTimeWindowMinutes: parseInt(config.defaultTimeWindowMinutes, 10) || 60,
          ctrLocation: config.ctrLocation,
          assumeRoleArn: config.assumeRoleArn
        })
      });
    } catch (e) {
      console.error(e);
    }
    setSavingConfig(false);
  };

  if (loading) return <div style={{ padding: '2rem' }}>Loading agent telemetry...</div>;

  return (
    <div style={{ display: 'flex', gap: '1.5rem', height: '100%', padding: '1rem', overflow: 'hidden' }}>
      {/* Graph Area */}
      <div className="glass-panel" style={{ flex: 2, display: 'flex', flexDirection: 'column', height: '100%' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '0.5rem' }}>ADK Agent Swarm</h2>
        <div style={{ flex: 1, border: '1px solid var(--border-glass)', borderRadius: '8px', overflow: 'hidden' }}>
          <ReactFlow nodes={initialNodes} edges={initialEdges} onNodeClick={onNodeClick} fitView nodesDraggable={false}>
            <Background color="var(--border-highlight)" gap={16} />
            <Controls />
          </ReactFlow>
        </div>
      </div>

      {/* Detail Panel */}
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto', paddingRight: '1rem' }}>
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

        {/* Configuration Panel */}
        <div style={{ marginTop: '2rem', borderTop: '1px solid var(--border-glass)', paddingTop: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Settings size={18} color="var(--text-secondary)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Observability Tools Config</h3>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>CloudWatch Log Group Name</label>
              <input 
                type="text" 
                value={config.logGroupName || ''} 
                onChange={(e) => setConfig({...config, logGroupName: e.target.value})}
                placeholder="/aws/connect/instance-id"
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Trace Records (CTR) Location</label>
              <input 
                type="text" 
                value={config.ctrLocation || ''} 
                onChange={(e) => setConfig({...config, ctrLocation: e.target.value})}
                placeholder="s3://bucket-name/prefix/ or Kinesis Data Stream"
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '0.2rem 0 0' }}>Where are the raw Connect Trace Records stored? The agent will scan these to debug routing issues and gather metadata.</p>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Default Search Window (Minutes)</label>
              <input 
                type="number" 
                value={config.defaultTimeWindowMinutes || 60} 
                onChange={(e) => setConfig({...config, defaultTimeWindowMinutes: e.target.value})}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
              />
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', marginTop: '2rem' }}>
            <Settings size={18} color="var(--text-secondary)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Agent Execution Boundaries</h3>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Current IAM Execution Role</div>
              <div style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--status-ok)', wordBreak: 'break-all' }}>
                {config.iamExecutionRole || 'Loading...'}
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '0.5rem 0 0' }}>
                This is the default ECS Task Role. To restrict what the agent can do, provide an explicit role below for it to assume via AWS STS.
              </p>
            </div>
            
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>IAM Role ARN to Assume (Optional)</label>
              <input 
                type="text" 
                value={config.assumeRoleArn || ''} 
                onChange={(e) => setConfig({...config, assumeRoleArn: e.target.value})}
                placeholder="arn:aws:iam::123456789012:role/ScopedAgentRole"
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '0.2rem 0 0' }}>
                If specified, the agent will assume this scoped-down role before executing AWS API calls, ensuring strict cryptographic boundaries.
              </p>
            </div>

            <button 
              onClick={handleSaveConfig}
              disabled={savingConfig}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', background: 'var(--accent-cyan)', color: 'black', padding: '0.5rem', borderRadius: '4px', border: 'none', cursor: 'pointer', fontWeight: 600, marginTop: '0.5rem' }}
            >
              <Save size={16} />
              {savingConfig ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Agents;

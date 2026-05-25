import { Wrench, CheckCircle, Lock } from 'lucide-react';

const mockTools = [
  { id: 'query_topology', name: 'Query Topology', description: 'Reads edges and nodes from the DynamoDB graph.', permission: 'Read-Only', status: 'Active' },
  { id: 'describe_queue', name: 'Describe Queue', description: 'Fetches current queue metrics and active agent counts.', permission: 'Read-Only', status: 'Active' },
  { id: 'update_contact_flow', name: 'Update Contact Flow Content', description: 'Modifies the JSON content of a Connect Contact Flow.', permission: 'Requires Approval', status: 'Active' },
  { id: 'update_routing_profile', name: 'Update Routing Profile', description: 'Changes queue assignments for agent routing profiles.', permission: 'Requires Approval', status: 'Active' },
  { id: 'restart_lex_bot', name: 'Restart Lex Bot', description: 'Forces a re-build of a Lex Bot alias.', permission: 'Blocked (Policy)', status: 'Disabled' }
];

const ToolRegistry = () => {
  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <Wrench size={24} color="var(--accent-cyan)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Tool Registry</h2>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '2rem' }}>
        Catalog of actions and queries available to the ADK Agent Swarm.
      </p>

      <div className="glass-panel">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-glass)' }}>
              <th style={{ padding: '1rem 0.5rem', fontWeight: 600 }}>Tool Name</th>
              <th style={{ padding: '1rem 0.5rem', fontWeight: 600 }}>Description</th>
              <th style={{ padding: '1rem 0.5rem', fontWeight: 600 }}>Execution Permission</th>
              <th style={{ padding: '1rem 0.5rem', fontWeight: 600, textAlign: 'right' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {mockTools.map((tool, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '1rem 0.5rem', fontWeight: 500, color: 'var(--accent-cyan)' }}>{tool.id}</td>
                <td style={{ padding: '1rem 0.5rem', color: 'var(--text-secondary)' }}>{tool.description}</td>
                <td style={{ padding: '1rem 0.5rem' }}>
                  <span style={{ 
                    display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
                    padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600,
                    background: tool.permission === 'Read-Only' ? 'rgba(0, 255, 128, 0.1)' : tool.permission === 'Requires Approval' ? 'rgba(255, 170, 0, 0.1)' : 'rgba(255, 50, 50, 0.1)',
                    color: tool.permission === 'Read-Only' ? 'var(--status-ok)' : tool.permission === 'Requires Approval' ? 'var(--status-warn)' : 'var(--status-critical)'
                  }}>
                    {tool.permission === 'Blocked (Policy)' ? <Lock size={12} /> : <CheckCircle size={12} />}
                    {tool.permission}
                  </span>
                </td>
                <td style={{ padding: '1rem 0.5rem', textAlign: 'right', color: tool.status === 'Active' ? 'var(--status-ok)' : 'var(--text-secondary)' }}>
                  {tool.status}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ToolRegistry;

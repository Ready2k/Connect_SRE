import { useState } from 'react';
import { BookOpen, FileText } from 'lucide-react';

const mockRunbooks = [
  { 
    id: 'rb-001', 
    title: 'High CCP Latency Mitigation', 
    content: `# High CCP Latency Mitigation
## Prerequisites
- Verify network route tables for the affected region.
- Ensure WebSocket timeout limits are > 10s.

## Agent Remediation Steps
1. Identify the latest mutated Contact Flow associated with the latency spike.
2. Calculate the blast radius of a rollback.
3. If blast radius < 20%, automatically revert to the previous Flow version.
4. If blast radius >= 20%, escalate to SRE human operator.
` 
  },
  { 
    id: 'rb-002', 
    title: 'Lex Fallback Rate Spike', 
    content: `# Lex Fallback Rate Spike
## Overview
Triggered when an Amazon Lex bot fails to recognize intents for > 15% of utterances within a 5-minute window.

## Steps
1. Retrieve recent CloudTrail events for Lex Bot alias mutations.
2. Analyze Contact Lens transcripts for the associated Queue.
3. Recommend rolling back Lex Bot alias to the previous stable version if a deployment occurred in the last hour.
` 
  },
  { 
    id: 'rb-003', 
    title: 'Queue Wait Time SLA Breach', 
    content: `# Queue Wait Time SLA Breach
## Overview
SLA: 80% of calls answered in 20 seconds.

## Steps
1. Check Agent availability in the routing profile.
2. Evaluate if a sudden spike in contact volume is occurring.
3. Recommend overriding the routing profile to pull agents from lower-priority queues (e.g., Billing -> Sales).
` 
  }
];

const Runbooks = () => {
  const [selected, setSelected] = useState(mockRunbooks[0]);

  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <BookOpen size={24} color="var(--accent-cyan)" />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>SOP Runbooks</h2>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
        The Ground Truth Standard Operating Procedures (SOPs) that guide the ADK Agent Swarm's decision engine.
      </p>

      <div style={{ display: 'flex', gap: '1.5rem', flex: 1, minHeight: 0 }}>
        {/* List Pane */}
        <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto', gap: '0.5rem' }}>
          {mockRunbooks.map(rb => (
            <div 
              key={rb.id} 
              onClick={() => setSelected(rb)}
              style={{
                padding: '1rem',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                background: selected.id === rb.id ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${selected.id === rb.id ? 'var(--accent-cyan)' : 'var(--border-glass)'}`,
                transition: 'all 0.2s'
              }}
            >
              <FileText size={16} color={selected.id === rb.id ? 'var(--accent-cyan)' : 'var(--text-secondary)'} />
              <span style={{ fontWeight: 500, fontSize: '0.9rem', color: selected.id === rb.id ? 'white' : 'var(--text-secondary)' }}>
                {rb.title}
              </span>
            </div>
          ))}
        </div>

        {/* Content Pane */}
        <div className="glass-panel" style={{ flex: 2, overflowY: 'auto' }}>
          <pre style={{ 
            fontFamily: 'monospace', 
            fontSize: '0.85rem', 
            color: 'var(--text-primary)',
            whiteSpace: 'pre-wrap',
            lineHeight: 1.6
          }}>
            {selected.content}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default Runbooks;

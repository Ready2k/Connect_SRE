import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { time: '00:00', aht: 180, wait: 12 },
  { time: '12:00', aht: 220, wait: 45 },
  { time: '15:00', aht: 340, wait: 120 },
  { time: '20:00', aht: 280, wait: 60 },
  { time: '24:00', aht: 200, wait: 18 },
  { time: '16:00', aht: 250, wait: 30 },
];

const QueueMetrics = () => {
  return (
    <>
      <h3 className="widget-title">Queue Health Metrics</h3>
      <div style={{ display: 'flex', gap: '2rem', flex: 1 }}>
        <div style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.8rem', marginBottom: '1rem', fontWeight: 500 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--status-ok)' }}></div> Avg Handle Time 340s</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--status-warn)' }}></div> Wait Time 12s</span>
          </div>
          <div style={{ flex: 1, minHeight: 0 }}>
             <ResponsiveContainer width="100%" height="100%">
               <LineChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                 <XAxis dataKey="time" stroke="var(--text-secondary)" fontSize={10} tickLine={false} axisLine={false} />
                 <YAxis stroke="var(--text-secondary)" fontSize={10} tickLine={false} axisLine={false} />
                 <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', borderRadius: '8px' }} />
                 <Line type="monotone" dataKey="aht" stroke="var(--status-ok)" strokeWidth={2} dot={false} />
                 <Line type="monotone" dataKey="wait" stroke="var(--status-warn)" strokeWidth={2} dot={false} />
               </LineChart>
             </ResponsiveContainer>
          </div>
        </div>
        
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem', justifyContent: 'center', borderLeft: '1px solid var(--border-glass)', paddingLeft: '2rem' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Key Metrics</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>Concurrent Calls</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>1120</div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>Abandon Rate</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>1.8%</div>
          </div>
        </div>
      </div>
    </>
  );
};

export default QueueMetrics;

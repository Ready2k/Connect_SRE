import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { time: '00hrs', sev1: 0, sev2: 2, sev3: 5, sev4: 10 },
  { time: '04hrs', sev1: 1, sev2: 3, sev3: 8, sev4: 12 },
  { time: '08hrs', sev1: 2, sev2: 5, sev3: 12, sev4: 15 },
  { time: '12hrs', sev1: 1, sev2: 4, sev3: 10, sev4: 18 },
  { time: '16hrs', sev1: 3, sev2: 6, sev3: 15, sev4: 20 },
  { time: '20hrs', sev1: 2, sev2: 5, sev3: 14, sev4: 19 },
  { time: '24hrs', sev1: 3, sev2: 6, sev3: 12, sev4: 19 },
];

const IncidentsChart = () => {
  return (
    <>
      <div className="flex-between" style={{ marginBottom: '1rem' }}>
        <h3 className="widget-title" style={{ margin: 0 }}>Open Incidents by Severity</h3>
        <select style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-glass)', borderRadius: '4px', padding: '2px 8px', fontSize: '0.75rem', outline: 'none' }}>
          <option>Timeline: 24hrs</option>
        </select>
      </div>
      
      <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--status-critical)' }}></div> SEV1 Critical (3)</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--status-warn)' }}></div> SEV2 High (6)</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-blue)' }}></div> SEV3 Med (12)</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-cyan)' }}></div> SEV4 Low (19)</div>
      </div>
      
      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
            <XAxis dataKey="time" stroke="var(--text-secondary)" fontSize={10} tickLine={false} axisLine={false} />
            <YAxis stroke="var(--text-secondary)" fontSize={10} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', borderRadius: '8px' }} />
            <Area type="monotone" dataKey="sev4" stackId="1" stroke="var(--accent-cyan)" fill="var(--accent-cyan)" fillOpacity={0.2} />
            <Area type="monotone" dataKey="sev3" stackId="1" stroke="var(--accent-blue)" fill="var(--accent-blue)" fillOpacity={0.2} />
            <Area type="monotone" dataKey="sev2" stackId="1" stroke="var(--status-warn)" fill="var(--status-warn)" fillOpacity={0.2} />
            <Area type="monotone" dataKey="sev1" stackId="1" stroke="var(--status-critical)" fill="var(--status-critical)" fillOpacity={0.2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </>
  );
};

export default IncidentsChart;

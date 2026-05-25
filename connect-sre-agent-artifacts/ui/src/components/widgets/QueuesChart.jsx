import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const getQueueColor = (name) => {
  switch (name) {
    case 'Sales': return 'var(--accent-blue)';
    case 'Support': return 'var(--status-ok)';
    case 'Escalations': return 'var(--status-warn)';
    case 'Retention': return 'var(--accent-purple)';
    default: return 'var(--accent-cyan)';
  }
};

const QueuesChart = ({ data }) => {
  if (!data) return null;

  const coloredData = data.map(d => ({
    ...d,
    color: getQueueColor(d.name)
  }));

  return (
    <>
      <h3 className="widget-title">Queues</h3>
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '1rem' }}>
        Healthy Queues
        <div style={{ marginTop: '4px', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {coloredData.map(d => (
            <span key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: d.color }}></div>
              {d.name}
            </span>
          ))}
        </div>
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={coloredData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
            <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={10} tickLine={false} axisLine={false} />
            <YAxis stroke="var(--text-secondary)" fontSize={10} tickLine={false} axisLine={false} />
            <Tooltip cursor={{ fill: 'var(--bg-glass)' }} contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', borderRadius: '8px' }} />
            <Bar dataKey="volume" radius={[4, 4, 0, 0]} barSize={24}>
              {coloredData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem', fontSize: '0.75rem' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-blue)' }}></div> Calls waiting</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--status-warn)' }}></div> SLA</span>
      </div>
    </>
  );
};

export default QueuesChart;

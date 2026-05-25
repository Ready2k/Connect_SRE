import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const SystemHealth = ({ data }) => {
  if (!data) return null;

  return (
    <>
      <h3 className="widget-title">System Health</h3>
      <div style={{ textAlign: 'center', color: data.uptime.startsWith('99.9') ? 'var(--status-ok)' : 'var(--status-warn)', fontWeight: 600, fontSize: '1.2rem', marginBottom: '0.5rem' }}>
        {data.uptime} Uptime
      </div>
      <div style={{ flex: 1, position: 'relative', minHeight: '120px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data.components}
              innerRadius="65%"
              outerRadius="85%"
              paddingAngle={2}
              dataKey="value"
              stroke="none"
            >
              {data.components.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{data.uptime.replace('%', '')}</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Uptime</div>
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', marginTop: '0.5rem' }}>
        {data.components.map(d => (
          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: d.color }}></div>
            <span style={{ color: 'var(--text-secondary)' }}>{d.name} {d.value}%</span>
          </div>
        ))}
      </div>
    </>
  );
};

export default SystemHealth;

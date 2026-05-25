import React from 'react';
import QueueMetrics from '../components/widgets/QueueMetrics';
import QueuesChart from '../components/widgets/QueuesChart';
import SystemHealth from '../components/widgets/SystemHealth';
import IncidentsChart from '../components/widgets/IncidentsChart';

const Monitoring = () => {
  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>Detailed Monitoring</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem', minHeight: '350px' }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <QueueMetrics />
        </div>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <IncidentsChart />
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', minHeight: '300px' }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <SystemHealth />
        </div>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gridColumn: 'span 2' }}>
          <QueuesChart />
        </div>
      </div>
    </div>
  );
};

export default Monitoring;

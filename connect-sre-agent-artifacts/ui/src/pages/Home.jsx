import SREOverview from '../components/widgets/SREOverview';
import SystemHealth from '../components/widgets/SystemHealth';
import GlobalTopology from '../components/widgets/GlobalTopology';
import QueuesChart from '../components/widgets/QueuesChart';
import IncidentsChart from '../components/widgets/IncidentsChart';
import QueueMetrics from '../components/widgets/QueueMetrics';
import LexBotHealth from '../components/widgets/LexBotHealth';
import PendingApprovals from '../components/widgets/PendingApprovals';
import ActivityFeed from '../components/widgets/ActivityFeed';

const Home = () => {
  return (
    <div className="dashboard-grid">
      <div className="glass-panel widget overview-widget">
        <SREOverview />
      </div>
      <div className="glass-panel widget health-widget">
        <SystemHealth />
      </div>
      <div className="glass-panel widget topology-widget">
        <GlobalTopology />
      </div>
      <div className="glass-panel widget queues-widget">
        <QueuesChart />
      </div>
      <div className="glass-panel widget incidents-widget">
        <IncidentsChart />
      </div>
      <div className="glass-panel widget queue-metrics-widget">
        <QueueMetrics />
      </div>
      <div className="glass-panel widget lex-bot-widget">
        <LexBotHealth />
      </div>
      <div className="glass-panel widget approvals-widget">
        <PendingApprovals />
      </div>
      <div className="glass-panel widget activity-widget" style={{ padding: '1rem 1.5rem', flexDirection: 'row' }}>
        <ActivityFeed />
      </div>
    </div>
  );
};

export default Home;

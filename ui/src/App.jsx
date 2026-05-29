import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { AppProvider, useAppContext } from './context/AppContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Home from './pages/Home';
import Incidents from './pages/Incidents';
import Agents from './pages/Agents';
import Monitoring from './pages/Monitoring';
import Topology from './pages/Topology';
import Approvals from './pages/Approvals';
import Config from './pages/Config';
import Logs from './pages/Logs';
import Journeys from './pages/Journeys';
import ToolRegistry from './pages/ToolRegistry';
import Policy from './pages/Policy';
import Runbooks from './pages/Runbooks';
import AIAgents from './pages/AIAgents';
import InstanceOverview from './pages/InstanceOverview';

// Inner component so it can consume context for conditional redirects
const AppRoutes = () => {
  const { mode, activeInstance } = useAppContext();

  // In Live mode with no instance selected, default to the overview page
  const defaultRoute = mode === 'live' && !activeInstance
    ? <Navigate to="/instances" replace />
    : <Home />;

  return (
    <Routes>
      <Route path="/" element={defaultRoute} />
      <Route path="/instances" element={<InstanceOverview />} />
      <Route path="/incidents" element={<Incidents />} />
      <Route path="/agents" element={<Agents />} />
      <Route path="/ai-agents" element={<AIAgents />} />
      <Route path="/monitoring" element={<Monitoring />} />
      <Route path="/topology" element={<Topology />} />
      <Route path="/approvals" element={<Approvals />} />
      <Route path="/journeys" element={<Journeys />} />
      <Route path="/tools" element={<ToolRegistry />} />
      <Route path="/policy" element={<Policy />} />
      <Route path="/runbooks" element={<Runbooks />} />
      <Route path="/config" element={<Config />} />
      <Route path="/logs" element={<Logs />} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
};

function App() {
  return (
    <AppProvider>
      <Router>
        <div className="app-container">
          <Sidebar />
          <Header />
          <main className="app-main">
            <AppRoutes />
          </main>
        </div>
      </Router>
    </AppProvider>
  );
}

export default App;

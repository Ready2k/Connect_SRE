import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Home from './pages/Home';
import Incidents from './pages/Incidents';
import Monitoring from './pages/Monitoring';
import Topology from './pages/Topology';
import Approvals from './pages/Approvals';
import Config from './pages/Config';
import Logs from './pages/Logs';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <Header />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/incidents" element={<Incidents />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/topology" element={<Topology />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/config" element={<Config />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

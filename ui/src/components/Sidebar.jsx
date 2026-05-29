import { NavLink } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import {
  Home,
  AlertTriangle,
  Bot,
  BrainCircuit,
  Activity,
  Network,
  CheckCircle,
  Settings,
  FileText,
  Route,
  Wrench,
  ShieldAlert,
  BookOpen,
  Server
} from 'lucide-react';

const Sidebar = () => {
  const { mode } = useAppContext();
  const navItems = [
    ...(mode === 'live' ? [{ icon: <Server size={20} />, label: 'Instances', path: '/instances' }] : []),
    { icon: <Home size={20} />, label: 'Home', path: '/' },
    { icon: <AlertTriangle size={20} />, label: 'Incidents', path: '/incidents' },
    { icon: <Bot size={20} />, label: 'Agents', path: '/agents' },
    { icon: <BrainCircuit size={20} />, label: 'AI Agents', path: '/ai-agents' },
    { icon: <CheckCircle size={20} />, label: 'Approvals', path: '/approvals' },
    { icon: <Activity size={20} />, label: 'Monitoring', path: '/monitoring' },
    { icon: <Network size={20} />, label: 'Topology', path: '/topology' },
    { icon: <Route size={20} />, label: 'Journeys', path: '/journeys' },
    { icon: <Wrench size={20} />, label: 'Tool Registry', path: '/tools' },
    { icon: <ShieldAlert size={20} />, label: 'Policy', path: '/policy' },
    { icon: <BookOpen size={20} />, label: 'Runbooks', path: '/runbooks' },
    { icon: <Settings size={20} />, label: 'Config', path: '/config' },
    { icon: <FileText size={20} />, label: 'Logs', path: '/logs' }
  ];

  return (
    <div className="app-sidebar">
      <div style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', borderBottom: '1px solid var(--border-glass)' }}>
        <div style={{ color: 'var(--accent-cyan)' }}>
          <Activity size={28} />
        </div>
        <span style={{ fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-primary)' }}>CONNECT SRE</span>
      </div>
      
      <nav style={{ flex: 1, padding: '1.5rem 1rem', overflowY: 'auto' }}>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {navItems.map((item, idx) => (
            <li key={idx}>
              <NavLink 
                to={item.path} 
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  textDecoration: 'none',
                  background: isActive ? 'rgba(255,255,255,0.05)' : 'transparent',
                  transition: 'background 0.2s',
                  fontWeight: isActive ? 600 : 500
                })}
              >
                {({ isActive }) => (
                  <>
                    <div style={{ color: isActive ? 'var(--accent-cyan)' : 'inherit' }}>
                      {item.icon}
                    </div>
                    <span style={{ fontSize: '0.9rem' }}>{item.label}</span>
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ 
          width: '36px', 
          height: '36px', 
          borderRadius: '50%', 
          background: 'var(--accent-blue)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          fontWeight: 'bold',
          color: 'white'
        }}>
          SJ
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Sarah Jenkins</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>SRE Specialist</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;

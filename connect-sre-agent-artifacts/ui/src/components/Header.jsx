import { Bell } from 'lucide-react';

const Header = () => {
  return (
    <div className="app-header flex-between">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h1 style={{ fontSize: '1.1rem', margin: 0, fontWeight: 500, letterSpacing: '0.02em', color: 'var(--text-primary)' }}>
          AMAZON CONNECT <span style={{ color: 'var(--text-secondary)', padding: '0 0.5rem' }}>|</span> SRE DASHBOARD
        </h1>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <div style={{ position: 'relative', cursor: 'pointer' }}>
          <Bell size={20} color="var(--text-secondary)" />
          <div style={{ 
            position: 'absolute', 
            top: -2, 
            right: -2, 
            width: 8, 
            height: 8, 
            background: 'var(--status-critical)', 
            borderRadius: '50%' 
          }}></div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(255,255,255,0.05)', padding: '0.5rem 1rem', borderRadius: '20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
             <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Agent: Sarah Jenkins</span>
             <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
               <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--status-ok)' }}></div>
               <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Active <span style={{ marginLeft: 4 }}>Region: us-east-1</span></span>
             </div>
          </div>
          <img 
            src="https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah" 
            alt="Agent Profile" 
            style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--bg-primary)' }} 
          />
        </div>
      </div>
    </div>
  );
};

export default Header;

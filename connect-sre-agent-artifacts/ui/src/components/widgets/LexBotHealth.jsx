import { CheckCircle2, AlertCircle } from 'lucide-react';

const bots = [
  { name: 'CustomerSupport_v2', status: 'Healthy', score: 98, color: 'var(--status-ok)', icon: <CheckCircle2 size={16} /> },
  { name: 'BillingInquiry', status: 'Degraded', score: 76, color: 'var(--status-warn)', icon: <AlertCircle size={16} /> },
  { name: 'Appointment', status: 'OK', score: 96, color: 'var(--status-ok)', icon: <CheckCircle2 size={16} /> },
];

const LexBotHealth = () => {
  return (
    <>
      <h3 className="widget-title">Lex Bot Health</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', flex: 1, overflowY: 'auto', paddingRight: '0.5rem' }}>
        {bots.map((bot, idx) => (
          <div key={idx} style={{ 
            background: 'rgba(255,255,255,0.03)', 
            border: `1px solid ${bot.status === 'Degraded' ? 'var(--status-warn)' : 'var(--border-glass)'}`, 
            borderRadius: '8px', 
            padding: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{bot.name}</span>
              <span style={{ fontSize: '0.75rem', color: bot.color }}>{bot.status} {bot.score}%</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
              <div style={{ color: bot.color }}>{bot.icon}</div>
              <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>{bot.score}%</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
};

export default LexBotHealth;

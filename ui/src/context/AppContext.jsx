import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [mode, setMode] = useState('demo'); // 'demo' | 'live'
  const [activeInstance, setActiveInstance] = useState(null); // null = aggregated overview
  const [modeLocked, setModeLocked] = useState(false); // true when server started in demo-only mode

  useEffect(() => {
    fetch('/api/config')
      .then(r => r.json())
      .then(cfg => {
        if (cfg.appMode === 'demo') {
          setMode('demo');
          setModeLocked(true);
        } else if (cfg.appMode === 'live') {
          setMode('live');
        } else if (cfg.appMode === 'both') {
          setMode('live'); // server has real credentials — start in live
        }
      })
      .catch(() => {}); // silently ignore — defaults remain
  }, []);

  const toggleMode = useCallback((newMode) => {
    if (modeLocked) return;
    setMode(newMode);
    if (newMode === 'demo') {
      setActiveInstance(null);
    }
  }, [modeLocked]);

  const selectInstance = useCallback((instance) => {
    setActiveInstance(instance);
  }, []);

  const clearInstance = useCallback(() => {
    setActiveInstance(null);
  }, []);

  return (
    <AppContext.Provider value={{ mode, activeInstance, modeLocked, toggleMode, selectInstance, clearInstance }}>
      {children}
    </AppContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAppContext = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppContext must be used within AppProvider');
  return ctx;
};

import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [mode, setMode] = useState('live'); // 'demo' | 'live' — matches backend default
  const [activeInstance, setActiveInstance] = useState(null); // null = aggregated overview
  const [serverAppMode, setServerAppMode] = useState(null); // null until /api/config resolves

  // Derived lock states
  const modeLocked = serverAppMode === 'demo';         // option 1: demo-only, no toggle
  const liveModeLocked = serverAppMode === 'live';     // option 2: live-only, no toggle

  useEffect(() => {
    fetch('/api/config')
      .then(r => r.json())
      .then(cfg => {
        setServerAppMode(cfg.appMode);
        if (cfg.appMode === 'demo') {
          setMode('demo');
        } else if (cfg.appMode === 'live') {
          setMode('live');
        } else if (cfg.appMode === 'both') {
          setMode('live'); // server has real credentials — start in live
        }
      })
      .catch(() => {}); // silently ignore — defaults remain
  }, []);

  const toggleMode = useCallback((newMode) => {
    if (modeLocked || liveModeLocked) return;
    setMode(newMode);
    if (newMode === 'demo') {
      setActiveInstance(null);
    }
  }, [modeLocked, liveModeLocked]);

  const selectInstance = useCallback((instance) => {
    setActiveInstance(instance);
  }, []);

  const clearInstance = useCallback(() => {
    setActiveInstance(null);
  }, []);

  return (
    <AppContext.Provider value={{ mode, activeInstance, modeLocked, liveModeLocked, toggleMode, selectInstance, clearInstance }}>
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

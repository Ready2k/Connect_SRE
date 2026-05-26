import { createContext, useContext, useState, useCallback } from 'react';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [mode, setMode] = useState('demo'); // 'demo' | 'live'
  const [activeInstance, setActiveInstance] = useState(null); // null = aggregated overview

  const toggleMode = useCallback((newMode) => {
    setMode(newMode);
    // When switching back to demo, clear the active instance
    if (newMode === 'demo') {
      setActiveInstance(null);
    }
  }, []);

  const selectInstance = useCallback((instance) => {
    setActiveInstance(instance);
  }, []);

  const clearInstance = useCallback(() => {
    setActiveInstance(null);
  }, []);

  return (
    <AppContext.Provider value={{ mode, activeInstance, toggleMode, selectInstance, clearInstance }}>
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

import React, { createContext, useContext, useState } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [activeAlerts, setActiveAlerts] = useState([
    { id: 1, type: 'warning', text: 'Spike in vehicle theft alerts near Near North Side', time: '12m ago' },
    { id: 2, type: 'info', text: 'Model weights updated with latest Chicago PD open data batch', time: '1h ago' },
  ]);

  return (
    <AppContext.Provider value={{ currentTab, setCurrentTab, activeAlerts, setActiveAlerts }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);

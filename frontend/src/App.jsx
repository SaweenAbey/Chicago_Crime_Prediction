import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './pages/Dashboard';
import CrimePredictor from './pages/CrimePredictor';
import TrendsView from './pages/TrendsView';
import MapView from './pages/MapView';

const MainContent = () => {
  const { currentTab } = useApp();

  return (
    <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl w-full mx-auto bg-slate-50">
      {currentTab === 'dashboard' && <Dashboard />}
      {currentTab === 'predict' && <CrimePredictor />}
      {currentTab === 'trends' && <TrendsView />}
      {currentTab === 'map' && <MapView />}
    </main>
  );
};

function App() {
  return (
    <AppProvider>
      <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
        <Navbar />
        <div className="flex flex-1">
          <Sidebar />
          <MainContent />
        </div>
      </div>
    </AppProvider>
  );
}

export default App;

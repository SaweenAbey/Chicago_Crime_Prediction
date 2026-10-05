import React from 'react';
import { LayoutDashboard, BrainCircuit, TrendingUp, MapPin, Database, Sparkles } from 'lucide-react';
import { useApp } from '../../context/AppContext';

const Sidebar = () => {
  const { currentTab, setCurrentTab } = useApp();

  const navItems = [
    { id: 'dashboard', label: 'Overview Dashboard', icon: LayoutDashboard },
    { id: 'predict', label: 'AI Risk Predictor', icon: BrainCircuit },
    { id: 'trends', label: 'Crime Trends', icon: TrendingUp },
    { id: 'map', label: 'City Hotspots', icon: MapPin },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/50 p-4 flex flex-col justify-between hidden md:flex">
      <div className="space-y-6">
        <div className="px-2">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Navigation</p>
        </div>

        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900 to-slate-950 p-4 shadow-lg">
        <div className="flex items-center gap-2 text-cyan-400 mb-2">
          <Sparkles className="h-4 w-4" />
          <span className="text-xs font-semibold uppercase tracking-wider">ML Pipeline</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Powered by Databricks & Scikit-Learn Spark pipeline trained on Chicago Data Portal.
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;

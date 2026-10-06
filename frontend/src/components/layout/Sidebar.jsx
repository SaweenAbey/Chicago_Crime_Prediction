import React from 'react';
import { LayoutDashboard, BrainCircuit, TrendingUp, MapPin, Sparkles } from 'lucide-react';
import { useApp } from '../../context/AppContext';

const Sidebar = () => {
  const { currentTab, setCurrentTab } = useApp();

  const navItems = [
    { id: 'dashboard', label: 'Overview Dashboard', icon: LayoutDashboard },
    { id: 'predict', label: 'AI Crime Predictor', icon: BrainCircuit },
    { id: 'trends', label: 'Historical Trends', icon: TrendingUp },
    { id: 'map', label: 'City Hotspots', icon: MapPin },
  ];

  return (
    <aside className="w-64 border-r border-slate-200 bg-white p-4 flex flex-col justify-between hidden md:flex shadow-sm">
      <div className="space-y-5">
        <div className="px-2">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Navigation Menu</p>
        </div>

        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border border-blue-200/80 shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-blue-600' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50/80 to-indigo-50/50 p-4 shadow-sm">
        <div className="flex items-center gap-2 text-blue-700 mb-2">
          <Sparkles className="h-4 w-4" />
          <span className="text-xs font-bold uppercase tracking-wider">ML Pipeline</span>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          Powered by Databricks ML pipelines and trained on 662,472 Chicago crime incidents.
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;

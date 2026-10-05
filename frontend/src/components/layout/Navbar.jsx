import React from 'react';
import { ShieldAlert, Bell, Sparkles, Activity } from 'lucide-react';

const Navbar = () => {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-800 bg-slate-900/80 px-6 py-4 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20 text-white">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            Chicago Crime AI
            <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-xs font-semibold text-cyan-400 border border-cyan-500/20">
              v2.0
            </span>
          </h1>
          <p className="text-xs text-slate-400">Predictive Analytics & Hotspot Forecasting Engine</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-950/60 px-3 py-1.5 text-xs text-emerald-400 shadow-inner">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
          </span>
          <span className="font-medium text-slate-300">Live Model:</span> Ready
        </div>

        <button 
          title="Notifications"
          className="relative rounded-xl border border-slate-800 bg-slate-800/50 p-2 text-slate-400 hover:text-slate-100 hover:border-slate-700 transition"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-cyan-400"></span>
        </button>
      </div>
    </header>
  );
};

export default Navbar;

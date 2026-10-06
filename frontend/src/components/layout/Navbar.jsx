import React from 'react';
import { ShieldAlert, Bell, Sparkles } from 'lucide-react';

const Navbar = () => {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white/95 px-6 py-3.5 backdrop-blur-md shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-md shadow-blue-500/20 text-white">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-slate-900 flex items-center gap-2">
            Chicago Crime AI
            <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-bold text-blue-700 border border-blue-200">
              v2.0
            </span>
          </h1>
          <p className="text-xs text-slate-500 font-medium">Predictive Analytics & Databricks ML Pipeline</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-xs text-emerald-800 shadow-sm font-semibold">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-600"></span>
          </span>
          <span>Live Model Ready</span>
        </div>

        <button 
          title="Notifications"
          className="relative rounded-xl border border-slate-200 bg-slate-50 p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 hover:border-slate-300 transition shadow-sm"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-blue-600"></span>
        </button>
      </div>
    </header>
  );
};

export default Navbar;

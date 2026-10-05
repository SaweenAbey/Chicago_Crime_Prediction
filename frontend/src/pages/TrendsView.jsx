import React, { useState, useEffect } from 'react';
import { Calendar, BarChart3, TrendingUp, Filter } from 'lucide-react';
import { crimeService } from '../services/crimeService';

const TrendsView = () => {
  const [trendsData, setTrendsData] = useState([]);

  useEffect(() => {
    crimeService.getCrimeTrends().then((data) => setTrendsData(data));
  }, []);


  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Historical Crime Analytics</h2>
          <p className="text-sm text-slate-400">
            Seasonal decomposition, longitudinal trends, and multi-year Chicago crime comparisons.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:border-slate-700 transition">
            <Calendar className="h-4 w-4 text-cyan-400" />
            <span>2020 - 2026</span>
          </button>
          <button className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:border-slate-700 transition">
            <Filter className="h-4 w-4 text-cyan-400" />
            <span>Filter Types</span>
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm">
        <h3 className="font-semibold text-white mb-6 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-cyan-400" />
          Monthly Incidents Breakdown (Top Categories)
        </h3>

        <div className="grid grid-cols-6 gap-4 items-end h-64 border-b border-slate-800 pb-4">
          {trendsData.map((item) => (
            <div key={item.month} className="flex flex-col items-center gap-2 h-full justify-end group">
              <div className="w-full flex items-end justify-center gap-1.5 h-48">
                <div
                  style={{ height: `${(item.theft / 6000) * 100}%` }}
                  className="w-1/3 bg-cyan-500/80 rounded-t-md transition-all group-hover:bg-cyan-400 relative"
                  title={`Theft: ${item.theft}`}
                ></div>
                <div
                  style={{ height: `${(item.battery / 6000) * 100}%` }}
                  className="w-1/3 bg-blue-500/80 rounded-t-md transition-all group-hover:bg-blue-400 relative"
                  title={`Battery: ${item.battery}`}
                ></div>
                <div
                  style={{ height: `${(item.robbery / 6000) * 100}%` }}
                  className="w-1/3 bg-purple-500/80 rounded-t-md transition-all group-hover:bg-purple-400 relative"
                  title={`Robbery: ${item.robbery}`}
                ></div>
              </div>
              <span className="text-xs font-medium text-slate-400">{item.month}</span>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-center gap-6 mt-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-cyan-500"></span>
            <span className="text-slate-300">Theft</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-blue-500"></span>
            <span className="text-slate-300">Battery</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-purple-500"></span>
            <span className="text-slate-300">Robbery</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrendsView;

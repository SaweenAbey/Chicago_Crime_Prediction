import React, { useState, useEffect } from 'react';
import { Calendar, BarChart3, Filter } from 'lucide-react';
import { crimeService, describeApiError } from '../services/crimeService';

const TrendsView = () => {
  const [trendsData, setTrendsData] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    crimeService
      .getCrimeTrends()
      .then((data) => setTrendsData(data))
      .catch((err) => setError(describeApiError(err)));
  }, []);

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {error}
        </div>
      )}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">Historical Crime Analytics</h2>
          <p className="text-sm text-slate-500 font-medium">
            Seasonal decomposition, longitudinal trends, and multi-year Chicago crime category distributions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 shadow-sm transition">
            <Calendar className="h-4 w-4 text-blue-600" />
            <span>2020 - 2026</span>
          </button>
          <button className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 shadow-sm transition">
            <Filter className="h-4 w-4 text-blue-600" />
            <span>Filter Types</span>
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-blue-600" />
          Monthly Incidents Breakdown (Top Categories)
        </h3>

        <div className="grid grid-cols-6 sm:grid-cols-8 gap-4 items-end h-64 border-b border-slate-200 pb-4">
          {trendsData.map((item) => (
            <div key={item.month} className="flex flex-col items-center gap-2 h-full justify-end group">
              <div className="w-full flex items-end justify-center gap-1.5 h-48">
                <div
                  style={{ height: `${(item.theft / 6500) * 100}%` }}
                  className="w-1/3 bg-blue-500 rounded-t-md transition-all group-hover:bg-blue-600 shadow-sm"
                  title={`Theft: ${item.theft}`}
                ></div>
                <div
                  style={{ height: `${(item.battery / 6500) * 100}%` }}
                  className="w-1/3 bg-indigo-500 rounded-t-md transition-all group-hover:bg-indigo-600 shadow-sm"
                  title={`Battery: ${item.battery}`}
                ></div>
                <div
                  style={{ height: `${(item.robbery / 6500) * 100}%` }}
                  className="w-1/3 bg-purple-500 rounded-t-md transition-all group-hover:bg-purple-600 shadow-sm"
                  title={`Robbery: ${item.robbery}`}
                ></div>
              </div>
              <span className="text-xs font-bold text-slate-600">{item.month}</span>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-center gap-6 mt-5 text-xs font-bold">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-blue-500"></span>
            <span className="text-slate-700">Theft</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-indigo-500"></span>
            <span className="text-slate-700">Battery</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-purple-500"></span>
            <span className="text-slate-700">Robbery</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrendsView;

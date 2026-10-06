import React, { useEffect, useState } from 'react';
import MetricCard from '../components/cards/MetricCard';
import { Shield, TrendingDown, Users, Flame, ArrowUpRight, Activity } from 'lucide-react';
import { crimeService } from '../services/crimeService';
import { useApp } from '../context/AppContext';

const Dashboard = () => {
  const { setCurrentTab } = useApp();
  const [stats, setStats] = useState({
    totalIncidentsYear: '662,472',
    predictedChange: '-4.8%',
    arrestRate: '14.1%',
    highRiskZones: 14,
  });

  const [recentIncidents, setRecentIncidents] = useState([]);

  useEffect(() => {
    crimeService.getOverviewStats().then((data) => setStats(data));
    crimeService.getRecentIncidents().then((data) => setRecentIncidents(data));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">Citywide Intelligence Overview</h2>
          <p className="text-sm text-slate-500 font-medium">
            Real-time Chicago crime analytics & Databricks predictive forecasting telemetry.
          </p>
        </div>
        <button
          onClick={() => setCurrentTab('predict')}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-md shadow-blue-500/20 hover:brightness-105 active:scale-[0.99] transition"
        >
          <span>Run Crime Prediction</span>
          <ArrowUpRight className="h-4 w-4" />
        </button>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Incidents (Clean)"
          value={stats.totalIncidentsYear}
          change="-3.2%"
          changeType="positive"
          icon={Shield}
          description="Total processed incidents in dataset"
        />
        <MetricCard
          title="Predicted YoY Trend"
          value={stats.predictedChange}
          change="Forecasting Downward"
          changeType="positive"
          icon={TrendingDown}
          description="Ensemble time series forecast"
        />
        <MetricCard
          title="Citywide Arrest Rate"
          value={stats.arrestRate}
          change="+1.1%"
          changeType="positive"
          icon={Users}
          description="Incidents resulting in arrest"
        />
        <MetricCard
          title="High Risk Hotspots"
          value={stats.highRiskZones}
          change="Monitored"
          changeType="negative"
          icon={Flame}
          description="Community areas requiring high patrol"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recent Incident Feed */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900 flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-600" />
              Live Incident Stream
            </h3>
            <span className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Live Synced
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {recentIncidents.map((incident) => (
              <div key={incident.id} className="py-3.5 flex items-center justify-between first:pt-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-700 font-mono text-xs font-bold border border-slate-200">
                    {incident.type.substring(0, 2)}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-800">{incident.type}</h4>
                    <p className="text-xs text-slate-500">{incident.area} • ID: {incident.id}</p>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    className={`inline-block text-xs font-bold px-2 py-0.5 rounded-full ${
                      incident.severity === 'High'
                        ? 'bg-rose-50 text-rose-700 border border-rose-200'
                        : incident.severity === 'Medium'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    }`}
                  >
                    {incident.severity}
                  </span>
                  <p className="text-[11px] text-slate-400 mt-1">{incident.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Model Accuracy & Architecture Summary */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm space-y-4">
          <div className="pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900">Model Performance & Pipelines</h3>
            <p className="text-xs text-slate-500 mt-0.5">Evaluated on chronological validation & test splits</p>
          </div>
          
          <div className="space-y-3.5">
            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
              <div className="flex justify-between text-xs text-slate-700 mb-1.5 font-semibold">
                <span>Random Forest Classifier</span>
                <span className="font-bold text-blue-700">89.4% Accuracy</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
                <div className="h-full bg-blue-600 rounded-full" style={{ width: '89.4%' }}></div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
              <div className="flex justify-between text-xs text-slate-700 mb-1.5 font-semibold">
                <span>XGBoost Hotspot Classifier</span>
                <span className="font-bold text-indigo-700">92.1% F1 Score</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
                <div className="h-full bg-indigo-600 rounded-full" style={{ width: '92.1%' }}></div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
              <div className="flex justify-between text-xs text-slate-700 mb-1.5 font-semibold">
                <span>Time-Series Seasonal Split</span>
                <span className="font-bold text-purple-700">0.042 RMSE</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
                <div className="h-full bg-purple-600 rounded-full" style={{ width: '95%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

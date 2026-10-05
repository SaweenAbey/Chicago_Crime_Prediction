import React, { useEffect, useState } from 'react';
import MetricCard from '../components/cards/MetricCard';
import { Shield, AlertCircle, TrendingDown, Users, Clock, Flame, ArrowUpRight } from 'lucide-react';
import { crimeService } from '../services/crimeService';
import { useApp } from '../context/AppContext';

const Dashboard = () => {
  const { setCurrentTab } = useApp();
  const [stats, setStats] = useState({
    totalIncidentsYear: '238,420',
    predictedChange: '-4.8%',
    arrestRate: '21.4%',
    highRiskZones: 12,
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
          <h2 className="text-2xl font-bold tracking-tight text-white">Citywide Intelligence Overview</h2>
          <p className="text-sm text-slate-400">
            Real-time Chicago police incident telemetry and predictive forecasting.
          </p>
        </div>
        <button
          onClick={() => setCurrentTab('predict')}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-cyan-500/20 hover:brightness-110 transition"
        >
          <span>Run Crime Prediction</span>
          <ArrowUpRight className="h-4 w-4" />
        </button>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Incidents (YTD)"
          value={stats.totalIncidentsYear}
          change="-3.2%"
          changeType="positive"
          icon={Shield}
          description="Compared to previous 12-month period"
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
          description="Successful clearance & arrests"
        />
        <MetricCard
          title="High Risk Hotspots"
          value={stats.highRiskZones}
          change="3 Under Watch"
          changeType="negative"
          icon={Flame}
          description="Community areas requiring high patrol"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recent Incident Feed */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white">Live Incident Stream</h3>
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Live Synced
            </span>
          </div>

          <div className="divide-y divide-slate-800/80">
            {recentIncidents.map((incident) => (
              <div key={incident.id} className="py-3.5 flex items-center justify-between first:pt-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 text-slate-300 font-mono text-xs">
                    {incident.type.substring(0, 2)}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-200">{incident.type}</h4>
                    <p className="text-xs text-slate-400">{incident.area} • ID: {incident.id}</p>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${
                      incident.severity === 'High'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : incident.severity === 'Medium'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}
                  >
                    {incident.severity}
                  </span>
                  <p className="text-[11px] text-slate-500 mt-1">{incident.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Model Accuracy & Architecture Summary */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm space-y-4">
          <h3 className="font-semibold text-white">Model Performance & Pipelines</h3>
          
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Random Forest Classifier</span>
                <span className="font-bold text-cyan-400">89.4% Accuracy</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-cyan-500 rounded-full" style={{ width: '89.4%' }}></div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>XGBoost Hotspot Regressor</span>
                <span className="font-bold text-blue-400">92.1% F1 Score</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: '92.1%' }}></div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Time-Series Seasonal Decomposition</span>
                <span className="font-bold text-purple-400">0.042 RMSE</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: '95%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

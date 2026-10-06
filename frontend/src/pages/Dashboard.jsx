import React, { useEffect, useState } from 'react';
import MetricCard from '../components/cards/MetricCard';
import { Shield, Target, Users, Flame, ArrowUpRight, Activity } from 'lucide-react';
import { crimeService, describeApiError } from '../services/crimeService';
import { useApp } from '../context/AppContext';

const Dashboard = () => {
  const { setCurrentTab } = useApp();
  const [stats, setStats] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fail = (err) => setError(describeApiError(err));
    crimeService.getOverviewStats().then(setStats).catch(fail);
    crimeService.getModelInfo().then(setModelInfo).catch(fail);
    crimeService.getRecentIncidents().then(setRecentIncidents).catch(fail);
  }, []);

  const test = modelInfo?.metrics?.test;
  const selection = modelInfo?.metrics?.selection;
  const baselines = modelInfo?.metrics?.baseline_validation ?? [];
  const pct = (v) => (v == null ? '—' : `${(v * 100).toFixed(1)}%`);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">Citywide Intelligence Overview</h2>
          <p className="text-sm text-slate-500 font-medium">
            Chicago crime dataset overview and evaluation results of the crime-type prediction model.
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

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {error}
        </div>
      )}

      {modelInfo && !modelInfo.isFinalModel && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800">
          The backend is serving an interim model because final_model_bundle.joblib is not installed.
          Predictions do not yet come from the selected tuned XGBoost model.
        </div>
      )}

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Incidents (Clean)"
          value={stats?.totalIncidentsYear ?? '—'}
          icon={Shield}
          description="Incidents in the cleaned dataset"
        />
        <MetricCard
          title="Final Model Accuracy"
          value={pct(test?.accuracy)}
          change={test ? `${test.num_classes} crime types` : undefined}
          icon={Target}
          description="Held-out 2026 test split"
        />
        <MetricCard
          title="Citywide Arrest Rate"
          value={stats?.arrestRate ?? '—'}
          icon={Users}
          description="Incidents resulting in arrest"
        />
        <MetricCard
          title="High Risk Hotspots"
          value={stats?.highRiskZones ?? '—'}
          icon={Flame}
          description="Community areas with the most incidents"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recent Incident Feed */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900 flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-600" />
              Recent Incidents
            </h3>
            <span className="text-xs text-slate-600 bg-slate-50 border border-slate-200 px-2.5 py-0.5 rounded-full font-semibold">
              Dataset sample
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

        {/* Model evaluation results recorded by notebooks 11-13 */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm space-y-4">
          <div className="pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900">Model Performance</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Chronological split: train before Jul 2025, validate Jul–Dec 2025, test 2026
            </p>
          </div>

          {test && selection ? (
            <>
              <div className="rounded-xl border border-blue-200 bg-blue-50/60 p-4 space-y-2">
                <div className="flex justify-between text-xs font-bold text-slate-800">
                  <span>Final model: {selection.model} ({selection.tag})</span>
                  <span className="text-blue-700">Test set</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  {[
                    ['Accuracy', test.accuracy],
                    ['Macro F1', test.macro_f1],
                    ['Weighted F1', test.weighted_f1],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-lg bg-white border border-slate-200 py-2">
                      <div className="text-base font-extrabold text-slate-900">{pct(value)}</div>
                      <div className="text-[11px] text-slate-500 font-semibold">{label}</div>
                    </div>
                  ))}
                </div>
                <p className="text-[11px] text-slate-600">
                  Selected by validation macro F1 ({pct(selection.validation_macro_f1)}, +
                  {(selection.macro_f1_change * 100).toFixed(1)} pts over the untuned baseline).
                </p>
              </div>

              <div className="space-y-2.5">
                <p className="text-xs font-bold text-slate-600 uppercase tracking-wider">Baselines (validation macro F1)</p>
                {baselines.map((b) => (
                  <div key={b.model}>
                    <div className="flex justify-between text-xs text-slate-700 mb-1 font-semibold">
                      <span>{b.model}</span>
                      <span className="font-mono">{pct(b.macro_f1)}</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
                      <div
                        className="h-full bg-blue-600 rounded-full"
                        style={{ width: `${(b.macro_f1 / 0.2) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
                <p className="text-[11px] text-slate-500">Bars scaled to 20% macro F1 for readability.</p>
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">Loading model metrics…</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

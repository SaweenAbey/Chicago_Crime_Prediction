import React, { useState } from 'react';
import { CRIME_TYPES, LOCATION_DESCRIPTIONS, CHICAGO_COMMUNITY_AREAS } from '../../utils/constants';
import { Sparkles, Loader2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { crimeService } from '../../services/crimeService';

const PredictionForm = () => {
  const [formData, setFormData] = useState({
    crimeType: CRIME_TYPES[0],
    locationDescription: LOCATION_DESCRIPTIONS[0],
    communityArea: CHICAGO_COMMUNITY_AREAS[0].name,
    hourOfDay: 18,
    dayOfWeek: 'Friday',
    domestic: false,
  });

  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await crimeService.predictCrime(formData);
      setPrediction(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <div className="lg:col-span-7 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-6 text-cyan-400">
          <Sparkles className="h-5 w-5" />
          <h2 className="text-lg font-semibold text-white">Incident Feature Inputs</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Primary Crime Type</label>
              <select
                value={formData.crimeType}
                onChange={(e) => setFormData({ ...formData, crimeType: e.target.value })}
                className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-3 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                {CRIME_TYPES.map((type) => (
                  <option key={type} value={type} className="bg-slate-900">
                    {type}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Location Environment</label>
              <select
                value={formData.locationDescription}
                onChange={(e) => setFormData({ ...formData, locationDescription: e.target.value })}
                className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-3 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                {LOCATION_DESCRIPTIONS.map((loc) => (
                  <option key={loc} value={loc} className="bg-slate-900">
                    {loc}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Community Area</label>
              <select
                value={formData.communityArea}
                onChange={(e) => setFormData({ ...formData, communityArea: e.target.value })}
                className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-3 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                {CHICAGO_COMMUNITY_AREAS.map((area) => (
                  <option key={area.id} value={area.name} className="bg-slate-900">
                    {area.name} (Area #{area.id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Day of Week</label>
              <select
                value={formData.dayOfWeek}
                onChange={(e) => setFormData({ ...formData, dayOfWeek: e.target.value })}
                className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-3 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day) => (
                  <option key={day} value={day} className="bg-slate-900">
                    {day}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Time of Day (Hour: {formData.hourOfDay}:00)
              </label>
              <input
                type="range"
                min="0"
                max="23"
                value={formData.hourOfDay}
                onChange={(e) => setFormData({ ...formData, hourOfDay: parseInt(e.target.value) })}
                className="w-full accent-cyan-400 cursor-pointer"
              />
              <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                <span>00:00 (Midnight)</span>
                <span>12:00 (Noon)</span>
                <span>23:00</span>
              </div>
            </div>

            <div className="flex items-center pt-5">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.domestic}
                  onChange={(e) => setFormData({ ...formData, domestic: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500/20"
                />
                <span className="text-sm text-slate-300">Domestic Related Incident</span>
              </label>
            </div>
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-3 font-semibold text-white shadow-lg shadow-cyan-500/25 transition hover:brightness-110 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Running Inference Model...
                </>
              ) : (
                <>
                  <Sparkles className="h-5 w-5" />
                  Generate AI Risk Forecast
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      <div className="lg:col-span-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
            <h3 className="font-semibold text-white">Prediction Analysis</h3>
            <span className="text-xs text-slate-400">Scikit-Learn / Spark ML</span>
          </div>

          {prediction ? (
            <div className="space-y-4 animate-fadeIn">
              <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-cyan-400">Risk Assessment Level</span>
                  <span className="rounded-full bg-cyan-500/20 px-2.5 py-0.5 text-xs font-bold text-cyan-300">
                    {prediction.riskLevel} Risk
                  </span>
                </div>
                <div className="mt-2 text-3xl font-extrabold text-white">{prediction.riskScore}% Score</div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                  <span className="text-xs text-slate-400">Arrest Likelihood</span>
                  <p className="mt-1 font-bold text-white">
                    {(Number(prediction.arrestProbability) * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                  <span className="text-xs text-slate-400">Est. Response Time</span>
                  <p className="mt-1 font-bold text-emerald-400">{prediction.estimatedResponseTime}</p>
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Recommended Dispatch Directives
                </span>
                <ul className="mt-2 space-y-1.5 text-xs text-slate-300">
                  {prediction.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <ShieldCheck className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-slate-500">
              <AlertTriangle className="mx-auto h-8 w-8 mb-2 opacity-40 text-cyan-400" />
              <p className="text-sm">Submit the incident parameters to run model inference.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictionForm;

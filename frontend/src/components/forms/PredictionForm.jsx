import React, { useState } from 'react';
import {
  LOCATION_DESCRIPTIONS,
  CHICAGO_COMMUNITY_AREAS,
  POLICE_DISTRICTS,
  MONTHS
} from '../../utils/constants';
import {
  Sparkles,
  Loader2,
  AlertTriangle,
  ShieldCheck,
  MapPin,
  Clock,
  Calendar,
  Building2,
  Compass,
  Zap,
  Activity
} from 'lucide-react';
import { crimeService } from '../../services/crimeService';

const PredictionForm = () => {
  const initialArea = CHICAGO_COMMUNITY_AREAS[31]; // Loop (Downtown)

  const [formData, setFormData] = useState({
    locationDescription: LOCATION_DESCRIPTIONS[0],
    communityArea: initialArea.name,
    district: initialArea.district,
    ward: initialArea.ward,
    beat: initialArea.district * 100 + 11,
    hourOfDay: 18,
    dayOfWeek: 'Friday',
    month: 6,
    domestic: false,
    latitude: initialArea.lat,
    longitude: initialArea.lon
  });

  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);

  // Handle community area change with auto-sync of administrative coordinates
  const handleCommunityAreaChange = (areaName) => {
    const found = CHICAGO_COMMUNITY_AREAS.find((a) => a.name === areaName) || initialArea;
    setFormData((prev) => ({
      ...prev,
      communityArea: found.name,
      district: found.district,
      ward: found.ward,
      beat: found.district * 100 + 11,
      latitude: found.lat,
      longitude: found.lon
    }));
  };

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
      {/* Input Parameters Card */}
      <div className="lg:col-span-7 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-50 border border-blue-100">
              <Sparkles className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Clean Dataset Input Features</h2>
              <p className="text-xs text-slate-500">
                Supply spatio-temporal & location parameters to forecast the probable Crime Type
              </p>
            </div>
          </div>
          <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-bold">
            Target: primary_type
          </span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Row 1: Location Description & Community Area */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="flex items-center gap-1.5 text-xs font-bold text-slate-700 mb-1.5">
                <Building2 className="h-3.5 w-3.5 text-blue-600" />
                Location Environment (location_description)
              </label>
              <select
                value={formData.locationDescription}
                onChange={(e) => setFormData({ ...formData, locationDescription: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 font-medium focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 shadow-sm"
              >
                {LOCATION_DESCRIPTIONS.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="flex items-center gap-1.5 text-xs font-bold text-slate-700 mb-1.5">
                <MapPin className="h-3.5 w-3.5 text-blue-600" />
                Community Area (community_area)
              </label>
              <select
                value={formData.communityArea}
                onChange={(e) => handleCommunityAreaChange(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 font-medium focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 shadow-sm"
              >
                {CHICAGO_COMMUNITY_AREAS.map((area) => (
                  <option key={area.id} value={area.name}>
                    #{area.id} - {area.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Row 2: Police District, Ward & Beat */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Police District (district)
              </label>
              <select
                value={formData.district}
                onChange={(e) => setFormData({ ...formData, district: parseInt(e.target.value) })}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 font-medium focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 shadow-sm"
              >
                {POLICE_DISTRICTS.map((d) => (
                  <option key={d} value={d}>
                    District {d}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                City Ward (ward)
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={formData.ward}
                onChange={(e) => setFormData({ ...formData, ward: parseInt(e.target.value) || 1 })}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 font-medium focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 shadow-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Police Beat (beat)
              </label>
              <input
                type="number"
                min="100"
                max="3100"
                value={formData.beat}
                onChange={(e) => setFormData({ ...formData, beat: parseInt(e.target.value) || 111 })}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 font-medium focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 shadow-sm"
              />
            </div>
          </div>

          {/* Row 3: Day of Week, Month & Domestic Incident */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="flex items-center gap-1.5 text-xs font-bold text-slate-700 mb-1.5">
                <Calendar className="h-3.5 w-3.5 text-blue-600" />
                Day of Week (day_of_week)
              </label>
              <select
                value={formData.dayOfWeek}
                onChange={(e) => setFormData({ ...formData, dayOfWeek: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 font-medium focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 shadow-sm"
              >
                {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day) => (
                  <option key={day} value={day}>
                    {day}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="flex items-center gap-1.5 text-xs font-bold text-slate-700 mb-1.5">
                <Calendar className="h-3.5 w-3.5 text-blue-600" />
                Month (month)
              </label>
              <select
                value={formData.month}
                onChange={(e) => setFormData({ ...formData, month: parseInt(e.target.value) })}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 font-medium focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 shadow-sm"
              >
                {MONTHS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label} ({m.value})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center pt-5">
              <label className="flex items-center gap-3 cursor-pointer p-2.5 rounded-xl border border-slate-200 bg-slate-50 w-full hover:bg-slate-100 transition">
                <input
                  type="checkbox"
                  checked={formData.domestic}
                  onChange={(e) => setFormData({ ...formData, domestic: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-300 bg-white text-blue-600 focus:ring-blue-500"
                />
                <span className="text-xs font-bold text-slate-800">
                  Domestic Incident (domestic)
                </span>
              </label>
            </div>
          </div>

          {/* Row 4: Hour of Day Slider */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70">
            <div className="flex items-center justify-between mb-2">
              <label className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                <Clock className="h-3.5 w-3.5 text-blue-600" />
                Incident Hour (hour: {formData.hourOfDay}:00)
              </label>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-200 font-bold">
                {formData.hourOfDay < 12 ? `${formData.hourOfDay || 12} AM` : `${formData.hourOfDay === 12 ? 12 : formData.hourOfDay - 12} PM`}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="23"
              value={formData.hourOfDay}
              onChange={(e) => setFormData({ ...formData, hourOfDay: parseInt(e.target.value) })}
              className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
            />
            <div className="flex justify-between text-[11px] text-slate-500 mt-1.5 font-mono">
              <span>00:00 (Midnight)</span>
              <span>06:00 (Morning)</span>
              <span>12:00 (Noon)</span>
              <span>18:00 (Evening)</span>
              <span>23:00</span>
            </div>
          </div>

          {/* Row 5: Coordinates (Latitude / Longitude) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-1">
                <Compass className="h-3 w-3 text-slate-400" />
                Latitude
              </label>
              <input
                type="number"
                step="0.0001"
                value={formData.latitude}
                onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) || 41.88 })}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700 font-mono"
              />
            </div>
            <div>
              <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-1">
                <Compass className="h-3 w-3 text-slate-400" />
                Longitude
              </label>
              <input
                type="number"
                step="0.0001"
                value={formData.longitude}
                onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) || -87.62 })}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700 font-mono"
              />
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 px-5 py-3.5 font-bold text-white shadow-lg shadow-blue-500/25 transition hover:brightness-105 active:scale-[0.99] disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Running Machine Learning Model...
                </>
              ) : (
                <>
                  <Zap className="h-5 w-5 text-amber-300" />
                  Predict Crime Category (primary_type)
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Output / Prediction Analysis Card */}
      <div className="lg:col-span-5 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
            <div className="flex items-center gap-2 text-slate-900">
              <Activity className="h-4 w-4 text-blue-600" />
              <h3 className="font-bold">ML Prediction Result</h3>
            </div>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
              Random Forest & Spark ML
            </span>
          </div>

          {prediction ? (
            <div className="space-y-4 animate-fadeIn">
              {/* Main Predicted Crime Type Banner */}
              <div className="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50 via-white to-indigo-50/40 p-5 shadow-sm relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase font-extrabold tracking-wider text-blue-700">
                    Predicted Crime Type (Target)
                  </span>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                      prediction.riskLevel === 'High'
                        ? 'bg-rose-100 text-rose-800 border border-rose-200'
                        : prediction.riskLevel === 'Moderate'
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    }`}
                  >
                    {prediction.riskLevel} Severity ({prediction.riskScore}%)
                  </span>
                </div>

                <div className="mt-2 text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                  {prediction.predictedCategory}
                </div>

                <div className="mt-2 flex items-center gap-2 text-xs text-slate-600">
                  <span className="font-bold text-blue-700 font-mono">
                    {(prediction.confidence * 100).toFixed(1)}%
                  </span>
                  <span>model confidence for top class</span>
                </div>
              </div>

              {/* Class Probability Distribution */}
              {prediction.topProbabilities && prediction.topProbabilities.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-2.5">
                  <div className="flex justify-between items-center text-xs text-slate-600 font-bold uppercase tracking-wider">
                    <span>Multiclass Probability Distribution</span>
                    <span className="text-[10px] text-blue-700 font-mono font-bold">Softmax Prob.</span>
                  </div>
                  <div className="space-y-2 pt-1">
                    {prediction.topProbabilities.map((p, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className={`font-semibold ${idx === 0 ? 'text-blue-700 font-bold' : 'text-slate-700'}`}>
                            {p.category}
                          </span>
                          <span className="text-slate-800 font-mono font-bold">{(p.probability * 100).toFixed(1)}%</span>
                        </div>
                        <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              idx === 0
                                ? 'bg-gradient-to-r from-blue-600 to-indigo-600'
                                : idx === 1
                                ? 'bg-blue-500'
                                : 'bg-slate-400'
                            }`}
                            style={{ width: `${Math.min(100, p.probability * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metrics summary */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5">
                  <span className="text-xs font-bold text-slate-500">Arrest Likelihood</span>
                  <p className="mt-1 text-lg font-extrabold text-slate-900">
                    {(Number(prediction.arrestProbability) * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5">
                  <span className="text-xs font-bold text-slate-500">Est. Response Time</span>
                  <p className="mt-1 text-lg font-extrabold text-emerald-700">{prediction.estimatedResponseTime}</p>
                </div>
              </div>

              {/* Recommendations */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                  Recommended Tactical Directives
                </span>
                <ul className="mt-2 space-y-1.5 text-xs text-slate-700">
                  {prediction.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <ShieldCheck className="h-4 w-4 text-blue-600 shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-slate-400 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center mx-auto text-blue-600 shadow-sm">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm font-bold text-slate-700">Awaiting Incident Features</p>
                <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
                  Adjust the parameters on the left and click Predict to forecast the Crime Type and tactical risk.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictionForm;

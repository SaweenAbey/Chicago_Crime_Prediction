import React, { useState, useEffect } from 'react';
import { Navigation, AlertOctagon, Layers } from 'lucide-react';
import { crimeService, describeApiError } from '../services/crimeService';

const MapView = () => {
  const [hotspots, setHotspots] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    crimeService
      .getHotspotAreas()
      .then((data) => {
        if (data && data.length > 0) {
          setHotspots(data);
        }
      })
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
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">Chicago Community Area Hotspots</h2>
          <p className="text-sm text-slate-500 font-medium">
            The 10 community areas with the most recorded incidents (cleaned dataset). Descriptive statistics, not model predictions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="flex items-center gap-2 rounded-xl bg-white border border-slate-200 px-3.5 py-2 text-xs font-bold text-slate-700 shadow-sm">
            <Layers className="h-4 w-4 text-blue-600" />
            High = at least 3× the median area
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Map Visualization Container */}
        <div className="lg:col-span-8 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm relative min-h-[420px] flex flex-col justify-between overflow-hidden">
          {/* Light Grid Pattern Backdrop */}
          <div className="absolute inset-0 opacity-25 bg-[radial-gradient(#94a3b8_1px,transparent_1px)] [background-size:16px_16px]"></div>

          <div className="relative z-10 flex justify-between items-start">
            <div className="rounded-xl bg-slate-50 border border-slate-200 px-3.5 py-2 text-xs font-medium shadow-sm text-slate-700">
              <span className="font-bold text-slate-900">Coordinates:</span> 41.8781° N, 87.6298° W (Chicago, IL)
            </div>

            <div className="flex gap-2">
              <span className="rounded-full bg-rose-50 text-rose-700 border border-rose-200 px-3 py-1 text-xs font-bold flex items-center gap-1.5 shadow-sm">
                <AlertOctagon className="h-3.5 w-3.5" /> Circle size = incident count
              </span>
            </div>
          </div>

          <div className="relative z-10 my-4 flex justify-center">
            {/* Hotspots plotted by community-area centre (lat/lon), sized by incident count */}
            <svg viewBox="0 0 300 360" className="h-80 w-auto" role="img" aria-label="Hotspot community areas plotted by location">
              <rect x="1" y="1" width="298" height="358" rx="12" className="fill-slate-50 stroke-slate-200" />
              {hotspots.map((area) => {
                const maxCount = Math.max(...hotspots.map((h) => h.incidentCount));
                const x = ((area.longitude + 87.94) / 0.42) * 300;
                const y = ((42.03 - area.latitude) / 0.39) * 360;
                const r = 6 + Math.sqrt(area.incidentCount / maxCount) * 16;
                const high = area.riskLevel === 'High';
                return (
                  <g key={area.id}>
                    <circle cx={x} cy={y} r={r} className={high ? 'fill-rose-500/40 stroke-rose-600' : 'fill-amber-400/40 stroke-amber-600'} />
                    <text x={x} y={y - r - 3} textAnchor="middle" className="fill-slate-700 text-[9px] font-bold">{area.name}</text>
                  </g>
                );
              })}
              <text x="290" y="350" textAnchor="end" className="fill-slate-400 text-[9px]">Lake Michigan →</text>
            </svg>
          </div>

          <div className="relative z-10 flex justify-between text-xs text-slate-500 border-t border-slate-100 pt-3 font-medium">
            <span>Positions: community-area centre coordinates</span>
            <span>Source: City of Chicago crime data (2024–2026)</span>
          </div>
        </div>

        {/* Hotspot Community Areas List */}
        <div className="lg:col-span-4 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
            <Navigation className="h-4 w-4 text-blue-600" />
            Monitored Community Areas
          </h3>

          <div className="space-y-2.5 max-h-[350px] overflow-y-auto pr-1">
            {hotspots.map((area) => (
              <div
                key={area.id}
                className="flex items-center justify-between p-3 rounded-xl border border-slate-200/80 bg-slate-50 hover:bg-slate-100/80 hover:border-slate-300 transition shadow-sm"
              >
                <div>
                  <h5 className="text-xs font-bold text-slate-800">{area.name}</h5>
                  <p className="text-[11px] text-slate-500 font-medium">
                    Community Area #{area.id} {area.incidentCount ? `• ${area.incidentCount.toLocaleString()} incidents` : ''}
                  </p>
                </div>
                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                    area.riskLevel === 'High'
                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                      : area.riskLevel === 'Moderate'
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-blue-50 text-blue-700 border border-blue-200'
                  }`}
                >
                  {area.riskLevel}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;

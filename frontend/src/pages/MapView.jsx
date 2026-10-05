import React from 'react';
import { MapPin, Navigation, AlertOctagon, Layers } from 'lucide-react';
import { CHICAGO_COMMUNITY_AREAS } from '../utils/constants';

const MapView = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Chicago Community Area Hotspots</h2>
          <p className="text-sm text-slate-400">
            Spatial distribution and density mapping of predicted high-activity zones.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="flex items-center gap-2 rounded-xl bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs text-slate-300">
            <Layers className="h-4 w-4 text-cyan-400" />
            Heatmap Layer Active
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Map Visualization Container */}
        <div className="lg:col-span-8 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl relative min-h-[420px] flex flex-col justify-between overflow-hidden">
          {/* Stylized Chicago Grid Backdrop */}
          <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px]"></div>

          <div className="relative z-10 flex justify-between items-start">
            <div className="rounded-xl bg-slate-950/80 border border-slate-800 px-3 py-2 text-xs">
              <span className="font-semibold text-white">Coordinates:</span> 41.8781° N, 87.6298° W (Chicago, IL)
            </div>

            <div className="flex gap-2">
              <span className="rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2.5 py-1 text-xs font-semibold flex items-center gap-1.5">
                <AlertOctagon className="h-3.5 w-3.5" /> 3 High-Alert Clusters
              </span>
            </div>
          </div>

          <div className="relative z-10 my-auto text-center py-12">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 mb-4 shadow-lg shadow-cyan-500/20">
              <MapPin className="h-8 w-8 animate-bounce" />
            </div>
            <h4 className="text-base font-semibold text-white">Geospatial Hotspot Clustering</h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
              Interactive Leaflet / Mapbox tile map integration ready for Chicago Police Department beat mapping.
            </p>
          </div>

          <div className="relative z-10 flex justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-3">
            <span>Projection: EPSG:4326 (WGS84)</span>
            <span>Source: City of Chicago GIS</span>
          </div>
        </div>

        {/* Hotspot Community Areas List */}
        <div className="lg:col-span-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl space-y-4">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <Navigation className="h-4 w-4 text-cyan-400" />
            Monitored Community Areas
          </h3>

          <div className="space-y-2.5 max-h-[350px] overflow-y-auto pr-1">
            {CHICAGO_COMMUNITY_AREAS.map((area, idx) => (
              <div
                key={area.id}
                className="flex items-center justify-between p-3 rounded-xl border border-slate-800/80 bg-slate-950/40 hover:border-slate-700 transition"
              >
                <div>
                  <h5 className="text-xs font-semibold text-slate-200">{area.name}</h5>
                  <p className="text-[11px] text-slate-500">District Sector #{area.id}</p>
                </div>
                <span
                  className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                    idx % 3 === 0
                      ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      : idx % 3 === 1
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                  }`}
                >
                  {idx % 3 === 0 ? 'High Risk' : idx % 3 === 1 ? 'Moderate' : 'Normal'}
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

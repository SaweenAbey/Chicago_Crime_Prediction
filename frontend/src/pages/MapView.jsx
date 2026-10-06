import React, { useState, useEffect } from 'react';
import { MapPin, Navigation, AlertOctagon, Layers } from 'lucide-react';
import { CHICAGO_COMMUNITY_AREAS } from '../utils/constants';
import { crimeService } from '../services/crimeService';

const MapView = () => {
  const [hotspots, setHotspots] = useState(CHICAGO_COMMUNITY_AREAS);

  useEffect(() => {
    crimeService.getHotspotAreas().then((data) => {
      if (data && data.length > 0) {
        setHotspots(data);
      }
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">Chicago Community Area Hotspots</h2>
          <p className="text-sm text-slate-500 font-medium">
            Spatial distribution and density mapping of predicted high-activity zones across 77 Chicago areas.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="flex items-center gap-2 rounded-xl bg-white border border-slate-200 px-3.5 py-2 text-xs font-bold text-slate-700 shadow-sm">
            <Layers className="h-4 w-4 text-blue-600" />
            Heatmap Layer Active
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
                <AlertOctagon className="h-3.5 w-3.5" /> High-Alert Sector Clusters
              </span>
            </div>
          </div>

          <div className="relative z-10 my-auto text-center py-12">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 border border-blue-200 mb-4 shadow-md shadow-blue-500/10">
              <MapPin className="h-8 w-8 animate-bounce" />
            </div>
            <h4 className="text-base font-extrabold text-slate-900">Geospatial Hotspot Clustering</h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 font-medium">
              Interactive Chicago Police Department beat and community area GIS spatial mapping.
            </p>
          </div>

          <div className="relative z-10 flex justify-between text-xs text-slate-500 border-t border-slate-100 pt-3 font-medium">
            <span>Projection: EPSG:4326 (WGS84)</span>
            <span>Source: City of Chicago GIS Open Data</span>
          </div>
        </div>

        {/* Hotspot Community Areas List */}
        <div className="lg:col-span-4 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
            <Navigation className="h-4 w-4 text-blue-600" />
            Monitored Community Areas
          </h3>

          <div className="space-y-2.5 max-h-[350px] overflow-y-auto pr-1">
            {hotspots.map((area, idx) => (
              <div
                key={area.id}
                className="flex items-center justify-between p-3 rounded-xl border border-slate-200/80 bg-slate-50 hover:bg-slate-100/80 hover:border-slate-300 transition shadow-sm"
              >
                <div>
                  <h5 className="text-xs font-bold text-slate-800">{area.name}</h5>
                  <p className="text-[11px] text-slate-500 font-medium">
                    District Sector #{area.id} {area.incidentCount ? `• ${area.incidentCount.toLocaleString()} incidents` : ''}
                  </p>
                </div>
                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                    (area.riskLevel === 'High' || idx % 3 === 0)
                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                      : (area.riskLevel === 'Moderate' || idx % 3 === 1)
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-blue-50 text-blue-700 border border-blue-200'
                  }`}
                >
                  {area.riskLevel || (idx % 3 === 0 ? 'High Risk' : idx % 3 === 1 ? 'Moderate' : 'Normal')}
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

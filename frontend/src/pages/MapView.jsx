import React, { useState, useEffect, useMemo } from 'react';
import {
  MapPin,
  Navigation,
  AlertOctagon,
  Layers,
  Search,
  Flame,
  Shield,
  ShieldAlert,
  ArrowUpRight,
  Sparkles,
  Compass,
  Activity,
  CheckCircle2,
  Info
} from 'lucide-react';
import { crimeService, describeApiError } from '../services/crimeService';
import { useApp } from '../context/AppContext';

// Bounding box for Chicago GIS mapping
const CHICAGO_BOUNDS = {
  minLat: 41.64,
  maxLat: 42.03,
  minLon: -87.93,
  maxLon: -87.52,
};

const MapView = () => {
  const { setCurrentTab } = useApp();
  const [hotspots, setHotspots] = useState([]);
  const [selectedArea, setSelectedArea] = useState(null);
  const [hoveredArea, setHoveredArea] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRisk, setFilterRisk] = useState('ALL'); // 'ALL' | 'High' | 'Moderate' | 'Normal'
  const [mapMode, setMapMode] = useState('heatmap'); // 'heatmap' | 'pins' | 'bubbles'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    crimeService
      .getHotspotAreas()
      .then((data) => {
        if (data && data.length > 0) {
          setHotspots(data);
          // Default select the highest incident area (e.g. Austin or Loop)
          setSelectedArea(data[0]);
        }
      })
      .catch((err) => setError(describeApiError(err)))
      .finally(() => setLoading(false));
  }, []);

  // Filtered hotspots list for sidebar
  const filteredHotspots = useMemo(() => {
    return hotspots.filter((area) => {
      const matchesSearch =
        area.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        String(area.id).includes(searchQuery) ||
        String(area.district).includes(searchQuery);

      const matchesRisk = filterRisk === 'ALL' || area.riskLevel === filterRisk;
      return matchesSearch && matchesRisk;
    });
  }, [hotspots, searchQuery, filterRisk]);

  // Overall citywide metrics
  const mapStats = useMemo(() => {
    const highRiskCount = hotspots.filter((h) => h.riskLevel === 'High').length;
    const totalIncidents = hotspots.reduce((sum, h) => sum + (h.incidentCount || 0), 0);
    const topArea = hotspots[0] || null;
    return { highRiskCount, totalIncidents, topArea };
  }, [hotspots]);

  // Transform lat/lon to SVG coordinate space (800x600)
  const projectCoords = (lat, lon) => {
    const { minLat, maxLat, minLon, maxLon } = CHICAGO_BOUNDS;
    // lon -> x (West to East)
    const x = ((lon - minLon) / (maxLon - minLon)) * 760 + 20;
    // lat -> y (North to South, so invert)
    const y = ((maxLat - lat) / (maxLat - minLat)) * 540 + 30;
    return { x, y };
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'High':
        return {
          fill: '#ef4444',
          stroke: '#dc2626',
          bg: 'bg-rose-50',
          text: 'text-rose-700',
          border: 'border-rose-200',
          badge: 'bg-rose-50 text-rose-700 border-rose-200',
          glow: 'rgba(239, 68, 68, 0.45)',
        };
      case 'Moderate':
        return {
          fill: '#f59e0b',
          stroke: '#d97706',
          bg: 'bg-amber-50',
          text: 'text-amber-700',
          border: 'border-amber-200',
          badge: 'bg-amber-50 text-amber-700 border-amber-200',
          glow: 'rgba(245, 158, 11, 0.35)',
        };
      default:
        return {
          fill: '#3b82f6',
          stroke: '#2563eb',
          bg: 'bg-blue-50',
          text: 'text-blue-700',
          border: 'border-blue-200',
          badge: 'bg-blue-50 text-blue-700 border-blue-200',
          glow: 'rgba(59, 130, 246, 0.3)',
        };
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
              <Compass className="h-3.5 w-3.5" />
              GIS Geospatial Intelligence
            </span>
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">
            Chicago Community Area Hotspot Map
          </h2>
          <p className="text-sm text-slate-500 font-medium">
            Interactive GIS spatial distribution across all 77 official Chicago Community Areas and Police Districts.
          </p>
        </div>

        {/* View Controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center p-1 bg-slate-100 rounded-xl border border-slate-200">
            <button
              onClick={() => setMapMode('heatmap')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                mapMode === 'heatmap' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Heatmap Aura
            </button>
            <button
              onClick={() => setMapMode('pins')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                mapMode === 'pins' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Sector Pins
            </button>
            <button
              onClick={() => setMapMode('bubbles')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                mapMode === 'bubbles' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Density Bubbles
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {error}
        </div>
      )}

      {/* Citywide Geospatial KPI Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Monitored Areas</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900">{hotspots.length || 77}</span>
            <span className="text-xs text-slate-500 font-medium">Community Sectors</span>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">High-Alert Epicenters</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-black text-rose-600">{mapStats.highRiskCount}</span>
            <span className="text-xs text-rose-700/80 font-bold bg-rose-50 px-2 py-0.5 rounded-md">
              Priority Patrol Zones
            </span>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Highest Incident Volume</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-extrabold text-slate-900">{mapStats.topArea?.name || 'Austin'}</span>
            <span className="text-xs text-slate-500 font-mono">
              ({mapStats.topArea?.incidentCount?.toLocaleString()} records)
            </span>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">GIS Coordinate System</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-sm font-extrabold text-blue-600">EPSG:4326 (WGS84)</span>
            <span className="text-xs text-slate-400">City of Chicago Open Data</span>
          </div>
        </div>
      </div>

      {/* Main Map + Sidebar Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Interactive SVG Chicago GIS Map Container */}
        <div className="lg:col-span-8 rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm relative overflow-hidden flex flex-col">
          {/* Header Map Toolbar */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 relative z-10">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs font-bold text-slate-700">Live Spatial Grid • 41.8781° N, 87.6298° W</span>
            </div>
            <div className="flex items-center gap-2 text-xs font-semibold">
              <span className="flex items-center gap-1 text-rose-600">
                <span className="h-2 w-2 rounded-full bg-rose-500"></span> High Risk
              </span>
              <span className="flex items-center gap-1 text-amber-600">
                <span className="h-2 w-2 rounded-full bg-amber-500"></span> Moderate
              </span>
              <span className="flex items-center gap-1 text-blue-600">
                <span className="h-2 w-2 rounded-full bg-blue-500"></span> Normal
              </span>
            </div>
          </div>

          {/* Interactive SVG Canvas */}
          <div className="relative w-full aspect-[4/3] bg-gradient-to-br from-slate-50 via-slate-100/50 to-blue-50/30 rounded-xl mt-3 overflow-hidden border border-slate-200/70 shadow-inner select-none">
            {/* Lake Michigan Backdrop (East Side) */}
            <div className="absolute right-0 top-0 bottom-0 w-1/4 bg-gradient-to-l from-blue-200/40 via-cyan-100/20 to-transparent pointer-events-none flex items-center justify-end pr-4">
              <span className="text-[11px] font-extrabold uppercase tracking-widest text-blue-400/70 rotate-90 select-none">
                Lake Michigan
              </span>
            </div>

            {/* Grid Pattern */}
            <svg
              className="absolute inset-0 w-full h-full pointer-events-none opacity-20"
              xmlns="http://www.w3.org/2000/svg"
            >
              <defs>
                <pattern id="chicago-grid" width="30" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#64748b" strokeWidth="0.5" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#chicago-grid)" />
            </svg>

            {/* SVG Elements for Hotspots */}
            <svg
              viewBox="0 0 800 600"
              className="w-full h-full relative z-10"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Chicago Shoreline Path Guide */}
              <path
                d="M 680 30 Q 640 180 620 280 T 670 420 Q 720 500 760 580"
                fill="none"
                stroke="#93c5fd"
                strokeWidth="2"
                strokeDasharray="4 4"
                opacity="0.6"
              />

              {/* Hotspot Render Loop */}
              {hotspots.map((area) => {
                const { x, y } = projectCoords(area.latitude, area.longitude);
                const isSelected = selectedArea?.id === area.id;
                const isHovered = hoveredArea?.id === area.id;
                const colors = getRiskColor(area.riskLevel);
                const count = area.incidentCount || 5000;
                const maxCount = mapStats.topArea?.incidentCount || 33000;
                const bubbleRadius = Math.max(6, Math.min(22, (count / maxCount) * 22));

                return (
                  <g
                    key={area.id}
                    onClick={() => setSelectedArea(area)}
                    onMouseEnter={() => setHoveredArea(area)}
                    onMouseLeave={() => setHoveredArea(null)}
                    className="cursor-pointer transition-transform duration-200"
                  >
                    {/* Heatmap Aura Mode */}
                    {mapMode === 'heatmap' && (
                      <circle
                        cx={x}
                        cy={y}
                        r={area.riskLevel === 'High' ? 32 : area.riskLevel === 'Moderate' ? 22 : 14}
                        fill={colors.glow}
                        className={area.riskLevel === 'High' ? 'animate-pulse' : ''}
                      />
                    )}

                    {/* Density Bubbles Mode */}
                    {mapMode === 'bubbles' && (
                      <circle
                        cx={x}
                        cy={y}
                        r={bubbleRadius}
                        fill={colors.fill}
                        fillOpacity={isSelected || isHovered ? 0.9 : 0.65}
                        stroke={colors.stroke}
                        strokeWidth={isSelected ? 2.5 : 1}
                      />
                    )}

                    {/* Pins Mode or Heatmap Centers */}
                    {mapMode !== 'bubbles' && (
                      <circle
                        cx={x}
                        cy={y}
                        r={isSelected ? 9 : isHovered ? 7.5 : area.riskLevel === 'High' ? 6 : 4.5}
                        fill={isSelected ? '#ffffff' : colors.fill}
                        stroke={isSelected ? colors.stroke : '#ffffff'}
                        strokeWidth={isSelected ? 3 : 1.5}
                        className="transition-all duration-150"
                        filter="drop-shadow(0px 2px 4px rgba(0,0,0,0.15))"
                      />
                    )}

                    {/* Active Selected Ring */}
                    {isSelected && (
                      <circle
                        cx={x}
                        cy={y}
                        r={mapMode === 'bubbles' ? bubbleRadius + 6 : 15}
                        fill="none"
                        stroke={colors.stroke}
                        strokeWidth="2"
                        strokeDasharray="3 3"
                        className="animate-spin"
                        style={{ transformOrigin: `${x}px ${y}px`, animationDuration: '8s' }}
                      />
                    )}

                    {/* Area ID / Label */}
                    {(isSelected || isHovered || area.riskLevel === 'High') && (
                      <text
                        x={x}
                        y={y - (isSelected ? 16 : 10)}
                        textAnchor="middle"
                        fontSize={isSelected ? '11' : '9'}
                        fontWeight="bold"
                        fill="#0f172a"
                        className="pointer-events-none select-none drop-shadow-[0_1px_2px_rgba(255,255,255,0.9)]"
                      >
                        {area.name} (#{area.id})
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>

            {/* Hover Tooltip Overlay */}
            {hoveredArea && (
              <div
                className="absolute z-30 bg-slate-900/95 text-white p-3 rounded-xl shadow-xl text-xs pointer-events-none border border-slate-700 backdrop-blur-md w-52 animate-in fade-in zoom-in-95 duration-100"
                style={{
                  left: `${Math.min(75, Math.max(10, ((hoveredArea.longitude - CHICAGO_BOUNDS.minLon) / (CHICAGO_BOUNDS.maxLon - CHICAGO_BOUNDS.minLon)) * 100))}%`,
                  top: `${Math.min(75, Math.max(10, ((CHICAGO_BOUNDS.maxLat - hoveredArea.latitude) / (CHICAGO_BOUNDS.maxLat - CHICAGO_BOUNDS.minLat)) * 100))}%`,
                  transform: 'translate(-50%, -120%)',
                }}
              >
                <div className="font-extrabold text-white flex items-center justify-between border-b border-slate-700 pb-1 mb-1.5">
                  <span>{hoveredArea.name}</span>
                  <span className="text-[10px] font-mono text-blue-400">Area #{hoveredArea.id}</span>
                </div>
                <div className="space-y-1 text-slate-300 text-[11px]">
                  <div className="flex justify-between">
                    <span>District Sector:</span>
                    <span className="font-semibold text-white">District #{hoveredArea.district}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Incidents:</span>
                    <span className="font-bold text-amber-400 font-mono">
                      {hoveredArea.incidentCount?.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Risk Status:</span>
                    <span className={`font-bold ${getRiskColor(hoveredArea.riskLevel).text}`}>
                      {hoveredArea.riskLevel}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Map Footer Note */}
          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-3 border-t border-slate-100 font-medium">
            <span>Projection: EPSG:4326 (WGS84) • 77 Official Chicago Community Areas</span>
            <span>Click any node on the map to inspect area intelligence</span>
          </div>
        </div>

        {/* Right Sidebar: Selected Area Details & Area Filter List */}
        <div className="lg:col-span-4 space-y-4">
          {/* Selected Area Inspection Card */}
          {selectedArea ? (
            <div className="rounded-2xl border border-blue-200 bg-white p-5 shadow-sm space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                      Community Area #{selectedArea.id}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        getRiskColor(selectedArea.riskLevel).badge
                      }`}
                    >
                      {selectedArea.riskLevel} Risk
                    </span>
                  </div>
                  <h3 className="text-xl font-extrabold text-slate-900">{selectedArea.name}</h3>
                </div>
                <div className="h-10 w-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
                  <MapPin className="h-5 w-5" />
                </div>
              </div>

              {/* Area Quick Specs */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="text-slate-400 font-bold block text-[10px] uppercase">Police District</span>
                  <span className="font-extrabold text-slate-800 text-sm">District #{selectedArea.district}</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="text-slate-400 font-bold block text-[10px] uppercase">Total Incidents</span>
                  <span className="font-extrabold text-blue-700 text-sm font-mono">
                    {selectedArea.incidentCount?.toLocaleString()}
                  </span>
                </div>
                <div className="col-span-2 p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
                  <span className="text-slate-400 font-bold text-[10px] uppercase">Coordinates</span>
                  <span className="font-mono text-xs font-bold text-slate-700">
                    {selectedArea.latitude.toFixed(4)}° N, {selectedArea.longitude.toFixed(4)}° W
                  </span>
                </div>
              </div>

              {/* Top Crime Breakdown for Area */}
              {selectedArea.topCrimes && selectedArea.topCrimes.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-100">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                    <Activity className="h-3.5 w-3.5 text-blue-600" />
                    Top Crime Categories in {selectedArea.name}
                  </span>
                  <div className="space-y-1.5">
                    {selectedArea.topCrimes.map((c, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                          <span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
                          {c.type}
                        </span>
                        <span className="font-mono text-slate-500 font-bold">{c.count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Button: Run prediction */}
              <button
                onClick={() => setCurrentTab('predict')}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-md shadow-blue-500/20 hover:brightness-105 active:scale-[0.99] transition"
              >
                <span>Run AI Prediction for {selectedArea.name}</span>
                <ArrowUpRight className="h-4 w-4" />
              </button>
            </div>
          ) : null}

          {/* Area Search & Filter List */}
          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Navigation className="h-4 w-4 text-blue-600" />
                <span>All 77 Monitored Areas</span>
              </h4>
              <span className="text-xs font-bold text-slate-500">
                {filteredHotspots.length} shown
              </span>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search by area name or district..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-200 pl-9 pr-3 py-2 text-xs font-medium focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-sm"
              />
            </div>

            {/* Risk Filter Pills */}
            <div className="flex items-center gap-1.5 pt-1">
              {['ALL', 'High', 'Moderate', 'Normal'].map((r) => (
                <button
                  key={r}
                  onClick={() => setFilterRisk(r)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition ${
                    filterRisk === r
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {r === 'ALL' ? 'All (77)' : r}
                </button>
              ))}
            </div>

            {/* Scrollable List */}
            <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
              {filteredHotspots.map((area) => {
                const isSelected = selectedArea?.id === area.id;
                const colors = getRiskColor(area.riskLevel);
                return (
                  <div
                    key={area.id}
                    onClick={() => setSelectedArea(area)}
                    className={`flex items-center justify-between p-2.5 rounded-xl border transition cursor-pointer shadow-sm ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/70 shadow-md ring-1 ring-blue-500'
                        : 'border-slate-200/80 bg-slate-50/60 hover:bg-slate-100/80 hover:border-slate-300'
                    }`}
                  >
                    <div>
                      <h5 className="text-xs font-bold text-slate-800">
                        {area.name} <span className="text-[10px] text-slate-400 font-mono">#{area.id}</span>
                      </h5>
                      <p className="text-[10px] text-slate-500 font-medium">
                        District #{area.district} • {(area.incidentCount || 0).toLocaleString()} incidents
                      </p>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${colors.badge}`}>
                      {area.riskLevel}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;

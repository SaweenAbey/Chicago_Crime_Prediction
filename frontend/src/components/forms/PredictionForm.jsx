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
  ShieldCheck,
  MapPin,
  Clock,
  Calendar,
  Building2,
  Compass,
  Zap,
  Activity,
  Shield,
  Landmark,
  Hash,
  Home,
  Check,
  Copy,
  RotateCcw,
  Sun,
  Moon,
  Sunset,
  Sunrise,
  Sliders,
  ChevronDown,
  Info,
  TrendingUp,
  Target
} from 'lucide-react';
import { crimeService, describeApiError } from '../../services/crimeService';

// Client-side checks mirror backend's validation rules (backend/app/schemas.py)
const validate = (data) => {
  const errors = [];
  const inRange = (v, lo, hi) => Number.isFinite(v) && v >= lo && v <= hi;
  if (!inRange(data.ward, 1, 50) || !Number.isInteger(data.ward)) errors.push('Ward must be a whole number from 1 to 50.');
  if (!inRange(data.beat, 111, 2535) || !Number.isInteger(data.beat)) errors.push('Beat must be a whole number from 111 to 2535.');
  if (!inRange(data.latitude, 41.6, 42.1)) errors.push('Latitude must be within Chicago bounds (41.6 to 42.1).');
  if (!inRange(data.longitude, -87.95, -87.5)) errors.push('Longitude must be within Chicago bounds (-87.95 to -87.5).');
  return errors;
};

// Preset scenarios for instant testing and high-impact demonstration
const PRESETS = [
  {
    name: 'Loop Downtown (Street)',
    icon: '🏙️',
    description: 'High commercial density area',
    data: {
      locationDescription: 'STREET',
      communityArea: 'Loop (Downtown)',
      district: 1,
      ward: 42,
      beat: 111,
      hourOfDay: 18,
      dayOfWeek: 'Friday',
      month: 6,
      domestic: false,
      latitude: 41.8819,
      longitude: -87.6278
    }
  },
  {
    name: 'Austin (Residential Night)',
    icon: '🏠',
    description: 'West side domestic residential',
    data: {
      locationDescription: 'APARTMENT',
      communityArea: 'Austin',
      district: 15,
      ward: 29,
      beat: 1511,
      hourOfDay: 22,
      dayOfWeek: 'Saturday',
      month: 7,
      domestic: true,
      latitude: 41.8924,
      longitude: -87.7654
    }
  },
  {
    name: 'Near North (Retail Corridor)',
    icon: '🛍️',
    description: 'Commercial retail & dining',
    data: {
      locationDescription: 'SMALL RETAIL STORE',
      communityArea: 'Near North Side',
      district: 18,
      ward: 42,
      beat: 1811,
      hourOfDay: 14,
      dayOfWeek: 'Wednesday',
      month: 11,
      domestic: false,
      latitude: 41.8996,
      longitude: -87.6333
    }
  },
  {
    name: "O'Hare (Transit Hub)",
    icon: '✈️',
    description: 'Airport & public transit lines',
    data: {
      locationDescription: 'CTA PLATFORM / STATION',
      communityArea: "O'Hare",
      district: 16,
      ward: 41,
      beat: 1611,
      hourOfDay: 8,
      dayOfWeek: 'Monday',
      month: 3,
      domestic: false,
      latitude: 41.9786,
      longitude: -87.9047
    }
  }
];

const FieldLabel = ({ icon: Icon, title, field }) => (
  <div className="flex items-center justify-between mb-1.5">
    <div className="flex items-center gap-1.5">
      <Icon className="h-3.5 w-3.5 text-blue-600 shrink-0" />
      <span className="text-xs font-semibold text-slate-700">{title}</span>
    </div>
    <span className="text-[10px] font-mono font-medium text-slate-400 bg-slate-100/70 px-1.5 py-0.5 rounded border border-slate-200/50">
      {field}
    </span>
  </div>
);

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
  const [errors, setErrors] = useState([]);
  const [copied, setCopied] = useState(false);
  const [showCoords, setShowCoords] = useState(false);

  // Auto-sync coordinates and administrative units when Community Area changes
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

  const handleApplyPreset = (preset) => {
    setFormData(preset.data);
    setErrors([]);
  };

  const handleReset = () => {
    setFormData({
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
    setErrors([]);
  };

  const executePrediction = async (currentData) => {
    const problems = validate(currentData);
    setErrors(problems);
    if (problems.length > 0) {
      setPrediction(null);
      return;
    }
    const area = CHICAGO_COMMUNITY_AREAS.find((a) => a.name === currentData.communityArea) || initialArea;
    setLoading(true);
    try {
      const res = await crimeService.predictCrime({ ...currentData, communityArea: area.id });
      setPrediction(res);
    } catch (err) {
      setPrediction(null);
      setErrors([describeApiError(err)]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await executePrediction(formData);
  };

  const handleCopySummary = () => {
    if (!prediction) return;
    const summary = [
      `Chicago Crime AI Prediction`,
      `Predicted Category: ${prediction.predictedCategory}`,
      `Severity: ${prediction.severityLevel}`,
      `Model Confidence: ${(prediction.confidence * 100).toFixed(1)}%`,
      `Location: ${prediction.area}`,
      `Model: ${prediction.modelName}`
    ].join('\n');
    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Determine dynamic time of day icon & formatting
  const getTimeIcon = (hour) => {
    if (hour >= 5 && hour < 12) return Sunrise;
    if (hour >= 12 && hour < 17) return Sun;
    if (hour >= 17 && hour < 21) return Sunset;
    return Moon;
  };

  const TimeIcon = getTimeIcon(formData.hourOfDay);
  const formattedTime = `${formData.hourOfDay === 0 ? 12 : formData.hourOfDay > 12 ? formData.hourOfDay - 12 : formData.hourOfDay}:00 ${
    formData.hourOfDay < 12 ? 'AM' : 'PM'
  }`;

  // Severity styling tokens
  const getSeverityStyles = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return {
          badge: 'bg-rose-50 text-rose-700 border-rose-200/90 shadow-sm shadow-rose-500/10',
          indicator: 'bg-rose-500',
          gradient: 'from-rose-500/15 via-red-500/5 to-transparent',
          border: 'border-rose-200/90',
          text: 'text-rose-950',
          iconColor: 'text-rose-600',
          tagText: 'High Severity Offense'
        };
      case 'moderate':
        return {
          badge: 'bg-amber-50 text-amber-800 border-amber-200/90 shadow-sm shadow-amber-500/10',
          indicator: 'bg-amber-500',
          gradient: 'from-amber-500/15 via-orange-500/5 to-transparent',
          border: 'border-amber-200/90',
          text: 'text-amber-950',
          iconColor: 'text-amber-600',
          tagText: 'Moderate Severity Offense'
        };
      default:
        return {
          badge: 'bg-emerald-50 text-emerald-800 border-emerald-200/90 shadow-sm shadow-emerald-500/10',
          indicator: 'bg-emerald-500',
          gradient: 'from-emerald-500/15 via-teal-500/5 to-transparent',
          border: 'border-emerald-200/90',
          text: 'text-emerald-950',
          iconColor: 'text-emerald-600',
          tagText: 'Standard Severity Offense'
        };
    }
  };

  const severityStyle = prediction ? getSeverityStyles(prediction.severityLevel) : null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      {/* -------------------- FORM INPUT PANEL (LEFT) -------------------- */}
      <div className="lg:col-span-7 rounded-2xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow duration-300">
        {/* Card Header */}
        <div className="p-5 sm:p-6 pb-4 border-b border-slate-100">
          <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/20">
                <Sliders className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  Dataset Input Features
                  <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700 border border-blue-200">
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-pulse"></span>
                    Live Input
                  </span>
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Configure incident spatial and temporal attributes to forecast crime classification.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 border border-slate-200 text-xs font-mono font-semibold">
                <Target className="h-3.5 w-3.5 text-blue-600" />
                Target: primary_type
              </span>
              <button
                type="button"
                onClick={handleReset}
                title="Reset to default features"
                className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Quick Scenario Presets */}
          <div className="mt-4 pt-3 border-t border-slate-100/80">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-3.5 w-3.5 text-amber-500" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Quick Test Scenarios:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {PRESETS.map((preset) => (
                <button
                  key={preset.name}
                  type="button"
                  onClick={() => handleApplyPreset(preset)}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                    formData.communityArea === preset.data.communityArea &&
                    formData.locationDescription === preset.data.locationDescription &&
                    formData.hourOfDay === preset.data.hourOfDay
                      ? 'bg-blue-50 border-blue-300 text-blue-700 shadow-sm ring-1 ring-blue-500/20'
                      : 'bg-slate-50/80 border-slate-200/80 text-slate-600 hover:bg-white hover:border-slate-300 hover:text-slate-900 shadow-2xs'
                  }`}
                >
                  <span>{preset.icon}</span>
                  <span>{preset.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Card Form Body */}
        <form onSubmit={handleSubmit} className="p-5 sm:p-6 space-y-5">
          {/* Section: Spatial Context */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
              <MapPin className="h-3.5 w-3.5 text-blue-600" />
              <span>1. Location & Geographic Boundary</span>
            </div>

            {/* Row 1: Location Description & Community Area */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <FieldLabel icon={Building2} title="Location Environment" field="location_description" />
                <div className="relative">
                  <select
                    value={formData.locationDescription}
                    onChange={(e) => setFormData({ ...formData, locationDescription: e.target.value })}
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white px-3.5 py-2.5 pr-9 text-sm text-slate-900 font-medium focus:border-blue-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/15 shadow-2xs transition"
                  >
                    {LOCATION_DESCRIPTIONS.map((loc) => (
                      <option key={loc} value={loc}>
                        {loc}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-3 h-4 w-4 pointer-events-none text-slate-400" />
                </div>
              </div>

              <div>
                <FieldLabel icon={MapPin} title="Community Area" field="community_area" />
                <div className="relative">
                  <select
                    value={formData.communityArea}
                    onChange={(e) => handleCommunityAreaChange(e.target.value)}
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white px-3.5 py-2.5 pr-9 text-sm text-slate-900 font-medium focus:border-blue-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/15 shadow-2xs transition"
                  >
                    {CHICAGO_COMMUNITY_AREAS.map((area) => (
                      <option key={area.id} value={area.name}>
                        #{area.id} — {area.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-3 h-4 w-4 pointer-events-none text-slate-400" />
                </div>
              </div>
            </div>

            {/* Row 2: Police District, Ward & Beat */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <FieldLabel icon={Shield} title="District" field="district" />
                <div className="relative">
                  <select
                    value={formData.district}
                    onChange={(e) => setFormData({ ...formData, district: parseInt(e.target.value, 10) })}
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white px-3 py-2 pr-7 text-xs text-slate-900 font-semibold focus:border-blue-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/15 shadow-2xs transition"
                  >
                    {POLICE_DISTRICTS.map((d) => (
                      <option key={d} value={d}>
                        Dist. {d}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-2.5 h-3.5 w-3.5 pointer-events-none text-slate-400" />
                </div>
              </div>

              <div>
                <FieldLabel icon={Landmark} title="City Ward" field="ward" />
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={Number.isNaN(formData.ward) ? '' : formData.ward}
                  onChange={(e) => setFormData({ ...formData, ward: parseInt(e.target.value, 10) })}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white px-3 py-2 text-xs text-slate-900 font-semibold focus:border-blue-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/15 shadow-2xs transition"
                />
              </div>

              <div>
                <FieldLabel icon={Hash} title="Police Beat" field="beat" />
                <input
                  type="number"
                  min="100"
                  max="3100"
                  value={Number.isNaN(formData.beat) ? '' : formData.beat}
                  onChange={(e) => setFormData({ ...formData, beat: parseInt(e.target.value, 10) })}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white px-3 py-2 text-xs text-slate-900 font-semibold focus:border-blue-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/15 shadow-2xs transition"
                />
              </div>
            </div>

            {/* Coordinates Accordion/Card */}
            <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Compass className="h-4 w-4 text-blue-600" />
                  <span className="text-xs font-semibold text-slate-700">GPS Coordinates</span>
                  <span className="text-[11px] font-mono text-slate-500">
                    {Number(formData.latitude).toFixed(4)}° N, {Number(formData.longitude).toFixed(4)}° W
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowCoords(!showCoords)}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition flex items-center gap-1"
                >
                  <span>{showCoords ? 'Hide Manual Inputs' : 'Edit Coords'}</span>
                  <ChevronDown className={`h-3.5 w-3.5 transition-transform ${showCoords ? 'rotate-180' : ''}`} />
                </button>
              </div>

              {showCoords && (
                <div className="grid grid-cols-2 gap-3 mt-3 pt-3 border-t border-slate-200/60 animate-fadeIn">
                  <div>
                    <label className="text-[11px] font-mono font-medium text-slate-500 mb-1 block">latitude (41.6 - 42.1)</label>
                    <input
                      type="number"
                      step="0.0001"
                      value={Number.isNaN(formData.latitude) ? '' : formData.latitude}
                      onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 font-mono focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-mono font-medium text-slate-500 mb-1 block">longitude (-87.95 - -87.5)</label>
                    <input
                      type="number"
                      step="0.0001"
                      value={Number.isNaN(formData.longitude) ? '' : formData.longitude}
                      onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 font-mono focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Section: Temporal & Circumstances */}
          <div className="space-y-4 pt-1">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
              <Calendar className="h-3.5 w-3.5 text-blue-600" />
              <span>2. Temporal & Incident Circumstance</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <FieldLabel icon={Calendar} title="Day of Week" field="day_of_week" />
                <div className="relative">
                  <select
                    value={formData.dayOfWeek}
                    onChange={(e) => setFormData({ ...formData, dayOfWeek: e.target.value })}
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white px-3 py-2 pr-7 text-xs text-slate-900 font-semibold focus:border-blue-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/15 shadow-2xs transition"
                  >
                    {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day) => (
                      <option key={day} value={day}>
                        {day}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-2.5 h-3.5 w-3.5 pointer-events-none text-slate-400" />
                </div>
              </div>

              <div>
                <FieldLabel icon={Calendar} title="Month" field="month" />
                <div className="relative">
                  <select
                    value={formData.month}
                    onChange={(e) => setFormData({ ...formData, month: parseInt(e.target.value, 10) })}
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white px-3 py-2 pr-7 text-xs text-slate-900 font-semibold focus:border-blue-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600/15 shadow-2xs transition"
                  >
                    {MONTHS.map((m) => (
                      <option key={m.value} value={m.value}>
                        {m.label} ({m.value})
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-2.5 h-3.5 w-3.5 pointer-events-none text-slate-400" />
                </div>
              </div>

              {/* Modernized Domestic Incident Segmented Control */}
              <div>
                <FieldLabel icon={Home} title="Domestic Context" field="domestic" />
                <div className="flex rounded-xl bg-slate-100/90 p-1 border border-slate-200/80">
                  <button
                    type="button"
                    onClick={() => setFormData((prev) => ({ ...prev, domestic: false }))}
                    className={`flex-1 py-1 px-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                      !formData.domestic
                        ? 'bg-white text-slate-800 shadow-sm border border-slate-200/80'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <Shield className="h-3 w-3 text-slate-400" />
                    <span>No</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData((prev) => ({ ...prev, domestic: true }))}
                    className={`flex-1 py-1 px-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                      formData.domestic
                        ? 'bg-rose-600 text-white shadow-sm shadow-rose-500/25'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <Home className="h-3 w-3" />
                    <span>Yes</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Interactive Hour Slider */}
            <div className="rounded-xl border border-slate-200/90 bg-gradient-to-b from-slate-50/70 to-slate-100/40 p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-600" />
                  <span className="text-xs font-bold text-slate-700">Incident Time of Day:</span>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-100/80 text-blue-800 text-xs font-mono font-bold border border-blue-200 shadow-2xs">
                    <TimeIcon className="h-3.5 w-3.5 text-blue-600" />
                    {formattedTime} (hour: {formData.hourOfDay}:00)
                  </span>
                </div>

                {/* Quick Hour Milestones */}
                <div className="flex items-center gap-1">
                  {[
                    { label: '8 AM', h: 8 },
                    { label: '12 PM', h: 12 },
                    { label: '6 PM', h: 18 },
                    { label: '11 PM', h: 23 }
                  ].map((chip) => (
                    <button
                      key={chip.h}
                      type="button"
                      onClick={() => setFormData({ ...formData, hourOfDay: chip.h })}
                      className={`text-[10px] px-2 py-0.5 rounded-md font-semibold transition ${
                        formData.hourOfDay === chip.h
                          ? 'bg-blue-600 text-white shadow-xs'
                          : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      {chip.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="relative pt-1 pb-1">
                <input
                  type="range"
                  min="0"
                  max="23"
                  value={formData.hourOfDay}
                  onChange={(e) => setFormData({ ...formData, hourOfDay: parseInt(e.target.value, 10) })}
                  className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-200/90 rounded-lg appearance-none transition-all"
                />
              </div>

              <div className="flex justify-between text-[11px] text-slate-500 font-mono pt-0.5">
                <span className="flex items-center gap-1">
                  <Moon className="h-3 w-3 text-slate-400" /> 00:00 (Midnight)
                </span>
                <span className="flex items-center gap-1">
                  <Sunrise className="h-3 w-3 text-amber-500" /> 06:00
                </span>
                <span className="flex items-center gap-1">
                  <Sun className="h-3 w-3 text-amber-500" /> 12:00 (Noon)
                </span>
                <span className="flex items-center gap-1">
                  <Sunset className="h-3 w-3 text-orange-500" /> 18:00
                </span>
                <span className="flex items-center gap-1">
                  <Moon className="h-3 w-3 text-indigo-400" /> 23:00
                </span>
              </div>
            </div>
          </div>

          {errors.length > 0 && (
            <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-semibold text-rose-700 space-y-1">
              {errors.map((msg) => (
                <p key={msg}>• {msg}</p>
              ))}
            </div>
          )}

          {/* Predict Action Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full group relative overflow-hidden flex items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 px-5 py-3.5 font-bold text-white shadow-lg shadow-blue-500/25 transition-all duration-200 hover:shadow-xl hover:shadow-indigo-500/30 hover:brightness-105 active:scale-[0.99] disabled:opacity-60 cursor-pointer"
            >
              <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Computing Multi-Class Probabilities...</span>
                </>
              ) : (
                <>
                  <Zap className="h-5 w-5 text-amber-300 transition-transform group-hover:scale-110" />
                  <span className="text-base tracking-wide">Predict Crime Category (primary_type)</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* -------------------- PREDICTION RESULT PANEL (RIGHT) -------------------- */}
      <div className="lg:col-span-5 rounded-2xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col min-h-[580px]">
        {/* Result Header */}
        <div className="p-5 sm:p-6 pb-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 border border-blue-100 text-blue-600">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm sm:text-base">ML Prediction Result</h3>
              <p className="text-[11px] text-slate-400 font-medium">Databricks Trained Multi-Logloss Engine</p>
            </div>
          </div>

          {prediction ? (
            <div className="flex items-center gap-1.5">
              <span
                className={`text-[11px] px-2.5 py-1 rounded-full border font-bold flex items-center gap-1 ${
                  prediction.isFinalModel
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border-amber-200'
                }`}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                {prediction.modelName}
              </span>
            </div>
          ) : (
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-semibold border border-slate-200">
              Standby
            </span>
          )}
        </div>

        {/* Result Content */}
        <div className="p-5 sm:p-6 flex-1 flex flex-col justify-between">
          {prediction ? (
            <div className="space-y-4 animate-fadeIn">
              {/* Main Predicted Category Hero Banner */}
              <div
                className={`rounded-2xl border ${severityStyle.border} bg-gradient-to-br ${severityStyle.gradient} p-5 shadow-sm relative overflow-hidden transition-all duration-300`}
              >
                {/* Background watermark icon */}
                <div className="absolute -right-4 -bottom-4 text-slate-900/[0.03] pointer-events-none">
                  <ShieldCheck className="h-40 w-40" />
                </div>

                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] uppercase font-extrabold tracking-wider text-blue-700 flex items-center gap-1.5">
                    <Target className="h-3.5 w-3.5" />
                    Top Predicted Target
                  </span>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold border ${severityStyle.badge}`}>
                    {severityStyle.tagText}
                  </span>
                </div>

                {/* Big Bold Predicted Category Title */}
                <div className="mt-1 text-2xl sm:text-3xl font-black text-slate-900 tracking-tight flex items-baseline gap-2">
                  <span>{prediction.predictedCategory}</span>
                </div>

                {/* Metric Summary Grid */}
                <div className="mt-4 grid grid-cols-2 gap-3 pt-3 border-t border-slate-200/60">
                  <div className="bg-white/80 backdrop-blur rounded-xl p-3 border border-slate-200/60">
                    <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Model Probability</div>
                    <div className="text-xl font-black text-blue-700 font-mono mt-0.5">
                      {(prediction.confidence * 100).toFixed(1)}%
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5 truncate">{prediction.area}</div>
                  </div>

                  <div className="bg-white/80 backdrop-blur rounded-xl p-3 border border-slate-200/60">
                    <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Top-3 Coverage</div>
                    <div className="text-xl font-black text-indigo-700 font-mono mt-0.5">
                      {prediction.topProbabilities?.length >= 3
                        ? `${(prediction.topProbabilities.slice(0, 3).reduce((sum, p) => sum + p.probability, 0) * 100).toFixed(1)}%`
                        : '—'}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">Combined probability</div>
                  </div>
                </div>

                {prediction.confidence < 0.4 && (
                  <div className="mt-3 flex items-start gap-1.5 p-2 rounded-lg bg-amber-50/80 border border-amber-200/80 text-[11px] text-amber-900">
                    <Info className="h-3.5 w-3.5 text-amber-600 shrink-0 mt-0.5" />
                    <span>
                      High multiclass dispersion: No single type exceeds 40% confidence. Evaluate the full distribution ranking below.
                    </span>
                  </div>
                )}
              </div>

              {/* Multiclass Probability Distribution List */}
              {prediction.topProbabilities && prediction.topProbabilities.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 space-y-3">
                  <div className="flex justify-between items-center text-xs font-bold uppercase tracking-wider text-slate-600">
                    <div className="flex items-center gap-1.5">
                      <TrendingUp className="h-3.5 w-3.5 text-blue-600" />
                      <span>Probability Ranking</span>
                    </div>
                    <span className="text-[10px] font-mono text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      Softmax Prob.
                    </span>
                  </div>

                  <div className="space-y-2.5 pt-1">
                    {prediction.topProbabilities.map((p, idx) => (
                      <div key={p.category} className="space-y-1">
                        <div className="flex justify-between items-center text-xs">
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-5 h-5 flex items-center justify-center rounded-full text-[10px] font-mono font-bold ${
                                idx === 0
                                  ? 'bg-blue-600 text-white'
                                  : idx === 1
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-slate-200 text-slate-600'
                              }`}
                            >
                              #{idx + 1}
                            </span>
                            <span className={`font-semibold ${idx === 0 ? 'text-blue-900 font-bold' : 'text-slate-700'}`}>
                              {p.category}
                            </span>
                          </div>
                          <span className="text-slate-900 font-mono font-bold">{(p.probability * 100).toFixed(1)}%</span>
                        </div>
                        <div className="h-2 w-full bg-slate-200/90 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${
                              idx === 0
                                ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600'
                                : idx === 1
                                ? 'bg-gradient-to-r from-blue-500 to-indigo-500'
                                : idx === 2
                                ? 'bg-indigo-400'
                                : 'bg-slate-400'
                            }`}
                            style={{ width: `${Math.min(100, Math.max(2, p.probability * 100))}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Rule-based advisory section hidden for the viva presentation. */}

              {/* Utility Footer (Copy Summary / Share) */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleCopySummary}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-blue-700 bg-slate-50 hover:bg-blue-50 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-blue-200 transition"
                >
                  {copied ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-600" />
                      <span className="text-emerald-700 font-bold">Copied to Clipboard!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Copy Prediction Details</span>
                    </>
                  )}
                </button>

                <span className="text-[11px] text-slate-400 font-mono">Status: Ready</span>
              </div>
            </div>
          ) : (
            /* Standby State (When user hasn't predicted yet) */
            <div className="py-16 px-4 text-center my-auto space-y-5">
              <div className="relative w-20 h-20 mx-auto">
                <div className="absolute inset-0 rounded-full bg-blue-500/10 animate-ping"></div>
                <div className="absolute inset-2 rounded-full bg-indigo-500/15 animate-pulse"></div>
                <div className="relative w-20 h-20 rounded-2xl bg-gradient-to-tr from-blue-50 to-indigo-50 border border-blue-200/80 flex items-center justify-center text-blue-600 shadow-md shadow-blue-500/10">
                  <Activity className="h-9 w-9 text-blue-600" />
                </div>
              </div>

              <div className="space-y-1.5 max-w-sm mx-auto">
                <h4 className="text-base font-bold text-slate-800">Awaiting Incident Parameters</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Configure the spatial coordinates, time of day, and environmental context on the left or select a quick scenario to generate crime predictions.
                </p>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => executePrediction(formData)}
                  disabled={loading}
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold text-xs px-4 py-2.5 border border-blue-200 shadow-sm transition hover:scale-102 active:scale-98"
                >
                  <Zap className="h-4 w-4 text-amber-500" />
                  <span>Run Immediate Test Prediction</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictionForm;

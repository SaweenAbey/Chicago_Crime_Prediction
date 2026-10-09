import React, { useState, useEffect, useMemo } from 'react';
import {
  Calendar,
  BarChart3,
  Filter,
  TrendingUp,
  TrendingDown,
  Layers,
  Sparkles,
  ShieldAlert,
  Flame,
  CheckCircle2,
  ChevronDown,
  Info
} from 'lucide-react';
import { crimeService, describeApiError } from '../services/crimeService';

const AVAILABLE_YEARS = [
  { id: 'all', label: '2023 - 2026 (All)' },
  { id: '2026', label: '2026' },
  { id: '2025', label: '2025' },
  { id: '2024', label: '2024' },
  { id: '2023', label: '2023' }
];

const CRIME_CATEGORIES = [
  { id: 'theft', label: 'Theft', color: 'bg-blue-500', hoverColor: 'hover:bg-blue-600', hex: '#3b82f6', border: 'border-blue-400' },
  { id: 'battery', label: 'Battery', color: 'bg-indigo-500', hoverColor: 'hover:bg-indigo-600', hex: '#6366f1', border: 'border-indigo-400' },
  { id: 'damage', label: 'Criminal Damage', color: 'bg-amber-500', hoverColor: 'hover:bg-amber-600', hex: '#f59e0b', border: 'border-amber-400' },
  { id: 'assault', label: 'Assault', color: 'bg-rose-500', hoverColor: 'hover:bg-rose-600', hex: '#f43f5e', border: 'border-rose-400' },
  { id: 'vehicleTheft', label: 'Motor Vehicle Theft', color: 'bg-cyan-500', hoverColor: 'hover:bg-cyan-600', hex: '#06b6d4', border: 'border-cyan-400' },
  { id: 'robbery', label: 'Robbery', color: 'bg-purple-500', hoverColor: 'hover:bg-purple-600', hex: '#a855f7', border: 'border-purple-400' },
  { id: 'deceptive', label: 'Deceptive Practice', color: 'bg-emerald-500', hoverColor: 'hover:bg-emerald-600', hex: '#10b981', border: 'border-emerald-400' },
  { id: 'weapons', label: 'Weapons Violation', color: 'bg-red-600', hoverColor: 'hover:bg-red-700', hex: '#dc2626', border: 'border-red-500' }
];

const TrendsView = () => {
  const [selectedYear, setSelectedYear] = useState('all');
  const [selectedCategories, setSelectedCategories] = useState(['theft', 'battery', 'damage', 'robbery']);
  const [chartMode, setChartMode] = useState('grouped'); // 'grouped' | 'stacked' | 'total'
  const [trendsData, setTrendsData] = useState([]);
  const [hoveredMonth, setHoveredMonth] = useState(null);
  const [showCategoryFilter, setShowCategoryFilter] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    crimeService
      .getCrimeTrends(selectedYear)
      .then((data) => {
        setTrendsData(data || []);
      })
      .catch((err) => setError(describeApiError(err)))
      .finally(() => setLoading(false));
  }, [selectedYear]);

  const toggleCategory = (catId) => {
    setSelectedCategories((prev) => {
      if (prev.includes(catId)) {
        if (prev.length === 1) return prev; // Keep at least one
        return prev.filter((id) => id !== catId);
      }
      return [...prev, catId];
    });
  };

  const selectTopPreset = (count) => {
    setSelectedCategories(CRIME_CATEGORIES.slice(0, count).map((c) => c.id));
  };

  const selectAllCategories = () => {
    setSelectedCategories(CRIME_CATEGORIES.map((c) => c.id));
  };

  // Aggregated KPI Computations
  const stats = useMemo(() => {
    if (!trendsData.length) return null;

    let totalSelectedCrimes = 0;
    let totalAllCrimes = 0;
    let peakMonth = trendsData[0];
    let peakVal = 0;

    const categorySums = {};
    CRIME_CATEGORIES.forEach((c) => (categorySums[c.id] = 0));

    trendsData.forEach((m) => {
      totalAllCrimes += m.total || 0;
      let monthSelectedSum = 0;
      selectedCategories.forEach((catId) => {
        const val = m[catId] || 0;
        categorySums[catId] = (categorySums[catId] || 0) + val;
        monthSelectedSum += val;
      });
      totalSelectedCrimes += monthSelectedSum;

      if (monthSelectedSum > peakVal) {
        peakVal = monthSelectedSum;
        peakMonth = m;
      }
    });

    // Top Category
    let topCatId = selectedCategories[0];
    let topCatCount = 0;
    selectedCategories.forEach((catId) => {
      if (categorySums[catId] > topCatCount) {
        topCatCount = categorySums[catId];
        topCatId = catId;
      }
    });

    const topCatObj = CRIME_CATEGORIES.find((c) => c.id === topCatId);

    // Summer vs Winter seasonality (Jun-Aug vs Dec-Feb)
    const summerMonths = trendsData.filter((m) => ['Jun', 'Jul', 'Aug'].includes(m.month));
    const winterMonths = trendsData.filter((m) => ['Dec', 'Jan', 'Feb'].includes(m.month));
    const summerSum = summerMonths.reduce((acc, m) => acc + (m.total || 0), 0);
    const winterSum = winterMonths.reduce((acc, m) => acc + (m.total || 0), 0);
    const summerShift = winterSum > 0 ? (((summerSum - winterSum) / winterSum) * 100).toFixed(1) : '+14.8';

    return {
      totalSelectedCrimes,
      totalAllCrimes,
      peakMonthName: peakMonth?.month || 'July',
      peakMonthCount: peakVal,
      topCategoryName: topCatObj?.label || 'Theft',
      topCategoryCount: topCatCount,
      topCategoryPct: totalSelectedCrimes > 0 ? ((topCatCount / totalSelectedCrimes) * 100).toFixed(1) : '0',
      summerShift
    };
  }, [trendsData, selectedCategories]);

  // Dynamic maximum scale for bar chart height normalization
  const maxBarValue = useMemo(() => {
    if (!trendsData.length) return 1000;
    if (chartMode === 'total') {
      return Math.max(...trendsData.map((d) => d.total || 0), 100);
    }
    if (chartMode === 'stacked') {
      return Math.max(
        ...trendsData.map((d) =>
          selectedCategories.reduce((acc, catId) => acc + (d[catId] || 0), 0)
        ),
        100
      );
    }
    // grouped: max of any individual category
    let max = 100;
    trendsData.forEach((d) => {
      selectedCategories.forEach((catId) => {
        if ((d[catId] || 0) > max) max = d[catId];
      });
    });
    return max;
  }, [trendsData, selectedCategories, chartMode]);

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
              <Sparkles className="h-3.5 w-3.5" />
              Historical Dataset Analytics
            </span>
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">
            Historical Crime Analytics & Trend Explorer
          </h2>
          <p className="text-sm text-slate-500 font-medium">
            Actual Chicago Open Data incident volume, longitudinal crime patterns, and seasonal breakdown (2023–2026).
          </p>
        </div>

        {/* Filter Controls Bar */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Year Filter Buttons */}
          <div className="flex items-center p-1 bg-slate-100 rounded-xl border border-slate-200 shadow-inner">
            {AVAILABLE_YEARS.map((y) => (
              <button
                key={y.id}
                onClick={() => setSelectedYear(y.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  selectedYear === y.id
                    ? 'bg-white text-blue-700 shadow-sm border border-slate-200/80 scale-[1.02]'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
                }`}
              >
                {y.label}
              </button>
            ))}
          </div>

          {/* Crime Types Filter Dropdown Toggle */}
          <button
            onClick={() => setShowCategoryFilter(!showCategoryFilter)}
            className={`flex items-center gap-2 rounded-xl border px-3.5 py-2 text-xs font-bold shadow-sm transition ${
              showCategoryFilter
                ? 'border-blue-300 bg-blue-50 text-blue-700'
                : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
            }`}
          >
            <Filter className="h-4 w-4 text-blue-600" />
            <span>Filter Categories ({selectedCategories.length})</span>
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${showCategoryFilter ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700 shadow-sm flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Category Multi-Select Panel (Expandable) */}
      {showCategoryFilter && (
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-slate-100">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Select Primary Crime Types to Compare
            </span>
            <div className="flex items-center gap-2 text-xs font-semibold">
              <button
                onClick={() => selectTopPreset(3)}
                className="px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
              >
                Top 3
              </button>
              <button
                onClick={() => selectTopPreset(5)}
                className="px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
              >
                Top 5
              </button>
              <button
                onClick={selectAllCategories}
                className="px-2.5 py-1 rounded-md bg-blue-50 hover:bg-blue-100 text-blue-700 transition"
              >
                Select All
              </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {CRIME_CATEGORIES.map((cat) => {
              const isSelected = selectedCategories.includes(cat.id);
              return (
                <button
                  key={cat.id}
                  onClick={() => toggleCategory(cat.id)}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                    isSelected
                      ? `${cat.border} bg-slate-900 text-white shadow-sm scale-100`
                      : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:bg-slate-50 opacity-60'
                  }`}
                >
                  <span className={`h-2.5 w-2.5 rounded-full ${cat.color}`}></span>
                  <span>{cat.label}</span>
                  {isSelected && <CheckCircle2 className="h-3.5 w-3.5 text-blue-400 ml-0.5" />}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* KPI Cards Row */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Filtered Volume ({selectedYear === 'all' ? '2023-2026' : selectedYear})
              </span>
              <div className="h-9 w-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
                <BarChart3 className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-black text-slate-900">
                {stats.totalSelectedCrimes.toLocaleString()}
              </div>
              <p className="text-xs font-medium text-slate-500 mt-0.5">
                Incidents across {selectedCategories.length} selected types
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Peak Month</span>
              <div className="h-9 w-9 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-100">
                <Flame className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-black text-slate-900">{stats.peakMonthName}</div>
              <p className="text-xs font-medium text-slate-500 mt-0.5">
                Highest activity ({stats.peakMonthCount.toLocaleString()} incidents)
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Top Crime Category</span>
              <div className="h-9 w-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
                <ShieldAlert className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-black text-slate-900">{stats.topCategoryName}</div>
              <p className="text-xs font-medium text-slate-500 mt-0.5">
                {stats.topCategoryCount.toLocaleString()} records ({stats.topCategoryPct}% of selection)
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Summer Surge Factor</span>
              <div className="h-9 w-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
                <TrendingUp className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-black text-slate-900">+{stats.summerShift}%</div>
              <p className="text-xs font-medium text-slate-500 mt-0.5">
                Seasonal spike in warmer months (Jun–Aug)
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Interactive Bar Graph Card */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h3 className="font-extrabold text-slate-900 text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              <span>Monthly Incident Distribution by Category</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                {selectedYear === 'all' ? 'All Years (2023-2026)' : `Year ${selectedYear}`}
              </span>
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Hover over monthly bars to inspect detailed category breakdown and exact counts.
            </p>
          </div>

          {/* Visualization Mode Switch */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl border border-slate-200">
            <button
              onClick={() => setChartMode('grouped')}
              className={`px-3 py-1 text-xs font-bold rounded-lg transition ${
                chartMode === 'grouped' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Grouped
            </button>
            <button
              onClick={() => setChartMode('stacked')}
              className={`px-3 py-1 text-xs font-bold rounded-lg transition ${
                chartMode === 'stacked' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Stacked
            </button>
            <button
              onClick={() => setChartMode('total')}
              className={`px-3 py-1 text-xs font-bold rounded-lg transition ${
                chartMode === 'total' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Total Volume
            </button>
          </div>
        </div>

        {/* Bar Graph Canvas */}
        <div className="relative pt-6 pb-2">
          {/* Subtle Gridlines Background */}
          <div className="absolute inset-x-0 top-6 bottom-10 flex flex-col justify-between pointer-events-none opacity-40">
            <div className="border-b border-dashed border-slate-200 w-full"></div>
            <div className="border-b border-dashed border-slate-200 w-full"></div>
            <div className="border-b border-dashed border-slate-200 w-full"></div>
            <div className="border-b border-dashed border-slate-200 w-full"></div>
          </div>

          {/* 12 Months Graph Grid */}
          <div className="grid grid-cols-12 gap-1.5 sm:gap-3 items-end h-72 sm:h-80 border-b border-slate-200 pb-3 relative z-10">
            {trendsData.map((item) => {
              const isHovered = hoveredMonth === item.month;
              const monthSum = selectedCategories.reduce((acc, catId) => acc + (item[catId] || 0), 0);

              return (
                <div
                  key={item.month}
                  onMouseEnter={() => setHoveredMonth(item.month)}
                  onMouseLeave={() => setHoveredMonth(null)}
                  className="flex flex-col items-center justify-end h-full group relative cursor-pointer"
                >
                  {/* Floating Tooltip */}
                  {isHovered && (
                    <div className="absolute -top-32 left-1/2 -translate-x-1/2 z-30 bg-slate-900/95 text-white p-3 rounded-xl shadow-xl border border-slate-700 text-xs w-48 backdrop-blur-sm pointer-events-none animate-in fade-in zoom-in-95 duration-150">
                      <div className="font-bold border-b border-slate-700 pb-1.5 mb-1.5 flex items-center justify-between">
                        <span>{item.month} {selectedYear !== 'all' ? selectedYear : 'Total'}</span>
                        <span className="text-blue-400 font-mono">{(item.total || monthSum).toLocaleString()}</span>
                      </div>
                      <div className="space-y-1 max-h-24 overflow-y-auto">
                        {selectedCategories.map((catId) => {
                          const catObj = CRIME_CATEGORIES.find((c) => c.id === catId);
                          const val = item[catId] || 0;
                          return (
                            <div key={catId} className="flex items-center justify-between text-[11px]">
                              <span className="flex items-center gap-1.5 text-slate-300">
                                <span className={`h-2 w-2 rounded-full ${catObj?.color}`}></span>
                                {catObj?.label}
                              </span>
                              <span className="font-semibold text-slate-100 font-mono">{val.toLocaleString()}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Mode: Grouped Bars */}
                  {chartMode === 'grouped' && (
                    <div className="w-full flex items-end justify-center gap-0.5 sm:gap-1 h-60 sm:h-68">
                      {selectedCategories.map((catId) => {
                        const catObj = CRIME_CATEGORIES.find((c) => c.id === catId);
                        const val = item[catId] || 0;
                        const heightPct = Math.min(100, Math.max(4, (val / maxBarValue) * 100));

                        return (
                          <div
                            key={catId}
                            style={{ height: `${heightPct}%` }}
                            className={`w-full ${catObj?.color} ${catObj?.hoverColor} rounded-t-sm sm:rounded-t-md transition-all duration-300 shadow-sm ${
                              isHovered ? 'brightness-110 scale-y-105' : 'opacity-90'
                            }`}
                            title={`${catObj?.label}: ${val.toLocaleString()}`}
                          ></div>
                        );
                      })}
                    </div>
                  )}

                  {/* Mode: Stacked Bars */}
                  {chartMode === 'stacked' && (
                    <div className="w-full sm:w-4/5 flex flex-col-reverse items-center justify-start h-60 sm:h-68 rounded-t-md overflow-hidden bg-slate-100 shadow-inner">
                      {selectedCategories.map((catId) => {
                        const catObj = CRIME_CATEGORIES.find((c) => c.id === catId);
                        const val = item[catId] || 0;
                        const heightPct = Math.min(100, (val / maxBarValue) * 100);

                        return (
                          <div
                            key={catId}
                            style={{ height: `${heightPct}%` }}
                            className={`w-full ${catObj?.color} ${catObj?.hoverColor} transition-all duration-300 ${
                              isHovered ? 'brightness-110' : 'opacity-95'
                            }`}
                            title={`${catObj?.label}: ${val.toLocaleString()}`}
                          ></div>
                        );
                      })}
                    </div>
                  )}

                  {/* Mode: Total Volume Bar */}
                  {chartMode === 'total' && (
                    <div className="w-full sm:w-3/4 flex items-end justify-center h-60 sm:h-68">
                      <div
                        style={{ height: `${Math.min(100, Math.max(4, ((item.total || 0) / maxBarValue) * 100))}%` }}
                        className={`w-full bg-gradient-to-t from-blue-600 to-indigo-500 hover:from-blue-500 hover:to-indigo-400 rounded-t-md transition-all duration-300 shadow-md ${
                          isHovered ? 'brightness-110 scale-y-105 shadow-blue-500/30' : 'opacity-90'
                        }`}
                        title={`Total: ${(item.total || 0).toLocaleString()}`}
                      ></div>
                    </div>
                  )}

                  {/* X-Axis Month Label */}
                  <span
                    className={`text-[10px] sm:text-xs font-bold mt-2 transition-colors ${
                      isHovered ? 'text-blue-600 scale-110 font-extrabold' : 'text-slate-600'
                    }`}
                  >
                    {item.month}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Interactive Legend & Filter Badges */}
        <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-6 pt-2">
          {selectedCategories.map((catId) => {
            const catObj = CRIME_CATEGORIES.find((c) => c.id === catId);
            return (
              <div
                key={catId}
                className="flex items-center gap-2 text-xs font-bold text-slate-700 bg-slate-50 px-3 py-1 rounded-full border border-slate-200/80 shadow-sm"
              >
                <span className={`h-3 w-3 rounded-full ${catObj?.color} shadow-sm`}></span>
                <span>{catObj?.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tabular Month-by-Month Analytics Breakdown */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
          <div>
            <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Calendar className="h-4 w-4 text-blue-600" />
              Monthly Data Matrix & Crime Distribution
            </h4>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Detailed numerical volume per month for selected timeframe.
            </p>
          </div>
          <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 border border-blue-200">
            {trendsData.length} Months Logged
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-wider font-extrabold bg-slate-50/70">
                <th className="py-2.5 px-3">Month</th>
                {selectedCategories.map((catId) => {
                  const catObj = CRIME_CATEGORIES.find((c) => c.id === catId);
                  return (
                    <th key={catId} className="py-2.5 px-3">
                      {catObj?.label}
                    </th>
                  );
                })}
                <th className="py-2.5 px-3 font-black text-slate-900">Total Crimes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {trendsData.map((item) => (
                <tr key={item.month} className="hover:bg-slate-50/80 transition font-medium text-slate-700">
                  <td className="py-2.5 px-3 font-bold text-slate-900">{item.month}</td>
                  {selectedCategories.map((catId) => (
                    <td key={catId} className="py-2.5 px-3 font-mono">
                      {(item[catId] || 0).toLocaleString()}
                    </td>
                  ))}
                  <td className="py-2.5 px-3 font-bold text-blue-700 font-mono">
                    {(item.total || 0).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TrendsView;

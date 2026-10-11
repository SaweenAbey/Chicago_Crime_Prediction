import React, { useState, useEffect } from 'react';
import { Calendar, BarChart3 } from 'lucide-react';
import { crimeService, describeApiError } from '../services/crimeService';

const YEARS = [2024, 2025, 2026];
const COLORS = { 2024: '#3b82f6', 2025: '#6366f1', 2026: '#14b8a6' };
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const format = (n) => n.toLocaleString();
const count = (row, category) => category === 'total' ? row.theft + row.battery + row.robbery + row.other : row[category];

const TrendsView = () => {
  const [data, setData] = useState([]);
  const [error, setError] = useState(null);
  const [hoveredMonth, setHoveredMonth] = useState(null);
  const [category, setCategory] = useState('total');
  const [selectedYears, setSelectedYears] = useState(YEARS);
  const [startMonth, setStartMonth] = useState(1);
  const [endMonth, setEndMonth] = useState(12);
  const visibleMonths = MONTHS.map((label, index) => ({ label, number: index + 1 })).filter((m) => m.number >= startMonth && m.number <= endMonth);
  const filteredData = data.filter((r) => selectedYears.includes(r.year) && r.monthNumber >= startMonth && r.monthNumber <= endMonth);
  const coverageEnd = data.find((r) => r.year === 2026)?.coverageEnd;
  const resetFilters = () => { setSelectedYears(YEARS); setStartMonth(1); setEndMonth(12); setCategory('total'); };
  useEffect(() => {
    crimeService.getCrimeTrends().then(setData).catch((err) => setError(describeApiError(err)));
  }, []);
  const yearly = selectedYears.map((year) => {
    const rows = filteredData.filter((r) => r.year === year && r.available);
    return { year, available: rows.length > 0, total: rows.reduce((sum, r) => sum + count(r, category), 0), end: rows[0]?.coverageEnd };
  });
  const maxYear = Math.max(1, ...yearly.map((r) => r.total));
  const chartData = visibleMonths.map(({ label, number }) => {
    const entry = { month: label };
    selectedYears.forEach((year) => {
      const row = filteredData.find((r) => r.year === year && r.monthNumber === number);
      entry[year] = row?.available ? count(row, category) : null;
    });
    return entry;
  });
  const hasChartData = chartData.some((row) => selectedYears.some((year) => row[year] !== null));
  const axisMax = Math.ceil(Math.max(1, ...chartData.flatMap((row) => selectedYears.map((year) => row[year] || 0))) / 1000) * 1000;
  const groupWidth = 1020 / chartData.length;
  const barWidth = Math.min(44, groupWidth * 0.7 / selectedYears.length);
  const hoveredRow = chartData.find((row) => row.month === hoveredMonth);
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-2xl font-extrabold tracking-tight text-slate-900">Historical Crime Trends</h2>
          <p className="mt-1 text-sm text-slate-500">Compare recorded incidents across years and months.</p></div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold"><Calendar className="h-4 w-4 text-blue-600" />2024–2026</span>
          <label className="text-sm text-slate-600">Crime type
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="ml-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-800">
              <option value="total">All crimes</option><option value="theft">Theft</option><option value="battery">Battery</option><option value="robbery">Robbery</option><option value="other">Other crimes</option>
            </select>
          </label>
        </div>
      </div>
      <div className="flex flex-wrap items-end gap-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <fieldset><legend className="mb-2 text-xs font-semibold text-slate-500">Compare years</legend><div className="flex gap-2">
          {YEARS.map((year) => <label key={year} className="flex cursor-pointer items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm font-semibold"><input type="checkbox" checked={selectedYears.includes(year)} disabled={selectedYears.length === 1 && selectedYears.includes(year)} onChange={() => setSelectedYears((current) => current.includes(year) ? current.filter((y) => y !== year) : YEARS.filter((y) => y === year || current.includes(y)))} />{year}</label>)}
        </div></fieldset>
        <label className="text-sm text-slate-600">From month<select className="ml-2 rounded-lg border border-slate-200 px-3 py-2" value={startMonth} onChange={(e) => { const month = Number(e.target.value); setStartMonth(month); if (month > endMonth) setEndMonth(month); }}>{MONTHS.map((month, index) => <option key={month} value={index + 1}>{month}</option>)}</select></label>
        <label className="text-sm text-slate-600">To month<select className="ml-2 rounded-lg border border-slate-200 px-3 py-2" value={endMonth} onChange={(e) => { const month = Number(e.target.value); setEndMonth(month); if (month < startMonth) setStartMonth(month); }}>{MONTHS.map((month, index) => <option key={month} value={index + 1}>{month}</option>)}</select></label>
        <button onClick={resetFilters} className="rounded-lg px-3 py-2 text-sm font-semibold text-blue-600 hover:bg-blue-50">Reset filters</button>
        <p className="w-full text-xs text-slate-500">Filters apply to the totals and graph. Select Jan to Aug to compare complete months across all three years.</p>
      </div>
      {error && <div role="alert" className="rounded-xl bg-rose-50 p-4 text-rose-700">{error}</div>}
      {!error && !data.length && <p role="status" className="text-slate-500">Loading historical records…</p>}
      {!!data.length && <>
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          2026 includes records through {coverageEnd || 'the latest available date'}; September is partial and later months are unavailable. A smaller 2026 total does not necessarily mean crime decreased.
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {yearly.map((row) => <div key={row.year} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-lg font-bold">{row.year}</span><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">{!row.available ? 'No data' : row.year === 2026 && endMonth >= 9 ? 'Partial coverage' : startMonth === 1 && endMonth === 12 ? 'Full year' : 'Selected months'}</span></div>
            <p className="mt-4 text-3xl font-extrabold tracking-tight" style={{ color: COLORS[row.year] }}>{row.available ? format(row.total) : '—'}</p>
            <p className="mt-1 text-xs text-slate-500">{row.available ? `Incidents: ${MONTHS[startMonth - 1]} to ${MONTHS[endMonth - 1]}` : 'Records unavailable'}</p>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full" style={{ width: `${row.total / maxYear * 100}%`, background: COLORS[row.year] }} /></div>
          </div>)}
        </div>
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="flex items-center gap-2 text-lg font-bold"><BarChart3 className="h-5 w-5 text-blue-600" />Monthly comparison</h3>
          <p className="mt-1 text-sm text-slate-500">Each group compares the same month across years. Hover over a bar for its count.</p>
          <div className="mt-5 flex flex-wrap gap-5 text-sm">{selectedYears.map((year) => <span key={year} className="flex items-center gap-2"><span className="h-3 w-3 rounded" style={{ background: COLORS[year] }} />{year}{year === 2026 && endMonth >= 9 ? ' · partial' : ''}</span>)}</div>
          <div className="mt-7 rounded-xl bg-slate-50/60 px-1 py-5 sm:px-3">
            {hasChartData ? <div className="h-80 w-full sm:h-96" role="img" aria-label="Monthly recorded incidents compared by selected year and crime type">
              <div className="relative h-full w-full" onMouseLeave={() => setHoveredMonth(null)}>
                <svg viewBox="0 0 1120 360" className="h-full w-full" preserveAspectRatio="none" aria-label="Monthly comparison bar chart">
                  {[0, 1, 2, 3, 4].map((tick) => {
                    const y = 20 + tick * 72;
                    return <g key={tick}><line x1="70" x2="1090" y1={y} y2={y} stroke="#e2e8f0" strokeDasharray="3 5" /><text x="58" y={y + 4} textAnchor="end" fill="#94a3b8" fontSize="12">{format(axisMax * (1 - tick / 4))}</text></g>;
                  })}
                  {chartData.map((row, index) => {
                    const center = 70 + groupWidth * (index + 0.5);
                    return <g key={row.month} onMouseEnter={() => setHoveredMonth(row.month)}>
                      <rect x={70 + index * groupWidth} y="15" width={groupWidth} height="300" fill={hoveredMonth === row.month ? '#e2e8f0' : 'transparent'} opacity="0.35" rx="8" />
                      {selectedYears.map((year, yearIndex) => {
                        if (row[year] === null) return null;
                        const height = row[year] / axisMax * 288;
                        return <rect key={year} x={center - selectedYears.length * barWidth / 2 + yearIndex * barWidth + 2} y={308 - height} width={Math.max(1, barWidth - 4)} height={height} rx="5" fill={COLORS[year]} tabIndex={0} onFocus={() => setHoveredMonth(row.month)} onBlur={() => setHoveredMonth(null)}><title>{row.month} {year}: {format(row[year])} incidents</title></rect>;
                      })}
                      <text x={center} y="337" textAnchor="middle" fill="#64748b" fontSize="12">{row.month}</text>
                    </g>;
                  })}
                </svg>
                {hoveredRow && <div className="pointer-events-none absolute right-4 top-0 min-w-48 rounded-xl border border-slate-200 bg-white p-4 shadow-xl">
                  <p className="mb-3 text-sm font-bold text-slate-900">{hoveredRow.month} comparison</p>
                  {selectedYears.map((year) => <div key={year} className="my-2 flex items-center justify-between gap-6 text-sm"><span className="flex items-center gap-2 text-slate-600"><span className="h-2.5 w-2.5 rounded-full" style={{ background: COLORS[year] }} />{year}</span><span className="font-semibold">{hoveredRow[year] === null ? 'No data' : format(hoveredRow[year])}</span></div>)}
                  {hoveredRow.month === 'Sep' && selectedYears.includes(2026) && <p className="mt-3 text-xs text-amber-700">September 2026 is partial.</p>}
                </div>}
              </div>
            </div> : <div className="flex h-64 flex-col items-center justify-center text-center"><BarChart3 className="mb-3 h-9 w-9 text-slate-300" /><p className="font-semibold text-slate-700">No records for these filters</p><p className="mt-1 text-sm text-slate-500">Choose another year or month range.</p></div>}
          </div>
          <div className="mt-5 flex flex-wrap justify-between gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500"><span>Recorded incidents per month. Missing records are left blank.</span><span>Source: Chicago crime dataset</span></div>
        </section>
      </>}
    </div>
  );
};
export default TrendsView;

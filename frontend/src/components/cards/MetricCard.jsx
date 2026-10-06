import React from 'react';

const MetricCard = ({ title, value, change, changeType = 'positive', icon: Icon, description }) => {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm hover:shadow-md transition">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{title}</p>
        {Icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600 border border-blue-100">
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <h3 className="text-2xl font-extrabold tracking-tight text-slate-900">{value}</h3>
        {change && (
          <span
            className={`text-xs font-bold px-2 py-0.5 rounded-full ${
              changeType === 'positive'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-rose-50 text-rose-700 border border-rose-200'
            }`}
          >
            {change}
          </span>
        )}
      </div>

      {description && <p className="mt-2 text-xs text-slate-500">{description}</p>}
    </div>
  );
};

export default MetricCard;

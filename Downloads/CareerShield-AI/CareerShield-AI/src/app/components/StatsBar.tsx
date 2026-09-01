import React from 'react';

const stats = [
  { id: 'stat-scans', value: '2.4M+', label: 'Job Postings Scanned', color: 'text-red-400' },
  { id: 'stat-scams', value: '94,821', label: 'Scams Detected', color: 'text-red-400' },
  { id: 'stat-accuracy', value: '98.7%', label: 'Detection Accuracy', color: 'text-emerald-400' },
  { id: 'stat-pii', value: '1.1M+', label: 'PII Records Stripped', color: 'text-amber-400' },
  { id: 'stat-latency', value: '2.4s', label: 'Avg. Scan Latency', color: 'text-slate-300' },
];

export default function StatsBar() {
  return (
    <section className="border-y border-slate-800/60 bg-slate-900/40 py-10 px-6 lg:px-8 xl:px-10 2xl:px-16">
      <div className="max-w-screen-2xl mx-auto">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-8">
          {stats?.map((stat) => (
            <div key={stat?.id} className="text-center">
              <p className={`text-2xl sm:text-3xl font-bold font-mono tabular-nums ${stat?.color} mb-1`}>
                {stat?.value}
              </p>
              <p className="text-xs text-slate-500 font-mono uppercase tracking-wider">{stat?.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
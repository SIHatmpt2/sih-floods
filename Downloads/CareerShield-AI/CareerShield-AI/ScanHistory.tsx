'use client';

import React, { useState } from 'react';
import { Clock, ChevronDown, AlertTriangle, CheckCircle2, AlertCircle } from 'lucide-react';
import type { HistoryEntry } from './ScannerPageClient';

interface ScanHistoryProps {
  history: HistoryEntry[];
}

export default function ScanHistory({ history }: ScanHistoryProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const getRiskBadge = (riskLevel: HistoryEntry['riskLevel'], score: number) => {
    if (riskLevel === 'HIGH_RISK') {
      return {
        icon: <AlertTriangle size={11} className="text-red-400" />,
        label: String(score),
        classes: 'bg-red-500/10 border-red-500/30 text-red-400',
      };
    }
    if (riskLevel === 'SUSPICIOUS') {
      return {
        icon: <AlertCircle size={11} className="text-amber-400" />,
        label: String(score),
        classes: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      };
    }
    return {
      icon: <CheckCircle2 size={11} className="text-emerald-400" />,
      label: String(score),
      classes: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
    };
  };

  return (
    <div className="card-glass rounded-2xl border border-slate-800/60">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-5 hover:bg-slate-800/20 transition-colors duration-200 rounded-t-2xl"
        aria-expanded={isExpanded}
        aria-label="Toggle scan history"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-center">
            <Clock size={15} className="text-slate-400" />
          </div>
          <div className="text-left">
            <h2 className="text-sm font-semibold text-slate-200">Scan History</h2>
            <p className="text-xs font-mono text-slate-600">{history.length} recent scans</p>
          </div>
        </div>
        <ChevronDown
          size={16}
          className={`text-slate-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Table */}
      {isExpanded && (
        <div className="px-5 pb-5 animate-fade-in">
          {history.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm font-mono text-slate-600">No scans yet. Run your first scan above.</p>
            </div>
          ) : (
            <>
              {/* Header row */}
              <div className="hidden sm:grid grid-cols-12 gap-4 px-3 py-2 text-xs font-mono text-slate-600 uppercase tracking-wider border-b border-slate-800/60 mb-2">
                <span className="col-span-1">Score</span>
                <span className="col-span-3">Verdict</span>
                <span className="col-span-6">Preview</span>
                <span className="col-span-2 text-right">Timestamp</span>
              </div>

              {/* Rows */}
              <div className="space-y-1.5">
                {history.map((entry) => {
                  const badge = getRiskBadge(entry.riskLevel, entry.score);
                  return (
                    <div key={entry.id} className="scan-history-row group">
                      <div className="hidden sm:grid grid-cols-12 gap-4 items-center w-full">
                        {/* Score badge */}
                        <div className="col-span-1">
                          <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full border text-xs font-mono font-bold ${badge.classes}`}>
                            {badge.icon}
                            {badge.label}
                          </div>
                        </div>

                        {/* Verdict */}
                        <div className="col-span-3">
                          <p className={`text-xs font-mono truncate ${
                            entry.riskLevel === 'HIGH_RISK' ?'text-red-400'
                              : entry.riskLevel === 'SUSPICIOUS' ?'text-amber-400' :'text-emerald-400'
                          }`}>
                            {entry.riskLevel === 'HIGH_RISK' ? 'HIGH RISK' : entry.riskLevel === 'SUSPICIOUS' ? 'SUSPICIOUS' : 'LIKELY SAFE'}
                          </p>
                        </div>

                        {/* Preview */}
                        <div className="col-span-6">
                          <p className="text-xs text-slate-500 font-mono truncate">{entry.preview}</p>
                        </div>

                        {/* Timestamp */}
                        <div className="col-span-2 text-right">
                          <p className="text-xs font-mono text-slate-600">{entry.timestamp}</p>
                        </div>
                      </div>

                      {/* Mobile layout */}
                      <div className="sm:hidden flex items-start gap-3 w-full">
                        <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full border text-xs font-mono font-bold flex-shrink-0 ${badge.classes}`}>
                          {badge.icon}
                          {badge.label}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={`text-xs font-mono font-semibold mb-0.5 ${
                            entry.riskLevel === 'HIGH_RISK' ? 'text-red-400' : entry.riskLevel === 'SUSPICIOUS' ? 'text-amber-400' : 'text-emerald-400'
                          }`}>
                            {entry.riskLevel === 'HIGH_RISK' ? 'HIGH RISK' : entry.riskLevel === 'SUSPICIOUS' ? 'SUSPICIOUS' : 'LIKELY SAFE'}
                          </p>
                          <p className="text-xs text-slate-500 font-mono truncate">{entry.preview}</p>
                          <p className="text-xs font-mono text-slate-600 mt-0.5">{entry.timestamp}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-800/40 flex items-center justify-between">
                <p className="text-xs font-mono text-slate-600">
                  Showing {history.length} of {history.length} scans · Session only, not persisted
                </p>
                <div className="flex items-center gap-3 text-xs font-mono">
                  <span className="flex items-center gap-1 text-red-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                    {history.filter(h => h.riskLevel === 'HIGH_RISK').length} high risk
                  </span>
                  <span className="flex items-center gap-1 text-amber-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    {history.filter(h => h.riskLevel === 'SUSPICIOUS').length} suspicious
                  </span>
                  <span className="flex items-center gap-1 text-emerald-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    {history.filter(h => h.riskLevel === 'LIKELY_SAFE').length} safe
                  </span>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
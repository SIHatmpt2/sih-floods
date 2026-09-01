'use client';

import React, { useState } from 'react';
import { toast } from 'sonner';
import InputPanel from './InputPanel';
import ResultsPanel from './ResultsPanel';
import ScanHistory from './ScanHistory';

export interface ForensicFlag {
  id: string;
  type: 'danger' | 'warning' | 'safe';
  label: string;
  detail: string;
}

export interface VectorScores {
  communication_security: number;
  financial_risk: number;
  urgency_pressure: number;
  compensation_match: number;
}

export interface ScanResult {
  score: number;
  riskLevel: 'HIGH_RISK' | 'SUSPICIOUS' | 'LIKELY_SAFE';
  verdict: string;
  flags: ForensicFlag[];
  vector_scores: VectorScores;
  action_checklist: string[];
  reasoning: string;
  piiStripped: number;
  piiTypes: string[];
  scanDuration: number;
  model: string;
}

export interface HistoryEntry {
  id: string;
  timestamp: string;
  score: number;
  riskLevel: 'HIGH_RISK' | 'SUSPICIOUS' | 'LIKELY_SAFE';
  verdict: string;
  preview: string;
}

export interface FileData {
  base64: string;
  mimeType: string;
  fileName: string;
}

const INITIAL_HISTORY: HistoryEntry[] = [
  {
    id: 'hist-001',
    timestamp: '2026-08-20 19:44',
    score: 22,
    riskLevel: 'HIGH_RISK',
    verdict: 'HIGH RISK: LIKELY SCAM',
    preview: 'Remote Data Entry Specialist — $8,500/mo, no experience needed...',
  },
  {
    id: 'hist-002',
    timestamp: '2026-08-20 18:12',
    score: 91,
    riskLevel: 'LIKELY_SAFE',
    verdict: 'LIKELY SAFE: LOW FRAUD INDICATORS',
    preview: 'Senior Frontend Engineer at Meridian Systems — 5+ years React...',
  },
  {
    id: 'hist-003',
    timestamp: '2026-08-20 16:55',
    score: 47,
    riskLevel: 'SUSPICIOUS',
    verdict: 'SUSPICIOUS: FURTHER VERIFICATION REQUIRED',
    preview: 'Work from home immediately, earn $5000/week, guaranteed income...',
  },
  {
    id: 'hist-004',
    timestamp: '2026-08-19 22:30',
    score: 88,
    riskLevel: 'LIKELY_SAFE',
    verdict: 'LIKELY SAFE: LOW FRAUD INDICATORS',
    preview: 'Product Manager — Series B fintech, hybrid NYC/remote...',
  },
];

export default function ScannerPageClient() {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [scanHistory, setScanHistory] = useState<HistoryEntry[]>(INITIAL_HISTORY);
  const [inputText, setInputText] = useState('');

  const handleScan = async (text: string, fileData?: FileData) => {
    const hasText = text.trim().length > 0;
    const hasFile = !!fileData;

    if (!hasText && !hasFile) {
      toast.error('Input required', {
        description: 'Please paste a job posting or upload a file to scan.',
      });
      return;
    }

    setIsScanning(true);
    setScanResult(null);
    setInputText(text);

    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, fileData: fileData ?? null }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Scan failed');
      }

      const result: ScanResult = await response.json();
      setScanResult(result);

      const previewSource = text || (fileData ? `[File: ${fileData.fileName}]` : '');
      const newEntry: HistoryEntry = {
        id: `hist-${Date.now()}`,
        timestamp: new Date().toISOString().slice(0, 16).replace('T', ' '),
        score: result.score,
        riskLevel: result.riskLevel,
        verdict: result.verdict,
        preview: previewSource.slice(0, 80) + (previewSource.length > 80 ? '...' : ''),
      };

      setScanHistory((prev) => [newEntry, ...prev.slice(0, 9)]);

      if (result.riskLevel === 'HIGH_RISK') {
        toast.error('High Risk Detected', {
          description: `Trust Score: ${result.score}/100 — ${result.flags.filter(f => f.type === 'danger').length} critical flags found.`,
        });
      } else if (result.riskLevel === 'SUSPICIOUS') {
        toast.warning('Suspicious Signals', {
          description: `Trust Score: ${result.score}/100 — Verify this posting before proceeding.`,
        });
      } else {
        toast.success('Scan Complete', {
          description: `Trust Score: ${result.score}/100 — Low fraud indicators detected.`,
        });
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Scan pipeline failed. Please try again.';
      toast.error('Scan Failed', { description: message });
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">
            Fraud Scanner
            <span className="ml-2 text-xs font-mono text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded-full align-middle">
              LIVE
            </span>
          </h1>
          <p className="text-sm text-slate-500 font-mono">
            CareerShield-v2.1 · Gemini-Pro backend · PII pipeline active
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800/60">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono text-emerald-400">ALL SYSTEMS OPERATIONAL</span>
          </div>
        </div>
      </div>

      {/* Split pane */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <InputPanel onScan={handleScan} isScanning={isScanning} />
        <ResultsPanel result={scanResult} isScanning={isScanning} />
      </div>

      {/* Scan history */}
      <ScanHistory history={scanHistory} />
    </div>
  );
}
'use client';

import React, { useRef, useState } from 'react';
import { Shield, AlertTriangle, CheckCircle2, Clock, Cpu, Download, Square, CheckSquare } from 'lucide-react';
import type { ScanResult, VectorScores } from './ScannerPageClient';
import TrustScoreGauge from './TrustScoreGauge';

interface ResultsPanelProps {
  result: ScanResult | null;
  isScanning: boolean;
}

export default function ResultsPanel({ result, isScanning }: ResultsPanelProps) {
  return (
    <div className="card-glass rounded-2xl border border-slate-800/60 flex flex-col min-h-[520px]">
      {/* Header */}
      <div className="flex items-center justify-between p-5 border-b border-slate-800/60">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-center">
            <Shield size={15} className="text-slate-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Analysis Output</h2>
            <p className="text-xs font-mono text-slate-600">Forensic intelligence report</p>
          </div>
        </div>
        {result && (
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-600">
            <Clock size={11} />
            {(result.scanDuration / 1000).toFixed(1)}s scan
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 p-5">
        {isScanning && <ScanningState />}
        {!isScanning && !result && <EmptyState />}
        {!isScanning && result && <ResultContent result={result} />}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[380px] text-center">
      <div className="relative mb-6">
        <div className="w-20 h-20 rounded-full bg-slate-900/60 border border-slate-800/60 flex items-center justify-center">
          <Shield size={32} className="text-slate-700" />
        </div>
        <div className="absolute inset-0 rounded-full border border-slate-700/20 animate-pulse-slow" />
      </div>
      <h3 className="text-base font-semibold text-slate-500 mb-2">Awaiting Data...</h3>
      <p className="text-xs font-mono text-slate-600 max-w-xs leading-relaxed">
        Paste a job posting, recruiter message, or upload a file in the left panel and click &quot;Scan&quot; to begin forensic analysis.
      </p>
      <div className="mt-6 flex flex-col gap-1.5 text-xs font-mono text-slate-700">
        {['Trust Score (0–100)', '4-Vector Risk Breakdown', 'Forensic Flag Breakdown', 'Action Checklist', 'PII Sanitization Report'].map((item) => (
          <div key={`empty-${item}`} className="flex items-center gap-2">
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

function ScanningState() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[380px] text-center">
      <div className="relative mb-6">
        <div className="w-20 h-20 rounded-full bg-red-500/5 border border-red-500/20 flex items-center justify-center">
          <div className="radar-spin">
            <Shield size={32} className="text-red-400" />
          </div>
        </div>
        {[1, 2, 3].map((i) => (
          <div
            key={`scan-ring-${i}`}
            className="absolute rounded-full border border-red-500/20"
            style={{
              inset: `-${i * 12}px`,
              animation: `pulse-ring ${1.5 + i * 0.4}s ease-out infinite`,
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
      <h3 className="text-base font-semibold text-red-400 font-mono mb-2">
        Analyzing Threat Vectors...
      </h3>
      <div className="space-y-2 text-xs font-mono text-slate-600 mb-6">
        {[
          { step: '01', label: 'Stripping PII identifiers', done: true },
          { step: '02', label: 'Running NLP fraud pattern scan', done: true },
          { step: '03', label: 'Querying Gemini forensic model', done: false },
          { step: '04', label: 'Generating explainable flags', done: false },
        ].map((item) => (
          <div key={`step-${item.step}`} className="flex items-center gap-2">
            {item.done ? (
              <CheckCircle2 size={11} className="text-emerald-500" />
            ) : (
              <span className="w-2.5 h-2.5 rounded-full border border-slate-600 animate-pulse" />
            )}
            <span className="text-slate-500">
              [{item.step}] {item.label}
            </span>
          </div>
        ))}
      </div>
      <div className="w-48 h-1 bg-slate-800 rounded-full overflow-hidden">
        <div className="h-full bg-red-500 rounded-full skeleton-shimmer" style={{ width: '70%' }} />
      </div>
    </div>
  );
}

// ── Vector Score Bar ──────────────────────────────────────────────────────────
interface VectorBarProps {
  label: string;
  score: number;
  description: string;
}

function VectorBar({ label, score, description }: VectorBarProps) {
  const isGreen = score >= 70;
  const isYellow = score >= 40 && score < 70;

  const barColor = isGreen
    ? 'bg-emerald-500'
    : isYellow
    ? 'bg-amber-400' :'bg-red-500';

  const textColor = isGreen
    ? 'text-emerald-400'
    : isYellow
    ? 'text-amber-400' :'text-red-400';

  const glowColor = isGreen
    ? 'shadow-emerald-500/30'
    : isYellow
    ? 'shadow-amber-400/30'
    : 'shadow-red-500/30';

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-mono text-slate-400 font-semibold">{label}</span>
          <span className="ml-2 text-xs font-mono text-slate-600">{description}</span>
        </div>
        <span className={`text-xs font-mono font-bold ${textColor}`}>{score}</span>
      </div>
      <div className="h-1.5 w-full bg-slate-800/80 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out shadow-sm ${barColor} ${glowColor}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

// ── Action Checklist ──────────────────────────────────────────────────────────
interface ActionChecklistProps {
  items: string[];
  riskLevel: 'HIGH_RISK' | 'SUSPICIOUS' | 'LIKELY_SAFE';
}

function ActionChecklist({ items, riskLevel }: ActionChecklistProps) {
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  const toggleItem = (index: number) => {
    setChecked((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const isHighRisk = riskLevel === 'HIGH_RISK';
  const isSuspicious = riskLevel === 'SUSPICIOUS';

  const headerColor = isHighRisk
    ? 'text-red-400 border-red-500/30 bg-red-500/5'
    : isSuspicious
    ? 'text-amber-400 border-amber-500/30 bg-amber-500/5' :'text-emerald-400 border-emerald-500/30 bg-emerald-500/5';

  const checkColor = isHighRisk
    ? 'text-red-400'
    : isSuspicious
    ? 'text-amber-400' :'text-emerald-400';

  const label = isHighRisk
    ? '⚠ PROTECTIVE ACTION CHECKLIST'
    : isSuspicious
    ? '⚠ VERIFICATION CHECKLIST' :'✓ SAFETY HYGIENE CHECKLIST';

  if (!items || items.length === 0) return null;

  return (
    <div className={`rounded-xl border p-4 ${headerColor}`}>
      <p className={`text-xs font-mono font-bold uppercase tracking-widest mb-3 ${isHighRisk ? 'text-red-400' : isSuspicious ? 'text-amber-400' : 'text-emerald-400'}`}>
        {label}
      </p>
      <div className="space-y-2.5">
        {items.map((item, index) => {
          const isDone = checked[index];
          return (
            <button
              key={`checklist-${index}`}
              type="button"
              onClick={() => toggleItem(index)}
              className="w-full flex items-start gap-3 text-left group transition-all duration-150"
              aria-label={`${isDone ? 'Uncheck' : 'Check'}: ${item}`}
            >
              <div className={`flex-shrink-0 mt-0.5 transition-colors duration-150 ${isDone ? checkColor : 'text-slate-600 group-hover:text-slate-400'}`}>
                {isDone ? <CheckSquare size={14} /> : <Square size={14} />}
              </div>
              <span className={`text-xs leading-relaxed transition-all duration-150 ${
                isDone
                  ? 'text-slate-600 line-through' :'text-slate-300 group-hover:text-slate-200'
              }`}>
                {item}
              </span>
            </button>
          );
        })}
      </div>
      <p className="text-xs font-mono text-slate-700 mt-3">
        {Object.values(checked).filter(Boolean).length}/{items.length} steps verified
      </p>
    </div>
  );
}

// ── PDF Export ────────────────────────────────────────────────────────────────
async function exportReportAsPDF(result: ScanResult) {
  const { jsPDF } = await import('jspdf');
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

  const pageW = doc.internal.pageSize.getWidth();
  const margin = 18;
  const contentW = pageW - margin * 2;
  let y = 20;

  const addLine = (extra = 4) => { y += extra; };

  const checkPageBreak = (needed = 20) => {
    if (y + needed > 270) { doc.addPage(); y = 20; }
  };

  // ── Header ──────────────────────────────────────────────────────────────
  doc.setFillColor(15, 23, 42);
  doc.rect(0, 0, pageW, 38, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  doc.setTextColor(248, 250, 252);
  doc.text('CareerShield AI', margin, 16);

  doc.setFont('courier', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(239, 68, 68);
  doc.text('FORENSIC VERIFICATION REPORT', margin, 23);

  doc.setTextColor(100, 116, 139);
  doc.setFontSize(7.5);
  const ts = new Date().toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  });
  doc.text(`Generated: ${ts}`, margin, 30);
  doc.text(`Model: ${result.model}`, pageW - margin, 30, { align: 'right' });
  doc.text(`Scan Duration: ${(result.scanDuration / 1000).toFixed(2)}s`, pageW - margin, 35, { align: 'right' });

  y = 46;

  // ── Trust Score & Verdict ────────────────────────────────────────────────
  const isHighRisk = result.riskLevel === 'HIGH_RISK';
  const isSuspicious = result.riskLevel === 'SUSPICIOUS';

  const scoreColor: [number, number, number] = isHighRisk
    ? [239, 68, 68]
    : isSuspicious
    ? [245, 158, 11]
    : [52, 211, 153];

  doc.setFillColor(30, 41, 59);
  doc.roundedRect(margin, y, contentW, 28, 3, 3, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(28);
  doc.setTextColor(...scoreColor);
  doc.text(`${result.score}`, margin + 10, y + 18);

  doc.setFontSize(10);
  doc.setTextColor(148, 163, 184);
  doc.text('/100', margin + 10 + doc.getTextWidth(`${result.score}`) + 1, y + 18);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.setTextColor(...scoreColor);
  const verdictLines = doc.splitTextToSize(result.verdict, contentW - 55);
  doc.text(verdictLines, margin + 55, y + 10);

  doc.setFont('courier', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(100, 116, 139);
  doc.text('TRUST SCORE', margin + 10, y + 24);

  y += 34;

  // ── 4-Vector Risk Breakdown ──────────────────────────────────────────────
  if (result.vector_scores) {
    checkPageBreak(60);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(148, 163, 184);
    doc.text('4-VECTOR RISK BREAKDOWN', margin, y);
    addLine(6);

    const vectors: Array<{ key: keyof VectorScores; label: string }> = [
      { key: 'communication_security', label: 'Communication Security' },
      { key: 'financial_risk', label: 'Financial Risk' },
      { key: 'urgency_pressure', label: 'Urgency Pressure' },
      { key: 'compensation_match', label: 'Compensation Match' },
    ];

    doc.setFillColor(30, 41, 59);
    doc.roundedRect(margin, y, contentW, vectors.length * 14 + 6, 2, 2, 'F');

    vectors.forEach(({ key, label }, i) => {
      const score = result.vector_scores[key];
      const vy = y + 6 + i * 14;

      const vColor: [number, number, number] = score >= 70
        ? [52, 211, 153]
        : score >= 40
        ? [245, 158, 11]
        : [239, 68, 68];

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8);
      doc.setTextColor(148, 163, 184);
      doc.text(label, margin + 4, vy + 4);

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(...vColor);
      doc.text(`${score}`, pageW - margin - 12, vy + 4);

      // Progress bar background
      const barX = margin + 4;
      const barY = vy + 6;
      const barW = contentW - 20;
      const barH = 2.5;
      doc.setFillColor(51, 65, 85);
      doc.roundedRect(barX, barY, barW, barH, 1, 1, 'F');
      // Progress bar fill
      doc.setFillColor(...vColor);
      doc.roundedRect(barX, barY, (barW * score) / 100, barH, 1, 1, 'F');
    });

    y += vectors.length * 14 + 12;
  }

  // ── Reasoning ────────────────────────────────────────────────────────────
  if (result.reasoning) {
    checkPageBreak(30);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(148, 163, 184);
    doc.text('AI REASONING', margin, y);
    addLine(6);

    doc.setFillColor(15, 23, 42);
    const reasonLines = doc.splitTextToSize(result.reasoning, contentW - 8);
    const reasonBoxH = reasonLines.length * 5 + 8;
    doc.roundedRect(margin, y, contentW, reasonBoxH, 2, 2, 'F');

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8.5);
    doc.setTextColor(203, 213, 225);
    doc.text(reasonLines, margin + 4, y + 6);
    y += reasonBoxH + 8;
  }

  // ── Forensic Flags ───────────────────────────────────────────────────────
  checkPageBreak(20);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(148, 163, 184);
  doc.text(`FORENSIC FLAGS (${result.flags.length})`, margin, y);
  addLine(6);

  for (const flag of result.flags) {
    const flagColor: [number, number, number] =
      flag.type === 'danger' ? [239, 68, 68] :
      flag.type === 'warning' ? [245, 158, 11] :
      [52, 211, 153];

    const prefix = flag.type === 'safe' ? '✓' : flag.type === 'warning' ? '⚠' : '✗';
    const flagLines = doc.splitTextToSize(`${prefix}  ${flag.label}`, contentW - 6);
    const flagBoxH = flagLines.length * 5 + 6;

    checkPageBreak(flagBoxH + 4);

    doc.setFillColor(30, 41, 59);
    doc.roundedRect(margin, y, contentW, flagBoxH, 2, 2, 'F');
    doc.setDrawColor(...flagColor);
    doc.setLineWidth(0.6);
    doc.line(margin, y + 1, margin, y + flagBoxH - 1);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8.5);
    doc.setTextColor(...flagColor);
    doc.text(flagLines, margin + 5, y + 5);

    y += flagBoxH + 3;
  }

  addLine(4);

  // ── Action Checklist ─────────────────────────────────────────────────────
  if (result.action_checklist && result.action_checklist.length > 0) {
    checkPageBreak(20);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(148, 163, 184);
    doc.text('ACTION CHECKLIST', margin, y);
    addLine(6);

    const checklistColor: [number, number, number] = isHighRisk
      ? [239, 68, 68]
      : isSuspicious
      ? [245, 158, 11]
      : [52, 211, 153];

    for (let i = 0; i < result.action_checklist.length; i++) {
      const item = result.action_checklist[i];
      const itemLines = doc.splitTextToSize(`${i + 1}. ${item}`, contentW - 10);
      const itemBoxH = itemLines.length * 5 + 6;

      checkPageBreak(itemBoxH + 4);

      doc.setFillColor(30, 41, 59);
      doc.roundedRect(margin, y, contentW, itemBoxH, 2, 2, 'F');
      doc.setDrawColor(...checklistColor);
      doc.setLineWidth(0.4);
      doc.line(margin, y + 1, margin, y + itemBoxH - 1);

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8.5);
      doc.setTextColor(203, 213, 225);
      doc.text(itemLines, margin + 5, y + 5);

      y += itemBoxH + 3;
    }

    addLine(4);
  }

  // ── PII Status ───────────────────────────────────────────────────────────
  checkPageBreak(22);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(148, 163, 184);
  doc.text('PII SANITIZATION STATUS', margin, y);
  addLine(6);

  doc.setFillColor(15, 23, 42);
  doc.roundedRect(margin, y, contentW, 16, 2, 2, 'F');

  doc.setFont('courier', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(52, 211, 153);
  doc.text('[✓] Personal identifiers successfully stripped before AI processing', margin + 4, y + 6);

  doc.setTextColor(100, 116, 139);
  const piiDetail = result.piiStripped > 0
    ? `Removed: ${result.piiTypes.join(', ')} · ${result.piiStripped} instance${result.piiStripped !== 1 ? 's' : ''} sanitized`
    : 'No PII detected in submitted text — pipeline verified clean';
  doc.text(piiDetail, margin + 4, y + 12);

  y += 22;

  // ── Footer ───────────────────────────────────────────────────────────────
  const footerY = doc.internal.pageSize.getHeight() - 12;
  doc.setDrawColor(30, 41, 59);
  doc.setLineWidth(0.4);
  doc.line(margin, footerY - 4, pageW - margin, footerY - 4);

  doc.setFont('courier', 'normal');
  doc.setFontSize(7);
  doc.setTextColor(71, 85, 105);
  doc.text('CareerShield AI · Confidential Forensic Report · For personal use only', margin, footerY);
  doc.text(`Page 1`, pageW - margin, footerY, { align: 'right' });

  const filename = `careershield-report-${Date.now()}.pdf`;
  doc.save(filename);
}

// ── Result Content ────────────────────────────────────────────────────────────
function ResultContent({ result }: { result: ScanResult }) {
  const isHighRisk = result.riskLevel === 'HIGH_RISK';
  const isSuspicious = result.riskLevel === 'SUSPICIOUS';
  const isSafe = result.riskLevel === 'LIKELY_SAFE';

  const verdictColor = isHighRisk
    ? 'text-red-400'
    : isSuspicious
    ? 'text-amber-400' :'text-emerald-400';

  const verdictBg = isHighRisk
    ? 'bg-red-500/10 border-red-500/30'
    : isSuspicious
    ? 'bg-amber-500/10 border-amber-500/30' :'bg-emerald-500/10 border-emerald-500/30';

  const vectors: Array<{ key: keyof VectorScores; label: string; description: string }> = [
    { key: 'communication_security', label: 'COMM. SECURITY', description: 'channels & contact' },
    { key: 'financial_risk', label: 'FINANCIAL RISK', description: 'fees & transfers' },
    { key: 'urgency_pressure', label: 'URGENCY PRESSURE', description: 'pressure tactics' },
    { key: 'compensation_match', label: 'COMPENSATION', description: 'market alignment' },
  ];

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Trust score + verdict */}
      <div className={`rounded-xl border p-4 ${verdictBg}`}>
        <div className="flex items-center gap-5">
          <TrustScoreGauge score={result.score} riskLevel={result.riskLevel} />
          <div className="flex-1">
            <p className="text-xs font-mono text-slate-500 mb-1 uppercase tracking-widest">VERDICT</p>
            <p className={`text-sm font-bold font-mono ${verdictColor} leading-tight mb-2`}>
              {result.verdict}
            </p>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                <Cpu size={11} className="text-slate-600" />
                <span className="text-xs font-mono text-slate-600">{result.model}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4-Vector Risk Breakdown */}
      {result.vector_scores && (
        <div className="rounded-xl bg-slate-900/60 border border-slate-700/40 p-4">
          <p className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-3">
            4-VECTOR RISK BREAKDOWN
          </p>
          <div className="space-y-3">
            {vectors.map(({ key, label, description }) => (
              <VectorBar
                key={key}
                label={label}
                score={result.vector_scores[key]}
                description={description}
              />
            ))}
          </div>
          <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-800/60">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-xs font-mono text-slate-600">≥70 Safe</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <span className="text-xs font-mono text-slate-600">40–69 Caution</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-xs font-mono text-slate-600">&lt;40 Risk</span>
            </div>
          </div>
        </div>
      )}

      {/* Reasoning */}
      {result.reasoning && (
        <div className="rounded-lg bg-slate-900/60 border border-slate-700/40 p-3">
          <p className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-1.5">AI REASONING</p>
          <p className="text-xs text-slate-300 leading-relaxed">{result.reasoning}</p>
        </div>
      )}

      {/* Forensic flags */}
      <div>
        <p className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-3">
          FORENSIC FLAGS ({result.flags.length})
        </p>
        <div className="space-y-2">
          {result.flags.map((flag) => (
            <div
              key={flag.id}
              className={`${
                flag.type === 'danger' ?'forensic-flag-danger'
                  : flag.type === 'warning' ?'forensic-flag-warning' :'forensic-flag-safe'
              }`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {flag.type === 'danger' ? (
                  <AlertTriangle size={13} className="text-red-400" />
                ) : flag.type === 'warning' ? (
                  <AlertTriangle size={13} className="text-amber-400" />
                ) : (
                  <CheckCircle2 size={13} className="text-emerald-400" />
                )}
              </div>
              <div className="min-w-0">
                <p
                  className={`text-xs font-semibold mb-0.5 ${
                    flag.type === 'danger' ?'text-red-300'
                      : flag.type === 'warning' ?'text-amber-300' :'text-emerald-300'
                  }`}
                >
                  {flag.label}
                </p>
                <p className="text-xs font-mono text-slate-500 leading-relaxed">{flag.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Checklist */}
      {result.action_checklist && result.action_checklist.length > 0 && (
        <ActionChecklist items={result.action_checklist} riskLevel={result.riskLevel} />
      )}

      {/* PII status */}
      <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3">
        <div className="flex items-start gap-2">
          <CheckCircle2 size={13} className="text-emerald-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-mono text-emerald-400 mb-1">
              [✓] Personal identifiers successfully stripped before AI processing
            </p>
            {result.piiStripped > 0 ? (
              <p className="text-xs font-mono text-slate-600">
                Removed: {result.piiTypes.join(', ')} · {result.piiStripped} instance{result.piiStripped !== 1 ? 's' : ''} sanitized
              </p>
            ) : (
              <p className="text-xs font-mono text-slate-600">
                No PII detected in submitted text — pipeline verified clean
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Export Report Button */}
      <button
        onClick={() => exportReportAsPDF(result)}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300 text-xs font-mono font-semibold hover:bg-slate-700/80 hover:border-slate-600/60 hover:text-slate-100 transition-all duration-200 group"
      >
        <Download size={13} className="group-hover:text-emerald-400 transition-colors" />
        Export Scan Report (PDF)
      </button>
    </div>
  );
}
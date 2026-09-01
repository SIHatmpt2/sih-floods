import React from 'react';
import { AlertTriangle, CheckCircle2, Shield, FileText, Zap, Eye } from 'lucide-react';
import Icon from '@/components/ui/AppIcon';


const exampleFlags = [
  {
    id: 'flag-ex-001',
    type: 'danger' as const,
    label: 'Wire transfer requested before employment',
    detail: '"Please wire $250 processing fee to receive your equipment kit"',
  },
  {
    id: 'flag-ex-002',
    type: 'danger' as const,
    label: 'Off-platform redirect detected',
    detail: '"Contact us only via Telegram @recruiter_fast — no email"',
  },
  {
    id: 'flag-ex-003',
    type: 'safe' as const,
    label: 'Standard background check process',
    detail: 'References to Checkr, HireRight, or similar verified BGC providers',
  },
  {
    id: 'flag-ex-004',
    type: 'danger' as const,
    label: 'Urgency pressure: "Immediate hire, apply today"',
    detail: 'Artificial scarcity language designed to bypass due diligence',
  },
];

const howItWorks = [
  {
    id: 'step-1',
    step: '01',
    icon: FileText,
    title: 'Paste Any Job Text',
    description: 'Job descriptions, recruiter DMs, offer letters, or LinkedIn messages — any format works.',
  },
  {
    id: 'step-2',
    step: '02',
    icon: Shield,
    title: 'PII Stripped Locally',
    description: 'Your name, email, and phone are removed before the text is sent to any AI model.',
  },
  {
    id: 'step-3',
    step: '03',
    icon: Zap,
    title: 'AI Forensic Analysis',
    description: 'Multi-model ensemble checks for 47 known fraud patterns, linguistic manipulation, and financial signals.',
  },
  {
    id: 'step-4',
    step: '04',
    icon: Eye,
    title: 'Explainable Results',
    description: 'Trust Score with attributed flags — you see exactly why each risk signal was triggered.',
  },
];

export default function FeatureDeepDive() {
  return (
    <section id="features" className="px-6 py-20 max-w-screen-2xl mx-auto lg:px-8 xl:px-10 2xl:px-16">
      {/* How it works */}
      <div className="mb-20">
        <div className="text-center mb-12">
          <p className="text-xs font-mono text-red-400 uppercase tracking-widest mb-3">
            SCAN PIPELINE
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-100 mb-4">
            How the Analysis Works
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {howItWorks.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div key={step.id} className="relative">
                {idx < howItWorks.length - 1 && (
                  <div className="hidden lg:block absolute top-8 left-full w-full h-px bg-gradient-to-r from-slate-700 to-transparent z-10" />
                )}
                <div className="card-glass rounded-2xl p-6 border border-slate-800/60 card-glass-hover">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-xs font-mono text-slate-600 font-bold">{step.step}</span>
                    <div className="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center">
                      <Icon size={18} className="text-red-400" />
                    </div>
                  </div>
                  <h3 className="text-sm font-semibold text-slate-200 mb-2">{step.title}</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Example forensic flags */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div>
          <p className="text-xs font-mono text-red-400 uppercase tracking-widest mb-3">
            FORENSIC FLAG EXAMPLES
          </p>
          <h2 className="text-3xl font-bold text-slate-100 mb-4">
            Every Flag Is Explained
          </h2>
          <p className="text-slate-500 mb-8 leading-relaxed">
            CareerShield AI doesn&apos;t just say &quot;this looks suspicious&quot; — it shows you the exact phrase, pattern, or signal that triggered each alert, with context on why it matters.
          </p>
          <div className="space-y-3">
            {exampleFlags.map((flag) => (
              <div
                key={flag.id}
                className={`${
                  flag.type === 'danger' ? 'forensic-flag-danger' : 'forensic-flag-safe'
                }`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {flag.type === 'danger' ? (
                    <AlertTriangle size={15} className="text-red-400" />
                  ) : (
                    <CheckCircle2 size={15} className="text-emerald-400" />
                  )}
                </div>
                <div>
                  <p className={`text-xs font-semibold mb-1 ${flag.type === 'danger' ? 'text-red-300' : 'text-emerald-300'}`}>
                    {flag.label}
                  </p>
                  <p className="text-xs font-mono text-slate-500">{flag.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Example score card */}
        <div className="card-glass rounded-2xl p-8 border border-slate-800/60">
          <div className="text-center mb-6">
            <p className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-4">TRUST SCORE OUTPUT</p>
            <div className="relative inline-flex items-center justify-center mb-4">
              <svg width="140" height="140" viewBox="0 0 140 140">
                <defs>
                  <linearGradient id="dangerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#b91c1c" />
                    <stop offset="100%" stopColor="#f87171" />
                  </linearGradient>
                </defs>
                <circle cx="70" cy="70" r="54" fill="none" stroke="rgba(239,68,68,0.08)" strokeWidth="10" />
                <circle
                  cx="70"
                  cy="70"
                  r="54"
                  fill="none"
                  stroke="url(#dangerGrad)"
                  strokeWidth="10"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 54 * 0.18} ${2 * Math.PI * 54}`}
                  style={{ filter: 'drop-shadow(0 0 8px rgba(239,68,68,0.7))' }}
                  transform="rotate(-90 70 70)"
                />
                <text x="70" y="64" textAnchor="middle" fill="#ef4444" fontSize="28" fontWeight="700" fontFamily="Fira Code, monospace">18</text>
                <text x="70" y="82" textAnchor="middle" fill="#64748b" fontSize="11" fontFamily="Fira Code, monospace">/100</text>
              </svg>
            </div>
            <p className="text-red-400 font-bold text-sm font-mono tracking-wide">HIGH RISK: LIKELY SCAM</p>
          </div>
          <div className="space-y-2 mb-4">
            {['Wire transfer detected', 'Telegram redirect found', 'Salary implausible (+340%)'].map((flag) => (
              <div key={`ex-flag-${flag}`} className="forensic-flag-danger">
                <AlertTriangle size={13} className="text-red-400 flex-shrink-0 mt-0.5" />
                <span className="text-xs font-mono text-slate-400">{flag}</span>
              </div>
            ))}
          </div>
          <div className="border-t border-slate-800/60 pt-3">
            <p className="text-xs font-mono text-emerald-500 text-center">
              [✓] 3 PII identifiers stripped before AI processing
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
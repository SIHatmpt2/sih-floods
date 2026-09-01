import React from 'react';
import Link from 'next/link';
import { Shield, Radar, ChevronRight, Lock } from 'lucide-react';

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center px-6 pt-24 pb-16 text-center">
      {/* Animated radar rings */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
        {[1, 2, 3, 4]?.map((i) => (
          <div
            key={`ring-${i}`}
            className="absolute rounded-full border border-red-500/10"
            style={{
              width: `${i * 200}px`,
              height: `${i * 200}px`,
              animation: `pulse-ring ${2 + i * 0.5}s ease-out infinite`,
              animationDelay: `${i * 0.3}s`,
            }}
          />
        ))}
      </div>
      {/* Badge */}
      <div className="animate-fade-in-up mb-6">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
          REAL-TIME THREAT INTELLIGENCE ACTIVE
          <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
        </div>
      </div>
      {/* Main headline */}
      <div className="animate-fade-in-up max-w-4xl mx-auto mb-6" style={{ animationDelay: '0.1s' }}>
        <h1 className="text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-bold tracking-tight leading-none mb-2">
          <span className="text-slate-100">CareerShield</span>
          <span className="text-red-500 text-glow-red"> AI</span>
          <span className="text-slate-600">.</span>
        </h1>
      </div>
      {/* Subheadline */}
      <div className="animate-fade-in-up max-w-2xl mx-auto mb-10" style={{ animationDelay: '0.2s' }}>
        <p className="text-lg sm:text-xl text-slate-400 leading-relaxed">
          Real-time, explainable AI that{' '}
          <span className="text-slate-200 font-medium">scores every job posting</span>{' '}
          and recruiter message for fraud—
          <span className="text-slate-200 font-medium">before you ever apply</span>.
        </p>
      </div>
      {/* CTA buttons */}
      <div className="animate-fade-in-up flex flex-col sm:flex-row items-center gap-4 mb-16" style={{ animationDelay: '0.3s' }}>
        <Link
          href="/scanner-dashboard"
          className="btn-primary-glow flex items-center gap-2.5 px-8 py-4 rounded-xl text-base font-semibold text-white group"
        >
          <Radar size={18} className="group-hover:rotate-12 transition-transform duration-300" />
          Launch Scanner
          <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform duration-200" />
        </Link>
        <a
          href="#features"
          className="flex items-center gap-2 px-8 py-4 rounded-xl text-base font-medium text-slate-400 border border-slate-700/60 hover:border-slate-600 hover:text-slate-200 transition-all duration-200"
        >
          <Shield size={18} />
          How It Works
        </a>
      </div>
      {/* Mini trust indicators */}
      <div className="animate-fade-in-up flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500" style={{ animationDelay: '0.4s' }}>
        {[
          { icon: <Lock size={13} />, label: 'PII Stripped Before Processing' },
          { icon: <Shield size={13} />, label: 'Zero Data Retention' },
          { icon: <Radar size={13} />, label: '2.4s Average Scan Time' },
        ]?.map((item) => (
          <div key={`trust-${item?.label}`} className="flex items-center gap-1.5">
            <span className="text-slate-600">{item?.icon}</span>
            <span className="font-mono text-xs">{item?.label}</span>
          </div>
        ))}
      </div>
      {/* Preview card */}
      <div className="animate-fade-in-up mt-16 w-full max-w-lg" style={{ animationDelay: '0.5s' }}>
        <div className="card-glass rounded-2xl p-6 border border-slate-800/80">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-mono text-slate-500 uppercase tracking-widest">SAMPLE ANALYSIS OUTPUT</span>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
              <span className="text-xs font-mono text-red-400">HIGH RISK</span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            {/* Mini score ring */}
            <div className="relative flex-shrink-0">
              <svg width="72" height="72" viewBox="0 0 72 72">
                <circle cx="36" cy="36" r="28" fill="none" stroke="rgba(239,68,68,0.1)" strokeWidth="6" />
                <circle
                  cx="36"
                  cy="36"
                  r="28"
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 28 * 0.18} ${2 * Math.PI * 28}`}
                  strokeDashoffset={2 * Math.PI * 28 * 0.25}
                  style={{ filter: 'drop-shadow(0 0 6px rgba(239,68,68,0.6))' }}
                  transform="rotate(-90 36 36)"
                />
                <text x="36" y="40" textAnchor="middle" fill="#ef4444" fontSize="14" fontWeight="700" fontFamily="Fira Code, monospace">18</text>
              </svg>
            </div>
            <div className="flex-1 text-left">
              <p className="text-xs font-mono text-red-400 mb-2 font-semibold">HIGH RISK: LIKELY SCAM</p>
              <div className="space-y-1.5">
                {[
                  'Wire transfer requested pre-hire',
                  'Telegram-only communication',
                  'Salary 400% above benchmark',
                ]?.map((flag) => (
                  <div key={`preview-${flag}`} className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                    <span className="text-red-500">⚠</span>
                    <span className="truncate">{flag}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
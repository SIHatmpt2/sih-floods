import React from 'react';
import { Radar, BarChart3, Lock } from 'lucide-react';
import Icon from '@/components/ui/AppIcon';


const valueProps = [
  {
    id: 'prop-multimodal',
    icon: Radar,
    iconColor: 'text-red-400',
    iconBg: 'bg-red-500/10 border-red-500/20',
    title: 'Real-Time Multimodal Scan',
    description:
      'Analyzes job descriptions, recruiter emails, and offer letters simultaneously. Detects linguistic manipulation, financial fraud signals, and identity harvesting patterns in under 3 seconds.',
    tags: ['NLP Analysis', 'Pattern Matching', 'Behavioral Signals'],
    tagColor: 'bg-red-500/10 text-red-400',
  },
  {
    id: 'prop-trust-score',
    icon: BarChart3,
    iconColor: 'text-amber-400',
    iconBg: 'bg-amber-500/10 border-amber-500/20',
    title: 'Explainable Trust Score',
    description:
      'Every score comes with a forensic breakdown of exactly which phrases, patterns, and signals triggered each flag. No black-box verdicts — every decision is traceable and auditable.',
    tags: ['0–100 Risk Score', 'Flag Attribution', 'Confidence Level'],
    tagColor: 'bg-amber-500/10 text-amber-400',
  },
  {
    id: 'prop-pii',
    icon: Lock,
    iconColor: 'text-emerald-400',
    iconBg: 'bg-emerald-500/10 border-emerald-500/20',
    title: 'PII-Sanitized Pipeline',
    description:
      'Your name, email, phone number, and other identifiers are stripped before any text reaches the AI model. We analyze the job, not you. Zero personal data retained post-scan.',
    tags: ['GDPR Aligned', 'Zero Retention', 'Pre-AI Scrubbing'],
    tagColor: 'bg-emerald-500/10 text-emerald-400',
  },
];

export default function ValuePropsGrid() {
  return (
    <section className="px-6 py-20 max-w-screen-2xl mx-auto lg:px-8 xl:px-10 2xl:px-16">
      <div className="text-center mb-12">
        <p className="text-xs font-mono text-red-400 uppercase tracking-widest mb-3">
          DETECTION CAPABILITIES
        </p>
        <h2 className="text-3xl sm:text-4xl font-bold text-slate-100 mb-4">
          Three Layers of Protection
        </h2>
        <p className="text-slate-500 max-w-lg mx-auto">
          Every scan runs all three analysis modules simultaneously, giving you a complete threat picture in seconds.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {valueProps?.map((prop) => {
          const Icon = prop?.icon;
          return (
            <div
              key={prop?.id}
              className="card-glass rounded-2xl p-6 card-glass-hover group border border-slate-800/60"
            >
              {/* Icon */}
              <div className={`w-12 h-12 rounded-xl border ${prop?.iconBg} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300`}>
                <Icon size={22} className={prop?.iconColor} />
              </div>
              {/* Title */}
              <h3 className="text-lg font-semibold text-slate-100 mb-3">{prop?.title}</h3>
              {/* Description */}
              <p className="text-sm text-slate-500 leading-relaxed mb-5">{prop?.description}</p>
              {/* Tags */}
              <div className="flex flex-wrap gap-2">
                {prop?.tags?.map((tag) => (
                  <span
                    key={`${prop?.id}-tag-${tag}`}
                    className={`text-xs font-mono px-2.5 py-1 rounded-full ${prop?.tagColor} border border-current/20`}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
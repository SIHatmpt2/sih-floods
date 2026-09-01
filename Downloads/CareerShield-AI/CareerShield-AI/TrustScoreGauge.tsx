'use client';

import React, { useEffect, useState } from 'react';

interface TrustScoreGaugeProps {
  score: number;
  riskLevel: 'HIGH_RISK' | 'SUSPICIOUS' | 'LIKELY_SAFE';
}

export default function TrustScoreGauge({ score, riskLevel }: TrustScoreGaugeProps) {
  const [displayScore, setDisplayScore] = useState(0);
  const [animated, setAnimated] = useState(false);

  const isHighRisk = riskLevel === 'HIGH_RISK';
  const isSuspicious = riskLevel === 'SUSPICIOUS';

  const strokeColor = isHighRisk ? '#ef4444' : isSuspicious ? '#f59e0b' : '#34d399';
  const glowColor = isHighRisk
    ? 'rgba(239,68,68,0.7)'
    : isSuspicious
    ? 'rgba(245,158,11,0.7)'
    : 'rgba(52,211,153,0.7)';
  const trackColor = isHighRisk
    ? 'rgba(239,68,68,0.08)'
    : isSuspicious
    ? 'rgba(245,158,11,0.08)'
    : 'rgba(52,211,153,0.08)';

  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const fraction = displayScore / 100;
  const strokeDasharray = `${circumference * fraction} ${circumference}`;

  useEffect(() => {
    setDisplayScore(0);
    setAnimated(false);

    const timeout = setTimeout(() => {
      setAnimated(true);
      let current = 0;
      const increment = Math.ceil(score / 30);
      const interval = setInterval(() => {
        current = Math.min(current + increment, score);
        setDisplayScore(current);
        if (current >= score) clearInterval(interval);
      }, 40);
      return () => clearInterval(interval);
    }, 100);

    return () => clearTimeout(timeout);
  }, [score]);

  return (
    <div className="relative flex-shrink-0">
      <svg
        width="96"
        height="96"
        viewBox="0 0 96 96"
        style={{ filter: animated ? `drop-shadow(0 0 8px ${glowColor})` : 'none', transition: 'filter 0.5s ease' }}
      >
        <defs>
          <linearGradient id={`gauge-grad-${riskLevel}`} x1="0%" y1="0%" x2="100%" y2="100%">
            {isHighRisk ? (
              <>
                <stop offset="0%" stopColor="#b91c1c" />
                <stop offset="100%" stopColor="#f87171" />
              </>
            ) : isSuspicious ? (
              <>
                <stop offset="0%" stopColor="#d97706" />
                <stop offset="100%" stopColor="#fcd34d" />
              </>
            ) : (
              <>
                <stop offset="0%" stopColor="#059669" />
                <stop offset="100%" stopColor="#6ee7b7" />
              </>
            )}
          </linearGradient>
        </defs>

        {/* Track */}
        <circle
          cx="48"
          cy="48"
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth="8"
        />

        {/* Progress arc */}
        <circle
          cx="48"
          cy="48"
          r={radius}
          fill="none"
          stroke={`url(#gauge-grad-${riskLevel})`}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={strokeDasharray}
          transform="rotate(-90 48 48)"
          style={{ transition: 'stroke-dasharray 0.05s linear' }}
        />

        {/* Score text */}
        <text
          x="48"
          y="44"
          textAnchor="middle"
          fill={strokeColor}
          fontSize="18"
          fontWeight="700"
          fontFamily="Fira Code, monospace"
          className="score-counter"
        >
          {displayScore}
        </text>
        <text
          x="48"
          y="58"
          textAnchor="middle"
          fill="#475569"
          fontSize="9"
          fontFamily="Fira Code, monospace"
        >
          /100
        </text>
      </svg>
    </div>
  );
}
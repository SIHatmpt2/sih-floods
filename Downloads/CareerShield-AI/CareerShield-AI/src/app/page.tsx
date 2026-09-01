import React from 'react';
import Topbar from '@/components/Topbar';
import HeroSection from './components/HeroSection';
import ValuePropsGrid from './components/ValuePropsGrid';
import StatsBar from './components/StatsBar';
import FeatureDeepDive from './components/FeatureDeepDive';
import LandingFooterCTA from './components/LandingFooterCTA';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background grid-bg relative overflow-hidden">
      {/* Noise overlay */}
      <div className="fixed inset-0 noise-overlay pointer-events-none z-0" />

      {/* Ambient glow orbs */}
      <div
        className="fixed top-0 left-1/4 w-96 h-96 rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(239,68,68,0.06) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />
      <div
        className="fixed bottom-1/4 right-1/4 w-80 h-80 rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(52,211,153,0.04) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />

      <Topbar />

      <main className="relative z-10">
        <HeroSection />
        <ValuePropsGrid />
        <StatsBar />
        <FeatureDeepDive />
        <LandingFooterCTA />
      </main>
    </div>
  );
}
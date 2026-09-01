import React from 'react';
import Topbar from '@/components/Topbar';
import ScannerPageClient from './components/ScannerPageClient';

export default function ScannerDashboardPage() {
  return (
    <div className="min-h-screen bg-background grid-bg relative overflow-hidden">
      {/* Ambient glow */}
      <div
        className="fixed top-1/4 left-0 w-64 h-64 pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(239,68,68,0.05) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />
      <div
        className="fixed bottom-1/3 right-0 w-64 h-64 pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(52,211,153,0.04) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />
      <Topbar />
      <main className="relative z-10 pt-20 pb-16 px-6 lg:px-8 xl:px-10 2xl:px-16 max-w-screen-2xl mx-auto">
        <ScannerPageClient />
      </main>
    </div>
  );
}
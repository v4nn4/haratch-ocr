"use client";

import React, { useState, useEffect } from 'react';
import ComputationGrid from '@/components/ComputationGrid';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Loader2, RefreshCw, Layers, CheckCircle2, Clock, Terminal, Eye, EyeOff } from 'lucide-react';
import OCRFeed from '@/components/OCRFeed';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [runner, setRunner] = useState<any>({ status: 'idle', ram_mb: 0, disk_mb: 0 });
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [feedEnabled, setFeedEnabled] = useState(true);

  const fetchData = async () => {
    try {
      // Fetch both data and runner status
      const [resStatus, resRunner] = await Promise.all([
        fetch('/api/status'),
        fetch('/api/runner')
      ]);

      const result = await resStatus.json();
      const runnerData = await resRunner.json();

      setData(result);
      setRunner(runnerData);
      setLastUpdated(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background text-zinc-500">
        <Loader2 className="w-12 h-12 animate-spin mb-4 text-blue-500" />
        <p className="text-lg font-medium animate-pulse opacity-50 uppercase tracking-widest">Initialising System...</p>
      </div>
    );
  }

  const totalIssues = data ? Object.keys(data).length : 0;
  const completedIssues = data ? Object.values(data).filter((i: any) => i.isComplete).length : 0;
  const totalPages = data ? Object.values(data).reduce((acc: number, i: any) => acc + i.pages.length, 0) : 0;

  // Global Archive Stats (Aug 1925 to May 2009)
  const ARCHIVE_TOTAL_MONTHS = 1006;
  const completionRate = (completedIssues / ARCHIVE_TOTAL_MONTHS) * 100;

  const remainingIssues = ARCHIVE_TOTAL_MONTHS - completedIssues;
  const pace = runner.pace || 0;
  const etaHours = pace > 0 ? remainingIssues / pace : null;

  return (
    <main className="min-h-screen bg-background text-foreground p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b border-border pb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight text-foreground uppercase">
                Haratch Archive OCR
              </h1>
              <div className={`px-2 py-0.5 text-[10px] font-bold rounded-sm border uppercase tracking-wider ${String(runner?.status || '').startsWith('processing') || runner?.status === 'active'
                ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20 animate-pulse'
                : 'bg-zinc-500/10 text-zinc-500 border-zinc-500/20'
                }`}>
                {runner.status}
              </div>
            </div>
            <p className="text-zinc-500 mt-1 flex items-center gap-2 text-sm">
              <Clock className="w-3.5 h-3.5" />
              GCS MONITORING SYSTEM
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-end gap-1">
              <div className="flex items-center gap-3 text-[10px] font-mono text-zinc-400 uppercase">
                <span>RAM: {Math.round(runner.ram_mb || 0)}MB</span>
                <span className="w-px h-2 bg-border" />
                <span>DISK: {Math.round(runner.disk_mb || 0)}MB / 1024MB</span>
              </div>
              <div className="w-32 h-1 bg-zinc-100 dark:bg-zinc-900 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${(runner.disk_mb || 0) > 800 ? 'bg-amber-500' : 'bg-blue-500'}`}
                  style={{ width: `${Math.min(((runner.disk_mb || 0) / 1024) * 100, 100)}%` }}
                />
              </div>
            </div>
            <ThemeToggle />
            <div className="flex items-center gap-3 text-[11px] font-mono text-zinc-500 bg-background border border-border px-3 py-1.5 rounded-sm shadow-sm uppercase">
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
              Last updated: {lastUpdated?.toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-background border border-border p-6 rounded-sm shadow-sm">
            <div className="flex items-center gap-3 mb-2 text-blue-600 dark:text-blue-500">
              <Layers className="w-4 h-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider">Processed Pages</h3>
            </div>
            <p className="text-4xl font-light tracking-tight">{totalPages.toLocaleString()}</p>
          </div>

          <div className="bg-background border border-border p-6 rounded-sm shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3 text-emerald-600 dark:text-emerald-500">
                <CheckCircle2 className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-wider">Archive Coverage</h3>
              </div>
              <span className="text-xs font-mono font-bold text-emerald-600/50">{completionRate.toFixed(1)}%</span>
            </div>
            <p className="text-4xl font-light tracking-tight">{completedIssues} <span className="text-sm text-zinc-400 font-normal">/ {ARCHIVE_TOTAL_MONTHS}</span></p>
            <div className="mt-4 w-full h-1 bg-zinc-100 dark:bg-zinc-900 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-1000"
                style={{ width: `${completionRate}%` }}
              />
            </div>
          </div>

          <div className="bg-background border border-border p-6 rounded-sm shadow-sm">
            <div className="flex items-center gap-3 mb-2 text-amber-500">
              <RefreshCw className={`w-4 h-4 ${pace > 0 ? 'animate-spin-slow' : ''}`} />
              <h3 className="text-xs font-bold uppercase tracking-wider">Processing Pace</h3>
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-4xl font-light tracking-tight">{pace > 0 ? pace.toFixed(1) : '--'}</p>
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Issues / Hr</span>
            </div>
            {etaHours !== null && (
              <p className="mt-2 text-[10px] font-mono text-zinc-500 uppercase">
                Est. Completion: <span className="text-zinc-700 dark:text-zinc-300 font-bold">{Math.round(etaHours / 24)} days</span> ({Math.round(etaHours)} hrs)
              </p>
            )}
          </div>

          <div className="bg-background border border-border p-6 rounded-sm shadow-sm">
            <div className="flex items-center gap-3 mb-2 text-zinc-500">
              <Clock className="w-4 h-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider">Runner Health</h3>
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-4xl font-light tracking-tight">{Math.round((runner.ram_mb || 0))} </p>
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">MB RAM</span>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          {/* Progress Map (Takes 2/3 space on large screens) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h2 className="text-sm font-bold uppercase tracking-widest text-zinc-500">Computation Progress Map</h2>
              <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-wider">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 bg-zinc-200 dark:bg-zinc-800" />
                  <span className="text-zinc-400">Queued</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 bg-blue-500" />
                  <span className="text-zinc-400">Processing</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 bg-emerald-500" />
                  <span className="text-zinc-400">Complete</span>
                </div>
              </div>
            </div>
            <ComputationGrid data={data} />
          </div>

          {/* Live Feed (Takes 1/3 space on large screens) */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h2 className="text-sm font-bold uppercase tracking-widest text-zinc-500">Live OCR Stream</h2>
              <div className="flex items-center gap-2">
                {feedEnabled && (
                  <div className="px-2 py-0.5 text-[9px] font-bold rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 animate-pulse uppercase">
                    Live Data
                  </div>
                )}
                <button
                  onClick={() => setFeedEnabled(!feedEnabled)}
                  className={`p-1.5 rounded-sm border transition-colors ${feedEnabled
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500 hover:bg-emerald-500/20'
                    : 'bg-zinc-800 border-zinc-700 text-zinc-500 hover:bg-zinc-700'
                    }`}
                  title={feedEnabled ? 'Hide OCR Feed' : 'Show OCR Feed'}
                >
                  {feedEnabled ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                </button>
              </div>
            </div>
            {feedEnabled ? (
              <OCRFeed latestSnippet={runner?.latest_ocr} currentPage={runner?.current_page} />
            ) : (
              <div className="bg-zinc-100 dark:bg-zinc-950 border border-border rounded-sm h-[400px] flex flex-col items-center justify-center text-zinc-400 dark:text-zinc-600">
                <EyeOff className="w-8 h-8 mb-2 opacity-30" />
                <p className="text-[10px] uppercase tracking-widest">Feed Disabled</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

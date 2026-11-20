"use client";

import React from "react";
import { ShieldAlert, ShieldCheck, AlertTriangle, TrendingDown } from "lucide-react";

interface RadialRiskScoreProps {
  score: number; // e.g. 12 or 38
  maxScore?: number;
  verifiedCount: number;
  unverifiableCount: number;
  inconsistentCount: number;
  className?: string;
}

export default function RadialRiskScore({
  score,
  maxScore = 100,
  verifiedCount,
  unverifiableCount,
  inconsistentCount,
  className = "",
}: RadialRiskScoreProps) {
  const totalClaims = verifiedCount + unverifiableCount + inconsistentCount || 1;
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const progressPercent = Math.min(Math.max(score / maxScore, 0), 1);
  const strokeDashoffset = circumference - progressPercent * circumference;

  // Severity color
  const isLow = score <= 25;
  const isModerate = score > 25 && score <= 60;
  const scoreColor = isLow ? "#00F5A0" : isModerate ? "#F59E0B" : "#EF4444";
  const scoreLabel = isLow ? "LOW RESIDUAL RISK" : isModerate ? "MODERATE RISK" : "CRITICAL RISK";

  return (
    <div className={`p-6 rounded-2xl bg-[#0D1317] border border-slate-800 flex flex-col items-center justify-between relative overflow-hidden shadow-2xl ${className}`}>
      {/* Background Accent Grid */}
      <div className="absolute inset-0 tech-grid opacity-15 pointer-events-none" />

      {/* Top Header */}
      <div className="w-full flex items-center justify-between border-b border-slate-800/80 pb-3 mb-4 font-mono text-xs text-slate-400">
        <span className="flex items-center gap-1.5 uppercase tracking-widest text-[10px]">
          <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: scoreColor }} />
          RISK ENGINE · DETERMINISTIC
        </span>
        <span className="text-slate-500 font-bold">VERDICT v1.0</span>
      </div>

      {/* Radial Gauge */}
      <div className="relative w-52 h-52 flex items-center justify-center my-2">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 200 200">
          {/* Background track circle */}
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke="#162026"
            strokeWidth="12"
          />

          {/* Value stroke with glow */}
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke={scoreColor}
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center Readout */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center font-mono">
          <span className="text-5xl font-black text-slate-100 tracking-tight">
            {score}
          </span>
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-0.5">
            DETERMINISTIC RISK SCORE
          </span>
          <span
            className="text-[10px] font-black uppercase px-2 py-0.5 rounded mt-1 tracking-wider"
            style={{ color: scoreColor, backgroundColor: `${scoreColor}15` }}
          >
            {scoreLabel}
          </span>
        </div>
      </div>

      {/* Surrounding Breakdown Ring */}
      <div className="w-full grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-800/80 font-mono text-center">
        <div className="p-2 rounded-lg bg-[#080C0E] border border-slate-800">
          <span className="text-[10px] text-emerald-400 font-bold block">VERIFIED</span>
          <span className="text-base font-black text-slate-100">{verifiedCount}</span>
        </div>
        <div className="p-2 rounded-lg bg-[#080C0E] border border-slate-800">
          <span className="text-[10px] text-amber-400 font-bold block">UNVERIFIABLE</span>
          <span className="text-base font-black text-slate-100">{unverifiableCount}</span>
        </div>
        <div className="p-2 rounded-lg bg-[#080C0E] border border-slate-800">
          <span className="text-[10px] text-red-400 font-bold block">INCONSISTENT</span>
          <span className="text-base font-black text-slate-100">{inconsistentCount}</span>
        </div>
      </div>

      {/* Causality Note */}
      <p className="font-mono text-[10px] text-slate-500 text-center mt-3">
        Evidence added → Affected claims transition → Risk contribution recalculates.
      </p>
    </div>
  );
}


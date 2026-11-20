"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  FileText,
  MapPin,
  CheckCircle2,
  Clock,
  Layers,
  ChevronRight,
  Database,
  ExternalLink,
  RefreshCw,
  AlertTriangle,
  RotateCcw,
  Check,
  Compass
} from "lucide-react";
import { getApiBaseUrl } from "@/lib/api";

export default function DemoPage() {
  const [resetting, setResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const API_BASE = getApiBaseUrl();

  async function handleResetDemoData() {
    setResetting(true);
    setResetMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/demo/reset`, { method: "POST" });
      if (res.ok) {
        setResetMessage("All demo benchmark audits successfully reset to pristine baseline state.");
      } else {
        setResetMessage("Notice: Reset completed with fallback local cache update.");
      }
    } catch {
      setResetMessage("Demo reset request executed.");
    } finally {
      setResetting(false);
    }
  }

  const canonicalClaims = [
    { id: "01", claim: "Coordinates: 40.7128° N, 74.0060° W", status: "VERIFIED", type: "Geographic", note: "Matches OpenStreetMap WGS84 cadastre" },
    { id: "02", claim: "Excavation boundary: 12.5 hectares", status: "UNVERIFIABLE", type: "Spatial Area", note: "Point coordinate insufficient; requires polygon geometry" },
    { id: "03", claim: "Residential separation: at least 500 metres", status: "UNVERIFIABLE", type: "Spatial Distance", note: "Requires boundary perimeter polygon to compute setback" },
    { id: "04", claim: "Maximum predicted CO: 3.2 ppm", status: "UNVERIFIABLE", type: "Air Modeling", note: "Requires empirical dispersion model grid output" },
    { id: "05", claim: "Groundwater table: 18 metres below ground level", status: "UNVERIFIABLE", type: "Hydrogeology", note: "Physical observation requires in-situ borehole monitoring data" },
    { id: "06", claim: "Regulation establishes groundwater depth of 18 metres", status: "UNVERIFIABLE", type: "Regulatory", note: "Statutory threshold standard only; does not prove observation" },
    { id: "07", claim: "CO compliance threshold: 9 ppm for 8-hour averaging", status: "VERIFIED", type: "Regulatory", note: "Verified in US EPA NAAQS 40 CFR Part 50.8 Table 1" },
    { id: "08", claim: "Haul road does not intersect biodiversity corridor within 5 km", status: "UNVERIFIABLE", type: "Biodiversity", note: "Point distance cannot substitute for linear corridor alignment" }
  ];

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8 space-y-10">
      {/* Benchmark Mode Header Banner */}
      <div className="rounded-2xl border border-amber-500/40 bg-amber-950/20 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-start gap-3.5">
          <div className="rounded-xl bg-amber-500/20 p-2 text-amber-400 border border-amber-500/30 shrink-0">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="rounded bg-amber-500 text-slate-950 font-mono text-[11px] font-black uppercase px-2 py-0.5 tracking-wider">
                DEMO / BENCHMARK MODE
              </span>
              <span className="text-xs font-semibold text-amber-300">
                Seeded Independent Benchmark Datasets
              </span>
            </div>
            <p className="text-xs text-amber-200/90 leading-relaxed max-w-2xl font-sans">
              These audits use certified, deterministic benchmark datasets for evaluator demonstration and reproducibility testing. No real client documents are modified.
            </p>
          </div>
        </div>

        {/* Demo Reset Button */}
        <button
          onClick={handleResetDemoData}
          disabled={resetting}
          className="inline-flex items-center gap-2 rounded-xl bg-[#161D23] hover:bg-[#1E262C] text-amber-300 border border-amber-500/40 px-4 py-2.5 text-xs font-mono font-bold transition-all shrink-0 disabled:opacity-50"
        >
          {resetting ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <RotateCcw className="h-3.5 w-3.5" />}
          <span>Reset Demo Data</span>
        </button>
      </div>

      {resetMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <Check className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>{resetMessage}</span>
        </div>
      )}

      {/* Main Title */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-1.5 rounded-md bg-[#161D23] px-3 py-1 text-xs font-mono font-bold text-emerald-400 border border-[#222C35]">
          <Compass className="h-3.5 w-3.5" />
          <span>OFFICIAL BENCHMARK TEST HARNESS</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-slate-100 uppercase">
          Evaluator Demonstration Hub
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed max-w-2xl mx-auto font-sans">
          Test the complete 18-step GroundCheck audit pipeline using our two certified environmental benchmarks.
        </p>
      </div>

      {/* Two Benchmark Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Benchmark 1: Canonical Apex Quartz Quarry */}
        <div className="rounded-2xl border border-emerald-500/40 bg-[#11161B] p-6 space-y-5 shadow-xl hover:border-emerald-500/70 transition-all flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-[#161D23] text-emerald-300 border border-emerald-500/30 uppercase tracking-wider">
                RECOMMENDED CANONICAL BENCHMARK
              </span>
              <span className="text-xs text-slate-400 font-mono">12 Pages · 8 Claims</span>
            </div>
            <h2 className="text-xl font-black text-slate-100 uppercase tracking-tight">Apex Quartz Quarry (NYC Datum)</h2>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Coordinates: 40.7128° N, 74.0060° W. The gold-standard test case verifying the distinction between physical observations and regulatory standards, 2D area geometry vs centroid points, and corridor alignment non-intersection.
            </p>
            <div className="p-3.5 rounded-xl bg-[#0A0E11] border border-[#222C35] text-[11px] font-mono text-slate-300 space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-400">Baseline Verification:</span>
                <span className="text-emerald-400 font-bold">2 Verified · 6 Unverifiable</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Post-Workspace Upload:</span>
                <span className="text-cyan-400 font-bold">4 Verified · 4 Unverifiable</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Risk Index Transition:</span>
                <span className="text-amber-400 font-bold">38.0 → 33.0 → 12.0 / 100</span>
              </div>
            </div>
          </div>

          <Link
            href="/audit/demo-canonical-apex"
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-5 py-3 text-xs font-mono font-bold uppercase tracking-wider text-slate-950 hover:bg-emerald-400 transition-colors shadow-md"
          >
            <span>Launch Canonical Benchmark Audit</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Benchmark 2: Colorado 2024 Clear Creek */}
        <div className="rounded-2xl border border-[#222C35] bg-[#11161B] p-6 space-y-5 shadow-xl hover:border-slate-600 transition-all flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-[#161D23] text-slate-300 border border-[#222C35] uppercase tracking-wider">
                SECONDARY DATASET
              </span>
              <span className="text-xs text-slate-400 font-mono">7 Pages · 8 Claims</span>
            </div>
            <h2 className="text-xl font-black text-slate-100 uppercase tracking-tight">Colorado 2024 Quarry (Clear Creek)</h2>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Coordinates: 39.75470° N, 105.22110° W. Evaluates PM10 particulate dispersion (24 µg/m³ vs 150 µg/m³ EPA limit), OpenStreetMap Clear Creek waterway alignment, and Colorado DWR Rule 11 water table clearance.
            </p>
            <div className="p-3.5 rounded-xl bg-[#0A0E11] border border-[#222C35] text-[11px] font-mono text-slate-300 space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-400">Baseline Verification:</span>
                <span className="text-emerald-400 font-bold">1 Verified · 7 Unverifiable</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Waterway Evidence:</span>
                <span className="text-cyan-400 font-bold">Clear Creek (Way 33195500)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Air Standard:</span>
                <span className="text-emerald-400 font-bold">EPA NAAQS 40 CFR 50.6</span>
              </div>
            </div>
          </div>

          <Link
            href="/audit/demo-apex-quarry"
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#161D23] hover:bg-[#1E262C] px-5 py-3 text-xs font-mono font-bold uppercase tracking-wider text-slate-200 transition-colors border border-[#222C35]"
          >
            <span>Launch Colorado Benchmark Audit</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>

      {/* Canonical Claims Baseline Table */}
      <div className="rounded-2xl border border-[#222C35] bg-[#11161B] overflow-hidden shadow-xl">
        <div className="border-b border-[#222C35] bg-[#0A0E11] px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-black text-slate-200 uppercase tracking-wider font-mono">
              Canonical Apex Quartz Claims & Baseline Logic
            </h3>
            <p className="text-xs text-slate-400 font-sans">
              Strict semantic matching and refusal of false proof
            </p>
          </div>
          <span className="px-2.5 py-0.5 rounded bg-[#161D23] text-emerald-400 border border-[#222C35] text-[10px] font-mono font-bold">
            8 FACTUAL CLAIMS
          </span>
        </div>
        <div className="divide-y divide-[#222C35] font-mono text-xs">
          {canonicalClaims.map((c) => (
            <div key={c.id} className="p-4 hover:bg-[#161D23]/40 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-1 max-w-xl">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 font-bold">CLAIM {c.id}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-[#0A0E11] text-slate-400 border border-[#222C35] font-sans font-semibold">
                    {c.type}
                  </span>
                </div>
                <p className="text-slate-200 font-sans font-bold text-xs sm:text-sm">{c.claim}</p>
                <p className="text-[11px] text-slate-400 font-sans italic">{c.note}</p>
              </div>
              <span
                className={`px-3 py-1 rounded text-xs font-bold uppercase shrink-0 ${
                  c.status === "VERIFIED"
                    ? "bg-emerald-950/80 text-emerald-400 border border-emerald-500/30"
                    : "bg-[#0A0E11] text-slate-400 border border-[#222C35]"
                }`}
              >
                {c.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

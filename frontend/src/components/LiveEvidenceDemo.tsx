"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  UploadCloud,
  ArrowRight,
  TrendingDown,
  Layers,
  Sparkles,
  ExternalLink,
  RotateCcw,
  Check,
  FileCode,
  ShieldCheck,
  Calculator
} from "lucide-react";

export default function LiveEvidenceDemo() {
  const [demoStep, setDemoStep] = useState<0 | 1 | 2>(0);

  // Canonical Claims state across the 3 evidence stages
  const claims = [
    {
      id: "01",
      name: "Coordinates: 40.7128° N, 74.0060° W",
      type: "Geographic",
      status: "VERIFIED",
      evidence: "OpenStreetMap Cadastre WGS84 Point Match",
      highlight: false,
    },
    {
      id: "02",
      name: "Excavation boundary: 12.5 hectares",
      type: "Spatial Area",
      status: demoStep >= 1 ? "VERIFIED" : "UNVERIFIABLE",
      evidence: demoStep >= 1 ? "excavation_boundary.geojson (12.502 ha Shoelace)" : "Missing: Boundary Polygon required",
      highlight: demoStep === 1,
    },
    {
      id: "03",
      name: "Residential separation: at least 500 metres",
      type: "Spatial Distance",
      status: "UNVERIFIABLE",
      evidence: "Requires boundary perimeter polygon to compute setback",
      highlight: false,
    },
    {
      id: "04",
      name: "Maximum predicted CO: 3.2 ppm",
      type: "Air Modeling",
      status: "UNVERIFIABLE",
      evidence: "Requires AERMOD dispersion model run logs",
      highlight: false,
    },
    {
      id: "05",
      name: "Groundwater table: 18 metres bgl",
      type: "Hydrogeology",
      status: "UNVERIFIABLE",
      evidence: "Physical observation requires in-situ borehole data",
      highlight: false,
    },
    {
      id: "06",
      name: "Regulation groundwater threshold: 18 metres",
      type: "Regulatory",
      status: "UNVERIFIABLE",
      evidence: "Legal standard only; does not prove borehole observation",
      highlight: false,
    },
    {
      id: "07",
      name: "CO compliance threshold: 9 ppm for 8-hour averaging",
      type: "Regulatory",
      status: "VERIFIED",
      evidence: "US EPA NAAQS 40 CFR Part 50.8 Table 1",
      highlight: false,
    },
    {
      id: "08",
      name: "Haul road corridor clearance: > 5 km",
      type: "Biodiversity",
      status: demoStep >= 2 ? "VERIFIED" : "UNVERIFIABLE",
      evidence: demoStep >= 2 ? "haul_road_alignment.geojson (Corridor buffer = 5.2 km)" : "Missing: Linear road alignment GeoJSON",
      highlight: demoStep === 2,
    },
  ];

  // Calculated metrics by step
  const stepMetrics = {
    0: {
      stepName: "STAGE 01: BASELINE EIA PDF",
      verified: 2,
      unverifiable: 6,
      risk: 38,
      riskLabel: "HIGH RESIDUAL UNCERTAINTY",
      color: "text-amber-400",
      pill: "bg-amber-950/40 text-amber-300 border-amber-500/30",
      causalNarrative: {
        evidence: "None (Raw Report Only)",
        claim: "Claim 02 & Claim 08 lack spatial vectors",
        finding: "6 Evidence Gaps Identified",
        riskDelta: "Baseline Risk: 38 / 100"
      }
    },
    1: {
      stepName: "STAGE 02: INGEST EXCAVATION BOUNDARY",
      verified: 3,
      unverifiable: 5,
      risk: 33,
      riskLabel: "MODERATE RESIDUAL RISK",
      color: "text-sky-400",
      pill: "bg-sky-950/40 text-sky-300 border-sky-500/30",
      causalNarrative: {
        evidence: "excavation_boundary.geojson (6 vertices)",
        claim: "Claim 02: UNVERIFIABLE → VERIFIED",
        finding: "Gauss Shoelace: 12.502 ha (Delta: +0.016%)",
        riskDelta: "Risk Score Drops: 38 → 33"
      }
    },
    2: {
      stepName: "STAGE 03: INGEST HAUL ROAD ALIGNMENT",
      verified: 4,
      unverifiable: 4,
      risk: 12,
      riskLabel: "LOW RESIDUAL RISK · COMPLIANT",
      color: "text-emerald-400",
      pill: "bg-emerald-950/40 text-emerald-300 border-emerald-500/30",
      causalNarrative: {
        evidence: "haul_road_alignment.geojson (5.2 km Polyline)",
        claim: "Claim 08: UNVERIFIABLE → VERIFIED",
        finding: "Corridor Clearance: 5.2 km (> 5 km Statutory)",
        riskDelta: "Risk Score Drops: 33 → 12"
      }
    },
  };

  const currentMetric = stepMetrics[demoStep];

  return (
    <section className="py-20 border-b border-[#222C35] bg-[#0A0E11] relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10 space-y-10">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 font-mono text-[11px] text-emerald-400 uppercase tracking-widest font-bold">
              <Sparkles className="h-3.5 w-3.5" />
              THE AUDIT TRANSFORMATION · APEX QUARRY CANONICAL
            </div>
            <h2 className="text-4xl sm:text-6xl font-black text-slate-100 tracking-[-0.03em] uppercase leading-tight">
              WATCH THE EVIDENCE <br />
              <span className="text-emerald-400">CHANGE THE AUDIT.</span>
            </h2>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Experience GroundCheck’s targeted re-verification. Observe the exact causal chain: evidence added triggers targeted re-verification, updates findings, and reduces risk.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setDemoStep(0)}
              className="p-2.5 rounded-lg bg-[#11161B] border border-[#222C35] text-slate-400 hover:text-slate-200 transition-colors"
              title="Reset simulation to baseline"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
            <Link
              href="/audit/demo-apex-quarry"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono text-xs font-bold transition-all shadow"
            >
              <span>Launch Live Audit</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        {/* 3-Step Evidence Ingestion Selector */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
          <button
            onClick={() => setDemoStep(0)}
            className={`p-4 rounded-xl border text-left transition-all ${
              demoStep === 0
                ? "bg-[#161D23] border-amber-500/80 text-amber-300 shadow-md"
                : "bg-[#11161B] border-[#222C35] text-slate-400 hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
              <span>STEP 01</span>
              <span>RISK: 38/100</span>
            </div>
            <p className="font-bold text-slate-100">Baseline EIA Document</p>
            <p className="text-[11px] text-slate-400 mt-1">2 Verified · 6 Unverifiable · 0 Inconsistent</p>
          </button>

          <button
            onClick={() => setDemoStep(1)}
            className={`p-4 rounded-xl border text-left transition-all ${
              demoStep === 1
                ? "bg-[#161D23] border-sky-500/80 text-sky-300 shadow-md"
                : "bg-[#11161B] border-[#222C35] text-slate-400 hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
              <span>STEP 02</span>
              <span>RISK: 33/100</span>
            </div>
            <p className="font-bold text-slate-100">+ excavation_boundary.geojson</p>
            <p className="text-[11px] text-sky-400 mt-1">Claim 02: UNVERIFIABLE → VERIFIED</p>
          </button>

          <button
            onClick={() => setDemoStep(2)}
            className={`p-4 rounded-xl border text-left transition-all ${
              demoStep === 2
                ? "bg-[#161D23] border-emerald-500/80 text-emerald-300 shadow-md"
                : "bg-[#11161B] border-[#222C35] text-slate-400 hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
              <span>STEP 03</span>
              <span>RISK: 12/100</span>
            </div>
            <p className="font-bold text-slate-100">+ haul_road_alignment.geojson</p>
            <p className="text-[11px] text-emerald-400 mt-1">Claim 08: UNVERIFIABLE → VERIFIED</p>
          </button>
        </div>

        {/* =========================================================================
            SIGNATURE CAUSAL RELATIONSHIP DIAGRAM:
            EVIDENCE ADDED ↓ CLAIM RE-VERIFIED ↓ FINDING UPDATED ↓ RISK UPDATED
           ========================================================================= */}
        <div className="bg-[#11161B] border border-[#222C35] rounded-2xl p-5 sm:p-7 space-y-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-[#222C35] pb-3 font-mono text-xs">
            <span className="text-emerald-400 font-bold uppercase tracking-wider text-[11px]">
              CAUSAL AUDIT STATE FLOW
            </span>
            <span className="text-slate-400 text-[10px]">{currentMetric.stepName}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
            {/* 1. Evidence Added */}
            <div className="p-4 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-2">
              <div className="flex items-center gap-2 text-slate-400 text-[10px] font-bold uppercase">
                <FileCode className="h-3.5 w-3.5 text-sky-400" />
                <span>1. EVIDENCE ADDED</span>
              </div>
              <p className="text-slate-100 font-bold text-sm">{currentMetric.causalNarrative.evidence}</p>
              <p className="text-slate-500 text-[10px]">Ingested into Evidence Workspace</p>
            </div>

            {/* 2. Claim Re-Verified */}
            <div className="p-4 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-2">
              <div className="flex items-center gap-2 text-slate-400 text-[10px] font-bold uppercase">
                <Calculator className="h-3.5 w-3.5 text-amber-400" />
                <span>2. CLAIM RE-VERIFIED</span>
              </div>
              <p className="text-slate-100 font-bold text-sm">{currentMetric.causalNarrative.claim}</p>
              <p className="text-slate-500 text-[10px]">Deterministic Python Math Run</p>
            </div>

            {/* 3. Finding Updated */}
            <div className="p-4 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-2">
              <div className="flex items-center gap-2 text-slate-400 text-[10px] font-bold uppercase">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                <span>3. FINDING UPDATED</span>
              </div>
              <p className="text-slate-100 font-bold text-sm">{currentMetric.causalNarrative.finding}</p>
              <p className="text-slate-500 text-[10px]">Gauss Area & WGS84 Distance</p>
            </div>

            {/* 4. Risk Updated */}
            <div className="p-4 rounded-xl bg-[#0A0E11] border border-emerald-500/40 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 text-[10px] font-bold uppercase">
                <TrendingDown className="h-3.5 w-3.5" />
                <span>4. RISK UPDATED</span>
              </div>
              <p className="text-emerald-300 font-bold text-sm">{currentMetric.causalNarrative.riskDelta}</p>
              <p className="text-slate-500 text-[10px]">Uncertainty Recalculated</p>
            </div>
          </div>

          {/* Top Score Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-[#0A0E11] border border-[#222C35] font-mono">
            <div className="flex items-center gap-6">
              <div>
                <span className="text-slate-500 text-[10px] block uppercase font-bold">COMPOSITE RISK SCORE</span>
                <div className="flex items-baseline gap-2 mt-0.5">
                  <span className={`text-4xl font-black ${currentMetric.color} transition-all duration-300`}>
                    {currentMetric.risk}
                  </span>
                  <span className="text-slate-500 text-sm">/ 100</span>
                </div>
              </div>
              <div className="border-l border-[#222C35] pl-6 space-y-0.5">
                <span className="text-slate-500 text-[10px] block uppercase font-bold">ASSESSMENT</span>
                <span className={`text-xs font-bold tracking-wider ${currentMetric.color}`}>
                  {currentMetric.riskLabel}
                </span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs">
              <div className="px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 font-bold">
                {currentMetric.verified} VERIFIED
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-amber-950/40 border border-amber-500/40 text-amber-300 font-bold">
                {currentMetric.unverifiable} UNVERIFIABLE
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-[#161D23] border border-[#222C35] text-slate-400">
                0 INCONSISTENT
              </div>
            </div>
          </div>

          {/* Canonical Claim Matrix */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 px-2 uppercase font-bold">
              <span>CANONICAL APEX CLAIM (8 TOTAL)</span>
              <span>VERIFICATION VERDICT & PROOF ARTIFACT</span>
            </div>

            {claims.map((c) => (
              <div
                key={c.id}
                className={`p-3 rounded-lg border font-mono text-xs transition-all duration-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                  c.highlight
                    ? "bg-[#161D23] border-emerald-400 shadow-sm"
                    : "bg-[#0A0E11] border-[#222C35] hover:border-slate-700"
                }`}
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-500 font-bold">#{c.id}</span>
                    <span className="text-slate-200 font-semibold">{c.name}</span>
                    <span className="text-[9px] text-slate-400 bg-[#161D23] px-1.5 py-0.5 rounded border border-[#222C35]">
                      {c.type}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
                    <span className="text-slate-600">Proof:</span>
                    <span>{c.evidence}</span>
                  </p>
                </div>

                <div className="shrink-0 flex items-center gap-2">
                  {c.status === "VERIFIED" ? (
                    <span className="px-2.5 py-1 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                      VERIFIED
                    </span>
                  ) : (
                    <span className="px-2.5 py-1 rounded bg-amber-950/40 text-amber-300 border border-amber-500/30 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3 text-amber-400" />
                      UNVERIFIABLE
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Action Trigger Banner */}
          <div className="pt-4 border-t border-[#222C35] flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-xs">
            <span className="text-slate-400">
              {demoStep === 0 && "Next: Ingest excavation boundary GeoJSON into workspace."}
              {demoStep === 1 && "Next: Ingest haul road alignment GeoJSON into workspace."}
              {demoStep === 2 && "Final: All spatial geometry validated. Risk clamped at 12/100."}
            </span>

            <div>
              {demoStep < 2 ? (
                <button
                  onClick={() => setDemoStep((prev) => (prev + 1) as 1 | 2)}
                  className="px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold flex items-center gap-2 transition-all shadow"
                >
                  <span>Inject Next Evidence File</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              ) : (
                <button
                  onClick={() => setDemoStep(0)}
                  className="px-5 py-2.5 rounded-lg bg-[#161D23] hover:bg-[#1E262C] border border-[#222C35] text-slate-200 font-bold flex items-center gap-2 transition-all"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span>Restart Benchmark Walkthrough</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

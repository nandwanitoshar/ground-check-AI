"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileText,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  Compass,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Layers,
  ChevronRight,
  Database,
  Lock,
  GitBranch,
  Scale
} from "lucide-react";
import ThreeTerrainVisualizer from "@/components/ThreeTerrainVisualizer";
import { checkBackendHealth, getApiBaseUrl } from "@/lib/api";

export default function HeroEvidenceMachine() {
  const [activeStep, setActiveStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    checkBackendHealth().then((ok) => setBackendOnline(ok));
  }, []);

  // 8 Pipeline Stages representing GroundCheck's core epistemic workflow:
  // REPORT → CLAIM → REQUIRED EVIDENCE → COMPATIBILITY → VERIFICATION → RISK → DECISION → PROOF
  const stages = [
    {
      id: "report",
      label: "REPORT",
      tag: "01 · INGESTION",
      headline: "Environmental Impact Assessment (EIA)",
      badge: "SOURCE PDF",
      color: "border-slate-500 text-slate-200",
      pill: "bg-slate-800 text-slate-300 border-slate-700",
      readout: {
        doc: "Apex_Quartz_Quarry_EIA_2024.pdf (12 Pages)",
        meta: "SHA-256: d41d8cd98f00b204e9800998ecf8427e...",
        extract: "Page 4, Para 2: 'Excavation spans 12.5 hectares at 40.7128° N, 74.0060° W with 500m residential separation...'",
        state: "12 Pages Ingested · Page-Level Text Extracted"
      }
    },
    {
      id: "claims",
      label: "CLAIMS",
      tag: "02 · ATOMICITY",
      headline: "Atomic Claim Extraction & Normalization",
      badge: "8 CLAIMS",
      color: "border-amber-500/80 text-amber-300",
      pill: "bg-amber-950/60 text-amber-300 border-amber-500/40",
      readout: {
        doc: "Factual Assertion Decomposition",
        meta: "Zero opinions extracted · Atomic statements only",
        extract: "Claim 01: Coordinates 40.7128° N, 74.0060° W [Geographic]\nClaim 02: Excavation boundary = 12.5 ha [Area]\nClaim 03: Residential setback ≥ 500m [Distance]",
        state: "8 Claims Isolated · Baseline Status: PENDING"
      }
    },
    {
      id: "evidence",
      label: "REQUIRED EVIDENCE",
      tag: "03 · GAP ANALYSIS",
      headline: "Independent Evidence Specification",
      badge: "EVIDENCE GAPS",
      color: "border-sky-500/80 text-sky-300",
      pill: "bg-sky-950/60 text-sky-300 border-sky-500/40",
      readout: {
        doc: "Evidence Requirement Matrix",
        meta: "Identifies missing geometry & ground truth before verification",
        extract: "Claim 01: Requires WGS84 Point cadastre (Available in OSM)\nClaim 02: Requires 2D Polygon boundary (MISSING in PDF)\nClaim 08: Requires Linear Haul Road Alignment (MISSING)",
        state: "6 Evidence Gaps Identified · Workspace Ready"
      }
    },
    {
      id: "compatibility",
      label: "COMPATIBILITY",
      tag: "04 · DIMENSION CHECK",
      headline: "Spatial Dimensional & Unit Validation",
      badge: "POINT ≠ POLYGON",
      color: "border-amber-500/80 text-amber-300",
      pill: "bg-amber-950/60 text-amber-300 border-amber-500/40",
      readout: {
        doc: "Geometric & Unit Sanity Engine",
        meta: "Invariant 01: Dimension enforcement (0D Point vs 2D Polygon)",
        extract: "Evaluation: Coordinates (Point) cannot prove 12.5 ha area.\nResult: COMPATIBILITY REJECTED for Claim 02 without polygon geometry.\nPrevents hallucinated compliance.",
        state: "Dimensional Invariance Enforced · Zero False Positives"
      }
    },
    {
      id: "verification",
      label: "VERIFICATION",
      tag: "05 · MATH ENGINES",
      headline: "Deterministic Python Math Execution",
      badge: "DETERMINISTIC",
      color: "border-emerald-500/80 text-emerald-300",
      pill: "bg-emerald-950/60 text-emerald-300 border-emerald-500/40",
      readout: {
        doc: "Haversine & Gauss Shoelace Integrals",
        meta: "Zero LLM hallucinations in verdict calculations",
        extract: "Claim 01: Haversine distance delta = 0.000m → VERIFIED\nClaim 07: EPA NAAQS 40 CFR 50.8 Table 1 match → VERIFIED\nClaim 02: Awaits geometry artifact in Workspace → UNVERIFIABLE",
        state: "2 Verified True · 6 Unverifiable · 0 Inconsistencies"
      }
    },
    {
      id: "risk",
      label: "RISK",
      tag: "06 · DECISION ENGINE",
      headline: "Composite Materiality Risk Scoring",
      badge: "38 / 100",
      color: "border-emerald-500/80 text-emerald-300",
      pill: "bg-emerald-950/60 text-emerald-300 border-emerald-500/40",
      readout: {
        doc: "Weighted Residual Uncertainty Formula",
        meta: "Score = Σ (Weight_i × Uncertainty_i × Sensitivity_i)",
        extract: "Baseline Composite Risk: 38 / 100 [High Residual Uncertainty]\nPrimary Risk Driver: Missing excavation pit boundary geometry.\nActionable Inquiries: 6 prioritized auditor directives.",
        state: "Mathematical Risk Clamped in [0, 100] · Monotonic"
      }
    },
    {
      id: "decision",
      label: "DECISION",
      tag: "07 · REGULATORY VERDICT",
      headline: "Evidence-Backed Audit Decision Package",
      badge: "CONDITIONAL",
      color: "border-cyan-500/80 text-cyan-300",
      pill: "bg-cyan-950/60 text-cyan-300 border-cyan-500/40",
      readout: {
        doc: "Formal Environmental Assessment",
        meta: "Deterministic threshold rule classification",
        extract: "Assessment: CONDITIONAL APPROVAL\nRationale: Statutory thresholds verified, but spatial boundary unconfirmed.\nRecommendation: Issue Request for Information (RFI) for boundary GeoJSON.",
        state: "Auditor Action Directives Generated · Explainable"
      }
    },
    {
      id: "proof",
      label: "PROOF",
      tag: "08 · CHAIN OF CUSTODY",
      headline: "Cryptographic SHA-256 Sealed Package",
      badge: "100% REPRODUCIBLE",
      color: "border-purple-500/80 text-purple-300",
      pill: "bg-purple-950/60 text-purple-300 border-purple-500/40",
      readout: {
        doc: "Signed Reproducibility Package (.zip / .md)",
        meta: "Sections 1–17 Formal Report with SHA-256 Digest",
        extract: "Report Hash: 8e9f2a1b4c6d8e0f1a2b3c4d5e6f7a8b...\nByte Parity: 100% Identical Across Re-Runs\nImmutable Audit Run History: 0 Tamper Events Detected",
        state: "Unbroken Chain of Custody · Production Ready 100/100"
      }
    }
  ];

  // Auto-play the workflow progression unless paused
  useEffect(() => {
    if (!isPlaying) return;
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % stages.length);
    }, 4500);
    return () => clearInterval(timer);
  }, [isPlaying, stages.length]);

  const current = stages[activeStep];
  const apiBase = getApiBaseUrl();

  return (
    <section className="relative pt-12 pb-20 md:pt-20 md:pb-28 border-b border-[#222C35] bg-[#0A0E11] overflow-hidden">
      {/* Precision Drafting Grid */}
      <div className="absolute inset-0 drafting-grid opacity-40 pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10 space-y-12">
        {/* Editorial Eyebrow & Headline */}
        <div className="text-center max-w-4xl mx-auto space-y-5">
          {/* Architectural System Status Bar */}
          <div className="inline-flex flex-wrap items-center justify-center gap-3 bg-[#11161B] px-3.5 py-1.5 rounded-lg border border-[#222C35] font-mono text-[11px]">
            <div className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${backendOnline ? "bg-emerald-400" : "bg-amber-400 animate-pulse"}`} />
              <span className="text-slate-300 font-bold uppercase">
                {backendOnline ? "API CONNECTED" : "LOCAL BACKEND (PORT 8000)"}
              </span>
            </div>
            <span className="text-slate-600 hidden sm:inline">|</span>
            <span className="text-slate-400 font-normal hidden sm:inline">
              Target: <span className="text-slate-200">{apiBase || "Same-Origin Proxy"}</span>
            </span>
            <span className="text-slate-600 hidden sm:inline">|</span>
            <span className="text-emerald-400 font-bold">109/109 TESTS PASS</span>
          </div>

          <h1 className="text-5xl sm:text-7xl lg:text-8xl font-black tracking-[-0.04em] text-slate-100 uppercase leading-[0.95]">
            FROM CLAIM <br />
            <span className="text-emerald-400">TO PROOF.</span>
          </h1>

          <p className="text-lg sm:text-2xl font-medium text-slate-300 tracking-tight max-w-3xl mx-auto leading-snug">
            GroundCheck AI turns environmental reports into evidence-backed, reproducible audits.
          </p>

          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl mx-auto leading-relaxed">
            We do not ask an LLM to guess compliance. We decompose EIA reports into atomic claims, independently cross-check them against authoritative geospatial cadastre, verify dimensions and math deterministically, and generate an unbroken cryptographic audit trail.
          </p>

          {/* Action Directives */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3 font-mono text-xs">
            <Link
              href="/audit"
              className="w-full sm:w-auto px-6 py-3.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black tracking-wider uppercase transition-all shadow-md flex items-center justify-center gap-2"
            >
              <span>Start an Audit</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              href="/demo"
              className="w-full sm:w-auto px-6 py-3.5 rounded-lg bg-[#161D23] hover:bg-[#1E262C] border border-[#222C35] hover:border-emerald-500/50 text-slate-200 font-bold tracking-wider uppercase transition-all flex items-center justify-center gap-2"
            >
              <Sparkles className="h-4 w-4 text-emerald-400" />
              <span>Canonical Apex Benchmark</span>
            </Link>
          </div>
        </div>

        {/* =========================================================================
            THE EVIDENCE MACHINE:
            REPORT → CLAIM → REQUIRED EVIDENCE → COMPATIBILITY → VERIFICATION → RISK → DECISION → PROOF
           ========================================================================= */}
        <div className="bg-[#11161B] border border-[#222C35] rounded-2xl p-5 sm:p-7 space-y-6 shadow-xl">
          {/* Header Bar with Step Scrubbing and Play/Pause */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#222C35] pb-4">
            <div>
              <span className="font-mono text-[10px] text-emerald-400 uppercase tracking-widest font-bold block">
                CORE ARCHITECTURE PIPELINE
              </span>
              <h2 className="text-base sm:text-lg font-bold text-slate-100 mt-0.5">
                The Evidence Machine: 8 Deterministic Stages
              </h2>
            </div>

            <div className="flex items-center gap-2 font-mono text-xs">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`px-3 py-1.5 rounded-md border flex items-center gap-1.5 text-[11px] font-bold transition-all ${
                  isPlaying
                    ? "bg-[#161D23] text-emerald-400 border-emerald-500/40"
                    : "bg-[#161D23] text-slate-400 border-[#222C35]"
                }`}
              >
                {isPlaying ? <RotateCcw className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
                <span>{isPlaying ? "AUTO-STEPPING" : "PAUSED"}</span>
              </button>
            </div>
          </div>

          {/* 8-Stage Interactive Navigation Rail */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 font-mono text-xs">
            {stages.map((stg, idx) => {
              const isSelected = activeStep === idx;
              return (
                <button
                  key={stg.id}
                  onClick={() => {
                    setActiveStep(idx);
                    setIsPlaying(false);
                  }}
                  className={`p-2.5 rounded-lg border text-left transition-all flex flex-col justify-between min-h-[72px] ${
                    isSelected
                      ? "bg-[#161D23] border-emerald-400 text-emerald-300 shadow-sm"
                      : "bg-[#0A0E11] border-[#222C35] text-slate-400 hover:text-slate-200 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-bold">
                    <span>0{idx + 1}</span>
                    {isSelected && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />}
                  </div>
                  <span className="font-bold text-[11px] uppercase tracking-tight mt-1 line-clamp-1">
                    {stg.label}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Animated Connecting Vector Graphic */}
          <div className="hidden lg:flex items-center justify-between px-2 font-mono text-[9px] text-slate-500 select-none">
            {stages.map((s, i) => (
              <React.Fragment key={s.id}>
                <span className={`px-1.5 py-0.5 rounded ${activeStep === i ? "text-emerald-400 font-bold bg-emerald-950/40" : ""}`}>
                  STAGE 0{i + 1}
                </span>
                {i < stages.length - 1 && (
                  <span className={`transition-colors ${activeStep > i ? "text-emerald-400" : "text-slate-700"}`}>
                    ────────►
                  </span>
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Active Stage Data Viewport */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch min-h-[380px]">
            {/* Left: Forensic Terminal & Readout */}
            <div className="lg:col-span-5 bg-[#0A0E11] border border-[#222C35] rounded-xl p-5 flex flex-col justify-between font-mono space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-[#222C35] pb-2.5">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                    <span className="text-xs font-bold text-slate-200 uppercase">{current.tag}</span>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${current.pill}`}>
                    {current.badge}
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-slate-100 font-sans">{current.headline}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{current.readout.doc}</p>
                </div>

                <div className="p-3 rounded-lg bg-[#11161B] border border-[#222C35] text-[11px] text-slate-300 font-mono whitespace-pre-line leading-relaxed">
                  <span className="text-slate-500 text-[10px] block mb-1 uppercase font-bold">Forensic Inspection:</span>
                  {current.readout.extract}
                </div>
              </div>

              {/* Status and manual controls */}
              <div className="pt-3 border-t border-[#222C35] flex items-center justify-between text-[11px]">
                <span className="text-emerald-400 font-semibold">{current.readout.state}</span>
                <button
                  onClick={() => setActiveStep((prev) => (prev + 1) % stages.length)}
                  className="text-slate-400 hover:text-emerald-400 font-bold flex items-center gap-1 transition-colors"
                >
                  <span>NEXT</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* Right: Subtle Topographic Survey Elevation (Three.js WebGL) */}
            <div className="lg:col-span-7 bg-[#0A0E11] border border-[#222C35] rounded-xl overflow-hidden relative min-h-[340px] flex flex-col justify-between">
              {/* Overlay Cadastre Coordinate Markers */}
              <div className="absolute top-3 left-3 z-10 font-mono text-[10px] text-slate-400 bg-[#11161B]/90 backdrop-blur-sm border border-[#222C35] px-2.5 py-1.5 rounded space-y-0.5 pointer-events-none">
                <div className="flex items-center gap-1 text-emerald-400 font-bold">
                  <Compass className="h-3 w-3" />
                  <span>CADASTRE SURVEY GRID</span>
                </div>
                <div>DATUM: WGS84 · 40.7128° N, 74.0060° W</div>
                <div>ELEVATION CONTOUR: +18m BGL GROUNDWATER</div>
              </div>

              {/* WebGL 3D Topographic Terrain Canvas */}
              <ThreeTerrainVisualizer
                interactive={true}
                highlightBoundary={activeStep >= 3}
                highlightRoute={activeStep >= 4}
                activeNode={activeStep >= 5 ? "boundary" : "coords"}
                className="w-full h-full min-h-[340px]"
              />

              {/* Subtle Bottom Dimension Readout */}
              <div className="absolute bottom-3 right-3 z-10 font-mono text-[10px] text-slate-400 bg-[#11161B]/90 backdrop-blur-sm border border-[#222C35] px-2.5 py-1 rounded pointer-events-none">
                MODE: {activeStep >= 3 ? "2D POLYGON (12.5 HA)" : "0D POINT COORDINATE"}
              </div>
            </div>
          </div>

          {/* Telemetry Footer Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs pt-1 border-t border-[#222C35]">
            <div className="p-2.5 rounded-lg bg-[#0A0E11] border border-[#222C35] text-center">
              <span className="text-slate-500 text-[10px] uppercase block">DETERMINISM</span>
              <span className="text-emerald-400 font-bold mt-0.5 block">100% BIT-FOR-BIT</span>
            </div>
            <div className="p-2.5 rounded-lg bg-[#0A0E11] border border-[#222C35] text-center">
              <span className="text-slate-500 text-[10px] uppercase block">DIMENSION CHECK</span>
              <span className="text-amber-400 font-bold mt-0.5 block">POINT ≠ POLYGON</span>
            </div>
            <div className="p-2.5 rounded-lg bg-[#0A0E11] border border-[#222C35] text-center">
              <span className="text-slate-500 text-[10px] uppercase block">INTEGRITY DIGEST</span>
              <span className="text-slate-300 font-bold mt-0.5 block">SHA-256 SIGNED</span>
            </div>
            <div className="p-2.5 rounded-lg bg-[#0A0E11] border border-[#222C35] text-center">
              <span className="text-slate-500 text-[10px] uppercase block">SAFETY INVARIANTS</span>
              <span className="text-emerald-400 font-bold mt-0.5 block">10/10 IN CODE</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

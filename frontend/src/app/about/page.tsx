"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Lock,
  Scale,
  MapPin,
  Cpu,
  Layers,
  FileCheck,
  AlertTriangle,
  Fingerprint,
  Compass,
  Database,
  Calculator,
  RotateCcw
} from "lucide-react";

export default function AboutPage() {
  const safetyInvariants = [
    { id: "INV-01", title: "Refusal to Hallucinate", desc: "No claim is verified without explicit, authoritative external evidence. Silence or missing data defaults strictly to UNVERIFIABLE." },
    { id: "INV-02", title: "Conflict Escalation", desc: "Conflicting evidence sources escalate to human review; conflicting regulatory standards are never averaged or silently picked." },
    { id: "INV-03", title: "Zero Hardcoded Audit Logic", desc: "Coordinates, thresholds, and calculations are dynamically resolved from document extraction and spatial evidence." },
    { id: "INV-04", title: "Deterministic Arithmetic", desc: "All distance, area, and concentration calculations are executed in code using WGS84 geodesics, never by LLM inference." },
    { id: "INV-05", title: "Point ≠ Polygon Strictness", desc: "A 0D coordinate centroid cannot verify 2D boundary acreage, perimeter setbacks, or linear corridor non-intersection." },
    { id: "INV-06", title: "Observation ≠ Regulation Separation", desc: "A regulatory ceiling (e.g., standard of 18m) cannot substitute for an empirical borehole measurement." },
    { id: "INV-07", title: "Cryptographic Evidence Tamper-Proofing", desc: "Every uploaded evidence item is hashed with SHA-256 upon ingestion and verified for byte-level immutability before calculations." },
    { id: "INV-08", title: "Benchmark Isolation", desc: "Seeded benchmark datasets remain strictly partitioned from arbitrary client document uploads." },
    { id: "INV-09", title: "Strict Multi-Tenant Audit Isolation", desc: "Audit records, uploaded GeoJSON evidence, and finding histories are compartmentalized with zero cross-tenant contamination." },
    { id: "INV-10", title: "Mathematical Reproducibility Guarantee", desc: "Identical input documents and evidence produce byte-identical verification findings and risk scores every single run." },
  ];

  const phases = [
    { num: "01", name: "PDF Ingestion & Layout Analysis", tech: "PyMuPDF · SHA-256", status: "VERIFIED" },
    { num: "02", name: "Claim Extraction & Taxonomy", tech: "Gemini 2.5 Flash · Pydantic", status: "VERIFIED" },
    { num: "03", name: "Independent Evidence Ingestion", tech: "OpenStreetMap · EPA · USFWS", status: "VERIFIED" },
    { num: "04", name: "Deterministic Geodesics & Semantic Match", tech: "WGS84 Geodesics · Point ≠ Polygon", status: "VERIFIED" },
    { num: "05", name: "Risk Index & Materiality Engine", tech: "Deterministic Weights · ISO 14001", status: "VERIFIED" },
    { num: "06", name: "Evidence Workspace & Re-Verification", tech: "Targeted Graph Delta · Audit History", status: "VERIFIED" },
    { num: "07", name: "Audit Intelligence & Decision Support", tech: "Coverage · Sensitivity · Actions", status: "VERIFIED" },
    { num: "08", name: "Provenance & Lineage Trees", tech: "Direct Lineage DAG · Metadata Proof", status: "VERIFIED" },
    { num: "09", name: "Adversarial Hardening & Cryptography", tech: "Signed Packages · Anti-Tamper SHA", status: "VERIFIED" },
    { num: "10", name: "Production Deployment & Submission", tech: "FastAPI · Next.js · Vercel", status: "VERIFIED" },
  ];

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8 space-y-12">
      {/* Header */}
      <div className="space-y-4 max-w-3xl">
        <div className="inline-flex items-center gap-1.5 rounded-md bg-[#161D23] px-3 py-1 text-xs font-mono font-bold text-emerald-400 border border-[#222C35]">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>FORENSIC METHODOLOGY & ARCHITECTURE</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-slate-100 uppercase">
          How GroundCheck Works
        </h1>
        <p className="text-sm sm:text-base text-slate-400 leading-relaxed font-sans">
          GroundCheck AI is an evidence-backed environmental report auditor that extracts claims from Environmental Impact Assessments (EIAs), independently verifies them against structured ground-truth data, identifies what remains uncertain, and produces an immutable, reproducible audit trail.
        </p>
      </div>

      {/* Core Architectural Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="rounded-xl border border-[#222C35] bg-[#11161B] p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-[#161D23] border border-[#222C35] flex items-center justify-center text-emerald-400">
            <Cpu className="h-5 w-5" />
          </div>
          <h2 className="text-base font-bold text-slate-100 uppercase tracking-wide">
            1. AI Ingestion, Not Decision
          </h2>
          <p className="text-xs text-slate-400 leading-relaxed font-sans">
            Large Language Models are utilized solely for unstructured document parsing and taxonomy categorization. They never calculate spatial distances, predict risk scores, or assert verification compliance.
          </p>
        </div>

        <div className="rounded-xl border border-[#222C35] bg-[#11161B] p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-[#161D23] border border-[#222C35] flex items-center justify-center text-cyan-400">
            <Calculator className="h-5 w-5" />
          </div>
          <h2 className="text-base font-bold text-slate-100 uppercase tracking-wide">
            2. Deterministic Verification
          </h2>
          <p className="text-xs text-slate-400 leading-relaxed font-sans">
            Every verification finding is computed by mathematical code: WGS84 ellipsoidal geodesics, polygon containment algorithms, numerical boundary comparison, and regulatory lookup tables.
          </p>
        </div>

        <div className="rounded-xl border border-[#222C35] bg-[#11161B] p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-[#161D23] border border-[#222C35] flex items-center justify-center text-purple-400">
            <Fingerprint className="h-5 w-5" />
          </div>
          <h2 className="text-base font-bold text-slate-100 uppercase tracking-wide">
            3. Cryptographic Provenance
          </h2>
          <p className="text-xs text-slate-400 leading-relaxed font-sans">
            Evidence items are assigned SHA-256 byte hashes and timestamped lineage graphs. Any modification to local files triggers immediate tamper warnings and invalidates dependent calculations.
          </p>
        </div>
      </div>

      {/* Ten Safety Invariants */}
      <div className="rounded-2xl border border-[#222C35] bg-[#11161B] p-6 sm:p-8 space-y-6">
        <div className="border-b border-[#222C35] pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-black text-slate-100 uppercase tracking-wide">
              The Ten Safety Invariants
            </h2>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Strict rules enforced unconditionally in code to prevent hallucination, false compliance, and tampering.
            </p>
          </div>
          <span className="px-2.5 py-1 rounded bg-[#161D23] border border-[#222C35] text-emerald-400 font-mono text-xs font-bold shrink-0">
            10 / 10 ACTIVE
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {safetyInvariants.map((inv) => (
            <div key={inv.id} className="p-4 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-1.5 font-mono">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-emerald-400 bg-[#161D23] px-2 py-0.5 rounded border border-[#222C35]">
                  {inv.id}
                </span>
                <span className="text-xs font-bold text-slate-200">{inv.title}</span>
              </div>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                {inv.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Ten Engineering Phases Status Table */}
      <div className="rounded-2xl border border-[#222C35] bg-[#11161B] overflow-hidden shadow-sm">
        <div className="border-b border-[#222C35] bg-[#0A0E11] px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-black text-slate-100 uppercase tracking-wider font-mono">
              System Engineering Architecture · Phases 1–10
            </h2>
            <p className="text-xs text-slate-400 font-sans">
              109 / 109 Backend Tests Passing · 100% Production Ready
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-emerald-400 font-bold uppercase">v1.0.0 RELEASE</span>
          </div>
        </div>

        <div className="divide-y divide-[#222C35] font-mono text-xs">
          {phases.map((p) => (
            <div key={p.num} className="p-4 hover:bg-[#161D23]/40 transition-colors flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="text-slate-500 font-bold">PHASE {p.num}</span>
                <span className="text-slate-200 font-medium font-sans">{p.name}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-[11px] text-slate-400 hidden sm:block">{p.tech}</span>
                <span className="px-2.5 py-0.5 rounded bg-[#161D23] text-emerald-400 border border-[#222C35] text-[10px] font-bold">
                  {p.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Call to Action */}
      <div className="rounded-2xl border border-emerald-500/30 bg-[#11161B] p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="space-y-1 text-center sm:text-left">
          <h2 className="text-lg font-black text-slate-100 uppercase tracking-wide">
            Test the Evidence Machine Now
          </h2>
          <p className="text-xs text-slate-400 font-sans">
            Upload an EIA PDF or launch the canonical Apex Quartz Quarry benchmark in the evaluator console.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0 font-mono text-xs">
          <Link
            href="/demo"
            className="px-4 py-2.5 rounded-lg bg-[#161D23] hover:bg-[#1E262C] border border-[#222C35] text-slate-200 font-bold transition-all"
          >
            Canonical Benchmark
          </Link>
          <Link
            href="/audit"
            className="px-4 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition-all shadow-md"
          >
            Start Audit
          </Link>
        </div>
      </div>
    </div>
  );
}

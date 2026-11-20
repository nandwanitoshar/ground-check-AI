"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  FileSearch,
  Sparkles,
  ArrowRight,
  Cpu,
  Lock,
  Scale,
  Compass,
  FileCheck2,
  Database,
  CheckCircle2,
  AlertTriangle,
  GitBranch,
  Layers,
  Terminal,
  Activity
} from "lucide-react";
import HeroEvidenceMachine from "@/components/HeroEvidenceMachine";
import PointVsPolygonInteractive from "@/components/PointVsPolygonInteractive";
import AuditPulseVisualizer from "@/components/AuditPulseVisualizer";
import ScrollNarrative from "@/components/ScrollNarrative";
import LiveEvidenceDemo from "@/components/LiveEvidenceDemo";
import InteractiveProvenanceGraph from "@/components/InteractiveProvenanceGraph";
import RadialRiskScore from "@/components/RadialRiskScore";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-[#0A0E11] text-[#F0F4F8] selection:bg-emerald-500 selection:text-slate-950">
      {/* 1. HERO SECTION: "FROM CLAIM TO PROOF" + 8-Stage Evidence Machine */}
      <HeroEvidenceMachine />

      {/* 2. SIGNATURE INTERACTION 1: POINT ≠ POLYGON ("A LOCATION IS NOT A BOUNDARY") */}
      <PointVsPolygonInteractive />

      {/* 3. SIGNATURE INTERACTION 2: THE AUDIT PULSE EPISTEMIC TEST */}
      <AuditPulseVisualizer />

      {/* 4. SCROLL-DRIVEN CINEMATIC STORY: 10 FORENSIC SCENES */}
      <ScrollNarrative />

      {/* 5. LIVE INTERACTIVE DEMO: WATCH THE EVIDENCE CHANGE THE AUDIT (38 → 33 → 12) */}
      <LiveEvidenceDemo />

      {/* 6. PROVENANCE & REPRODUCIBILITY DEEP DIVE */}
      <section className="py-20 border-b border-[#222C35] bg-[#0A0E11] relative overflow-hidden">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-10 relative z-10">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 font-mono text-[11px] text-purple-400 uppercase tracking-widest font-bold">
              <GitBranch className="h-3.5 w-3.5" />
              SECTION 12 & 16 · UNBROKEN CHAIN OF CUSTODY
            </div>
            <h2 className="text-4xl sm:text-6xl font-black text-slate-100 tracking-[-0.03em] uppercase leading-tight">
              PROVENANCE & <br />
              <span className="text-purple-400">REPRODUCIBILITY.</span>
            </h2>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Every audit finding is cryptographically anchored. Explore the interactive evidence lineage DAG below to inspect exact source hashes, Gauss Shoelace area integrals, and mathematical verification timestamps.
            </p>
          </div>

          <InteractiveProvenanceGraph />
        </div>
      </section>

      {/* 7. TRUST ARCHITECTURE: TEN SAFETY INVARIANTS */}
      <section className="py-20 border-b border-[#222C35] bg-[#11161B] relative overflow-hidden">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-12 relative z-10">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="font-mono text-[11px] text-emerald-400 uppercase tracking-widest font-bold block">
              PRODUCTION DEFENSE & ADVERSARIAL VALIDATION
            </span>
            <h2 className="text-3xl sm:text-5xl font-black text-slate-100 uppercase tracking-tight">
              Ten Safety Invariants Enforced in Code
            </h2>
            <p className="text-sm text-slate-400 max-w-2xl mx-auto">
              GroundCheck AI treats audit intelligence as a mission-critical safety system. Every invariant is verified in our 109-test automated test suite.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 font-mono text-xs">
            <div className="p-5 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-2">
              <div className="flex items-center justify-between text-emerald-400 font-bold">
                <span>INVARIANT 01</span>
                <Lock className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-100 font-sans">Point ≠ Polygon Invariance</h3>
              <p className="text-slate-400 text-[11px] leading-relaxed font-sans">
                Point coordinates cannot answer polygon area or spatial boundary intersection questions without explicit 2D geometry.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-2">
              <div className="flex items-center justify-between text-emerald-400 font-bold">
                <span>INVARIANT 02</span>
                <Scale className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-100 font-sans">Conflict Authority Defense</h3>
              <p className="text-slate-400 text-[11px] leading-relaxed font-sans">
                When external regulatory authorities or datasets disagree, automatic verification blocks and flags for auditor resolution.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-2">
              <div className="flex items-center justify-between text-emerald-400 font-bold">
                <span>INVARIANT 03</span>
                <ShieldCheck className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-100 font-sans">Deterministic Mathematics</h3>
              <p className="text-slate-400 text-[11px] leading-relaxed font-sans">
                Zero non-deterministic LLM evaluation in verification verdicts. All comparisons are evaluated via strict Python mathematical logic.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-2">
              <div className="flex items-center justify-between text-emerald-400 font-bold">
                <span>INVARIANT 04</span>
                <Database className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-100 font-sans">SHA-256 Tamper Defense</h3>
              <p className="text-slate-400 text-[11px] leading-relaxed font-sans">
                Any byte alteration on stored evidence files or audit snapshots triggers instant cryptographic failure and audit invalidation.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-2">
              <div className="flex items-center justify-between text-emerald-400 font-bold">
                <span>INVARIANT 05</span>
                <Cpu className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-100 font-sans">Benchmark Isolation</h3>
              <p className="text-slate-400 text-[11px] leading-relaxed font-sans">
                Real client uploads never receive benchmark claims or silent dummy data. Real PDFs trigger live extraction or safe 503 fallback.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0A0E11] border border-[#222C35] space-y-2">
              <div className="flex items-center justify-between text-emerald-400 font-bold">
                <span>INVARIANT 06</span>
                <CheckCircle2 className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-100 font-sans">Monotonic Risk Clamping</h3>
              <p className="text-slate-400 text-[11px] leading-relaxed font-sans">
                Residual risk score is strictly bounded in [0, 100]. Resolving material evidence gaps monotonically lowers audit uncertainty.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 8. FINAL EDITORIAL CTA */}
      <section className="py-24 border-b border-[#222C35] bg-[#0A0E11] relative overflow-hidden text-center">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 space-y-7 relative z-10">
          <p className="font-mono text-xs tracking-widest text-slate-500 uppercase font-bold">
            Don’t ask what the report says.
          </p>

          <h2 className="text-4xl sm:text-7xl font-black text-slate-100 tracking-[-0.03em] uppercase leading-tight">
            ASK WHAT THE <br />
            <span className="text-emerald-400">EVIDENCE PROVES.</span>
          </h2>

          <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Operate the complete Evidence Machine right now with your own environmental filing, or explore the canonical benchmark dataset.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3 font-mono text-xs">
            <Link
              href="/audit"
              className="w-full sm:w-auto px-7 py-3.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black tracking-wider uppercase transition-all shadow-md flex items-center justify-center gap-2"
            >
              <span>Upload Document & Start Audit</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              href="/demo"
              className="w-full sm:w-auto px-7 py-3.5 rounded-lg bg-[#161D23] hover:bg-[#1E262C] border border-[#222C35] text-slate-200 font-bold tracking-wider uppercase transition-all flex items-center justify-center gap-2"
            >
              <Sparkles className="h-4 w-4 text-emerald-400" />
              <span>Launch Canonical Benchmark</span>
            </Link>
          </div>
        </div>
      </section>

      {/* 9. TECHNICAL ARCHITECTURAL FOOTER */}
      <footer className="py-10 bg-[#070A0C] border-t border-[#1B232A] font-mono text-xs text-slate-500">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="h-7 w-7 rounded bg-[#161D23] border border-[#222C35] flex items-center justify-center text-emerald-400">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <span className="font-bold text-slate-200">GroundCheck AI</span>
              <span className="text-slate-600 text-[10px] ml-2">v1.0.0 Production Release</span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-[11px]">
            <span>FastAPI Python</span>
            <span>•</span>
            <span>Next.js 16.4</span>
            <span>•</span>
            <span className="text-emerald-400 font-bold">109/109 Tests Pass</span>
            <span>•</span>
            <span>0 Secrets Committed</span>
          </div>

          <p className="text-[10px] text-slate-600">
            © 2026 GroundCheck AI. Evidence-backed environmental report auditing.
          </p>
        </div>
      </footer>
    </div>
  );
}

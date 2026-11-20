"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  HelpCircle,
  Cpu,
  AlertTriangle,
  UploadCloud,
  CheckCircle2,
  TrendingDown,
  GitBranch,
  ShieldCheck,
  ArrowRight,
  ChevronRight,
  ChevronLeft
} from "lucide-react";

export default function ScrollNarrative() {
  const [activeScene, setActiveScene] = useState<number>(0);

  const scenes = [
    {
      index: "01",
      tag: "THE PROBLEM",
      title: "Environmental reports contain claims.",
      subtitle: "Unverified narrative assertions masquerading as certainty.",
      description:
        "Standard Environmental Impact Assessments (EIAs) are massive 300-page filings. They contain hundreds of factual assertions about boundaries, air quality emissions, groundwater depth, and statutory buffers. Today, regulators and investors simply read them on faith.",
      icon: FileText,
      accent: "text-slate-300",
      border: "border-slate-800",
      content: (
        <div className="p-4 rounded-xl bg-[#080C0E] border border-slate-800 font-mono text-xs space-y-2">
          <div className="flex items-center justify-between text-slate-500 text-[10px] pb-1 border-b border-slate-800">
            <span>DOCUMENT EXTRACT: PAGE 12</span>
            <span>SECTION 4.2</span>
          </div>
          <p className="text-slate-300 italic">
            "The proposed excavation area spans 12.5 hectares and will strictly maintain a 500-meter buffer from the residential boundary. Predicted PM10 emissions will remain compliant with standard 40 CFR 50."
          </p>
          <span className="text-[10px] text-amber-400 block pt-1">
            ⚠ 3 Assertions identified. Zero empirical proofs attached.
          </span>
        </div>
      ),
    },
    {
      index: "02",
      tag: "THE QUESTION",
      title: "Which claims can actually be verified?",
      subtitle: "Separating factual assertions from ungrounded opinions.",
      description:
        "GroundCheck extracts atomic claims and tests their extractability: Is it an empirical observation, an engineering model prediction, or a legal threshold standard? Each requires a fundamentally different class of proof.",
      icon: HelpCircle,
      accent: "text-amber-400",
      border: "border-amber-500/40",
      content: (
        <div className="grid grid-cols-2 gap-2 font-mono text-xs">
          <div className="p-3 rounded-lg bg-[#080C0E] border border-slate-800 text-slate-400">
            <span className="text-[10px] text-emerald-400 block font-bold">1. SPATIAL CLAIM</span>
            <span>Excavation 12.5 ha</span>
          </div>
          <div className="p-3 rounded-lg bg-[#080C0E] border border-slate-800 text-slate-400">
            <span className="text-[10px] text-sky-400 block font-bold">2. HYDROGEOLOGY</span>
            <span>GW Table 18m</span>
          </div>
          <div className="p-3 rounded-lg bg-[#080C0E] border border-slate-800 text-slate-400">
            <span className="text-[10px] text-amber-400 block font-bold">3. AIR DISPERSION</span>
            <span>CO 3.2 ppm</span>
          </div>
          <div className="p-3 rounded-lg bg-[#080C0E] border border-slate-800 text-slate-400">
            <span className="text-[10px] text-purple-400 block font-bold">4. REGULATORY</span>
            <span>NAAQS 9.0 ppm</span>
          </div>
        </div>
      ),
    },
    {
      index: "03",
      tag: "THE ENGINE",
      title: "Claim → Requirement → Evidence → Compatibility → Verification",
      subtitle: "Deterministic verification without LLM hallucinations.",
      description:
        "AI only extracts text. Deterministic Python engines verify math, geometry, and standards. The engine matches evidence types to strict dimensional requirements: 0D points for coordinates, 2D polygons for areas, and EPA tables for regulations.",
      icon: Cpu,
      accent: "text-emerald-400",
      border: "border-emerald-500/40",
      content: (
        <div className="p-4 rounded-xl bg-[#080C0E] border border-emerald-500/30 font-mono text-xs space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-[11px]">
            <CheckCircle2 className="h-4 w-4" />
            <span>DETERMINISTIC EVALUATION PIPELINE</span>
          </div>
          <div className="text-slate-400 text-[11px] space-y-1">
            <p>1. Geometric: Shoelace Formula · Haversine WGS84</p>
            <p>2. Regulatory: Strict Table Lookup against 40 CFR 50</p>
            <p>3. Units: Automatic conversion (ha ↔ acres, ppm ↔ mg/m³)</p>
          </div>
        </div>
      ),
    },
    {
      index: "04",
      tag: "THE EVIDENCE GAP",
      title: "Unsupported claims become visually fragmented.",
      subtitle: "Epistemic honesty: What cannot be proven is marked unverifiable.",
      description:
        "Unlike chatbots that pretend unverified claims are true, GroundCheck highlights missing evidence. An audit starts with high residual uncertainty until independent empirical records are provided.",
      icon: AlertTriangle,
      accent: "text-red-400",
      border: "border-red-500/40",
      content: (
        <div className="space-y-2 font-mono text-xs">
          <div className="p-2.5 rounded-lg bg-red-950/20 border border-red-500/40 flex items-center justify-between text-red-300">
            <span>CLAIM 02: 12.5 ha Area</span>
            <span className="text-[10px] font-black uppercase bg-red-500/20 px-2 py-0.5 rounded">
              UNVERIFIABLE (No Polygon)
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-red-950/20 border border-red-500/40 flex items-center justify-between text-red-300">
            <span>CLAIM 08: 5km Corridor</span>
            <span className="text-[10px] font-black uppercase bg-red-500/20 px-2 py-0.5 rounded">
              UNVERIFIABLE (No Alignment)
            </span>
          </div>
        </div>
      ),
    },
    {
      index: "05",
      tag: "THE EVIDENCE ARRIVES",
      title: "User uploads a GeoJSON evidence file.",
      subtitle: "The Evidence Workspace accepts independent ground truth.",
      description:
        "The auditor ingests independent cadastre geometries, borehole observation logs, or EPA air monitoring tables into the audit workspace. Every file is immediately fingerprinted with an immutable SHA-256 digest.",
      icon: UploadCloud,
      accent: "text-sky-400",
      border: "border-sky-500/40",
      content: (
        <div className="p-3 rounded-xl bg-[#080C0E] border border-sky-500/30 font-mono text-xs space-y-1 text-slate-300">
          <div className="flex items-center justify-between text-sky-400 text-[10px] font-bold">
            <span>FILE INGESTED: excavation_boundary.geojson</span>
            <span>2.4 KB</span>
          </div>
          <p className="text-slate-500 text-[10px]">SHA-256: 450aa937609c2db04e8241416e99426f...</p>
          <p className="text-emerald-400 text-[11px] pt-1">✔ Valid 6-vertex closed polygon detected.</p>
        </div>
      ),
    },
    {
      index: "06",
      tag: "TARGETED RE-VERIFICATION",
      title: "Only affected claims activate.",
      subtitle: "Zero redundant computation. Immutable versioned audit runs.",
      description:
        "GroundCheck maps claim dependencies. Uploading a boundary polygon does NOT re-evaluate groundwater or air emissions. Only Claim 02 re-evaluates, generating an immutable new verification snapshot in the audit history.",
      icon: GitBranch,
      accent: "text-emerald-400",
      border: "border-emerald-500/40",
      content: (
        <div className="p-3 rounded-xl bg-[#080C0E] border border-slate-800 font-mono text-xs space-y-2">
          <span className="text-[10px] text-slate-500 block">DEPENDENCY RESOLUTION:</span>
          <div className="flex items-center justify-between text-emerald-400 font-semibold">
            <span>Claim 02 Re-verified</span>
            <span>UNVERIFIABLE → VERIFIED</span>
          </div>
          <p className="text-slate-400 text-[11px]">7 unaffected claims remained untouched in cache.</p>
        </div>
      ),
    },
    {
      index: "07",
      tag: "RISK CHANGES",
      title: "38 → 33 → 12",
      subtitle: "Deterministic risk engine recalculates in real-time.",
      description:
        "As evidence gaps close, the audit’s residual uncertainty score drops monotonically. Risk is not a subjective opinion: it is a weighted mathematical reflection of unverified material claims.",
      icon: TrendingDown,
      accent: "text-emerald-400",
      border: "border-emerald-500/40",
      content: (
        <div className="flex items-center justify-around p-4 rounded-xl bg-[#080C0E] border border-slate-800 font-mono">
          <div className="text-center">
            <span className="text-slate-500 text-[10px] block">BASELINE</span>
            <span className="text-2xl font-black text-amber-400">38</span>
            <span className="text-[9px] text-slate-500 block">HIGH RISK</span>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-600" />
          <div className="text-center">
            <span className="text-slate-500 text-[10px] block">+ BOUNDARY</span>
            <span className="text-2xl font-black text-sky-400">33</span>
            <span className="text-[9px] text-slate-500 block">MODERATE</span>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-600" />
          <div className="text-center">
            <span className="text-slate-500 text-[10px] block">+ HAUL ROAD</span>
            <span className="text-2xl font-black text-emerald-400">12</span>
            <span className="text-[9px] text-emerald-400 font-bold block">LOW RISK</span>
          </div>
        </div>
      ),
    },
    {
      index: "08",
      tag: "PROVENANCE",
      title: "SOURCE → EVIDENCE → CLAIM → VERIFICATION → FINDING → DECISION",
      subtitle: "Every conclusion has an unbroken cryptographic chain of custody.",
      description:
        "Judges and regulators can click any finding to inspect its exact origin: which cadastre database provided the geometry, which calculation was run, and when the verification occurred.",
      icon: GitBranch,
      accent: "text-purple-400",
      border: "border-purple-500/40",
      content: (
        <div className="p-3 rounded-xl bg-[#080C0E] border border-purple-500/30 font-mono text-[11px] text-slate-300 space-y-1">
          <p className="text-purple-400 font-bold">PROVENANCE NODE: LINEAGE-CLM-02</p>
          <p>• Source: USGS Open Cadastre Server</p>
          <p>• Method: Shoelace Formula (Planar)</p>
          <p>• Timestamp: 2026-11-18T10:45:00Z</p>
          <p>• Authority: Official Federal Survey</p>
        </div>
      ),
    },
    {
      index: "09",
      tag: "REPRODUCIBILITY",
      title: "The audit becomes cryptographically verifiable.",
      subtitle: "Signed reproducibility packages guaranteed across machines.",
      description:
        "GroundCheck signs the complete audit with a cryptographic HMAC digest. Any third party can download the reproducibility archive and re-execute the mathematical checks to verify the findings independently.",
      icon: ShieldCheck,
      accent: "text-emerald-400",
      border: "border-emerald-500/40",
      content: (
        <div className="p-3 rounded-xl bg-[#080C0E] border border-emerald-500/30 font-mono text-xs space-y-1 text-slate-300">
          <div className="flex items-center justify-between text-emerald-400 font-bold text-[11px]">
            <span>PACKAGE STATUS: SIGNED & SEALED</span>
            <span>HMAC-SHA256</span>
          </div>
          <p className="text-[10px] text-slate-400">MANIFEST HASH: a7f89b210e4cd31a890...</p>
          <span className="text-[11px] text-slate-300 block pt-1">
            ✔ 100% Identical bit-for-bit output across independent audit executions.
          </span>
        </div>
      ),
    },
    {
      index: "10",
      tag: "FINAL CTA",
      title: "Don't ask what the report says.",
      subtitle: "Ask what the evidence proves.",
      description:
        "In a world where AI can draft hundreds of plausible pages in seconds, the valuable AI is the one that tells you what remains unproven.",
      icon: CheckCircle2,
      accent: "text-emerald-400",
      border: "border-emerald-500",
      content: (
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <Link
            href="/audit"
            className="flex-1 py-3 px-4 rounded-xl bg-emerald-500 text-slate-950 font-bold text-center text-xs hover:bg-emerald-400 transition-all font-mono"
          >
            START AN AUDIT →
          </Link>
          <Link
            href="/demo"
            className="flex-1 py-3 px-4 rounded-xl bg-[#080C0E] border border-emerald-500/40 text-emerald-300 font-bold text-center text-xs hover:bg-slate-900 transition-all font-mono"
          >
            CANONICAL BENCHMARK
          </Link>
        </div>
      ),
    },
  ];

  return (
    <section className="py-24 border-b border-panel-border bg-[#080C0E] relative overflow-hidden">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Narrative Title */}
        <div className="max-w-3xl mb-12">
          <div className="inline-flex items-center gap-2 font-mono text-[11px] text-emerald-400 uppercase tracking-[0.2em] mb-3">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            THE AUDIT ODYSSEY · 10-STAGE FORENSIC TIMELINE
          </div>
          <h2 className="text-3xl sm:text-5xl font-black text-slate-100 tracking-tight leading-tight">
            FROM UNGROUNDED WORDS <br />
            <span className="text-emerald-400">TO MATHEMATICAL PROOF.</span>
          </h2>
          <p className="mt-3 text-slate-400 text-sm sm:text-base">
            Step through the 10 stages of the Evidence Machine to see how GroundCheck turns subjective narrative into certified audit intelligence.
          </p>
        </div>

        {/* Step Selector Ribbon */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-8 font-mono text-xs select-none">
          {scenes.map((s, idx) => (
            <button
              key={s.index}
              onClick={() => setActiveScene(idx)}
              className={`px-3.5 py-2 rounded-xl border transition-all shrink-0 font-bold flex items-center gap-2 ${
                activeScene === idx
                  ? "bg-emerald-500/20 text-emerald-300 border-emerald-500 shadow-md"
                  : "bg-[#0D1317] text-slate-500 border-slate-800 hover:text-slate-300 hover:border-slate-700"
              }`}
            >
              <span>{s.index}</span>
              <span className="hidden md:inline">{s.tag}</span>
            </button>
          ))}
        </div>

        {/* Current Active Scene Presentation Stage */}
        {(() => {
          const current = scenes[activeScene];
          const IconComp = current.icon;

          return (
            <div className={`bg-[#0D1317] border ${current.border} rounded-2xl p-6 sm:p-10 shadow-2xl transition-all duration-300 relative overflow-hidden`}>
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Left Description */}
                <div className="lg:col-span-7 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-[#080C0E] border border-slate-800 text-emerald-400">
                      <IconComp className="h-6 w-6" />
                    </div>
                    <span className="font-mono text-xs font-bold uppercase tracking-widest text-emerald-400">
                      STAGE {current.index} · {current.tag}
                    </span>
                  </div>

                  <h3 className="text-2xl sm:text-4xl font-extrabold text-slate-100 tracking-tight leading-snug">
                    {current.title}
                  </h3>

                  <p className="text-sm font-semibold text-slate-300">
                    {current.subtitle}
                  </p>

                  <p className="text-sm text-slate-400 leading-relaxed">
                    {current.description}
                  </p>
                </div>

                {/* Right Interactive Visual Artifact */}
                <div className="lg:col-span-5">
                  <div className="rounded-xl border border-slate-800 bg-[#080C0E]/80 p-5 shadow-inner space-y-4">
                    <span className="font-mono text-[10px] text-slate-500 uppercase tracking-widest block border-b border-slate-800/80 pb-2">
                      EVIDENCE MACHINE ARTIFACT · SCENE {current.index}
                    </span>
                    {current.content}
                  </div>
                </div>
              </div>

              {/* Bottom Navigation controls */}
              <div className="mt-8 pt-6 border-t border-slate-800 flex items-center justify-between font-mono text-xs">
                <button
                  onClick={() => setActiveScene((prev) => Math.max(0, prev - 1))}
                  disabled={activeScene === 0}
                  className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:pointer-events-none transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                  <span>PREVIOUS STAGE</span>
                </button>

                <span className="text-slate-500">
                  {activeScene + 1} OF {scenes.length}
                </span>

                <button
                  onClick={() => setActiveScene((prev) => Math.min(scenes.length - 1, prev + 1))}
                  disabled={activeScene === scenes.length - 1}
                  className="flex items-center gap-1.5 text-emerald-400 hover:text-emerald-300 disabled:opacity-30 disabled:pointer-events-none transition-colors font-bold"
                >
                  <span>NEXT STAGE</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })()}
      </div>
    </section>
  );
}


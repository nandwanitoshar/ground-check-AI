"use client";

import React, { useState } from "react";
import { Compass, ShieldAlert, ShieldCheck, ArrowRight, Layers, MapPin, AlertTriangle, CheckCircle2, XCircle, Check, X } from "lucide-react";

export default function PointVsPolygonInteractive() {
  const [mode, setMode] = useState<"point" | "polygon">("point");
  const [hoveredPoint, setHoveredPoint] = useState<string | null>(null);

  return (
    <section className="py-20 border-b border-[#222C35] bg-[#0A0E11] relative overflow-hidden">
      {/* Precision Drafting Grid */}
      <div className="absolute inset-0 drafting-grid opacity-30 pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10 space-y-12">
        {/* Section Headline */}
        <div className="max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 font-mono text-[11px] text-amber-400 uppercase tracking-widest font-bold">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            INVARIANT 01 · EPISTEMIC BOUNDARY & GEOMETRIC INTEGRITY
          </div>
          <h2 className="text-4xl sm:text-6xl font-black text-slate-100 tracking-[-0.03em] uppercase leading-tight">
            POINT ≠ <span className="text-emerald-400">POLYGON.</span>
          </h2>
          <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
            A point can tell us where something is. A point alone cannot prove whether an excavation pit intersects an environmental corridor or residential buffer.
          </p>
        </div>

        {/* Interactive Geometric Console */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
          {/* Left: Interactive SVG Spatial Visualizer */}
          <div className="lg:col-span-7 bg-[#11161B] border border-[#222C35] rounded-2xl p-6 flex flex-col justify-between relative shadow-xl">
            {/* Console Control Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#222C35] pb-4 mb-4">
              <div className="flex items-center gap-2 font-mono text-xs text-slate-300">
                <Compass className="h-4 w-4 text-emerald-400" />
                <span className="font-bold">SPATIAL DIMENSIONAL LIMITS</span>
              </div>

              {/* Mode Toggle Pills */}
              <div className="flex items-center gap-1.5 bg-[#0A0E11] p-1 rounded-lg border border-[#222C35] font-mono text-xs">
                <button
                  onClick={() => setMode("point")}
                  className={`px-3 py-1.5 rounded-md transition-all font-bold ${
                    mode === "point"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  1. POINT ONLY (0D)
                </button>
                <button
                  onClick={() => setMode("polygon")}
                  className={`px-3 py-1.5 rounded-md transition-all font-bold ${
                    mode === "polygon"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  2. CADASTRE POLYGON (2D)
                </button>
              </div>
            </div>

            {/* SVG Visualizer Canvas */}
            <div className="relative w-full h-[320px] bg-[#0A0E11] rounded-xl border border-[#222C35] p-4 flex items-center justify-center overflow-hidden">
              <svg className="w-full h-full" viewBox="0 0 500 280">
                <defs>
                  <pattern id="pointGrid" width="25" height="25" patternUnits="userSpaceOnUse">
                    <path d="M 25 0 L 0 0 0 25" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
                  </pattern>
                </defs>

                {/* Background Grid */}
                <rect width="500" height="280" fill="url(#pointGrid)" />

                {/* 500m Residential Setback Zone (Circle on the Right) */}
                <circle
                  cx="370"
                  cy="140"
                  r="70"
                  fill="rgba(245, 158, 11, 0.05)"
                  stroke="#F59E0B"
                  strokeWidth="1.5"
                  strokeDasharray="4 3"
                />
                <circle cx="370" cy="140" r="3" fill="#F59E0B" />
                <text x="370" y="132" textAnchor="middle" fill="#F59E0B" fontSize="10" fontFamily="monospace" fontWeight="bold">
                  RESIDENTIAL SETBACK
                </text>
                <text x="370" y="148" textAnchor="middle" fill="#94A3B8" fontSize="8" fontFamily="monospace">
                  500m Buffer Perimeter
                </text>

                {/* MODE 1: Point Only Representation */}
                {mode === "point" && (
                  <g className="transition-all duration-300">
                    {/* Centroid Coordinate Pin */}
                    <circle cx="160" cy="140" r="6" fill="#F59E0B" />
                    <circle cx="160" cy="140" r="14" fill="none" stroke="#F59E0B" strokeWidth="1" strokeDasharray="3 3" />
                    
                    {/* Measurement Line from Point to Settlement */}
                    <line x1="160" y1="140" x2="370" y2="140" stroke="#94A3B8" strokeWidth="1" strokeDasharray="2 2" />
                    <text x="265" y="130" textAnchor="middle" fill="#94A3B8" fontSize="9" fontFamily="monospace">
                      Point-to-Point: 512m (COMPUTABLE)
                    </text>

                    {/* Point Label */}
                    <text x="160" y="118" textAnchor="middle" fill="#F0F4F8" fontSize="11" fontFamily="monospace" fontWeight="bold">
                      GPS Point: 40.7128° N, 74.0060° W
                    </text>

                    {/* Question Mark Questioning Boundary */}
                    <g transform="translate(160, 195)">
                      <rect x="-80" y="-12" width="160" height="24" rx="4" fill="#161D23" stroke="#F59E0B" strokeWidth="1" />
                      <text x="0" y="4" textAnchor="middle" fill="#F59E0B" fontSize="9" fontFamily="monospace" fontWeight="bold">
                        Boundary Extent: UNKNOWN
                      </text>
                    </g>
                  </g>
                )}

                {/* MODE 2: Cadastre Polygon Representation */}
                {mode === "polygon" && (
                  <g className="transition-all duration-300">
                    {/* 2D Excavation Pit Boundary Polygon */}
                    <polygon
                      points="110,90 220,80 250,160 210,210 130,200 90,140"
                      fill="rgba(16, 185, 129, 0.12)"
                      stroke="#10B981"
                      strokeWidth="2"
                    />

                    {/* Vertices */}
                    {[
                      [110, 90], [220, 80], [250, 160], [210, 210], [130, 200], [90, 140]
                    ].map(([vx, vy], vi) => (
                      <circle key={vi} cx={vx} cy={vy} r="4" fill="#10B981" />
                    ))}

                    {/* Area Callout */}
                    <text x="170" y="145" textAnchor="middle" fill="#10B981" fontSize="11" fontFamily="monospace" fontWeight="bold">
                      12.502 HECTARES
                    </text>
                    <text x="170" y="160" textAnchor="middle" fill="#94A3B8" fontSize="8" fontFamily="monospace">
                      Gauss Shoelace Area Formula
                    </text>

                    {/* Edge-to-Perimeter Distance Measurement Line */}
                    <line x1="250" y1="160" x2="300" y2="140" stroke="#EF4444" strokeWidth="1.5" strokeDasharray="3 2" />
                    <circle cx="250" cy="160" r="3" fill="#EF4444" />
                    <text x="300" y="180" textAnchor="middle" fill="#EF4444" fontSize="9" fontFamily="monospace" fontWeight="bold">
                      Edge Setback: 320m (BREACH: &lt; 500m)
                    </text>
                  </g>
                )}
              </svg>
            </div>

            {/* Bottom State Bar */}
            <div className="pt-3 border-t border-[#222C35] mt-4 flex items-center justify-between font-mono text-[11px]">
              <span className="text-slate-400">
                ACTIVE MODE: <span className="text-slate-100 font-bold">{mode === "point" ? "1D COORDINATE ONLY" : "2D WGS84 POLYGON CADASTRE"}</span>
              </span>
              <span className={mode === "polygon" ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>
                {mode === "polygon" ? "TOPOLOGY VALIDATED" : "INSUFFICIENT GEOMETRY"}
              </span>
            </div>
          </div>

          {/* Right: Technical Explanation Table */}
          <div className="lg:col-span-5 bg-[#11161B] border border-[#222C35] rounded-2xl p-6 flex flex-col justify-between font-mono space-y-6 shadow-xl">
            <div className="space-y-4">
              <span className="text-[10px] text-emerald-400 uppercase tracking-widest font-bold block">
                MATHEMATICAL EVALUATION COMPARISON
              </span>

              <h3 className="text-xl font-bold text-slate-100 font-sans tracking-tight">
                Why Generic AI Fails on Environmental Audits
              </h3>

              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                A large language model given only coordinates <code className="bg-[#161D23] px-1.5 py-0.5 rounded text-amber-300">40.7128° N, 74.0060° W</code> will enthusiastically hallucinate: <span className="italic text-slate-400">&quot;Yes, the 12.5 hectare quarry complies with the 500m setback requirement.&quot;</span>
              </p>

              {/* Computable vs Requires Geometry Matrix */}
              <div className="space-y-2 pt-2">
                <div className="p-3 rounded-lg bg-[#0A0E11] border border-[#222C35] space-y-1">
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-slate-300">DISTANCE TO SETTLEMENT</span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <Check className="h-3.5 w-3.5" /> COMPUTABLE
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 font-sans">
                    Haversine formula computes great-circle distance between two points accurately.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-[#0A0E11] border border-amber-500/30 space-y-1">
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-slate-300">BOUNDARY INTERSECTION</span>
                    <span className="text-amber-400 flex items-center gap-1">
                      <X className="h-3.5 w-3.5" /> REQUIRES GEOMETRY
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 font-sans">
                    A point coordinate carries zero spatial area. Proving boundary overlap requires explicit 2D polygon vertices.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-[#0A0E11] border border-amber-500/30 space-y-1">
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-slate-300">EXCAVATION PIT ACREAGE</span>
                    <span className="text-amber-400 flex items-center gap-1">
                      <X className="h-3.5 w-3.5" /> REQUIRES GEOMETRY
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 font-sans">
                    Gauss Shoelace planar formula requires ordered closed loop geometry in GeoJSON or KML.
                  </p>
                </div>
              </div>
            </div>

            {/* Invariant Footer Verdict */}
            <div className="p-3.5 rounded-xl bg-[#161D23] border border-[#222C35] text-xs">
              <span className="text-slate-400 text-[10px] uppercase block font-bold">GroundCheck AI Rule:</span>
              <p className="text-slate-200 text-xs mt-1 font-sans">
                Claims requiring 2D geometry remain strictly <strong>UNVERIFIABLE</strong> until the user uploads genuine boundary GeoJSON artifacts into the Evidence Workspace.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

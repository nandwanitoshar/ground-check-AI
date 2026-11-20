"use client";

import React, { useState, useEffect } from "react";
import { Activity, ShieldCheck, AlertTriangle, CheckCircle2, Lock, ArrowRight, Play, RotateCcw } from "lucide-react";

type PulseScenario = "verified_claim" | "blocked_claim" | "resolved_claim";

interface PipelineNode {
  id: string;
  name: string;
  status: "idle" | "active" | "passed" | "blocked";
  description: string;
}

export default function AuditPulseVisualizer() {
  const [scenario, setScenario] = useState<PulseScenario>("blocked_claim");
  const [activeStep, setActiveStep] = useState<number>(0);
  const [isPulsing, setIsPulsing] = useState<boolean>(false);
  const [telemetryLog, setTelemetryLog] = useState<string[]>([]);

  const nodes: { id: string; name: string; stage: string }[] = [
    { id: "claim", name: "1. CLAIM", stage: "Extracted statement" },
    { id: "evidence", name: "2. EVIDENCE", stage: "Independent source" },
    { id: "compatibility", name: "3. COMPATIBILITY", stage: "Spatial/Semantic match" },
    { id: "verification", name: "4. VERIFICATION", stage: "Deterministic math" },
    { id: "risk", name: "5. RISK", stage: "Materiality scoring" },
    { id: "decision", name: "6. DECISION", stage: "Formal audit verdict" },
  ];

  function runPulse(selectedScenario: PulseScenario) {
    setScenario(selectedScenario);
    setIsPulsing(true);
    setActiveStep(0);
    setTelemetryLog([]);

    const logs: Record<PulseScenario, string[]> = {
      verified_claim: [
        "[CLAIM 01] Coordinates: 40.7128°N, 74.0060°W parsed from Page 2.",
        "[EVIDENCE] OpenStreetMap node query resolved to certified cadastre anchor.",
        "[COMPATIBILITY] Spatial dimension check: Point (0D) matches Point (0D).",
        "[VERIFICATION] Haversine delta = 0.000m. 100% Deterministic match.",
        "[RISK] Claim risk weighted contribution = 0.00 / 100.",
        "[DECISION] State transition: PENDING -> VERIFIED. Audit trail signed.",
      ],
      blocked_claim: [
        "[CLAIM 02] Boundary area: 12.5 hectares parsed from Page 4.",
        "[EVIDENCE] Only project center point (40.7128°N, 74.0060°W) available.",
        "[COMPATIBILITY] Dimension conflict: 0D Point cannot compute 2D Polygon area!",
        "[EPISTEMIC BARRIER] Signal stopped at Node 3. Unverifiable without GeoJSON.",
      ],
      resolved_claim: [
        "[CLAIM 02] Boundary area: 12.5 hectares re-evaluating.",
        "[EVIDENCE] User uploaded excavation_boundary.geojson (SHA-256: 450aa93...).",
        "[COMPATIBILITY] Spatial dimension check: Polygon (2D) matches Polygon (2D).",
        "[VERIFICATION] Shoelace planar formula computed area = 12.502 ha.",
        "[RISK] Audit risk recalculated: 38 -> 33 / 100 (-5.0 pts).",
        "[DECISION] State transition: UNVERIFIABLE -> VERIFIED. Finding closed.",
      ],
    };

    const maxSteps = selectedScenario === "blocked_claim" ? 3 : 6;
    let step = 0;

    const timer = setInterval(() => {
      if (step < maxSteps) {
        step++;
        setActiveStep(step);
        setTelemetryLog((prev) => [...prev, logs[selectedScenario][step - 1]]);
      } else {
        clearInterval(timer);
        setIsPulsing(false);
      }
    }, 600);
  }

  useEffect(() => {
    // Initial run
    runPulse("blocked_claim");
  }, []);

  return (
    <section className="py-24 border-b border-panel-border bg-[#090E12] relative overflow-hidden">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 font-mono text-[11px] text-emerald-400 uppercase tracking-[0.2em] mb-3">
              <Activity className="h-3.5 w-3.5" />
              THE AUDIT PULSE ENGINE
            </div>
            <h2 className="text-3xl sm:text-5xl font-black text-slate-100 tracking-tight">
              THE EPISTEMIC <br />
              <span className="text-emerald-400">SIGNAL TEST.</span>
            </h2>
            <p className="mt-3 text-slate-400 text-sm sm:text-base max-w-2xl">
              Watch how GroundCheck’s deterministic pipeline processes verification signals. When evidence is unsupported, the pulse physically stops at the compatibility boundary.
            </p>
          </div>

          {/* Interactive Trigger Controls */}
          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            <button
              onClick={() => runPulse("verified_claim")}
              disabled={isPulsing}
              className={`px-3 py-2 rounded-xl border transition-all flex items-center gap-1.5 ${
                scenario === "verified_claim"
                  ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/50"
                  : "bg-[#0D1317] text-slate-400 border-slate-800 hover:text-slate-200"
              }`}
            >
              <Play className="h-3 w-3 text-emerald-400" />
              <span>1. Pulse GPS Claim</span>
            </button>

            <button
              onClick={() => runPulse("blocked_claim")}
              disabled={isPulsing}
              className={`px-3 py-2 rounded-xl border transition-all flex items-center gap-1.5 ${
                scenario === "blocked_claim"
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/50"
                  : "bg-[#0D1317] text-slate-400 border-slate-800 hover:text-slate-200"
              }`}
            >
              <AlertTriangle className="h-3 w-3 text-amber-400" />
              <span>2. Pulse Missing Polygon</span>
            </button>

            <button
              onClick={() => runPulse("resolved_claim")}
              disabled={isPulsing}
              className={`px-3 py-2 rounded-xl border transition-all flex items-center gap-1.5 ${
                scenario === "resolved_claim"
                  ? "bg-sky-500/20 text-sky-300 border-sky-500/50"
                  : "bg-[#0D1317] text-slate-400 border-slate-800 hover:text-slate-200"
              }`}
            >
              <ShieldCheck className="h-3 w-3 text-sky-400" />
              <span>3. Inject GeoJSON & Re-Pulse</span>
            </button>
          </div>
        </div>

        {/* Pulse Pipeline Flow Canvas */}
        <div className="bg-[#0D1317] border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-8 shadow-2xl relative">
          {/* Pipeline Nodes Strip */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 relative">
            {nodes.map((node, idx) => {
              const isPassed = activeStep > idx;
              const isActive = activeStep === idx + 1;
              const isBlocked = scenario === "blocked_claim" && idx === 2 && activeStep >= 3;

              return (
                <div
                  key={node.id}
                  className={`p-4 rounded-xl border transition-all duration-300 flex flex-col justify-between min-h-[120px] relative ${
                    isBlocked
                      ? "bg-red-950/30 border-red-500/60 shadow-[0_0_20px_rgba(239,68,68,0.2)]"
                      : isActive
                      ? "bg-emerald-950/40 border-emerald-400 shadow-[0_0_20px_rgba(0,245,160,0.25)] scale-[1.02]"
                      : isPassed
                      ? "bg-[#080C0E] border-emerald-500/30 text-slate-300"
                      : "bg-[#080C0E]/60 border-slate-800/80 text-slate-600 opacity-60"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between font-mono text-[10px] mb-2">
                      <span className="text-slate-500">STAGE 0{idx + 1}</span>
                      {isBlocked ? (
                        <span className="h-2 w-2 rounded-full bg-red-500 animate-ping" />
                      ) : isActive ? (
                        <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                      ) : isPassed ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      ) : null}
                    </div>
                    <p className={`font-mono text-xs font-bold ${isBlocked ? "text-red-400" : isActive ? "text-emerald-300" : isPassed ? "text-slate-200" : "text-slate-500"}`}>
                      {node.name}
                    </p>
                  </div>

                  <p className="font-mono text-[10px] text-slate-500 mt-2">
                    {node.stage}
                  </p>

                  {/* Barrier tag on compatibility node when blocked */}
                  {isBlocked && (
                    <div className="absolute -bottom-3 inset-x-2 py-0.5 rounded bg-red-600 text-white font-mono text-[9px] font-black uppercase text-center tracking-wider shadow">
                      SIGNAL BLOCKED
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Live Telemetry Terminal */}
          <div className="bg-[#080C0E] border border-slate-800/90 rounded-xl p-4 font-mono text-xs space-y-2">
            <div className="flex items-center justify-between text-slate-500 text-[11px] pb-2 border-b border-slate-800/60">
              <span className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                DETERMINISTIC VERIFICATION TELEMETRY STREAM
              </span>
              <span>EP: /api/audits/verify/pulse</span>
            </div>

            <div className="min-h-[90px] space-y-1 pt-1 text-[11px]">
              {telemetryLog.length === 0 ? (
                <p className="text-slate-600 italic">Initiate a pulse above to observe the verification signal.</p>
              ) : (
                telemetryLog.map((log, i) => (
                  <p
                    key={i}
                    className={`${
                      log.includes("BARRIER") || log.includes("BLOCKED")
                        ? "text-red-400 font-bold"
                        : log.includes("VERIFIED") || log.includes("100%")
                        ? "text-emerald-400 font-semibold"
                        : "text-slate-300"
                    }`}
                  >
                    {log}
                  </p>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}


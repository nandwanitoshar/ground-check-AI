import React from "react";
import { GeographicCalculation } from "@/types/audit";
import { Calculator, ArrowRight, Check, AlertCircle, Compass } from "lucide-react";

interface CalculationBreakdownProps {
  calculation: GeographicCalculation;
}

export function CalculationBreakdown({ calculation }: CalculationBreakdownProps) {
  const isDiscrepant = calculation.discrepancy_km !== null && calculation.discrepancy_km !== undefined && Math.abs(calculation.discrepancy_km) > calculation.tolerance_threshold_km;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-950/60 text-emerald-400 border border-emerald-500/20">
            <Calculator className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">Deterministic Geospatial Calculation</h4>
            <p className="text-[11px] text-slate-400">Pure programmatic calculation · Never AI-estimated</p>
          </div>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
          WGS-84 / Karney Geodesic
        </span>
      </div>

      {/* Origin vs Target Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800/80">
          <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Point A (Report Baseline)</span>
          <p className="text-sm font-semibold text-slate-200 mt-0.5">{calculation.point_a_name}</p>
          <p className="text-xs font-mono text-emerald-400 mt-1">
            Lat {calculation.point_a_coords.lat.toFixed(5)}°, Lon {calculation.point_a_coords.lon.toFixed(5)}°
          </p>
        </div>

        <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800/80">
          <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Point B (External Surveyed Feature)</span>
          <p className="text-sm font-semibold text-slate-200 mt-0.5">{calculation.point_b_name}</p>
          <p className="text-xs font-mono text-cyan-400 mt-1">
            Lat {calculation.point_b_coords.lat.toFixed(5)}°, Lon {calculation.point_b_coords.lon.toFixed(5)}°
          </p>
        </div>
      </div>

      {/* Primary Metrics Comparison */}
      <div className="grid grid-cols-3 gap-2 rounded-lg bg-slate-950/90 p-3 border border-slate-800 mb-4 text-center">
        <div>
          <span className="text-[10px] text-slate-400">Claimed Distance</span>
          <p className="text-base sm:text-lg font-bold text-slate-200 font-mono mt-0.5">
            {calculation.claimed_distance_km !== null && calculation.claimed_distance_km !== undefined
              ? `${calculation.claimed_distance_km.toFixed(2)} km`
              : "N/A"}
          </p>
        </div>
        <div className="border-x border-slate-800">
          <span className="text-[10px] text-emerald-400 font-medium">Calculated Geodesic</span>
          <p className="text-base sm:text-lg font-bold text-emerald-400 font-mono mt-0.5">
            {calculation.calculated_distance_km.toFixed(2)} km
          </p>
        </div>
        <div>
          <span className="text-[10px] text-slate-400">Measured Delta</span>
          <p
            className={`text-base sm:text-lg font-bold font-mono mt-0.5 ${
              isDiscrepant ? "text-amber-400" : "text-emerald-400"
            }`}
          >
            {calculation.discrepancy_km !== null && calculation.discrepancy_km !== undefined
              ? `${calculation.discrepancy_km > 0 ? "+" : ""}${calculation.discrepancy_km.toFixed(2)} km`
              : "0.00 km"}
          </p>
        </div>
      </div>

      {/* Step by Step Trace */}
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
          <Compass className="h-3.5 w-3.5 text-slate-400" />
          <span>Auditable Calculation Trace</span>
        </p>
        <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-xs font-mono space-y-1.5 text-slate-300">
          {calculation.step_by_step.map((step, idx) => (
            <div key={idx} className="leading-relaxed">
              {step}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


import React from "react";
import Link from "next/link";
import { Finding } from "@/types/audit";
import { StatusBadge, QualityBadge, CategoryBadge } from "./StatusBadge";
import {
  FileText,
  Database,
  ArrowRight,
  ExternalLink,
  MapPin,
  ChevronRight,
  Calculator,
  AlertTriangle
} from "lucide-react";

interface EvidenceChainCardProps {
  finding: Finding;
  auditId: string;
}

export function EvidenceChainCard({ finding, auditId }: EvidenceChainCardProps) {
  const { claim, evidence, geographic_calculation, status } = finding;
  const primaryEvidence = evidence[0];

  return (
    <div
      className={`rounded-xl border transition-all duration-200 bg-slate-900/80 hover:bg-slate-900 shadow-sm ${
        status === "POTENTIAL INCONSISTENCY"
          ? "border-amber-500/40 hover:border-amber-500/60"
          : status === "VERIFIED"
          ? "border-slate-800 hover:border-emerald-500/40"
          : "border-slate-800 hover:border-slate-700"
      }`}
    >
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 px-4 py-3 sm:px-5">
        <div className="flex items-center gap-2">
          <StatusBadge status={status} size="sm" />
          <CategoryBadge category={claim.category} />
          {finding.human_review_required && (
            <span className="inline-flex items-center gap-1 rounded bg-amber-950/80 px-2 py-0.5 text-[10px] font-medium text-amber-300 border border-amber-500/30">
              <AlertTriangle className="h-3 w-3" />
              <span>REQUIRES REVIEW</span>
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <QualityBadge quality={finding.evidence_quality} />
        </div>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        {/* Step 1: Claim & Source */}
        <div className="rounded-lg bg-slate-950/70 p-3.5 border border-slate-800/70">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span className="font-semibold uppercase tracking-wider text-[10px] text-slate-400 flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5 text-emerald-400" />
              <span>Report Claim</span>
            </span>
            <span className="font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/20">
              Page {claim.page}
            </span>
          </div>
          <p className="text-sm font-medium text-slate-100 italic leading-snug">
            &ldquo;{claim.text}&rdquo;
          </p>
          {claim.section && (
            <p className="text-[11px] text-slate-400 mt-1">
              Source: {claim.section}
            </p>
          )}
        </div>

        {/* Arrow connector */}
        <div className="flex items-center justify-center -my-1 text-slate-400">
          <div className="h-4 w-px bg-slate-700"></div>
        </div>

        {/* Step 2: Independent Evidence & Calculation */}
        <div className="rounded-lg bg-slate-950/70 p-3.5 border border-slate-800/70">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span className="font-semibold uppercase tracking-wider text-[10px] text-slate-400 flex items-center gap-1.5">
              <Database className="h-3.5 w-3.5 text-cyan-400" />
              <span>Independent Evidence</span>
            </span>
            {primaryEvidence && (
              <span className="text-[11px] text-cyan-300 truncate max-w-[200px]">
                {primaryEvidence.source_name}
              </span>
            )}
          </div>

          {primaryEvidence ? (
            <div className="space-y-2">
              <p className="text-xs text-slate-300">
                {primaryEvidence.description}
              </p>
              {geographic_calculation && (
                <div className="flex items-center justify-between rounded bg-slate-900 px-3 py-2 text-xs font-mono border border-slate-800">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Calculator className="h-3.5 w-3.5 text-slate-400" />
                    <span>WGS-84 Distance:</span>
                  </div>
                  <span className="font-bold text-emerald-400">
                    {geographic_calculation.calculated_distance_km.toFixed(2)} km
                  </span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">
              No authoritative independent public records or sensors found within verifiable radius.
            </p>
          )}
        </div>

        {/* Step 3: Explanation / Verdict Summary */}
        <div className="text-xs text-slate-300 leading-relaxed pt-1">
          <p className="font-medium text-slate-200">
            {finding.summary}
          </p>
        </div>

        {/* Card Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-800/80">
          <span className="text-[11px] text-slate-400">
            {finding.evidence.length} evidence source{finding.evidence.length === 1 ? "" : "s"}
          </span>

          <Link
            href={`/audit/${auditId}/finding/${finding.id}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400 hover:text-emerald-300 hover:underline"
          >
            <span>Inspect Evidence Chain & Map</span>
            <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}


"use client";

import React from "react";
import { FileText, Bookmark, Database, Calculator, Scale, CheckCircle2, AlertTriangle, HelpCircle, ArrowDown } from "lucide-react";
import { VerificationStatus } from "@/types/audit";

interface EvidenceChainProps {
  claimText: string;
  pageNumber: number;
  evidenceTitle: string;
  evidenceSource: string;
  evidenceQuality: string;
  methodology: string;
  calculationSummary: string;
  status: VerificationStatus;
}

export function EvidenceChain({
  claimText,
  pageNumber,
  evidenceTitle,
  evidenceSource,
  evidenceQuality,
  methodology,
  calculationSummary,
  status,
}: EvidenceChainProps) {
  const isVerified = status === "verified";
  const isInconsistent = status === "potential_inconsistency";

  return (
    <div className="bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-4 flex items-center gap-2">
        <span>Deterministic Verification Chain</span>
        <span className="text-[10px] bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded-full font-mono">
          Audit Proof Trail
        </span>
      </h3>

      <div className="flex flex-col items-stretch space-y-2">
        {/* Step 1: Report Claim */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 shadow-2xs">
          <div className="p-2 rounded-md bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5">
            <FileText className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">1. Report Claim</div>
            <p className="text-xs text-slate-900 dark:text-slate-100 font-medium italic mt-0.5">
              &ldquo;{claimText}&rdquo;
            </p>
          </div>
        </div>

        <div className="flex justify-center text-slate-400 -my-1">
          <ArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 2: Page Reference */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 shadow-2xs">
          <div className="p-2 rounded-md bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5">
            <Bookmark className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">2. Document Citation</div>
            <div className="text-xs text-slate-800 dark:text-slate-200 font-mono mt-0.5">
              Page {pageNumber} in original uploaded Environmental Impact Assessment PDF
            </div>
          </div>
        </div>

        <div className="flex justify-center text-slate-400 -my-1">
          <ArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 3: Independent Evidence */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 shadow-2xs">
          <div className="p-2 rounded-md bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5">
            <Database className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-2">
              <span>3. Independent Evidence</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded font-sans bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 font-medium">
                {evidenceQuality} quality
              </span>
            </div>
            <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 mt-0.5">{evidenceTitle}</div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Source: {evidenceSource}</div>
          </div>
        </div>

        <div className="flex justify-center text-slate-400 -my-1">
          <ArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 4: Deterministic Calculation */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 shadow-2xs">
          <div className="p-2 rounded-md bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5">
            <Calculator className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
              4. Deterministic Calculation
            </div>
            <div className="text-xs text-slate-800 dark:text-slate-200 font-mono mt-0.5">
              {calculationSummary}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Methodology: {methodology}</div>
          </div>
        </div>

        <div className="flex justify-center text-slate-400 -my-1">
          <ArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 5: Rule & Comparison */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 shadow-2xs">
          <div className="p-2 rounded-md bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400 shrink-0 mt-0.5">
            <Scale className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
              5. Decision Rule
            </div>
            <div className="text-xs text-slate-800 dark:text-slate-200 mt-0.5">
              Strict deterministic comparison with explicit physical/regulatory tolerances.
            </div>
          </div>
        </div>

        <div className="flex justify-center text-slate-400 -my-1">
          <ArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 6: Finding Status */}
        <div
          className={`flex items-start gap-3 p-3.5 rounded-lg border shadow-xs ${
            isVerified
              ? "bg-emerald-50/80 dark:bg-emerald-950/30 border-emerald-300 dark:border-emerald-800"
              : isInconsistent
              ? "bg-amber-50/80 dark:bg-amber-950/30 border-amber-300 dark:border-amber-800"
              : "bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700"
          }`}
        >
          <div className="p-2 rounded-md shrink-0 mt-0.5">
            {isVerified ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            ) : isInconsistent ? (
              <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            ) : (
              <HelpCircle className="w-5 h-5 text-slate-500 dark:text-slate-400" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              6. Final Audit Finding
            </div>
            <div
              className={`text-sm font-bold uppercase tracking-wide mt-0.5 ${
                isVerified
                  ? "text-emerald-700 dark:text-emerald-300"
                  : isInconsistent
                  ? "text-amber-700 dark:text-amber-300"
                  : "text-slate-700 dark:text-slate-300"
              }`}
            >
              {status.replace("_", " ")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


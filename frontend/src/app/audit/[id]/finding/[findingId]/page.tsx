"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Calculator,
  Compass,
  FileText,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Database,
  Layers,
  ChevronRight,
  Info
} from "lucide-react";

import { VerificationResult, Claim, Evidence, ProjectLocation } from "@/types/audit";
import { getFindingById, getAuditClaims, getAuditEvidence, getAuditLocation } from "@/lib/api";
import { GeographicFindingMap } from "@/components/GeographicFindingMap";
import { EvidenceChain } from "@/components/EvidenceChain";

export default function FindingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const auditId = params?.id as string;
  const findingId = params?.findingId as string;

  const [finding, setFinding] = useState<VerificationResult | null>(null);
  const [claim, setClaim] = useState<Claim | null>(null);
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [location, setLocation] = useState<ProjectLocation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!auditId || !findingId) return;

    let isMounted = true;
    async function loadData() {
      try {
        setLoading(true);
        // 1. Fetch Finding
        const f = await getFindingById(auditId, findingId);
        if (!isMounted) return;
        setFinding(f);

        // 2. Fetch associated Claim
        const claims = await getAuditClaims(auditId);
        const matchedClaim = claims.find((c) => c.id === f.claimId);
        if (matchedClaim) setClaim(matchedClaim);

        // 3. Fetch associated Evidence
        const evs = await getAuditEvidence(auditId, { claimId: f.claimId });
        setEvidenceList(evs);

        // 4. Fetch Project Location
        const loc = await getAuditLocation(auditId);
        setLocation(loc);
      } catch (err: any) {
        if (isMounted) setError(err.message || "Failed to load finding details.");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [auditId, findingId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center p-6">
        <div className="w-10 h-10 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
          Loading deterministic finding & calculation audit trail...
        </p>
      </div>
    );
  }

  if (error || !finding) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 flex flex-col items-center justify-center">
        <div className="max-w-md w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 text-center shadow-lg">
          <AlertCircle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Finding Not Found</h2>
          <p className="text-xs text-slate-500 mt-2">{error || "Could not retrieve the specified finding record."}</p>
          <Link
            href={`/audit/${auditId}`}
            className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-lg text-xs font-semibold"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Audit Workspace
          </Link>
        </div>
      </div>
    );
  }

  const primaryEvidence = evidenceList.length > 0 ? evidenceList[0] : null;
  const isGeographic = finding.methodology.includes("geographic") || finding.methodology.includes("geodesic") || !!primaryEvidence?.geometry;
  const projectCoords: [number, number] = location?.coordinates || [39.75470, -105.22110];

  const isVerified = finding.status === "verified";
  const isInconsistent = finding.status === "potential_inconsistency";

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 pb-20">
      {/* Top Header */}
      <header className="sticky top-0 z-30 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href={`/audit/${auditId}`}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Audit</span>
            </Link>
            <div className="h-4 w-px bg-slate-200 dark:bg-slate-800" />
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-slate-400">Finding ID:</span>
              <span className="font-mono text-xs font-bold text-slate-700 dark:text-slate-300">{finding.id}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {finding.priority && (
              <span
                className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold border ${
                  finding.priority === "CRITICAL"
                    ? "bg-rose-50 text-rose-700 border-rose-300 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800"
                    : finding.priority === "HIGH"
                    ? "bg-orange-50 text-orange-700 border-orange-300 dark:bg-orange-950/60 dark:text-orange-300 dark:border-orange-800"
                    : finding.priority === "MEDIUM"
                    ? "bg-amber-50 text-amber-700 border-amber-300 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800"
                    : "bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800"
                }`}
              >
                Priority: {finding.priority}
              </span>
            )}
            {finding.semanticCompatibility && (
              <span
                className={`px-2.5 py-1 rounded-md text-xs font-mono font-medium border ${
                  finding.semanticCompatibility === "compatible"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800"
                    : finding.semanticCompatibility === "partially_compatible"
                    ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800"
                    : "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700"
                }`}
              >
                Semantic: {finding.semanticCompatibility.replace("_", " ")}
              </span>
            )}
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-2xs ${
                isVerified
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800"
                  : isInconsistent
                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800"
                  : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300 border border-slate-300 dark:border-slate-700"
              }`}
            >
              {isVerified ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : isInconsistent ? (
                <AlertTriangle className="w-4 h-4" />
              ) : (
                <HelpCircle className="w-4 h-4" />
              )}
              <span>{finding.status.replace("_", " ")}</span>
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {/* Banner Alert if Inconsistency or Limitations */}
        {isInconsistent && (
          <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/80 flex items-start gap-3 shadow-xs">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-900 dark:text-amber-200 leading-relaxed">
              <span className="font-bold">Potential Inconsistency Detected: </span>
              Independent retrieved evidence and deterministic analysis conflict with the reported claim. Note: This indicates a spatial or numerical discrepancy for auditor inspection, not an accusation of intentional fraud.
            </div>
          </div>
        )}

        {/* Phase 5 Priority & Auditor Risk Context */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-xs">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-800 dark:text-slate-200">Auditor Priority Level:</span>
              <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                finding.priority === "CRITICAL"
                  ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-300 dark:border-rose-800"
                  : finding.priority === "HIGH"
                  ? "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300 border border-orange-300 dark:border-orange-800"
                  : finding.priority === "MEDIUM"
                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300 dark:border-amber-800"
                  : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800"
              }`}>
                {finding.priority || "MEDIUM"}
              </span>
            </div>
            {finding.priorityReason && (
              <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                {finding.priorityReason}
              </p>
            )}
          </div>
          {finding.recommendedAction && (
            <div className="sm:max-w-md bg-slate-50 dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] text-slate-700 dark:text-slate-300">
              <span className="font-semibold text-emerald-600 dark:text-emerald-400 block mb-0.5">Recommended Action:</span>
              <span>{finding.recommendedAction}</span>
            </div>
          )}
        </div>

        {/* Section 1: The Core Finding Summary Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column (2 Cols): Claim & Evidence Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Report Claim Card */}
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-4 h-4" />
                  Reported EIA Claim
                </span>
                <span className="text-[11px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded">
                  Page {claim?.page || 1}
                </span>
              </div>
              <p className="text-base sm:text-lg font-medium text-slate-900 dark:text-slate-100 leading-relaxed">
                &ldquo;{claim?.text || "Claim text"}&rdquo;
              </p>
              {claim?.sourceText && (
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/60 text-xs text-slate-500 italic">
                  Exact excerpt: &ldquo;{claim.sourceText}&rdquo;
                </div>
              )}
            </div>

            {/* Independent Evidence Card */}
            {primaryEvidence ? (
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Database className="w-4 h-4" />
                    Independent Evidence Retrieved
                  </span>
                  <span className="text-[11px] font-medium bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 px-2.5 py-0.5 rounded-full capitalize">
                    {primaryEvidence.quality} Quality
                  </span>
                </div>
                <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100">
                  {primaryEvidence.title}
                </h3>
                <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-500">
                  <span>Source: <strong className="text-slate-700 dark:text-slate-300">{primaryEvidence.sourceName}</strong></span>
                  <span>•</span>
                  <span>Retrieved: {new Date(primaryEvidence.retrievedAt).toLocaleDateString()}</span>
                  {primaryEvidence.sourceUrl && (
                    <>
                      <span>•</span>
                      <a
                        href={primaryEvidence.sourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        Authoritative Source Link <ExternalLink className="w-3 h-3" />
                      </a>
                    </>
                  )}
                </div>
                {primaryEvidence.excerpt && (
                  <p className="mt-3 text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-100 dark:border-slate-800 font-sans">
                    {primaryEvidence.excerpt}
                  </p>
                )}
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs text-center text-xs text-slate-500">
                No independent evidence was retrieved for this claim.
              </div>
            )}

            {/* Semantic Compatibility & Verification Scope */}
            {(finding.claimRequiredMeasurement || finding.availableMeasurement) && (
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4" />
                    Proposition &amp; Measurement Semantics
                  </span>
                  {finding.semanticCompatibility && (
                    <span className="text-[11px] font-mono capitalize px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      Scope: {finding.semanticCompatibility.replace("_", " ")}
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {finding.claimRequiredMeasurement && (
                    <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Claim-Required Measurement</div>
                      <div className="text-slate-800 dark:text-slate-200 font-medium mt-1">
                        {finding.claimRequiredMeasurement}
                      </div>
                    </div>
                  )}

                  {finding.availableMeasurement && (
                    <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Available Independent Measurement</div>
                      <div className="text-slate-800 dark:text-slate-200 font-medium mt-1 font-mono">
                        {finding.availableMeasurement}
                      </div>
                    </div>
                  )}
                </div>

                {/* Informational Callout when Unverifiable with Available Measurement */}
                {finding.status === "unverifiable" && finding.availableMeasurement && (
                  <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-xs text-blue-900 dark:text-blue-200 space-y-1">
                    <div className="font-semibold flex items-center gap-1.5">
                      <Info className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
                      Informational Measurement Preserved for Audit Transparency
                    </div>
                    <p className="text-[11px] leading-relaxed text-blue-800/90 dark:text-blue-300">
                      GroundCheck deterministically evaluated available spatial/statutory data ({finding.availableMeasurement}). However, because the report claim asserted conditions requiring boundary geometry or direct monitoring records, this calculation is preserved as an informational reference and cannot be used to verify or contradict the reported claim.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Phase 5: Structured Evidence Gap Analysis */}
            {finding.evidenceGap && (
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-amber-300 dark:border-amber-500/40 p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4" />
                    Structured Evidence Gap Analysis
                  </span>
                  <span className="text-[10px] font-mono uppercase bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 px-2 py-0.5 rounded border border-amber-300 dark:border-amber-800">
                    {finding.evidenceGap.category.replace("_", " ")}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold block">Required for Verification</span>
                    <span className="text-slate-800 dark:text-slate-200 font-medium mt-1 block">{finding.evidenceGap.required}</span>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold block">Authoritatively Available</span>
                    <span className="text-slate-800 dark:text-slate-200 font-medium mt-1 block font-mono">{finding.evidenceGap.available}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60 text-xs text-amber-900 dark:text-amber-200 space-y-1">
                  <div><strong className="text-amber-700 dark:text-amber-300">Audit Impact:</strong> {finding.evidenceGap.impact}</div>
                  <div><strong className="text-amber-700 dark:text-amber-300">Recommended Follow-up:</strong> {finding.evidenceGap.recommendedEvidence}</div>
                </div>
              </div>
            )}

            {/* Phase 5: Reproducible Arithmetic Comparison */}
            {finding.arithmeticComparison && (
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-purple-200 dark:border-purple-500/40 p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Calculator className="w-4 h-4" />
                    Reproducible Arithmetic Comparison
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                    finding.arithmeticComparison.isCompliant
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800"
                      : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-300 dark:border-rose-800"
                  }`}>
                    {finding.arithmeticComparison.isCompliant ? "COMPLIANT" : "NON-COMPLIANT"}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-xs flex flex-wrap items-center justify-between gap-2">
                  <span className="text-purple-700 dark:text-purple-300 font-bold">{finding.arithmeticComparison.formulaExpression}</span>
                  <span className="text-slate-600 dark:text-slate-400 text-[11px]">{finding.arithmeticComparison.conclusion}</span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-slate-50 dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase block">Reported Value</span>
                    <span className="font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5 block">{String(finding.arithmeticComparison.inputA)}</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase block">Condition</span>
                    <span className="font-mono font-bold text-purple-600 dark:text-purple-400 mt-0.5 block">{finding.arithmeticComparison.operator}</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase block">Threshold / Standard</span>
                    <span className="font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5 block">{String(finding.arithmeticComparison.thresholdValue ?? finding.arithmeticComparison.inputB)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Phase 5: Cross-Claim Dependencies */}
            {finding.dependencies && finding.dependencies.length > 0 && (
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-xs space-y-2">
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
                  Cross-Claim Dependencies
                </span>
                <div className="space-y-1.5">
                  {finding.dependencies.map((dep, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs flex items-center justify-between">
                      <span className="text-slate-700 dark:text-slate-300">{dep.description}</span>
                      <span className="text-[10px] font-mono text-cyan-600 dark:text-cyan-400 uppercase">{dep.dependencyType}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Verification Math & Calculation Steps */}
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Calculator className="w-4 h-4" />
                  Deterministic Calculation Audit Trail
                </span>
                <span className="text-[11px] font-mono text-slate-500">
                  Methodology: {finding.methodology}
                </span>
              </div>

              {/* Quantitative Comparison Matrix */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 text-xs">
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Reported Value</div>
                  <div className="font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                    {finding.reportedValue !== undefined && finding.reportedValue !== null ? String(finding.reportedValue) : "N/A"}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Independently Observed</div>
                  <div className="font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                    {finding.independentlyObservedValue !== undefined && finding.independentlyObservedValue !== null ? String(finding.independentlyObservedValue) : "N/A"}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Discrepancy / Margin</div>
                  <div className="font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                    {finding.difference !== undefined && finding.difference !== null ? `${finding.difference} ${finding.units || ""}` : "0"}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Applied Tolerance</div>
                  <div className="font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                    {finding.tolerance || "Default"}
                  </div>
                </div>
              </div>

              {/* Step by Step Breakdown Cards */}
              <div className="space-y-3 pt-2">
                <div className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  Step-by-Step Mathematical Operations:
                </div>
                {finding.calculationSteps.length > 0 ? (
                  finding.calculationSteps.map((step) => (
                    <div
                      key={step.stepNumber}
                      className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-800 dark:text-slate-200">
                          Step {step.stepNumber}: <span className="font-mono text-purple-600 dark:text-purple-400">{step.operation}</span>
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                        {step.description}
                      </p>
                      <div className="pt-2 flex flex-wrap gap-2 text-[11px] font-mono">
                        <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-600 dark:text-slate-400">
                          Output: {typeof step.outputValue === "object" ? JSON.stringify(step.outputValue) : String(step.outputValue)}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 italic">No formal calculation steps were required for this finding.</p>
                )}
              </div>

              {/* Why & Explanation */}
              <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
                <div className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Why GroundCheck Reached This Finding:
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/40 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                  {finding.explanation}
                </p>
              </div>

              {/* Limitations & Uncertainty */}
              {(finding.limitations || finding.uncertainty) && (
                <div className="p-3 rounded-lg bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs space-y-1">
                  <div className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-slate-500" />
                    Limitations & Uncertainty Notes:
                  </div>
                  {finding.limitations && (
                    <div className="text-slate-600 dark:text-slate-400 pl-5">
                      • {finding.limitations}
                    </div>
                  )}
                  {finding.uncertainty && (
                    <div className="text-slate-600 dark:text-slate-400 pl-5">
                      • {finding.uncertainty}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Evidence Chain & Map */}
          <div className="space-y-6">
            {/* The Visual Evidence Chain Component */}
            <EvidenceChain
              claimText={claim?.text || "Reported Claim"}
              pageNumber={claim?.page || 1}
              evidenceTitle={primaryEvidence?.title || "Independent Source"}
              evidenceSource={primaryEvidence?.sourceName || "Open Geographic Register"}
              evidenceQuality={primaryEvidence?.quality || "Moderate"}
              methodology={finding.methodology}
              calculationSummary={
                finding.calculatedValue !== null && finding.calculatedValue !== undefined
                  ? `Calculated ${finding.calculatedValue} ${finding.units || ""}`
                  : "Deterministic Rule Evaluation"
              }
              status={finding.status}
            />

            {/* MapLibre Geographic Visualization */}
            {isGeographic && (
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Compass className="w-4 h-4 text-emerald-600" />
                    Geographic Spatial Inspection
                  </span>
                  <span className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 px-2 py-0.5 rounded font-mono">
                    MapLibre GL
                  </span>
                </div>

                <GeographicFindingMap
                  projectCoords={projectCoords}
                  evidenceGeometry={primaryEvidence?.geometry}
                  evidenceTitle={primaryEvidence?.title || "Evidence Feature"}
                  calculatedDistanceMeters={typeof finding.calculatedValue === "number" ? finding.calculatedValue : null}
                  methodology={finding.methodology}
                  difference={finding.difference}
                />

                <div className="text-[11px] text-slate-500 leading-snug">
                  Project coordinates ({projectCoords[0].toFixed(5)}° N, {projectCoords[1].toFixed(5)}° W) mapped against independent OpenStreetMap feature coordinates using WGS84 Karney geodesic projection.
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}


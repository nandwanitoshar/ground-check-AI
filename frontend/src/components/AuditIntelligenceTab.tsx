"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  FileQuestion,
  HelpCircle,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  RefreshCw,
  Compass,
  Layers,
  Scale,
  Activity,
  Calendar,
  Database,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  CheckCircle2,
  XCircle,
  FileSpreadsheet,
  UploadCloud,
  Eye,
  Info
} from "lucide-react";
import {
  AuditDecisionPackage,
  Claim,
  VerificationResult
} from "@/types/audit";
import { fetchAuditIntelligence } from "@/lib/api";
import RadialRiskScore from "@/components/RadialRiskScore";

interface AuditIntelligenceTabProps {
  auditId: string;
  claims: Claim[];
  verifications: VerificationResult[];
  onNavigateToWorkspace?: () => void;
}

export default function AuditIntelligenceTab({
  auditId,
  claims,
  verifications,
  onNavigateToWorkspace
}: AuditIntelligenceTabProps) {
  const [data, setData] = useState<AuditDecisionPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Expandable modals/drawers for explainability
  const [showRiskBreakdown, setShowRiskBreakdown] = useState(false);
  const [showCoverageBreakdown, setShowCoverageBreakdown] = useState(false);
  const [expandedWwcClaim, setExpandedWwcClaim] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchAuditIntelligence(auditId);
      setData(res);
      if (res && res.what_would_change.length > 0) {
        setExpandedWwcClaim(res.what_would_change[0].claim_id);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load audit intelligence decision package.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [auditId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 bg-slate-900/40 rounded-2xl border border-slate-800">
        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mb-3" />
        <p className="text-slate-300 font-medium">Computing deterministic decision support intelligence...</p>
        <p className="text-xs text-slate-500 mt-1">Evaluating materiality, evidence coverage, explainable risk, and sensitivity scenarios</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-rose-950/20 border border-rose-900/50 rounded-2xl p-6 text-center">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto mb-2" />
        <h3 className="text-lg font-semibold text-rose-200">Decision Intelligence Unavailable</h3>
        <p className="text-sm text-rose-300/80 mt-1 max-w-md mx-auto">{error || "Could not retrieve audit intelligence package."}</p>
        <button
          onClick={loadData}
          className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm inline-flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" /> Retry Analysis
        </button>
      </div>
    );
  }

  const { decision, risk_assessment, coverage, uncertainty, top_concerns, recommended_actions, what_would_change, cross_claim_impact } = data;

  // Status Badge Styling Helper
  const getStatusStyle = (status: string) => {
    switch (status) {
      case "CRITICAL REVIEW REQUIRED":
        return {
          bg: "bg-rose-950/60 border-rose-500/50 text-rose-300",
          icon: <ShieldAlert className="w-6 h-6 text-rose-400 animate-pulse" />,
          pill: "bg-rose-500/20 text-rose-300 border-rose-500/30"
        };
      case "HIGH RISK":
        return {
          bg: "bg-amber-950/60 border-amber-500/50 text-amber-300",
          icon: <AlertTriangle className="w-6 h-6 text-amber-400" />,
          pill: "bg-amber-500/20 text-amber-300 border-amber-500/30"
        };
      case "INSUFFICIENT EVIDENCE":
        return {
          bg: "bg-purple-950/60 border-purple-500/50 text-purple-300",
          icon: <FileQuestion className="w-6 h-6 text-purple-400" />,
          pill: "bg-purple-500/20 text-purple-300 border-purple-500/30"
        };
      case "LOW RISK":
        return {
          bg: "bg-emerald-950/60 border-emerald-500/50 text-emerald-300",
          icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />,
          pill: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
        };
      case "MODERATE RISK":
      default:
        return {
          bg: "bg-cyan-950/60 border-cyan-500/50 text-cyan-300",
          icon: <Compass className="w-6 h-6 text-cyan-400" />,
          pill: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30"
        };
    }
  };

  const statusStyle = getStatusStyle(decision.overall_status);

  return (
    <div className="space-y-8 animate-fadeIn text-slate-100">
      {/* 1. EXECUTIVE DECISION HERO BANNER */}
      <div className={`p-6 rounded-2xl border ${statusStyle.bg} backdrop-blur-sm relative overflow-hidden shadow-2xl`}>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Final Environmental Audit Assessment</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">Phase 7 Deterministic Engine</span>
            </div>
            <div className="flex items-center gap-3">
              {statusStyle.icon}
              <h2 className="text-3xl font-extrabold tracking-tight">{decision.overall_status}</h2>
            </div>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">{decision.status_rationale}</p>
            <div className="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-400">
              <span className="font-mono bg-slate-900/80 px-2.5 py-1 rounded border border-slate-800">
                Trigger: {decision.primary_trigger}
              </span>
              <span className="text-slate-500">•</span>
              <span className="text-slate-400 italic">{decision.matched_rule}</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
            {onNavigateToWorkspace && (
              <button
                onClick={onNavigateToWorkspace}
                className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-emerald-950 transition-all hover:scale-[1.02]"
              >
                <UploadCloud className="w-4 h-4" /> Open Evidence Workspace
              </button>
            )}
            <button
              onClick={loadData}
              className="px-3.5 py-2.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-medium flex items-center justify-center gap-2 border border-slate-700 transition"
              title="Refresh intelligence"
            >
              <RefreshCw className="w-4 h-4" /> Refresh
            </button>
          </div>
        </div>
      </div>

      {/* 2. CORE DECISION KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Risk Score with "Why?" */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition relative">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Deterministic Risk Index</span>
            <button
              onClick={() => setShowRiskBreakdown(!showRiskBreakdown)}
              className="text-cyan-400 hover:text-cyan-300 underline font-normal flex items-center gap-1 text-[11px]"
            >
              Why? <HelpCircle className="w-3 h-3" />
            </button>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-100">{risk_assessment.final_score}</span>
            <span className="text-xs text-slate-500 font-mono">/ 100</span>
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
            {risk_assessment.final_score >= 60 ? (
              <span className="text-rose-400 font-semibold flex items-center gap-1"><TrendingUp className="w-3.5 h-3.5" /> High Risk</span>
            ) : risk_assessment.final_score >= 25 ? (
              <span className="text-cyan-400 font-semibold flex items-center gap-1"><Compass className="w-3.5 h-3.5" /> Moderate Risk</span>
            ) : (
              <span className="text-emerald-400 font-semibold flex items-center gap-1"><TrendingDown className="w-3.5 h-3.5" /> Low Risk</span>
            )}
            <span className="text-slate-600">•</span>
            <span>{risk_assessment.contributions.length} score factors</span>
          </div>
        </div>

        {/* KPI 2: Evidence Coverage with "Why?" */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition relative">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Evidence Coverage</span>
            <button
              onClick={() => setShowCoverageBreakdown(!showCoverageBreakdown)}
              className="text-cyan-400 hover:text-cyan-300 underline font-normal flex items-center gap-1 text-[11px]"
            >
              Formula <Info className="w-3 h-3" />
            </button>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-100">{coverage.coverage_percentage}%</span>
            <span className="text-xs text-slate-500 font-mono">weighted</span>
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
            <span className="text-emerald-400 font-medium">{coverage.material_claims_fully_supported} of {coverage.material_claims_total} material verified</span>
            {coverage.material_claims_partially_supported > 0 && (
              <>
                <span className="text-slate-600">•</span>
                <span className="text-amber-400">{coverage.material_claims_partially_supported} partial</span>
              </>
            )}
          </div>
        </div>

        {/* KPI 3: Material Claims */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            Material Claims Total
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-100">{coverage.material_claims_total}</span>
            <span className="text-xs text-slate-500">of {claims.length} total claims</span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {coverage.material_claims_unsupported > 0 ? (
              <span className="text-amber-400 font-medium">{coverage.material_claims_unsupported} material gaps unresolved</span>
            ) : (
              <span className="text-emerald-400 font-medium">All material claims resolved</span>
            )}
          </div>
        </div>

        {/* KPI 4: Residual Uncertainty Level */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            Residual Uncertainty
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-2xl font-black ${
              uncertainty.overall_level === "HIGH" ? "text-rose-400" :
              uncertainty.overall_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400"
            }`}>
              {uncertainty.overall_level}
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-400 truncate" title={uncertainty.summary_reason}>
            {uncertainty.summary_reason}
          </div>
        </div>
      </div>

      {/* EXPANDABLE MODAL: RISK EXPLAINABILITY (Why?) */}
      {showRiskBreakdown && (
        <div className="bg-[#0D1317] border border-cyan-500/40 rounded-2xl p-6 shadow-2xl animate-fadeIn space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Compass className="w-5 h-5 text-cyan-400" /> Explainable Risk Score Breakdown
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Every score point is deterministically mapped to verified facts, evidence gaps, or discrepancies.</p>
            </div>
            <button
              onClick={() => setShowRiskBreakdown(false)}
              className="text-slate-400 hover:text-slate-200 text-sm px-2.5 py-1 rounded bg-[#080C0E] border border-slate-800"
            >
              ✕ Close
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            <div className="lg:col-span-5">
              <RadialRiskScore
                score={risk_assessment.final_score}
                verifiedCount={verifications.filter(v => v.verification_status === "VERIFIED").length}
                unverifiableCount={verifications.filter(v => v.verification_status === "UNVERIFIABLE").length}
                inconsistentCount={verifications.filter(v => v.verification_status === "INCONSISTENT").length}
              />
            </div>
            <div className="lg:col-span-7 space-y-3">
              <span className="font-mono text-[10px] text-slate-500 uppercase tracking-widest block">DETERMINISTIC FORMULA</span>
              <div className="bg-[#080C0E] p-3.5 rounded-xl border border-slate-800 font-mono text-xs text-slate-300">
                {risk_assessment.formula_summary}
              </div>
              <p className="text-xs text-slate-400 leading-relaxed font-mono">
                Formula: Risk = Clamped in [0, 100]. High Material Unverified (+10) + Setback Ambiguity (+15) + Missing Linear Corridor (+10).
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Impact</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Claim Target</th>
                  <th className="py-2.5 px-3">Deterministic Scoring Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {risk_assessment.contributions.map((c, i) => (
                  <tr key={i} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-mono font-bold">
                      <span className={`px-2 py-0.5 rounded ${
                        c.points > 0 ? "bg-rose-500/20 text-rose-300" : "bg-emerald-500/20 text-emerald-300"
                      }`}>
                        {c.points > 0 ? `+${c.points}` : c.points} pts
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 capitalize">{c.category.replace("_", " ")}</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">
                      {c.claim_id ? `Claim #${c.claim_id.split('_').slice(-1)[0]}` : "Report Level"}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{c.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* EXPANDABLE MODAL: EVIDENCE COVERAGE (Formula) */}
      {showCoverageBreakdown && (
        <div className="bg-slate-900 border border-cyan-500/40 rounded-2xl p-6 shadow-2xl animate-fadeIn space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Info className="w-5 h-5 text-cyan-400" /> Evidence Coverage Formula & Weights
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">{coverage.formula_explanation}</p>
            </div>
            <button
              onClick={() => setShowCoverageBreakdown(false)}
              className="text-slate-400 hover:text-slate-200 text-sm px-2 py-1 rounded bg-slate-800"
            >
              ✕ Close
            </button>
          </div>

          <div className="overflow-x-auto max-h-80">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800 sticky top-0">
                <tr>
                  <th className="py-2.5 px-3">Claim</th>
                  <th className="py-2.5 px-3">Materiality</th>
                  <th className="py-2.5 px-3">Weight</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Earned Points</th>
                  <th className="py-2.5 px-3">Audit Evidence Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {coverage.items.map((it, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-medium text-slate-200 max-w-xs truncate" title={it.claim_text}>
                      #{it.claim_id.split('_').slice(-1)[0]}: {it.claim_text}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        it.materiality === "MATERIAL" ? "bg-purple-500/20 text-purple-300 border border-purple-500/30" :
                        it.materiality === "IMPORTANT" ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30" :
                        "bg-slate-800 text-slate-400"
                      }`}>
                        {it.materiality}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono">{it.weight.toFixed(1)}</td>
                    <td className="py-2.5 px-3 uppercase font-mono text-[11px]">{it.verification_status}</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-emerald-400">{it.earned_weight.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-slate-300">{it.support_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. TOP AUDIT CONCERNS */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-3">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" /> Top Audit Concerns
        </h3>
        <div className="space-y-2">
          {top_concerns.map((tc, idx) => (
            <div key={idx} className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl text-sm flex items-start gap-3">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-slate-800 text-slate-400 text-xs flex items-center justify-center font-mono">
                {idx + 1}
              </span>
              <p className="text-slate-300 leading-snug">{tc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 4. WHAT WOULD CHANGE THIS AUDIT? (DECISION SENSITIVITY) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" /> What Would Change This Audit?
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Deterministic sensitivity analysis projecting what specific evidence would materially alter unresolved findings.
            </p>
          </div>
        </div>

        {what_would_change.length === 0 ? (
          <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-2xl text-center text-slate-400 text-sm">
            All material environmental assertions have been independently corroborated. No unresolved sensitivity conditions remaining.
          </div>
        ) : (
          <div className="space-y-3">
            {what_would_change.map((wwc) => {
              const isExpanded = expandedWwcClaim === wwc.claim_id;
              return (
                <div
                  key={wwc.claim_id}
                  className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-700 transition"
                >
                  <button
                    onClick={() => setExpandedWwcClaim(isExpanded ? null : wwc.claim_id)}
                    className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/30 transition"
                  >
                    <div className="space-y-1 pr-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-cyan-400">Claim #{wwc.claim_id.split('_').slice(-1)[0]}</span>
                        <span className="text-slate-500">•</span>
                        <span className="text-xs text-slate-400">Page {wwc.page}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                          {wwc.materiality}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-amber-300 border border-amber-500/30">
                          {wwc.current_status}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-slate-200 line-clamp-1">{wwc.claim_text}</p>
                      <p className="text-xs text-slate-400 flex items-center gap-1.5 pt-0.5">
                        <span className="text-slate-500">Missing Evidence:</span>
                        <span className="text-slate-300 font-mono">{wwc.missing_evidence}</span>
                      </p>
                    </div>

                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className="text-xs text-cyan-400 hidden sm:inline">
                        {isExpanded ? "Collapse" : "View Scenarios"}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-slate-400" />
                      )}
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="p-4 pt-0 border-t border-slate-800/80 bg-slate-950/60 space-y-3">
                      <div className="text-xs text-slate-400 pt-3">
                        Projected outcomes if proponent or auditor supplies evidence matching required schema (<code className="text-cyan-300">{wwc.required_evidence_type}</code>):
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {wwc.potential_outcomes.map((out, outIdx) => {
                          const isVerified = out.resulting_status === "VERIFIED";
                          const isIncon = out.resulting_status === "POTENTIAL_INCONSISTENCY";
                          return (
                            <div
                              key={outIdx}
                              className={`p-3.5 rounded-xl border ${
                                isVerified
                                  ? "bg-emerald-950/20 border-emerald-900/60"
                                  : isIncon
                                  ? "bg-rose-950/20 border-rose-900/60"
                                  : "bg-slate-900/80 border-slate-800"
                              } space-y-2`}
                            >
                              <div className="flex items-center justify-between">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                                  isVerified ? "bg-emerald-500/20 text-emerald-300" :
                                  isIncon ? "bg-rose-500/20 text-rose-300" :
                                  "bg-slate-800 text-slate-300"
                                }`}>
                                  {out.resulting_status}
                                </span>
                                <span className={`text-[11px] font-mono font-bold ${
                                  out.risk_impact.startsWith("-") ? "text-emerald-400" :
                                  out.risk_impact.startsWith("+") ? "text-rose-400" : "text-slate-400"
                                }`}>
                                  {out.risk_impact.split(' ')[0]}
                                </span>
                              </div>

                              <p className="text-xs font-semibold text-slate-200 leading-snug">{out.condition}</p>
                              <p className="text-[11px] text-slate-400 leading-relaxed">{out.explanation}</p>
                              <div className="text-[11px] text-cyan-400/90 font-medium pt-1 border-t border-slate-800/60">
                                Impact: {out.decision_impact}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 5. PRIORITIZED RECOMMENDED AUDITOR ACTIONS */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Scale className="w-5 h-5 text-emerald-400" /> Prioritized Auditor Action Plan
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Ranked, high-impact actions designed to resolve the highest materiality evidence gaps.
            </p>
          </div>
        </div>

        <div className="space-y-3">
          {recommended_actions.map((act) => (
            <div
              key={act.priority}
              className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold flex items-center justify-center flex-shrink-0 text-sm">
                  #{act.priority}
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-slate-200 leading-snug">{act.action}</h4>
                  <p className="text-xs text-slate-400">{act.reason}</p>
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <span className="text-[11px] text-emerald-400 font-medium">Impact: {act.expected_impact}</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-[11px] font-mono text-cyan-300">Format: {act.evidence_type_required}</span>
                    {act.affected_claims.length > 0 && (
                      <>
                        <span className="text-slate-600">•</span>
                        <span className="text-[11px] text-purple-300">
                          Affects: {act.affected_claims.map(c => `Claim #${c.split('_').slice(-1)[0]}`).join(", ")}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {onNavigateToWorkspace && (
                <button
                  onClick={onNavigateToWorkspace}
                  className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold flex items-center gap-1.5 border border-slate-700 whitespace-nowrap transition flex-shrink-0"
                >
                  Fulfill in Workspace <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 6. RESIDUAL UNCERTAINTY MATRIX */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Compass className="w-4 h-4 text-cyan-400" /> Multi-Dimensional Residual Uncertainty
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Evaluation of residual uncertainty across spatial, measurement, regulatory, source, and temporal dimensions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {uncertainty.dimensions.map((dim, idx) => (
            <div key={idx} className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-slate-300 uppercase">
                  {dim.dimension} Uncertainty
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                  dim.level === "HIGH" ? "bg-rose-500/20 text-rose-300 border border-rose-500/30" :
                  dim.level === "MEDIUM" ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" :
                  "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                }`}>
                  {dim.level}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{dim.description}</p>
              <div className="text-[11px] text-cyan-400/90 pt-1 border-t border-slate-800/80">
                Mitigation: {dim.mitigating_action}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 7. CROSS-CLAIM IMPACT GRAPH */}
      {cross_claim_impact.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" /> Cross-Claim Impact Cascades
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Demonstrates how a single missing evidence file impacts multiple claims, risk index, and final decision.
            </p>
          </div>

          <div className="space-y-3">
            {cross_claim_impact.map((node, nIdx) => (
              <div key={nIdx} className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-emerald-400">{node.evidence_name}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-xs text-cyan-300 font-mono">
                    Direct: {node.directly_affected_claims.map(c => `Claim #${c.split('_').slice(-1)[0]}`).join(", ")}
                  </span>
                  {node.indirectly_affected_claims.length > 0 && (
                    <>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                      <span className="text-xs text-purple-300 font-mono">
                        Downstream: {node.indirectly_affected_claims.map(c => `Claim #${c.split('_').slice(-1)[0]}`).join(", ")}
                      </span>
                    </>
                  )}
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{node.downstream_impact}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


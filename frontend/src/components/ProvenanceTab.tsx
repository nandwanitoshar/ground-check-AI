"use client";

import React, { useState, useEffect } from "react";
import {
  EvidenceProvenance,
  EvidenceLineageGraph,
  ReproducibilityCheckResult,
  Claim
} from "@/types/audit";
import {
  fetchAuditProvenance,
  fetchAllClaimLineages,
  runReproducibilityCheck,
  fetchReproducibilitySummary,
  getReproducibilityPackageDownloadUrl
} from "@/lib/api";
import InteractiveProvenanceGraph from "@/components/InteractiveProvenanceGraph";

interface ProvenanceTabProps {
  auditId: string;
  claims?: Claim[];
}

export function ProvenanceTab({ auditId, claims = [] }: ProvenanceTabProps) {
  const [provenanceList, setProvenanceList] = useState<EvidenceProvenance[]>([]);
  const [lineages, setLineages] = useState<EvidenceLineageGraph[]>([]);
  const [reproResult, setReproResult] = useState<ReproducibilityCheckResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [checking, setChecking] = useState<boolean>(false);
  const [selectedClaimId, setSelectedClaimId] = useState<string>("");
  const [expandedProvId, setExpandedProvId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [auditId]);

  async function loadData() {
    setLoading(true);
    try {
      const [prov, lins, repro] = await Promise.all([
        fetchAuditProvenance(auditId),
        fetchAllClaimLineages(auditId),
        fetchReproducibilitySummary(auditId)
      ]);
      setProvenanceList(prov);
      setLineages(lins);
      setReproResult(repro);
      if (claims.length > 0 && !selectedClaimId) {
        setSelectedClaimId(claims[0].id);
      } else if (lins.length > 0 && !selectedClaimId) {
        setSelectedClaimId(lins[0].claim_id);
      }
    } catch (err) {
      console.error("Failed to load provenance data:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRunCheck() {
    setChecking(true);
    try {
      const res = await runReproducibilityCheck(auditId);
      setReproResult(res);
      // Refresh provenance list to reflect updated integrity checks
      const updatedProv = await fetchAuditProvenance(auditId);
      setProvenanceList(updatedProv);
    } catch (err) {
      console.error("Reproducibility check failed:", err);
    } finally {
      setChecking(false);
    }
  }

  const selectedLineage = lineages.find((l) => l.claim_id === selectedClaimId);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium text-slate-400">Verifying cryptographic digests & source provenance...</p>
      </div>
    );
  }

  const overallStatus = reproResult?.overall_status || (reproResult as any)?.overallStatus || "PASS";

  return (
    <div className="space-y-8">
      {/* Top Banner & Control Bar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-1 text-xs font-semibold uppercase tracking-wider rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Phase 8
              </span>
              <h2 className="text-xl font-bold text-slate-100">
                Evidence Provenance & External Source Verification
              </h2>
            </div>
            <p className="text-sm text-slate-400">
              Deterministic cryptographic SHA-256 auditing, complete lineage tracing, and reproducibility packaging.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleRunCheck}
              disabled={checking}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-sm disabled:opacity-50"
            >
              {checking ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Auditing Hashes...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Run Reproducibility Check</span>
                </>
              )}
            </button>

            <a
              href={getReproducibilityPackageDownloadUrl(auditId)}
              download
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition shadow-sm"
            >
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Download Reproducibility Package (ZIP)</span>
            </a>
          </div>
        </div>

        {/* Reproducibility Summary Pillars */}
        {reproResult && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-800">
            <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Evidence Integrity</span>
              <div className="flex items-center gap-2 mt-2">
                <span className={`inline-block w-2.5 h-2.5 rounded-full ${reproResult.evidence_integrity_status === "PASS" ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]" : "bg-rose-500"}`}></span>
                <span className="text-base font-bold text-slate-200">{reproResult.evidence_integrity_status}</span>
              </div>
              <span className="text-xs text-slate-400 mt-1 block">SHA-256 byte parity</span>
            </div>

            <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Math Reproducibility</span>
              <div className="flex items-center gap-2 mt-2">
                <span className={`inline-block w-2.5 h-2.5 rounded-full ${reproResult.calculation_reproducibility_status === "PASS" ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]" : "bg-rose-500"}`}></span>
                <span className="text-base font-bold text-slate-200">{reproResult.calculation_reproducibility_status}</span>
              </div>
              <span className="text-xs text-slate-400 mt-1 block">Formulas re-verified</span>
            </div>

            <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Verification Snapshot</span>
              <div className="flex items-center gap-2 mt-2">
                <span className={`inline-block w-2.5 h-2.5 rounded-full ${reproResult.verification_snapshot_status === "PASS" ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]" : "bg-amber-400"}`}></span>
                <span className="text-base font-bold text-slate-200">{reproResult.verification_snapshot_status}</span>
              </div>
              <span className="text-xs text-slate-400 mt-1 block">Run history diff match</span>
            </div>

            <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Source Metadata</span>
              <div className="flex items-center gap-2 mt-2">
                <span className={`inline-block w-2.5 h-2.5 rounded-full ${reproResult.source_metadata_status === "PASS" ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]" : "bg-amber-400"}`}></span>
                <span className="text-base font-bold text-slate-200">{reproResult.source_metadata_status}</span>
              </div>
              <span className="text-xs text-slate-400 mt-1 block">Authority & citations</span>
            </div>
          </div>
        )}
      </div>

      {/* Interactive Cryptographic Provenance DAG Visualizer */}
      <InteractiveProvenanceGraph className="mb-2" />

      {/* Lineage Visualizer */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <span>Multi-Step Evidence Lineage Graph</span>
              <span className="text-xs font-normal text-slate-400">
                (Source → Evidence → Claim → Verification → Finding → Decision)
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Select a claim statement below to inspect its complete deterministic verification lineage chain.
            </p>
          </div>

          {/* Claim Selector Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 max-w-full">
            {lineages.map((lin, idx) => {
              const isSelected = lin.claim_id === selectedClaimId;
              const claimLabel = `Claim #${idx + 1}`;
              return (
                <button
                  key={lin.claim_id}
                  onClick={() => setSelectedClaimId(lin.claim_id)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                    isSelected
                      ? "bg-emerald-600 text-white shadow-sm"
                      : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  {claimLabel}
                </button>
              );
            })}
          </div>
        </div>

        {selectedLineage ? (
          <div className="space-y-6">
            <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 text-xs text-slate-300">
              <span className="font-semibold text-emerald-400">Lineage Summary:</span> {selectedLineage.summary}
            </div>

            {/* Pipeline Stage Nodes */}
            <div className="grid grid-cols-1 md:grid-cols-6 gap-3 relative">
              {selectedLineage.nodes.map((node, i) => {
                const stageColor =
                  node.stage === "source"
                    ? "border-sky-500/50 bg-sky-950/20 text-sky-400"
                    : node.stage === "evidence"
                    ? "border-indigo-500/50 bg-indigo-950/20 text-indigo-400"
                    : node.stage === "claim"
                    ? "border-amber-500/50 bg-amber-950/20 text-amber-400"
                    : node.stage === "verification"
                    ? "border-purple-500/50 bg-purple-950/20 text-purple-400"
                    : node.stage === "finding"
                    ? "border-emerald-500/50 bg-emerald-950/20 text-emerald-400"
                    : "border-teal-500/50 bg-teal-950/20 text-teal-400";

                return (
                  <div
                    key={node.identifier || i}
                    className={`border rounded-lg p-3 space-y-2 flex flex-col justify-between ${stageColor}`}
                  >
                    <div>
                      <div className="flex items-center justify-between text-[10px] uppercase font-bold tracking-wider opacity-75">
                        <span>Stage {i + 1}</span>
                        <span>{node.stage}</span>
                      </div>
                      <h4 className="text-xs font-bold text-slate-200 mt-1 line-clamp-2">{node.label}</h4>
                    </div>

                    <div className="text-[11px] text-slate-400 space-y-1 bg-slate-900/60 p-2 rounded border border-slate-800/80">
                      {Object.entries(node.details || {}).map(([key, val]) => (
                        <div key={key} className="break-all">
                          <span className="font-semibold text-slate-300">{key}:</span>{" "}
                          <span>{typeof val === "object" ? JSON.stringify(val) : String(val)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500 text-sm">
            Select a claim above to render its lineage pipeline.
          </div>
        )}
      </div>

      {/* Structured Evidence Provenance Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <span>Authoritative Source Provenance & Integrity Registry</span>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
              {provenanceList.length} sources registered
            </span>
          </h3>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {provenanceList.map((prov) => {
            const isExpanded = expandedProvId === prov.id;
            const isTampered = prov.integrity_status === "TAMPERED";

            return (
              <div
                key={prov.id}
                className={`bg-slate-900 border rounded-xl p-5 transition shadow-lg ${
                  isTampered ? "border-rose-500/80 bg-rose-950/10" : "border-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                        {prov.source_type}
                      </span>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                          isTampered
                            ? "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                            : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                        }`}
                      >
                        {prov.integrity_status}
                      </span>
                      <span className="text-xs text-slate-400">
                        Confidence: <strong className="text-slate-200">{prov.provenance_confidence}</strong>
                      </span>
                      <span className="text-xs text-slate-400">
                        Quality: <strong className="text-slate-200">{prov.source_quality}</strong>
                      </span>
                    </div>

                    <h4 className="text-base font-bold text-slate-100">{prov.source_name}</h4>
                    <p className="text-xs text-slate-400">
                      Publisher: <strong className="text-slate-200">{prov.publisher || "Official Authority"}</strong> &bull;{" "}
                      Retrieved: <span className="font-mono text-slate-300">{new Date(prov.retrieved_at).toLocaleString()}</span>
                    </p>
                  </div>

                  <div className="flex flex-col items-start lg:items-end gap-2 text-xs font-mono text-slate-400">
                    <div className="flex items-center gap-1.5 bg-slate-950 px-3 py-1.5 rounded-md border border-slate-800">
                      <span className="text-slate-500">SHA-256:</span>
                      <span className="text-emerald-400 font-bold" title={prov.content_hash}>
                        {prov.content_hash.slice(0, 16)}...
                      </span>
                    </div>
                    <button
                      onClick={() => setExpandedProvId(isExpanded ? null : prov.id)}
                      className="text-emerald-400 hover:text-emerald-300 text-xs font-semibold flex items-center gap-1 transition"
                    >
                      <span>{isExpanded ? "Hide Trust & Transformations" : "Why Should I Trust This? (Audit Details)"}</span>
                      <svg
                        className={`w-3.5 h-3.5 transform transition-transform ${isExpanded ? "rotate-180" : ""}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Expanded Details Section */}
                {isExpanded && (
                  <div className="mt-6 pt-6 border-t border-slate-800 space-y-6">
                    {/* Trust Checklist Matrix */}
                    <div>
                      <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                        Deterministic Trust Checklist (7-Point Audit Verification)
                      </h5>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 text-xs">
                        {Object.entries(prov.trust_checklist || {}).map(([rule, passed]) => (
                          <div
                            key={rule}
                            className={`flex items-center gap-2 p-2.5 rounded-lg border ${
                              passed
                                ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
                                : "bg-slate-800/40 border-slate-700/60 text-slate-400"
                            }`}
                          >
                            <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              {passed ? (
                                <path
                                  fillRule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                  clipRule="evenodd"
                                />
                              ) : (
                                <path
                                  fillRule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                  clipRule="evenodd"
                                />
                              )}
                            </svg>
                            <span className="capitalize">{rule.replace(/_/g, " ")}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Metadata: Regulatory or Geospatial */}
                    {prov.regulatory_metadata && (
                      <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs space-y-2">
                        <span className="font-bold text-sky-400 uppercase tracking-wider block">
                          Statutory & Regulatory Metadata
                        </span>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-slate-300">
                          <div>
                            <span className="text-slate-500 block">Instrument:</span>
                            <span className="font-medium">{prov.regulatory_metadata.instrument_type}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Legal Citation:</span>
                            <span className="font-medium font-mono">{prov.regulatory_metadata.citation || "N/A"}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Enforcing Authority:</span>
                            <span className="font-medium">{prov.regulatory_metadata.authority || "N/A"}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Effective Date:</span>
                            <span className="font-medium">{prov.regulatory_metadata.effective_date || "Current"}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {prov.geospatial_metadata && (
                      <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs space-y-2">
                        <span className="font-bold text-indigo-400 uppercase tracking-wider block">
                          Geospatial Metadata & Projection
                        </span>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-slate-300">
                          <div>
                            <span className="text-slate-500 block">CRS / EPSG:</span>
                            <span className="font-medium font-mono">{prov.geospatial_metadata.crs} ({prov.geospatial_metadata.epsg_code})</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Geometry Type:</span>
                            <span className="font-medium">{prov.geospatial_metadata.geometry_type}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Precision:</span>
                            <span className="font-medium">{prov.geospatial_metadata.coordinate_precision}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Source Dataset:</span>
                            <span className="font-medium">{prov.geospatial_metadata.source_dataset}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Immutable Transformation History */}
                    <div>
                      <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                        Immutable Transformation History
                      </h5>
                      <div className="space-y-2">
                        {prov.transformation_history.map((step) => (
                          <div
                            key={step.step_number}
                            className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2"
                          >
                            <div className="space-y-0.5">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-emerald-400 font-bold">Step {step.step_number}:</span>
                                <span className="font-semibold text-slate-200">{step.operation}</span>
                              </div>
                              <div className="text-[11px] text-slate-400">
                                Tool: {step.tool_version} &bull; Timestamp: {new Date(step.timestamp).toLocaleString()}
                              </div>
                            </div>
                            <div className="font-mono text-[11px] text-slate-400 shrink-0">
                              Input: <span className="text-slate-300">{step.input_hash.slice(0, 10)}...</span> &rarr;{" "}
                              Output: <span className="text-emerald-400">{step.output_hash.slice(0, 10)}...</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}


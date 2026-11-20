"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  UploadCloud,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileText,
  Layers,
  History,
  RefreshCw,
  Trash2,
  ArrowRight,
  ShieldCheck,
  Scale,
  Database,
  MapPin,
  Clock,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Check,
  Activity
} from "lucide-react";
import {
  EvidenceItem,
  EvidenceRequirement,
  VerificationRun,
  AuditTrailEvent,
  Claim,
  VerificationResult,
  WorkspaceEvidenceType
} from "@/types/audit";
import {
  uploadWorkspaceEvidence,
  fetchEvidenceWorkspaceItems,
  deleteWorkspaceEvidence,
  reverifyAudit,
  fetchVerificationRuns,
  fetchAuditTrail,
  fetchEvidenceRequirements,
  ApiError
} from "@/lib/api";

interface EvidenceWorkspaceTabProps {
  auditId: string;
  claims: Claim[];
  verifications: VerificationResult[];
  onReverificationComplete: () => Promise<void>;
}

export default function EvidenceWorkspaceTab({
  auditId,
  claims,
  verifications,
  onReverificationComplete,
}: EvidenceWorkspaceTabProps) {
  const [workspaceItems, setWorkspaceItems] = useState<EvidenceItem[]>([]);
  const [verificationRuns, setVerificationRuns] = useState<VerificationRun[]>([]);
  const [auditTrailEvents, setAuditTrailEvents] = useState<AuditTrailEvent[]>([]);
  const [requirements, setRequirements] = useState<EvidenceRequirement[]>([]);

  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [reverifying, setReverifying] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);

  // Upload Form state
  const [selectedClaimId, setSelectedClaimId] = useState<string>("");
  const [selectedType, setSelectedType] = useState<WorkspaceEvidenceType>("spatial");
  const [description, setDescription] = useState<string>("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sub-navigation tab
  const [subView, setSubView] = useState<"workspace" | "requirements" | "history" | "trail">("workspace");

  const loadData = async () => {
    try {
      setLoading(true);
      const [items, runs, trail, reqs] = await Promise.all([
        fetchEvidenceWorkspaceItems(auditId),
        fetchVerificationRuns(auditId),
        fetchAuditTrail(auditId),
        fetchEvidenceRequirements(auditId),
      ]);
      setWorkspaceItems(items);
      setVerificationRuns(runs);
      setAuditTrailEvents(trail);
      setRequirements(reqs);
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Failed to load evidence workspace data." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [auditId]);

  const handleFileUpload = async (file: File) => {
    try {
      setUploading(true);
      setFeedback(null);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("evidence_type", selectedType);
      if (selectedClaimId) {
        formData.append("claim_id", selectedClaimId);
      }
      if (description) {
        formData.append("description", description);
      }

      const uploaded = await uploadWorkspaceEvidence(auditId, formData);

      if (uploaded.validationStatus === "duplicate") {
        setFeedback({
          type: "info",
          text: `Duplicate file detected (${uploaded.filename}). Using existing validated record (SHA-256: ${uploaded.fileHash.slice(0, 10)}...).`,
        });
      } else if (uploaded.validationStatus === "valid") {
        setFeedback({
          type: "success",
          text: `Evidence '${uploaded.filename}' uploaded and validated successfully (${uploaded.geometryType || uploaded.evidenceType}). Ready for re-verification.`,
        });
      } else {
        setFeedback({
          type: "error",
          text: `Evidence '${uploaded.filename}' validation failed: ${uploaded.validationMessage}`,
        });
      }

      setDescription("");
      await loadData();
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Evidence upload failed." });
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDelete = async (evidenceId: string) => {
    try {
      await deleteWorkspaceEvidence(auditId, evidenceId);
      setFeedback({ type: "info", text: "Evidence item removed from workspace." });
      await loadData();
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Failed to delete evidence item." });
    }
  };

  const handleReverify = async (targetClaimId?: string, evidenceItemId?: string) => {
    try {
      setReverifying(true);
      setFeedback(null);

      const run = await reverifyAudit(
        auditId,
        targetClaimId ? [targetClaimId] : undefined,
        evidenceItemId
      );

      const changedCount = run.findingsChanged;
      if (changedCount > 0) {
        setFeedback({
          type: "success",
          text: `Re-verification Run #${run.runNumber} complete! ${changedCount} claim finding(s) updated deterministically.`,
        });
      } else {
        setFeedback({
          type: "info",
          text: `Re-verification Run #${run.runNumber} executed. Findings evaluated; no status changes resulted from current evidence.`,
        });
      }

      await loadData();
      await onReverificationComplete();
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Re-verification failed." });
    } finally {
      setReverifying(false);
    }
  };

  const openUploadForClaim = (claimId: string, reqType: WorkspaceEvidenceType) => {
    setSelectedClaimId(claimId);
    setSelectedType(reqType);
    setSubView("workspace");
    if (fileInputRef.current) {
      fileInputRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Navigation */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-slate-950 p-4 rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-emerald-950 px-2.5 py-0.5 text-xs font-bold text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">
              Phase 6 Active
            </span>
            <h2 className="text-sm font-bold text-slate-100">
              Evidence Workspace & Deterministic Re-Verification
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Provide missing GIS boundary polygons, borehole monitoring logs, or regulatory standards to resolve evidence gaps and update findings with full auditability.
          </p>
        </div>

        {/* Global Re-Verify Action */}
        <button
          onClick={() => handleReverify()}
          disabled={reverifying || workspaceItems.length === 0}
          className={`px-4 py-2 text-xs font-bold rounded-xl flex items-center gap-2 transition-all shadow-lg ${
            workspaceItems.length === 0
              ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
              : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-950/50 hover:shadow-emerald-900/60 active:scale-95"
          }`}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${reverifying ? "animate-spin" : ""}`} />
          <span>{reverifying ? "Re-Evaluating..." : "Re-Verify Affected Claims"}</span>
        </button>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between animate-in fade-in ${
            feedback.type === "success"
              ? "bg-emerald-950/80 border-emerald-500/40 text-emerald-200"
              : feedback.type === "error"
              ? "bg-rose-950/80 border-rose-500/40 text-rose-200"
              : "bg-cyan-950/80 border-cyan-500/40 text-cyan-200"
          }`}
        >
          <div className="flex items-center gap-2.5">
            {feedback.type === "success" && <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />}
            {feedback.type === "error" && <XCircle className="h-4 w-4 text-rose-400 flex-shrink-0" />}
            {feedback.type === "info" && <AlertCircle className="h-4 w-4 text-cyan-400 flex-shrink-0" />}
            <span>{feedback.text}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            className="text-slate-400 hover:text-slate-200 p-1 rounded"
          >
            ×
          </button>
        </div>
      )}

      {/* Sub-Navigation Pills */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setSubView("workspace")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
            subView === "workspace"
              ? "bg-slate-800 text-emerald-300 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <UploadCloud className="h-3.5 w-3.5" />
          <span>Workspace & Upload ({workspaceItems.length})</span>
        </button>

        <button
          onClick={() => setSubView("requirements")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
            subView === "requirements"
              ? "bg-slate-800 text-amber-300 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Claim Evidence Requirements ({requirements.length})</span>
        </button>

        <button
          onClick={() => setSubView("history")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
            subView === "history"
              ? "bg-slate-800 text-cyan-300 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <History className="h-3.5 w-3.5" />
          <span>Re-Verification Runs ({verificationRuns.length})</span>
        </button>

        <button
          onClick={() => setSubView("trail")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
            subView === "trail"
              ? "bg-slate-800 text-purple-300 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Activity className="h-3.5 w-3.5" />
          <span>Audit Trail ({auditTrailEvents.length})</span>
        </button>
      </div>

      {/* ========================================================= */}
      {/* SUB-VIEW 1: WORKSPACE & EVIDENCE UPLOADER */}
      {/* ========================================================= */}
      {subView === "workspace" && (
        <div className="space-y-6">
          {/* Uploader Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/20 text-emerald-400">
                  <UploadCloud className="h-4 w-4" />
                </span>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Upload Missing Evidence
                </h3>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                Formats: .geojson, .kml, .kmz, .csv, .pdf, .txt (Max 25MB)
              </span>
            </div>

            {/* Target Claim & Type Selectors */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                  Target Claim
                </label>
                <select
                  value={selectedClaimId}
                  onChange={(e) => setSelectedClaimId(e.target.value)}
                  className="w-full text-xs bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="">Auto-infer from content / All gaps</option>
                  {claims.map((c) => (
                    <option key={c.id} value={c.id}>
                      Claim #{c.id.split("_").pop()}: {c.text.slice(0, 50)}...
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                  Evidence Category
                </label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value as WorkspaceEvidenceType)}
                  className="w-full text-xs bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="spatial">Spatial (GeoJSON, KML, Boundary Polygon, LineString)</option>
                  <option value="measurement">Measurement (CSV sensor logs, borehole depth)</option>
                  <option value="regulatory">Regulatory (PDF standards, statutory limit)</option>
                  <option value="supporting">Supporting Document (PDF, TXT)</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                  Provenance / Note (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. County GIS Land Cadastre 2026"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full text-xs bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Drag & Drop Zone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                isDragging
                  ? "border-emerald-500 bg-emerald-950/20"
                  : "border-slate-800 hover:border-slate-700 bg-slate-950/60 hover:bg-slate-950"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".geojson,.json,.kml,.kmz,.csv,.pdf,.txt"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
              />
              <div className="flex flex-col items-center justify-center gap-2">
                <UploadCloud className="h-8 w-8 text-emerald-400/80 animate-pulse" />
                <span className="text-xs font-semibold text-slate-200">
                  {uploading ? "Uploading & Validating Evidence..." : "Drop evidence file here or click to browse"}
                </span>
                <span className="text-[11px] text-slate-500">
                  Cryptographic SHA-256 hash computed immediately to prevent duplicates and ensure reproducible provenance.
                </span>
              </div>
            </div>
          </div>

          {/* Uploaded Evidence Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Uploaded Workspace Evidence Inventory ({workspaceItems.length})
              </h3>
              <span className="text-[11px] text-slate-400">
                Validated against semantic claim requirements
              </span>
            </div>

            {workspaceItems.length === 0 ? (
              <div className="bg-slate-950 border border-slate-800 rounded-2xl p-8 text-center">
                <Database className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                <p className="text-xs text-slate-400 font-medium">
                  No independent evidence uploaded yet.
                </p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Upload a boundary Polygon GeoJSON for Claim 02 or haul road LineString for Claim 08 to trigger targeted re-verification.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {workspaceItems.map((item) => (
                  <div
                    key={item.id}
                    className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:border-slate-700 transition-colors"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-bold text-slate-200 font-mono">
                          {item.filename}
                        </span>
                        <span className="rounded bg-slate-900 border border-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                          v{item.version}
                        </span>
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border ${
                            item.validationStatus === "valid"
                              ? "bg-emerald-950 text-emerald-400 border-emerald-500/30"
                              : item.validationStatus === "duplicate"
                              ? "bg-amber-950 text-amber-400 border-amber-500/30"
                              : "bg-rose-950 text-rose-400 border-rose-500/30"
                          }`}
                        >
                          {item.validationStatus}
                        </span>
                        {item.geometryType && (
                          <span className="rounded bg-cyan-950 border border-cyan-500/30 px-2 py-0.5 text-[10px] font-semibold text-cyan-300">
                            {item.geometryType}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-300">
                        {item.validationMessage}
                      </p>

                      <div className="flex items-center gap-4 text-[10px] text-slate-500 font-mono">
                        <span>SHA-256: {item.fileHash.slice(0, 16)}...</span>
                        <span>Size: {(item.fileSizeBytes / 1024).toFixed(1)} KB</span>
                        <span>Uploaded: {new Date(item.uploadedAt).toLocaleTimeString()}</span>
                        {item.affectedClaimIds && item.affectedClaimIds.length > 0 && (
                          <span className="text-emerald-400 font-semibold">
                            Targets: Claim {item.affectedClaimIds.map((c) => c.split("_").pop()).join(", ")}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => handleReverify(undefined, item.id)}
                        disabled={reverifying || item.validationStatus !== "valid"}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors ${
                          item.validationStatus === "valid"
                            ? "bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-500/30"
                            : "bg-slate-900 text-slate-600 border border-slate-800 cursor-not-allowed"
                        }`}
                      >
                        <RefreshCw className={`h-3 w-3 ${reverifying ? "animate-spin" : ""}`} />
                        <span>Re-Verify</span>
                      </button>

                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-900 transition-colors"
                        title="Delete evidence"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* SUB-VIEW 2: CLAIM EVIDENCE REQUIREMENTS MATRIX */}
      {/* ========================================================= */}
      {subView === "requirements" && (
        <div className="space-y-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Claim-Specific Evidence Requirements Layer
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Every environmental claim has distinct geometric, empirical, or regulatory requirements. Claims remain unverifiable until valid evidence is provided.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {requirements.map((req) => (
              <div
                key={req.claimId}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-bold font-mono text-slate-300">
                      Claim #{req.claimId.split("_").pop()}
                    </span>
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border ${
                        req.currentStatus === "verified"
                          ? "bg-emerald-950 text-emerald-400 border-emerald-500/30"
                          : req.currentStatus === "potential_inconsistency"
                          ? "bg-rose-950 text-rose-400 border-rose-500/30"
                          : "bg-slate-950 text-amber-400 border-amber-500/30"
                      }`}
                    >
                      {req.currentStatus}
                    </span>
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">
                      Priority: {req.priority}
                    </span>
                  </div>

                  {req.currentStatus === "unverifiable" && (
                    <button
                      onClick={() => openUploadForClaim(req.claimId, req.requiredEvidenceType)}
                      className="px-3 py-1 rounded-lg text-xs font-bold bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-500/40 flex items-center gap-1.5 transition-colors"
                    >
                      <UploadCloud className="h-3 w-3" />
                      <span>Upload Required Evidence</span>
                    </button>
                  )}
                </div>

                <p className="text-xs text-slate-200 font-medium">
                  &ldquo;{req.claimText}&rdquo;
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 text-[11px] bg-slate-950 p-3 rounded-xl border border-slate-800/80">
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">
                      Required Evidence
                    </span>
                    <span className="text-emerald-400 font-medium">
                      {req.requiredEvidence}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">
                      Missing Component
                    </span>
                    <span className="text-amber-400 font-medium">
                      {req.missingEvidence}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">
                      Recommended Action
                    </span>
                    <span className="text-cyan-300 font-medium">
                      {req.recommendedEvidence}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* SUB-VIEW 3: RE-VERIFICATION RUNS & BEFORE/AFTER DIFF */}
      {/* ========================================================= */}
      {subView === "history" && (
        <div className="space-y-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Immutable Re-Verification Run History
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Historical record preserving prior verification results without mutating audit history. Shows exact Before/After finding transitions.
            </p>
          </div>

          {verificationRuns.length === 0 ? (
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-8 text-center">
              <History className="h-8 w-8 text-slate-600 mx-auto mb-2" />
              <p className="text-xs text-slate-400 font-medium">
                No targeted re-verification runs executed yet.
              </p>
              <p className="text-[11px] text-slate-500 mt-1">
                Upload new spatial or empirical evidence to initiate Run #1.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {verificationRuns.map((run) => (
                <div
                  key={run.id}
                  className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl"
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-cyan-950 px-2 py-0.5 text-xs font-bold font-mono text-cyan-300 border border-cyan-500/30">
                        Run #{run.runNumber}
                      </span>
                      <span className="text-xs font-bold text-slate-200">
                        Triggered by {run.triggeredBy}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        ({new Date(run.startedAt).toLocaleString()})
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="rounded bg-slate-950 px-2.5 py-0.5 text-xs font-bold font-mono text-emerald-400 border border-slate-800">
                        {run.findingsChanged} Finding(s) Updated
                      </span>
                    </div>
                  </div>

                  {/* Diffs List */}
                  <div className="space-y-3">
                    {run.diffs.map((diff) => (
                      <div
                        key={diff.claimId}
                        className="bg-slate-950 border border-slate-800/80 rounded-xl p-3.5 space-y-2.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold font-mono text-slate-300">
                            Claim #{diff.claimId.split("_").pop()}
                          </span>

                          <div className="flex items-center gap-2 font-mono text-xs">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                diff.previousStatus === "verified"
                                  ? "bg-emerald-950 text-emerald-400"
                                  : "bg-slate-900 text-amber-400"
                              }`}
                            >
                              {diff.previousStatus}
                            </span>
                            <ArrowRight className="h-3 w-3 text-slate-500" />
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                diff.newStatus === "verified"
                                  ? "bg-emerald-950 text-emerald-400 border border-emerald-500/30"
                                  : "bg-slate-900 text-amber-400"
                              }`}
                            >
                              {diff.newStatus}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-slate-300 font-medium">
                          &ldquo;{diff.claimText}&rdquo;
                        </p>

                        <div className="text-xs space-y-1 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                          <div className="flex items-start gap-2">
                            <span className="text-slate-500 text-[10px] font-bold uppercase min-w-[70px]">
                              Previous:
                            </span>
                            <span className="text-slate-400">{diff.previousExplanation}</span>
                          </div>
                          <div className="flex items-start gap-2">
                            <span className="text-emerald-400 text-[10px] font-bold uppercase min-w-[70px]">
                              Updated:
                            </span>
                            <span className="text-slate-200">{diff.newExplanation}</span>
                          </div>
                        </div>

                        {diff.evidenceAddedFilenames && diff.evidenceAddedFilenames.length > 0 && (
                          <div className="text-[10px] text-slate-500 font-mono">
                            Evidence Applied: {diff.evidenceAddedFilenames.join(", ")}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ========================================================= */}
      {/* SUB-VIEW 4: AUDIT TRAIL TIMELINE */}
      {/* ========================================================= */}
      {subView === "trail" && (
        <div className="space-y-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Audit Lifecycle Event Trail
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Complete chronological audit trail recording document ingestion, evidence uploads, validation steps, and re-verification transitions.
            </p>
          </div>

          <div className="space-y-2">
            {auditTrailEvents.map((evt) => (
              <div
                key={evt.id}
                className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 flex items-center justify-between gap-4 text-xs font-mono"
              >
                <div className="flex items-center gap-3">
                  <span className="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-400">
                    {evt.actor}
                  </span>
                  <span className="font-semibold text-slate-200 font-sans">
                    {evt.action}
                  </span>
                  {evt.affectedObject && (
                    <span className="text-slate-500 text-[11px]">
                      [{evt.affectedObject}]
                    </span>
                  )}
                  {evt.previousState && evt.newState && (
                    <span className="text-emerald-400 text-[11px]">
                      ({evt.previousState} → {evt.newState})
                    </span>
                  )}
                </div>

                <span className="text-[10px] text-slate-500">
                  {new Date(evt.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


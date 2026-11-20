"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  FileText,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  AlertCircle,
  FileSearch,
  Sparkles,
  Loader2,
  Filter,
  Eye,
  X,
  ExternalLink,
  Layers,
  Scale,
  MapPin,
  Clock,
  AlertTriangle,
  Database,
  Compass,
  Link as LinkIcon,
  HelpCircle,
  Check,
  Calculator,
  Download,
  BarChart3,
  ListChecks,
  FileSpreadsheet,
  UploadCloud,
  Lock
} from "lucide-react";
import EvidenceWorkspaceTab from "@/components/EvidenceWorkspaceTab";
import AuditIntelligenceTab from "@/components/AuditIntelligenceTab";
import { ProvenanceTab } from "@/components/ProvenanceTab";
import { SecurityIntegrityPanel } from "@/components/SecurityIntegrityPanel";
import RadialRiskScore from "@/components/RadialRiskScore";
import {
  getAuditDetail,
  extractAuditClaims,
  seedBenchmarkClaims,
  getAuditClaims,
  getAuditLocation,
  retrieveClaimEvidence,
  batchRetrieveEvidence,
  getAuditEvidence,
  batchVerifyAudit,
  verifyClaim,
  getAuditVerifications,
  getAuditSummary,
  getAuditReport,
  getAuditReportDownloadUrl,
  getAuditEvidenceGaps,
  getCrossClaimConsistency,
  ApiError
} from "@/lib/api";
import {
  AuditDetail,
  Claim,
  Evidence,
  ProjectLocation,
  EvidenceQuality,
  VerificationResult,
  AuditRiskSummary,
  EvidenceGap,
  CrossClaimConsistency,
  FindingPriority
} from "@/types/audit";

interface PageProps {
  params: Promise<{ id: string }>;
}

function renderHighlightedSnippet(fullText: string, searchSnippet: string | null) {
  if (!searchSnippet || !searchSnippet.trim()) {
    return fullText;
  }
  const cleanSnippet = searchSnippet.trim();
  const lowerText = fullText.toLowerCase();
  const lowerSnippet = cleanSnippet.toLowerCase();

  const exactIdx = lowerText.indexOf(lowerSnippet);
  if (exactIdx !== -1) {
    const before = fullText.slice(0, exactIdx);
    const match = fullText.slice(exactIdx, exactIdx + cleanSnippet.length);
    const after = fullText.slice(exactIdx + cleanSnippet.length);
    return (
      <>
        {before}
        <mark className="bg-amber-400/30 text-amber-200 border-b-2 border-amber-400 px-1 py-0.5 rounded font-bold shadow-sm">
          {match}
        </mark>
        {after}
      </>
    );
  }

  // Fallback: match by first 20 chars
  const words = cleanSnippet.split(/\s+/).filter((w) => w.length > 3);
  if (words.length > 0) {
    const firstWord = words[0].toLowerCase();
    const wordIdx = lowerText.indexOf(firstWord);
    if (wordIdx !== -1) {
      const approxLen = Math.min(cleanSnippet.length, fullText.length - wordIdx);
      const before = fullText.slice(0, wordIdx);
      const match = fullText.slice(wordIdx, wordIdx + approxLen);
      const after = fullText.slice(wordIdx + approxLen);
      return (
        <>
          {before}
          <mark className="bg-amber-400/30 text-amber-200 border-b-2 border-amber-400 px-1 py-0.5 rounded font-bold shadow-sm">
            {match}
          </mark>
          {after}
        </>
      );
    }
  }

  return fullText;
}

export default function AuditWorkspacePage({ params }: PageProps) {
  const resolvedParams = use(params);
  const auditId = resolvedParams.id;

  const [audit, setAudit] = useState<AuditDetail | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [projectLocation, setProjectLocation] = useState<ProjectLocation | null>(null);

  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [seedingBenchmark, setSeedingBenchmark] = useState(false);
  const [retrievingEvidence, setRetrievingEvidence] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);
  const [verificationError, setVerificationError] = useState<string | null>(null);
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [pipelineStepText, setPipelineStepText] = useState("");


  // Phase 4 Verifications state
  const [verifications, setVerifications] = useState<VerificationResult[]>([]);

  // Phase 5 Audit Intelligence state
  const [summary, setSummary] = useState<AuditRiskSummary | null>(null);
  const [evidenceGaps, setEvidenceGaps] = useState<EvidenceGap[]>([]);
  const [crossClaimResults, setCrossClaimResults] = useState<CrossClaimConsistency[]>([]);
  const [selectedPriorityFilter, setSelectedPriorityFilter] = useState<string>("All");

  // Active view tab: "claims" | "evidence" | "gaps" | "consistency" | "chain" | "workspace" | "intelligence" | "provenance" | "security"
  const [activeTab, setActiveTab] = useState<"claims" | "evidence" | "gaps" | "consistency" | "chain" | "workspace" | "intelligence" | "provenance" | "security">("claims");

  // Document viewer state
  const [selectedPageIndex, setSelectedPageIndex] = useState(0);
  const [highlightedText, setHighlightedText] = useState<string | null>(null);

  // Filter states
  const [selectedFilter, setSelectedFilter] = useState<string>("All");
  const [selectedEvidenceQuality, setSelectedEvidenceQuality] = useState<string>("All");

  // Claim Detail Modal
  const [activeClaimDetail, setActiveClaimDetail] = useState<Claim | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const auditData = await getAuditDetail(auditId);
        setAudit(auditData);

        // Load claims if extracted
        const claimsData = await getAuditClaims(auditId);
        setClaims(claimsData);

        // Load independent evidence
        const evData = await getAuditEvidence(auditId);
        setEvidenceList(evData);

        // Load project location
        const locData = await getAuditLocation(auditId);
        setProjectLocation(locData);

        // Load Phase 4 & 5 verifications
        const verifData = await getAuditVerifications(auditId);
        setVerifications(verifData);

        if (verifData.length > 0) {
          try {
            const sum = await getAuditSummary(auditId);
            setSummary(sum);
            setEvidenceGaps(sum.evidenceGaps || []);
            setCrossClaimResults(sum.crossClaimConsistency || []);
          } catch {
            // Handled gracefully if intelligence endpoint is not yet run
          }
        }
      } catch (err: any) {
        setError(err.message || "Failed to load audit workspace.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [auditId]);

  const handleExtractClaims = async () => {
    if (extracting) return;
    setExtracting(true);
    setExtractionError(null);

    try {
      const response = await extractAuditClaims(auditId);
      setClaims(response.claims);
      // Reload audit to update pipeline stage
      const updatedAudit = await getAuditDetail(auditId);
      setAudit(updatedAudit);
    } catch (err: any) {
      setExtractionError(
        err.message ||
          "Claim extraction could not be completed. Your document is still available. Please try the analysis again."
      );
    } finally {
      setExtracting(false);
    }
  };

  const handleRunBenchmark = async (benchmarkType: string = "canonical_apex_quartz") => {
    if (seedingBenchmark) return;
    setSeedingBenchmark(true);
    setExtractionError(null);

    try {
      const response = await seedBenchmarkClaims(auditId, benchmarkType);
      setClaims(response.claims);
      const updatedAudit = await getAuditDetail(auditId);
      setAudit(updatedAudit);
      const evData = await getAuditEvidence(auditId);
      setEvidenceList(evData);
    } catch (err: any) {
      setExtractionError(err.message || "Could not load benchmark claims.");
    } finally {
      setSeedingBenchmark(false);
    }
  };

  const handleRunFullPipeline = async () => {
    if (runningPipeline) return;
    setRunningPipeline(true);
    setExtractionError(null);
    setEvidenceError(null);
    setVerificationError(null);

    try {
      // Step 1: Claim extraction if not done
      let currentClaims = claims;
      if (currentClaims.length === 0) {
        setPipelineStepText("Extracting Claims");
        const claimRes = await extractAuditClaims(auditId);
        currentClaims = claimRes.claims;
        setClaims(currentClaims);
      }


      // Step 2: Evidence retrieval if not done
      let currentEvidence = evidenceList;
      if (currentEvidence.length === 0) {
        setPipelineStepText("Retrieving Independent Evidence");
        const evRes = await batchRetrieveEvidence(auditId);
        currentEvidence = evRes.evidence;
        setEvidenceList(currentEvidence);
      }

      // Step 3: Deterministic verification
      setPipelineStepText("Executing Deterministic Verifier");
      const verifRes = await batchVerifyAudit(auditId);
      setVerifications(verifRes.results);
      const updatedClaims = await getAuditClaims(auditId);
      setClaims(updatedClaims);

      // Step 4: Executive Intelligence Summary
      setPipelineStepText("Compiling Executive Intelligence");
      try {
        const sum = await getAuditSummary(auditId);
        setSummary(sum);
        setEvidenceGaps(sum.evidenceGaps || []);
        setCrossClaimResults(sum.crossClaimConsistency || []);
      } catch (sumErr) {
        console.error("Could not fetch intelligence summary:", sumErr);
      }

      const updatedAudit = await getAuditDetail(auditId);
      setAudit(updatedAudit);
      setActiveTab("claims");
    } catch (err: any) {
      setVerificationError(err.message || "Failed running complete audit pipeline.");
    } finally {
      setRunningPipeline(false);
      setPipelineStepText("");
    }
  };

  const handleBatchRetrieveEvidence = async () => {
    if (retrievingEvidence) return;
    setRetrievingEvidence(true);
    setEvidenceError(null);

    try {
      const res = await batchRetrieveEvidence(auditId);
      setEvidenceList(res.evidence);
      const updatedAudit = await getAuditDetail(auditId);
      setAudit(updatedAudit);
      setActiveTab("evidence");
    } catch (err: any) {
      setEvidenceError(
        err.message || "Independent evidence retrieval failed. Please try again."
      );
    } finally {
      setRetrievingEvidence(false);
    }
  };

  const handleRetrieveSingleClaimEvidence = async (claimId: string) => {
    try {
      const res = await retrieveClaimEvidence(auditId, claimId);
      // Update evidence list with newly retrieved items
      setEvidenceList((prev) => {
        const remaining = prev.filter((e) => e.claimId !== claimId);
        return [...remaining, ...res.evidence];
      });
      const updatedAudit = await getAuditDetail(auditId);
      setAudit(updatedAudit);
    } catch (err: any) {
      setEvidenceError(err.message || "Failed to retrieve evidence for this claim.");
    }
  };

  const handleBatchVerify = async () => {
    if (verifying) return;
    setVerifying(true);
    setVerificationError(null);

    try {
      const res = await batchVerifyAudit(auditId);
      setVerifications(res.results);
      const updatedClaims = await getAuditClaims(auditId);
      setClaims(updatedClaims);
      const updatedAudit = await getAuditDetail(auditId);
      setAudit(updatedAudit);

      try {
        const sum = await getAuditSummary(auditId);
        setSummary(sum);
        setEvidenceGaps(sum.evidenceGaps || []);
        setCrossClaimResults(sum.crossClaimConsistency || []);
      } catch (sumErr) {
        console.error("Could not fetch audit intelligence summary:", sumErr);
      }
    } catch (err: any) {
      setVerificationError(err.message || "Batch verification failed. Please try again.");
    } finally {
      setVerifying(false);
    }
  };

  const handleVerifySingleClaim = async (claimId: string) => {
    try {
      const res = await verifyClaim(auditId, claimId);
      setVerifications((prev) => {
        const remaining = prev.filter((v) => v.claimId !== claimId);
        return [...remaining, res];
      });
      const updatedClaims = await getAuditClaims(auditId);
      setClaims(updatedClaims);
    } catch (err: any) {
      setVerificationError(err.message || "Single claim verification failed.");
    }
  };

  const handleViewSource = (claim: Claim) => {
    const targetPageIdx = Math.max(0, claim.page - 1);
    setSelectedPageIndex(targetPageIdx);
    setHighlightedText(claim.sourceText);
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center space-y-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent mx-auto"></div>
          <p className="text-xs text-slate-400 font-medium">Loading Document Workspace...</p>
        </div>
      </div>
    );
  }

  if (error || !audit) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-rose-950/60 border border-rose-500/30 flex items-center justify-center text-rose-400 mx-auto">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h1 className="text-xl font-bold text-slate-100">Audit Not Found</h1>
        <p className="text-xs text-slate-400 leading-relaxed">{error}</p>
        <div className="pt-2">
          <Link
            href="/audit"
            className="inline-flex items-center gap-2 rounded-xl bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Return to Upload</span>
          </Link>
        </div>
      </div>
    );
  }

  const currentPage = audit.pages[selectedPageIndex] || null;

  // Filter claims
  const filteredClaims = claims.filter((claim) => {
    // Priority filter
    if (selectedPriorityFilter !== "All") {
      const v = verifications.find((ver) => ver.claimId === claim.id);
      const priority = v?.priority || "MEDIUM";
      if (priority !== selectedPriorityFilter) return false;
    }

    if (selectedFilter === "All") return true;
    if (selectedFilter === "High") return claim.importance === "high";
    if (selectedFilter === "Medium") return claim.importance === "medium";
    if (selectedFilter === "Low") return claim.importance === "low";
    if (selectedFilter === "Geographic") return claim.verificationType === "geographic";
    if (selectedFilter === "Numeric") return claim.verificationType === "numeric";
    if (selectedFilter === "Regulatory") return claim.verificationType === "regulatory";
    return true;
  });

  // Filter evidence
  const filteredEvidence = evidenceList.filter((e) => {
    if (selectedEvidenceQuality === "All") return true;
    if (selectedEvidenceQuality === "Strong") return e.quality === "strong";
    if (selectedEvidenceQuality === "Moderate") return e.quality === "moderate";
    if (selectedEvidenceQuality === "Limited") return e.quality === "limited";
    if (selectedEvidenceQuality === "Geographic") return e.type === "geographic";
    if (selectedEvidenceQuality === "Regulatory") return e.type === "regulatory";
    return true;
  });

  const filterOptions = [
    { label: "All", count: claims.length },
    { label: "High", count: claims.filter((c) => c.importance === "high").length },
    { label: "Medium", count: claims.filter((c) => c.importance === "medium").length },
    { label: "Low", count: claims.filter((c) => c.importance === "low").length },
    { label: "Geographic", count: claims.filter((c) => c.verificationType === "geographic").length },
    { label: "Numeric", count: claims.filter((c) => c.verificationType === "numeric").length },
    { label: "Regulatory", count: claims.filter((c) => c.verificationType === "regulatory").length },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
      {/* Top Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/audit"
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-colors"
            title="Upload another document"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-100 truncate max-w-md sm:max-w-xl">
                {audit.title || audit.filename}
              </h1>
              <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-300">
                {audit.pageCount} Pages
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-mono mt-0.5">
              ID: {audit.id} · Uploaded: {new Date(audit.createdAt).toLocaleDateString()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {verifications.length > 0 ? (
            <a
              href={getAuditReportDownloadUrl(auditId)}
              download={`GroundCheck_Audit_Report_${auditId}.md`}
              className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white px-3.5 py-1.5 text-xs font-bold transition-all shadow-sm"
              title="Download full 14-section formal environmental audit report in Markdown"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export Audit Report (.md)</span>
            </a>
          ) : (
            <button
              onClick={handleRunFullPipeline}
              disabled={runningPipeline || extracting || retrievingEvidence || verifying}
              className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white px-3.5 py-1.5 text-xs font-bold transition-all shadow-sm disabled:opacity-50"
            >
              {runningPipeline ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>{pipelineStepText || "Auditing..."}</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Run Complete Audit</span>
                </>
              )}
            </button>
          )}

          {claims.length > 0 && evidenceList.length === 0 && !runningPipeline && (
            <button
              onClick={handleBatchRetrieveEvidence}
              disabled={retrievingEvidence}
              className="inline-flex items-center gap-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white px-3.5 py-1.5 text-xs font-bold transition-all shadow-sm disabled:opacity-50"
            >
              {retrievingEvidence ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Compass className="h-3.5 w-3.5" />
              )}
              <span>Retrieve Independent Evidence</span>
            </button>
          )}

          <Link
            href="/audit"
            className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors"
          >
            <FileSearch className="h-3.5 w-3.5" />
            <span>Upload Another</span>
          </Link>
        </div>
      </div>

      {/* Benchmark Mode Warning Banner (Strict Provenance Integrity) */}
      {audit.isBenchmark && (
        <div className="rounded-xl border border-amber-500/40 bg-amber-950/40 p-4 flex items-start gap-3.5 shadow-sm">
          <div className="rounded-lg bg-amber-500/20 p-2 text-amber-400 border border-amber-500/30 shrink-0">
            <Sparkles className="h-5 w-5" />
          </div>
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded bg-amber-500 text-slate-950 font-mono text-[11px] font-black uppercase px-2 py-0.5 tracking-wider">
                DEMO / BENCHMARK MODE
              </span>
              <span className="text-xs font-semibold text-amber-300">
                {audit.benchmarkType === "colorado_2024"
                  ? "Colorado 2024 Environmental Benchmark (39.75470° N, 105.22110° W / PM10 / Clear Creek)"
                  : "Canonical Apex Quartz Quarry Benchmark (40.7128° N, 74.0060° W / 8 Test Claims)"}
              </span>
            </div>
            <p className="text-xs text-amber-200/90 leading-relaxed">
              <strong>Provenance Notice:</strong> The claims and independent evidence displayed in this audit are seeded benchmark test data designed for deterministic verification engine auditing, not real AI document extraction. No fabricated claims are presented as real extractions.
            </p>
          </div>
        </div>
      )}

      {/* Project Location Banner (Section 6 & 7) */}
      {projectLocation && projectLocation.confidence !== "unavailable" && (
        <div className="rounded-xl border border-slate-800 bg-slate-950/80 px-4 py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-emerald-950/80 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <MapPin className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-200">Project Location:</span>
                <span className="text-slate-300 font-mono">{projectLocation.description}</span>
                {projectLocation.coordinates && (
                  <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/20">
                    {projectLocation.coordinates[0].toFixed(5)}° N, {Math.abs(projectLocation.coordinates[1]).toFixed(5)}° W
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Source: <span className="capitalize">{projectLocation.source.replace("_", " ")}</span> · Confidence:{" "}
                <span className={projectLocation.confidence === "high" ? "text-emerald-400" : "text-amber-400"}>
                  {projectLocation.confidence === "high" ? "High (Verified)" : "Requires Human Confirmation"}
                </span>
              </p>
            </div>
          </div>
          <span className="text-[10px] text-slate-400 font-mono bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
            OpenStreetMap Baseline Ready
          </span>
        </div>
      )}

      {/* Phase 5: Executive Risk Summary & Intelligence Profile */}
      {summary && (
        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-sm space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold block">
                Evidence-Backed Audit Intelligence
              </span>
              <h2 className="text-base font-bold text-slate-100 mt-0.5">
                Executive Risk Profile &amp; Integrity Analysis
              </h2>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400">Composite Risk Score:</span>
                <span className="font-mono font-bold text-sm text-slate-100">{summary.riskScore} / 100</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  summary.overallRiskLevel === "CRITICAL"
                    ? "bg-rose-950 text-rose-300 border border-rose-800"
                    : summary.overallRiskLevel === "HIGH"
                    ? "bg-orange-950 text-orange-300 border border-orange-800"
                    : summary.overallRiskLevel === "MEDIUM"
                    ? "bg-amber-950 text-amber-300 border border-amber-800"
                    : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                }`}>
                  {summary.overallRiskLevel} RISK
                </span>
              </div>

              <a
                href={getAuditReportDownloadUrl(auditId)}
                download={`GroundCheck_Audit_Report_${auditId}.md`}
                className="inline-flex items-center gap-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 text-xs font-semibold border border-slate-700 transition-colors"
              >
                <Download className="h-3.5 w-3.5 text-emerald-400" />
                <span>Export Report (.md)</span>
              </a>
            </div>
          </div>

          {/* Metric KPI Cards with Radial Deterministic Risk Score */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-center bg-slate-900/30 p-4 rounded-xl border border-slate-800/80">
            <div className="md:col-span-5 flex justify-center py-2">
              <RadialRiskScore
                score={summary.riskScore}
                verifiedCount={summary.verifiedCount}
                unverifiableCount={summary.unverifiableCount}
                inconsistentCount={summary.inconsistencyCount}
              />
            </div>
            <div className="md:col-span-7 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">Total Claims</span>
                <span className="text-xl font-bold font-mono text-slate-100 mt-1 block">{summary.totalClaims}</span>
              </div>
              <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/20 text-center">
                <span className="text-[10px] uppercase font-semibold text-emerald-400 block">Verified True</span>
                <span className="text-xl font-bold font-mono text-emerald-300 mt-1 block">{summary.verifiedCount}</span>
              </div>
              <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/20 text-center">
                <span className="text-[10px] uppercase font-semibold text-amber-400 block">Inconsistencies</span>
                <span className="text-xl font-bold font-mono text-amber-300 mt-1 block">{summary.inconsistencyCount}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">Unverifiable</span>
                <span className="text-xl font-bold font-mono text-slate-300 mt-1 block">{summary.unverifiableCount}</span>
              </div>
              <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/20 text-center col-span-2 sm:col-span-4">
                <div className="flex items-center justify-between px-2">
                  <span className="text-[10px] uppercase font-semibold text-cyan-400">Identified Evidence Gaps</span>
                  <span className="text-base font-bold font-mono text-cyan-300">{summary.evidenceGaps.length} Actionable Inquiries</span>
                </div>
              </div>
            </div>
          </div>

          {/* Priority Distribution Horizontal Bar */}
          <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-900 space-y-2 text-xs">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="font-semibold uppercase tracking-wider">Deterministic Finding Priorities</span>
              <span className="font-mono">
                Critical: {summary.priorityDistribution.CRITICAL || 0} · High: {summary.priorityDistribution.HIGH || 0} · Med: {summary.priorityDistribution.MEDIUM || 0} · Low: {summary.priorityDistribution.LOW || 0} · Info: {summary.priorityDistribution.INFORMATIONAL || 0}
              </span>
            </div>
            <div className="flex h-2.5 w-full rounded-full overflow-hidden bg-slate-800">
              {summary.totalClaims > 0 && (
                <>
                  <div style={{ width: `${((summary.priorityDistribution.CRITICAL || 0) / summary.totalClaims) * 100}%` }} className="bg-rose-500" title="Critical" />
                  <div style={{ width: `${((summary.priorityDistribution.HIGH || 0) / summary.totalClaims) * 100}%` }} className="bg-orange-500" title="High" />
                  <div style={{ width: `${((summary.priorityDistribution.MEDIUM || 0) / summary.totalClaims) * 100}%` }} className="bg-amber-400" title="Medium" />
                  <div style={{ width: `${((summary.priorityDistribution.LOW || 0) / summary.totalClaims) * 100}%` }} className="bg-emerald-500" title="Low" />
                  <div style={{ width: `${((summary.priorityDistribution.INFORMATIONAL || 0) / summary.totalClaims) * 100}%` }} className="bg-slate-500" title="Informational" />
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Split-Screen Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[640px]">
        {/* Left Column: DOCUMENT VIEWER */}
        <div className="lg:col-span-5 flex flex-col rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-sm">
          {/* Header & Pagination */}
          <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/80 px-4 py-3">
            <div className="flex items-center gap-2 text-xs text-slate-300 font-medium">
              <FileText className="h-4 w-4 text-emerald-400" />
              <span>Document Text Preview</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setSelectedPageIndex((prev) => Math.max(0, prev - 1));
                  setHighlightedText(null);
                }}
                disabled={selectedPageIndex === 0}
                className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-40"
                title="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              <span className="text-xs font-mono text-slate-300 px-1">
                Page {selectedPageIndex + 1} of {audit.pageCount}
              </span>

              <button
                onClick={() => {
                  setSelectedPageIndex((prev) => Math.min(audit.pageCount - 1, prev + 1));
                  setHighlightedText(null);
                }}
                disabled={selectedPageIndex >= audit.pageCount - 1}
                className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-40"
                title="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Quick Page Picker Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto border-b border-slate-800/80 bg-slate-950 px-4 py-2 text-xs">
            {audit.pages.map((p, idx) => (
              <button
                key={p.pageNumber}
                onClick={() => {
                  setSelectedPageIndex(idx);
                  setHighlightedText(null);
                }}
                className={`rounded px-2.5 py-1 font-mono transition-colors ${
                  selectedPageIndex === idx
                    ? "bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/40"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                }`}
              >
                P{p.pageNumber}
              </button>
            ))}
          </div>

          {/* Highlight indicator banner */}
          {highlightedText && (
            <div className="bg-amber-950/50 border-b border-amber-500/30 px-4 py-1.5 text-[11px] text-amber-200 flex items-center justify-between">
              <span className="truncate max-w-[280px]">Highlighting source quotation from selected claim</span>
              <button
                onClick={() => setHighlightedText(null)}
                className="text-amber-400 hover:text-amber-200 font-bold ml-2"
              >
                Clear
              </button>
            </div>
          )}

          {/* Extracted Page Text Container */}
          <div className="flex-1 p-5 overflow-y-auto max-h-[580px] bg-slate-950 text-slate-200 font-mono text-xs leading-relaxed">
            {currentPage ? (
              <div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 border-b border-slate-900 pb-2 mb-3">
                  <span>PAGE {currentPage.pageNumber}</span>
                  <span>{currentPage.wordCount} words extracted</span>
                </div>
                {currentPage.text ? (
                  <div className="whitespace-pre-wrap font-mono text-slate-300 select-text leading-relaxed">
                    {renderHighlightedSnippet(currentPage.text, highlightedText)}
                  </div>
                ) : (
                  <p className="text-slate-500 italic py-8 text-center">
                    [Blank page or image-only page without embedded text layer]
                  </p>
                )}
              </div>
            ) : (
              <p className="text-slate-500 italic py-8 text-center">No page text available.</p>
            )}
          </div>
        </div>

        {/* Right Column: CLAIMS & INDEPENDENT EVIDENCE WORKSPACE */}
        <div className="lg:col-span-7 flex flex-col space-y-5">
          {/* Stepper Status */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Processing Pipeline
              </h2>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/20">
                {evidenceList.length > 0 ? "Phase 3 Ready" : claims.length > 0 ? "Phase 2 Completed" : "Phase 1 Ready"}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
              {audit.stages.map((stage) => {
                const isCompleted = stage.status === "completed";
                const isProcessing = stage.status === "processing";

                return (
                  <div key={stage.id} className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-900/40 border border-slate-900">
                    <div className="mt-0.5 shrink-0">
                      {isCompleted ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : isProcessing ? (
                        <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border border-slate-700 flex items-center justify-center text-[10px] text-slate-500">
                          ○
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className={`font-semibold truncate ${isCompleted ? "text-slate-200" : "text-slate-400"}`}>
                          {stage.name}
                        </p>
                        {isCompleted && <span className="text-[9px] text-emerald-400 font-mono shrink-0 ml-1">DONE</span>}
                      </div>
                      <p className="text-[10px] mt-0.5 text-slate-500 italic truncate">
                        {stage.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Evidence Error Banner */}
          {evidenceError && (
            <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-4 text-xs text-rose-300 space-y-2">
              <div className="flex items-center gap-2 font-semibold text-rose-200">
                <AlertCircle className="h-4 w-4 text-rose-400" />
                <span>Evidence Retrieval Notice</span>
              </div>
              <p className="leading-relaxed">{evidenceError}</p>
            </div>
          )}

          {/* Action Card when Claims have not yet been extracted */}
          {claims.length === 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6 shadow-sm space-y-4 text-center">
              <div className="w-12 h-12 rounded-xl bg-emerald-950/80 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-slate-100">
                  Document Ingestion Complete · Ready for Audit
                </h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                  {audit.pageCount} pages parsed successfully. Extract factual, testable environmental claims to begin deterministic verification against independent open data.
                </p>
              </div>

              {extractionError && (
                <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-4 text-xs text-rose-300 text-left space-y-3">
                  <div className="flex items-center gap-2 font-semibold text-rose-200">
                    <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
                    <span>Real Extraction Unavailable</span>
                  </div>
                  <p className="mt-1 font-mono text-[11px] text-rose-200/90">{extractionError}</p>

                  <div className="pt-2 border-t border-rose-500/20 flex flex-wrap items-center justify-between gap-3">
                    <span className="text-[11px] text-slate-300">
                      You can evaluate GroundCheck using official seeded benchmark claims:
                    </span>
                    <button
                      onClick={() => handleRunBenchmark("canonical_apex_quartz")}
                      disabled={seedingBenchmark || runningPipeline}
                      className="inline-flex items-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 px-3.5 py-1.5 text-xs font-bold transition-all disabled:opacity-50"
                    >
                      {seedingBenchmark ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Sparkles className="h-3.5 w-3.5" />
                      )}
                      <span>Run Apex Quartz Benchmark (Demo Mode)</span>
                    </button>
                  </div>
                </div>
              )}

              <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
                <button
                  onClick={handleRunFullPipeline}
                  disabled={runningPipeline || extracting || seedingBenchmark}
                  className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-5 py-2.5 text-xs font-bold shadow-md transition-all disabled:opacity-50"
                >
                  {runningPipeline ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Running End-to-End Audit ({pipelineStepText})...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="h-4 w-4" />
                      <span>Run Complete Audit Pipeline</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleExtractClaims}
                  disabled={extracting || runningPipeline || seedingBenchmark}
                  className="inline-flex items-center gap-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-4 py-2.5 text-xs font-semibold transition-all disabled:opacity-50"
                >
                  {extracting ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                  )}
                  <span>Step 1: Extract Claims (Gemini)</span>
                </button>

                <button
                  onClick={() => handleRunBenchmark("canonical_apex_quartz")}
                  disabled={seedingBenchmark || runningPipeline || extracting}
                  className="inline-flex items-center gap-2 rounded-xl bg-purple-950/60 hover:bg-purple-900/60 text-purple-200 border border-purple-500/40 px-4 py-2.5 text-xs font-semibold transition-all disabled:opacity-50"
                >
                  {seedingBenchmark ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                  )}
                  <span>Load Benchmark Mode</span>
                </button>
              </div>
            </div>
          )}

          {/* Action Card when Claims extracted but Evidence not retrieved */}
          {claims.length > 0 && evidenceList.length === 0 && (
            <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/30 p-4 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <div className="h-7 w-7 rounded-lg bg-cyan-950 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                  <Compass className="h-4 w-4" />
                </div>
                <div>
                  <p className="font-semibold text-cyan-200">
                    {claims.length} Environmental Claims Extracted · Ready for Evidence Retrieval
                  </p>
                  <p className="text-[11px] text-cyan-300/80">
                    Retrieve independent empirical benchmarks from OpenStreetMap, EPA NAAQS, USFWS IPaC, and Colorado DWR.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRunFullPipeline}
                  disabled={runningPipeline}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 text-xs font-bold transition-all disabled:opacity-50"
                >
                  {runningPipeline ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5" />}
                  <span>Run Full Audit</span>
                </button>
                <button
                  onClick={handleBatchRetrieveEvidence}
                  disabled={retrievingEvidence}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1.5 text-xs font-semibold transition-all disabled:opacity-50"
                >
                  {retrievingEvidence ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Compass className="h-3.5 w-3.5" />}
                  <span>Retrieve Evidence</span>
                </button>
              </div>
            </div>
          )}

          {/* Action Card when Evidence retrieved but Verifications pending */}
          {evidenceList.length > 0 && verifications.length === 0 && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/30 p-4 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <div className="h-7 w-7 rounded-lg bg-emerald-950 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                  <Calculator className="h-4 w-4" />
                </div>
                <div>
                  <p className="font-semibold text-emerald-200">
                    {evidenceList.length} Independent Evidence Items Found · Ready for Verification
                  </p>
                  <p className="text-[11px] text-emerald-300/80">
                    Execute deterministic calculations, semantic compatibility, arithmetic checks, and evidence-gap analysis.
                  </p>
                </div>
              </div>
              <button
                onClick={handleBatchVerify}
                disabled={verifying}
                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white px-3.5 py-1.5 text-xs font-bold transition-all disabled:opacity-50"
              >
                {verifying ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Calculator className="h-3.5 w-3.5" />}
                <span>Verify Claims Deterministically</span>
              </button>
            </div>
          )}

          {/* Navigation Tabs (Claims / Evidence / Evidence Chain) */}
          {claims.length > 0 && (
            <div className="flex items-center justify-between border-b border-slate-800 pb-1">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab("claims")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                    activeTab === "claims"
                      ? "bg-slate-800 text-slate-100 border border-slate-700"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span>Report Claims ({claims.length})</span>
                </button>

                <button
                  onClick={() => setActiveTab("evidence")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                    activeTab === "evidence"
                      ? "bg-cyan-950 text-cyan-300 border border-cyan-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Database className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Evidence ({evidenceList.length})</span>
                </button>

                <button
                  onClick={() => setActiveTab("gaps")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                    activeTab === "gaps"
                      ? "bg-amber-950 text-amber-300 border border-amber-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <AlertCircle className="h-3.5 w-3.5 text-amber-400" />
                  <span>Evidence Gaps ({evidenceGaps.length})</span>
                </button>

                <button
                  onClick={() => setActiveTab("consistency")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                    activeTab === "consistency"
                      ? "bg-purple-950 text-purple-300 border border-purple-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <ListChecks className="h-3.5 w-3.5 text-purple-400" />
                  <span>Cross-Claim ({crossClaimResults.length})</span>
                </button>

                <button
                  onClick={() => setActiveTab("chain")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                    activeTab === "chain"
                      ? "bg-emerald-950 text-emerald-300 border border-emerald-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <LinkIcon className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Chain UI</span>
                </button>

                <button
                  onClick={() => setActiveTab("workspace")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                    activeTab === "workspace"
                      ? "bg-emerald-950 text-emerald-300 border border-emerald-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <UploadCloud className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Evidence Workspace</span>
                </button>

                <button
                  onClick={() => setActiveTab("intelligence")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                    activeTab === "intelligence"
                      ? "bg-cyan-950 text-cyan-300 border border-cyan-500/50 shadow-md shadow-cyan-950"
                      : "text-cyan-400 hover:text-cyan-200"
                  }`}
                >
                  <Compass className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Audit Intelligence</span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">Phase 7</span>
                </button>

                <button
                  onClick={() => setActiveTab("provenance")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                    activeTab === "provenance"
                      ? "bg-purple-950 text-purple-300 border border-purple-500/50 shadow-md shadow-purple-950"
                      : "text-purple-400 hover:text-purple-200"
                  }`}
                >
                  <ShieldCheck className="h-3.5 w-3.5 text-purple-400" />
                  <span>Provenance & Reproducibility</span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30">Phase 8</span>
                </button>

                <button
                  onClick={() => setActiveTab("security")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                    activeTab === "security"
                      ? "bg-purple-950 text-purple-300 border border-purple-500/50 shadow-md shadow-purple-950"
                      : "text-purple-400 hover:text-purple-200"
                  }`}
                >
                  <Lock className="h-3.5 w-3.5 text-purple-400" />
                  <span>Security & Readiness</span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30">Phase 9</span>
                </button>
              </div>

              <div className="flex items-center gap-2">
                {evidenceList.length === 0 && (
                  <button
                    onClick={handleBatchRetrieveEvidence}
                    disabled={retrievingEvidence}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 disabled:opacity-50"
                  >
                    {retrievingEvidence && <Loader2 className="h-3 w-3 animate-spin" />}
                    <span>Retrieve Evidence</span>
                  </button>
                )}

                <button
                  onClick={handleBatchVerify}
                  disabled={verifying}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 text-xs font-bold shadow-xs transition-colors disabled:opacity-50"
                >
                  {verifying ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Calculator className="h-3.5 w-3.5" />}
                  <span>{verifications.length > 0 ? "Re-Run Verification" : "Verify Claims Deterministically"}</span>
                </button>
              </div>
            </div>
          )}

          {/* Verification Error Notice */}
          {verificationError && (
            <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-4 text-xs text-rose-300 space-y-2">
              <div className="flex items-center gap-2 font-semibold text-rose-200">
                <AlertCircle className="h-4 w-4 text-rose-400" />
                <span>Verification Engine Error</span>
              </div>
              <p className="leading-relaxed">{verificationError}</p>
            </div>
          )}

          {/* Phase 4 Verification Findings Summary Bar */}
          {verifications.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950 rounded-2xl border border-slate-800 p-3.5 shadow-sm">
              <div className="flex items-center gap-2.5 p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="p-1.5 rounded-lg bg-emerald-950/70 border border-emerald-500/30 text-emerald-400">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Verified</div>
                  <div className="text-lg font-bold font-mono text-emerald-400">
                    {verifications.filter((v) => v.status === "verified").length}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2.5 p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="p-1.5 rounded-lg bg-amber-950/70 border border-amber-500/30 text-amber-400">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Inconsistencies</div>
                  <div className="text-lg font-bold font-mono text-amber-400">
                    {verifications.filter((v) => v.status === "potential_inconsistency").length}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2.5 p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300">
                  <HelpCircle className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Unverifiable</div>
                  <div className="text-lg font-bold font-mono text-slate-300">
                    {verifications.filter((v) => v.status === "unverifiable").length}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2.5 p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="p-1.5 rounded-lg bg-blue-950/70 border border-blue-500/30 text-blue-400">
                  <Clock className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Pending</div>
                  <div className="text-lg font-bold font-mono text-blue-400">
                    {claims.filter((c) => !verifications.some((v) => v.claimId === c.id)).length}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 1: CLAIMS DISPLAY */}
          {activeTab === "claims" && claims.length > 0 && (
            <div className="space-y-4">
              {/* Claims Overview Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-950 rounded-2xl border border-slate-800 p-4">
                <div>
                  <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                    Claims & Findings Overview
                  </span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-2xl font-bold font-mono text-slate-100">
                      {claims.length}
                    </span>
                    <span className="text-xs text-slate-400">
                      ({claims.filter((c) => c.importance === "high").length} High Priority)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {verifications.length > 0 ? (
                    <span className="rounded-full bg-emerald-950/60 px-3 py-1 text-xs font-medium text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                      <span>Deterministic Audit Active</span>
                    </span>
                  ) : (
                    <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-medium text-slate-300 border border-slate-700 flex items-center gap-1.5">
                      <Clock className="h-3 w-3 text-amber-400" />
                      <span>Ready for Verification</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Filter Pills */}
              <div className="flex flex-col gap-2 pb-1 text-xs">
                <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
                  <span className="text-[10px] uppercase font-bold text-slate-500 shrink-0">Type:</span>
                  {filterOptions.map((opt) => (
                    <button
                      key={opt.label}
                      onClick={() => setSelectedFilter(opt.label)}
                      className={`rounded-lg px-2.5 py-1 text-xs whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                        selectedFilter === opt.label
                          ? "bg-emerald-600 text-white font-semibold"
                          : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                      }`}
                    >
                      <span>{opt.label}</span>
                      <span className="rounded-full bg-slate-950/60 px-1.5 py-0.2 font-mono text-[10px]">
                        {opt.count}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Priority Filter Row */}
                {verifications.length > 0 && (
                  <div className="flex items-center gap-1.5 overflow-x-auto">
                    <span className="text-[10px] uppercase font-bold text-slate-500 shrink-0">Priority:</span>
                    {[
                      { label: "All", count: claims.length },
                      { label: "CRITICAL", count: verifications.filter((v) => v.priority === "CRITICAL").length },
                      { label: "HIGH", count: verifications.filter((v) => v.priority === "HIGH").length },
                      { label: "MEDIUM", count: verifications.filter((v) => (v.priority || "MEDIUM") === "MEDIUM").length },
                      { label: "LOW", count: verifications.filter((v) => v.priority === "LOW").length },
                    ].map((opt) => (
                      <button
                        key={opt.label}
                        onClick={() => setSelectedPriorityFilter(opt.label)}
                        className={`rounded-lg px-2 py-0.5 text-xs whitespace-nowrap transition-colors flex items-center gap-1 ${
                          selectedPriorityFilter === opt.label
                            ? "bg-slate-100 text-slate-900 font-bold"
                            : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                        }`}
                      >
                        <span>{opt.label}</span>
                        <span className="rounded-full bg-slate-800 px-1 py-0.2 font-mono text-[9px]">
                          {opt.count}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Claims Cards List */}
              <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
                {filteredClaims.map((claim) => {
                  const claimEv = evidenceList.filter((e) => e.claimId === claim.id);
                  const finding = verifications.find((v) => v.claimId === claim.id);

                  return (
                    <div
                      key={claim.id}
                      className="rounded-xl border border-slate-800 bg-slate-950 p-4 transition-all hover:border-slate-700 space-y-3"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                              claim.importance === "high"
                                ? "bg-amber-950/80 text-amber-400 border border-amber-500/30"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {claim.importance}
                          </span>
                          <span className="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-medium text-slate-300 border border-slate-800 capitalize">
                            {claim.category}
                          </span>
                          {claimEv.length > 0 && (
                            <span className="rounded bg-cyan-950/60 px-2 py-0.5 text-[10px] font-semibold text-cyan-300 border border-cyan-500/30 flex items-center gap-1">
                              <Database className="h-2.5 w-2.5" />
                              <span>{claimEv.length} Evidence</span>
                            </span>
                          )}

                          {/* Phase 5 Deterministic Priority Badge */}
                          {finding?.priority && (
                            <span
                              className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                                finding.priority === "CRITICAL"
                                  ? "bg-rose-950 text-rose-300 border border-rose-800"
                                  : finding.priority === "HIGH"
                                  ? "bg-orange-950 text-orange-300 border border-orange-800"
                                  : finding.priority === "MEDIUM"
                                  ? "bg-amber-950 text-amber-300 border border-amber-800"
                                  : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              }`}
                              title={finding.priorityReason}
                            >
                              {finding.priority}
                            </span>
                          )}

                          {/* Phase 5 Evidence Gap Tag */}
                          {finding?.evidenceGap && (
                            <span
                              className="rounded bg-amber-950/80 text-amber-300 border border-amber-500/30 px-2 py-0.5 text-[10px] font-semibold flex items-center gap-1"
                              title={finding.evidenceGap.impact}
                            >
                              <AlertCircle className="w-2.5 h-2.5" />
                              <span>Gap: {finding.evidenceGap.category.replace("_", " ")}</span>
                            </span>
                          )}

                          {/* Phase 4 Verification Badge */}
                          {finding ? (
                            finding.status === "verified" ? (
                              <span className="rounded bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold uppercase flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                                <span>Verified</span>
                              </span>
                            ) : finding.status === "potential_inconsistency" ? (
                              <span className="rounded bg-amber-950/80 text-amber-300 border border-amber-500/30 px-2 py-0.5 text-[10px] font-bold uppercase flex items-center gap-1">
                                <AlertTriangle className="w-3 h-3 text-amber-400" />
                                <span>Potential Inconsistency</span>
                              </span>
                            ) : (
                              <span className="rounded bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 text-[10px] font-bold uppercase flex items-center gap-1">
                                <HelpCircle className="w-3 h-3 text-slate-400" />
                                <span>Unverifiable</span>
                              </span>
                            )
                          ) : (
                            <span className="rounded bg-blue-950/60 text-blue-300 border border-blue-500/30 px-2 py-0.5 text-[10px] font-medium flex items-center gap-1">
                              <Clock className="w-2.5 h-2.5" />
                              <span>Pending</span>
                            </span>
                          )}
                        </div>

                        <span className="font-mono text-emerald-400 text-xs">
                          {claim.pages && claim.pages.length > 1
                            ? `Pages ${claim.pages.join(", ")}`
                            : `Page ${claim.page}`}
                        </span>
                      </div>

                      {/* Claim Text */}
                      <p className="text-xs sm:text-sm font-medium text-slate-100 leading-snug">
                        {claim.text}
                      </p>

                      {/* Phase 5 Arithmetic Comparison Snippet */}
                      {finding?.arithmeticComparison && (
                        <div className="text-[11px] bg-purple-950/40 rounded border border-purple-800/50 p-2 flex items-center justify-between text-purple-200">
                          <span className="text-purple-400 font-mono text-[10px] uppercase font-bold">Calculation Audit:</span>
                          <span className="font-mono font-semibold text-purple-300">{finding.arithmeticComparison.formulaExpression}</span>
                          <span className="text-[10px] text-slate-400 font-sans">({finding.arithmeticComparison.conclusion})</span>
                        </div>
                      )}

                      {/* Informational Measurement / Finding Indicator */}
                      {finding?.availableMeasurement && (
                        <div className="text-[11px] bg-slate-950/80 rounded border border-slate-800 p-2 flex items-center justify-between text-slate-300">
                          <span className="text-slate-400">
                            {finding.status === "unverifiable" ? "Informational Measurement:" : "Independently Observed:"}
                          </span>
                          <span className="font-mono text-emerald-400 font-semibold">{finding.availableMeasurement}</span>
                        </div>
                      )}

                      {/* Metadata & Actions */}
                      <div className="flex flex-wrap items-center justify-between pt-2 border-t border-slate-900 text-xs gap-2">
                        <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                          <span className="capitalize">{claim.verificationType}</span>
                          <span>·</span>
                          <span>Extractability: {claim.extractability}</span>
                        </div>

                        <div className="flex items-center gap-3">
                          {finding ? (
                            <Link
                              href={`/audit/${auditId}/finding/${finding.id}`}
                              className="inline-flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs font-semibold hover:underline"
                            >
                              <Calculator className="h-3 w-3" />
                              <span>View Math Trail →</span>
                            </Link>
                          ) : claimEv.length > 0 ? (
                            <button
                              onClick={() => handleVerifySingleClaim(claim.id)}
                              className="text-emerald-400 hover:text-emerald-300 text-xs font-semibold hover:underline"
                            >
                              Verify Deterministically
                            </button>
                          ) : null}

                          <button
                            onClick={() => handleViewSource(claim)}
                            className="inline-flex items-center gap-1 text-slate-300 hover:text-slate-100 text-xs hover:underline"
                          >
                            <Eye className="h-3 w-3" />
                            <span>Source</span>
                          </button>

                          <button
                            onClick={() => setActiveClaimDetail(claim)}
                            className="text-slate-400 hover:text-slate-200 text-xs hover:underline"
                          >
                            Details & Evidence
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 2: INDEPENDENT EVIDENCE EXPLORER (Sections 15, 16) */}
          {activeTab === "evidence" && (
            <div className="space-y-4">
              {/* Evidence Summary Counters (Section 16) */}
              <div className="grid grid-cols-4 gap-3 bg-slate-950 rounded-2xl border border-slate-800 p-4 text-center">
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Total Found</span>
                  <span className="text-2xl font-bold font-mono text-slate-100 mt-1 block">{evidenceList.length}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider block">Strong</span>
                  <span className="text-2xl font-bold font-mono text-emerald-400 mt-1 block">
                    {evidenceList.filter((e) => e.quality === "strong").length}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider block">Moderate</span>
                  <span className="text-2xl font-bold font-mono text-cyan-400 mt-1 block">
                    {evidenceList.filter((e) => e.quality === "moderate").length}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider block">Limited</span>
                  <span className="text-2xl font-bold font-mono text-amber-400 mt-1 block">
                    {evidenceList.filter((e) => e.quality === "limited").length}
                  </span>
                </div>
              </div>

              {/* Quality Filter Pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto text-xs pb-1">
                {["All", "Strong", "Moderate", "Limited", "Geographic", "Regulatory"].map((q) => (
                  <button
                    key={q}
                    onClick={() => setSelectedEvidenceQuality(q)}
                    className={`rounded-lg px-3 py-1 text-xs whitespace-nowrap transition-colors ${
                      selectedEvidenceQuality === q
                        ? "bg-cyan-600 text-white font-semibold"
                        : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                    }`}
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Evidence Cards List */}
              <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
                {filteredEvidence.map((ev) => (
                  <div
                    key={ev.id}
                    className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-3 transition-colors hover:border-slate-700"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                            ev.quality === "strong"
                              ? "bg-emerald-950/80 text-emerald-400 border border-emerald-500/30"
                              : ev.quality === "moderate"
                              ? "bg-cyan-950/80 text-cyan-300 border border-cyan-500/30"
                              : "bg-amber-950/80 text-amber-400 border border-amber-500/30"
                          }`}
                        >
                          Quality: {ev.quality}
                        </span>
                        <span className="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-medium text-slate-300 border border-slate-800 capitalize">
                          {ev.type}
                        </span>
                      </div>

                      <span className="text-[11px] font-mono text-slate-400">
                        {new Date(ev.retrievedAt).toLocaleDateString()}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-slate-100">{ev.title}</h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                        {ev.relationToClaim}
                      </p>
                    </div>

                    {ev.excerpt && (
                      <p className="text-xs text-slate-300 font-mono bg-slate-900/60 p-2.5 rounded-lg border border-slate-900 italic">
                        &ldquo;{ev.excerpt}&rdquo;
                      </p>
                    )}

                    <div className="flex items-center justify-between pt-2 border-t border-slate-900 text-xs">
                      <span className="text-slate-400 font-medium">Source: {ev.sourceName}</span>
                      {ev.sourceUrl && (
                        <a
                          href={ev.sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold"
                        >
                          <span>Open Source</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}

                {filteredEvidence.length === 0 && (
                  <div className="rounded-xl border border-slate-800 p-8 text-center text-xs text-slate-500 space-y-3">
                    <p>No independent evidence items found matching the filter.</p>
                    <button
                      onClick={handleBatchRetrieveEvidence}
                      disabled={retrievingEvidence}
                      className="inline-flex items-center gap-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 text-xs font-semibold"
                    >
                      <Compass className="h-3.5 w-3.5" />
                      <span>Execute Independent Evidence Retrieval</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB: STRUCTURED EVIDENCE GAPS */}
          {activeTab === "gaps" && (
            <div className="space-y-4">
              <div className="bg-slate-950 rounded-2xl border border-slate-800 p-4 space-y-1">
                <span className="text-[11px] uppercase tracking-wider text-amber-400 font-bold block">
                  Authoritative Evidence Gaps
                </span>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Deterministic audit gaps identified where claims assert conditions that cannot be authoritatively proven with point coordinates or statutory thresholds alone.
                </p>
              </div>

              {evidenceGaps.length > 0 ? (
                <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
                  {evidenceGaps.map((gap, idx) => (
                    <div key={idx} className="rounded-xl border border-amber-500/30 bg-slate-950 p-4 space-y-2.5 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-amber-400 uppercase font-bold text-[11px] bg-amber-950/60 px-2 py-0.5 rounded border border-amber-500/20">
                          {gap.category.replace("_", " ")}
                        </span>
                        <span className="text-[11px] text-slate-500 font-mono">Missing Scope</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-300 text-[11px]">
                        <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                          <strong className="text-slate-400 block mb-0.5">Required for Verification:</strong>
                          <span>{gap.required}</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                          <strong className="text-slate-400 block mb-0.5">Authoritatively Available:</strong>
                          <span className="font-mono">{gap.available}</span>
                        </div>
                      </div>
                      <div className="text-[11px] text-amber-200 bg-amber-950/30 p-2.5 rounded-lg border border-amber-500/20">
                        <strong className="text-amber-300">Audit Impact:</strong> {gap.impact}
                      </div>
                      <div className="text-[11px] text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                        <strong className="text-emerald-400">Recommended Follow-up Evidence:</strong> {gap.recommendedEvidence}
                      </div>
                      <div className="pt-1 flex justify-end">
                        <button
                          onClick={() => setActiveTab("workspace")}
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-[11px] font-bold bg-amber-950/80 hover:bg-amber-900 text-amber-300 border border-amber-500/40 transition-colors"
                        >
                          <UploadCloud className="h-3 w-3" />
                          <span>Resolve in Evidence Workspace</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl bg-slate-950 p-8 border border-slate-800 text-center text-xs text-slate-500 space-y-2">
                  <p>Run deterministic verification to evaluate structured evidence gaps.</p>
                  <button
                    onClick={handleBatchVerify}
                    disabled={verifying}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 text-xs font-semibold"
                  >
                    <Calculator className="h-3.5 w-3.5" />
                    <span>Run Verification</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB: CROSS-CLAIM CONSISTENCY & ARITHMETIC REASONING */}
          {activeTab === "consistency" && (
            <div className="space-y-4">
              <div className="bg-slate-950 rounded-2xl border border-slate-800 p-4 space-y-1">
                <span className="text-[11px] uppercase tracking-wider text-purple-400 font-bold block">
                  Report-Internal Cross-Claim Consistency
                </span>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Automated mathematical and logical verification checking internal consistency between disparate sections within the environmental report.
                </p>
              </div>

              {crossClaimResults.length > 0 ? (
                <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
                  {crossClaimResults.map((cc, idx) => (
                    <div key={idx} className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-200">{cc.parameter}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                          cc.isConsistent
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-500/30"
                            : "bg-rose-950 text-rose-300 border border-rose-500/30"
                        }`}>
                          {cc.isConsistent ? "CORROBORATED" : "INTERNAL CONTRADICTION"}
                        </span>
                      </div>
                      <p className="text-slate-300 text-[11px] leading-relaxed">{cc.explanation}</p>
                      {cc.arithmeticExpression && (
                        <div className="font-mono text-purple-300 bg-slate-900 p-2.5 rounded text-[11px] border border-slate-800">
                          {cc.arithmeticExpression}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl bg-slate-950 p-8 border border-slate-800 text-center text-xs text-slate-500 space-y-2">
                  <p>Run deterministic verification to compute report-internal cross-claim relationships.</p>
                  <button
                    onClick={handleBatchVerify}
                    disabled={verifying}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 text-xs font-semibold"
                  >
                    <Calculator className="h-3.5 w-3.5" />
                    <span>Run Verification</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: VISUAL EVIDENCE CHAIN UI (Section 17) */}
          {activeTab === "chain" && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  GroundCheck Independent Evidence Chain
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Traceable multi-step audit mapping from report quotation to independent empirical source.
                </p>
              </div>

              <div className="space-y-4 max-h-[580px] overflow-y-auto pr-1">
                {claims.slice(0, 5).map((claim) => {
                  const ev = evidenceList.find((e) => e.claimId === claim.id);
                  return (
                    <div
                      key={claim.id}
                      className="rounded-2xl border border-slate-800 bg-slate-950 p-5 space-y-3.5 shadow-sm"
                    >
                      {/* Step 1: Report Claim */}
                      <div className="flex items-start gap-3">
                        <div className="h-6 w-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-200 shrink-0">
                          1
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                              Report Claim · Page {claim.page}
                            </span>
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-900 text-slate-300">
                              {claim.category}
                            </span>
                          </div>
                          <p className="text-xs font-semibold text-slate-100 mt-0.5">&ldquo;{claim.text}&rdquo;</p>
                        </div>
                      </div>

                      {/* Arrow Down */}
                      <div className="pl-3 text-slate-600 font-mono text-xs">↓</div>

                      {/* Step 2: Independent Evidence */}
                      <div className="flex items-start gap-3">
                        <div className="h-6 w-6 rounded-full bg-cyan-950 border border-cyan-500/40 flex items-center justify-center text-[10px] font-bold text-cyan-300 shrink-0">
                          2
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400">
                              Independent Evidence
                            </span>
                            {ev && (
                              <span
                                className={`text-[10px] font-mono font-bold uppercase px-1.5 py-0.2 rounded ${
                                  ev.quality === "strong"
                                    ? "bg-emerald-950 text-emerald-400 border border-emerald-500/30"
                                    : "bg-cyan-950 text-cyan-300 border border-cyan-500/30"
                                }`}
                              >
                                Quality: {ev.quality}
                              </span>
                            )}
                          </div>
                          {ev ? (
                            <div className="mt-1 space-y-1">
                              <p className="text-xs font-medium text-slate-200">{ev.title}</p>
                              <p className="text-[11px] text-slate-400">{ev.relationToClaim}</p>
                              <div className="flex items-center gap-2 pt-1 text-[11px]">
                                <span className="text-slate-400">Source: {ev.sourceName}</span>
                                {ev.sourceUrl && (
                                  <a
                                    href={ev.sourceUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-cyan-400 hover:underline inline-flex items-center gap-0.5"
                                  >
                                    <span>[Verified Link]</span>
                                    <ExternalLink className="h-2.5 w-2.5" />
                                  </a>
                                )}
                              </div>
                            </div>
                          ) : (
                            <p className="text-xs text-slate-500 italic mt-0.5">
                              No independent evidence retrieved yet for this claim.
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Arrow Down */}
                      <div className="pl-3 text-slate-600 font-mono text-xs">↓</div>

                      {/* Step 3: Pending Verification Decision */}
                      <div className="flex items-center justify-between rounded-xl bg-slate-900/80 px-4 py-2.5 border border-slate-800 text-xs">
                        <div className="flex items-center gap-2 text-slate-400 text-[11px]">
                          <Clock className="h-3.5 w-3.5 text-amber-400" />
                          <span>Status:</span>
                        </div>
                        <span className="font-bold font-mono text-amber-300 text-[11px] uppercase tracking-wider">
                          Pending Deterministic Verification (Phase 4)
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB: EVIDENCE WORKSPACE & RE-VERIFICATION (Phase 6) */}
          {activeTab === "workspace" && (
            <EvidenceWorkspaceTab
              auditId={auditId}
              claims={claims}
              verifications={verifications}
              onReverificationComplete={async () => {
                const updatedVerifs = await getAuditVerifications(auditId);
                setVerifications(updatedVerifs);
                try {
                  const sum = await getAuditSummary(auditId);
                  setSummary(sum);
                  setEvidenceGaps(sum.evidenceGaps || []);
                  setCrossClaimResults(sum.crossClaimConsistency || []);
                } catch {}
                const updatedClaims = await getAuditClaims(auditId);
                setClaims(updatedClaims);
                const updatedAudit = await getAuditDetail(auditId);
                setAudit(updatedAudit);
              }}
            />
          )}

          {/* TAB: AUDIT INTELLIGENCE & DECISION SUPPORT (Phase 7) */}
          {activeTab === "intelligence" && (
            <AuditIntelligenceTab
              auditId={auditId}
              claims={claims}
              verifications={verifications}
              onNavigateToWorkspace={() => setActiveTab("workspace")}
            />
          )}

          {/* TAB: EVIDENCE PROVENANCE & REPRODUCIBILITY (Phase 8) */}
          {activeTab === "provenance" && (
            <ProvenanceTab
              auditId={auditId}
              claims={claims}
            />
          )}

          {/* TAB: SECURITY, ADVERSARIAL INTEGRITY & READINESS (Phase 9) */}
          {activeTab === "security" && (
            <SecurityIntegrityPanel
              auditId={auditId}
              isBenchmark={audit.isBenchmark}
            />
          )}
        </div>
      </div>

      {/* Claim Detail Modal / Drawer (Sections 15, 18) */}
      {activeClaimDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-800 bg-slate-900 p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="rounded bg-emerald-950 px-2 py-0.5 text-xs font-bold text-emerald-400 border border-emerald-500/30 uppercase">
                  Claim Detail
                </span>
                <span className="text-xs font-mono text-slate-400">
                  {activeClaimDetail.id}
                </span>
              </div>
              <button
                onClick={() => setActiveClaimDetail(null)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Claim Statement */}
            <div className="space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Claim
              </span>
              <p className="text-sm font-semibold text-slate-100 leading-relaxed">
                {activeClaimDetail.text}
              </p>
            </div>

            {/* Source Document & Page */}
            <div className="grid grid-cols-2 gap-4 text-xs bg-slate-950 p-3.5 rounded-xl border border-slate-800">
              <div>
                <span className="text-slate-400 text-[10px] uppercase font-semibold block">
                  Source Document
                </span>
                <span className="text-slate-200 font-medium truncate block">
                  {audit.filename}
                </span>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] uppercase font-semibold block">
                  Page Reference
                </span>
                <span className="text-emerald-400 font-mono font-bold">
                  {activeClaimDetail.pages && activeClaimDetail.pages.length > 1
                    ? `Pages ${activeClaimDetail.pages.join(", ")}`
                    : `Page ${activeClaimDetail.page}`}
                </span>
              </div>
            </div>

            {/* Category & Verification Metadata */}
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Category</span>
                <span className="text-slate-200 font-semibold capitalize mt-0.5 block">
                  {activeClaimDetail.category}
                </span>
              </div>
              <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Verification Type</span>
                <span className="text-slate-200 font-semibold capitalize mt-0.5 block">
                  {activeClaimDetail.verificationType}
                </span>
              </div>
              <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Importance</span>
                <span className="text-slate-200 font-semibold capitalize mt-0.5 block">
                  {activeClaimDetail.importance}
                </span>
              </div>
            </div>

            {/* Source Text Verbatim */}
            <div className="space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Source Text (Document Quotation)
              </span>
              <p className="text-xs text-slate-300 font-mono bg-slate-950 p-3 rounded-lg border border-slate-800 italic leading-relaxed">
                &ldquo;{activeClaimDetail.sourceText}&rdquo;
              </p>
              {activeClaimDetail.sourceVerified && (
                <p className="text-[10px] text-emerald-400 flex items-center gap-1 mt-1">
                  <CheckCircle2 className="h-3 w-3" />
                  <span>Quotation verified against document page text</span>
                </p>
              )}
            </div>

            {/* Section 15: INDEPENDENT EVIDENCE LINKED TO THIS CLAIM */}
            <div className="space-y-2 border-t border-slate-800 pt-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-cyan-400">
                  Independent Evidence
                </span>
                <button
                  onClick={() => handleRetrieveSingleClaimEvidence(activeClaimDetail.id)}
                  className="text-[11px] text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
                >
                  <Compass className="h-3 w-3" />
                  <span>Refresh Evidence</span>
                </button>
              </div>

              {evidenceList.filter((e) => e.claimId === activeClaimDetail.id).length > 0 ? (
                <div className="space-y-2">
                  {evidenceList
                    .filter((e) => e.claimId === activeClaimDetail.id)
                    .map((ev) => (
                      <div
                        key={ev.id}
                        className="rounded-xl bg-slate-950 p-3.5 border border-slate-800 space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <h5 className="font-semibold text-slate-100">{ev.title}</h5>
                          <span
                            className={`rounded px-1.5 py-0.2 text-[9px] font-bold uppercase ${
                              ev.quality === "strong"
                                ? "bg-emerald-950 text-emerald-400 border border-emerald-500/30"
                                : "bg-cyan-950 text-cyan-300 border border-cyan-500/30"
                            }`}
                          >
                            Quality: {ev.quality}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">{ev.relationToClaim}</p>
                        {ev.excerpt && (
                          <p className="text-[11px] text-slate-300 font-mono bg-slate-900/80 p-2 rounded border border-slate-850 italic">
                            &ldquo;{ev.excerpt}&rdquo;
                          </p>
                        )}
                        <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
                          <span>Source: {ev.sourceName}</span>
                          {ev.sourceUrl && (
                            <a
                              href={ev.sourceUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-cyan-400 hover:underline inline-flex items-center gap-1 font-semibold"
                            >
                              <span>View Source</span>
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <div className="rounded-xl bg-slate-950 p-3.5 border border-slate-800 text-xs text-slate-400 space-y-2 text-center">
                  <p>No independent evidence has been retrieved for this claim yet.</p>
                  <button
                    onClick={() => handleRetrieveSingleClaimEvidence(activeClaimDetail.id)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3 py-1.5 text-white font-semibold hover:bg-cyan-500"
                  >
                    <Compass className="h-3.5 w-3.5" />
                    <span>Retrieve Independent Evidence</span>
                  </button>
                </div>
              )}
            </div>

            {/* Strict Factual Status (Section 15, 18, 24) */}
            <div className="rounded-xl bg-slate-950 p-3 border border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-400 text-[11px] uppercase font-semibold">
                Verification Status
              </span>
              <span className="font-bold text-amber-300 bg-amber-950/80 px-2.5 py-1 rounded border border-amber-500/40">
                PENDING (Phase 4 Deterministic Engine)
              </span>
            </div>

            {/* Footer actions */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => {
                  handleViewSource(activeClaimDetail);
                  setActiveClaimDetail(null);
                }}
                className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 text-xs font-semibold transition-colors"
              >
                <Eye className="h-3.5 w-3.5" />
                <span>View on Document Page {activeClaimDetail.page}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

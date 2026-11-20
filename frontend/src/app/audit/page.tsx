"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  UploadCloud,
  FileText,
  Trash2,
  AlertCircle,
  Loader2,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  File,
  Sparkles,
  Compass
} from "lucide-react";
import { uploadAuditFile, ApiError, getApiBaseUrl } from "@/lib/api";

const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB

export default function AuditUploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    setErrorMessage(null);

    // Validate extension & mime type
    const isPdf = file.name.toLowerCase().endsWith(".pdf") || file.type === "application/pdf";
    if (!isPdf) {
      setErrorMessage("Invalid file type. Only PDF documents (.pdf) are supported.");
      return;
    }

    // Validate size
    if (file.size === 0) {
      setErrorMessage("Selected PDF is empty (0 bytes). Please select a valid document.");
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMessage("File exceeds 50MB size limit. Please choose a smaller report.");
      return;
    }

    setSelectedFile(file);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const loadCanonicalSample = async () => {
    setErrorMessage(null);
    try {
      const res = await fetch("/Apex_Quartz_Quarry_Test_EIA.pdf");
      if (!res.ok) throw new Error("Sample file not found");
      const blob = await res.blob();
      const file = new File([blob], "Apex_Quartz_Quarry_Test_EIA.pdf", { type: "application/pdf" });
      setSelectedFile(file);
    } catch {
      setErrorMessage("Unable to fetch sample PDF. Please select a file from your computer.");
    }
  };

  const handleStartAudit = async () => {
    if (!selectedFile || isUploading) return;

    setIsUploading(true);
    setErrorMessage(null);

    try {
      const response = await uploadAuditFile(selectedFile);
      // Redirect to audit workspace with real audit ID
      router.push(`/audit/${response.auditId}`);
    } catch (err: any) {
      setIsUploading(false);
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(
          err.message || "An unexpected error occurred during document upload. Please try again."
        );
      }
    }
  };

  const apiTarget = getApiBaseUrl();

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8 space-y-8">
      {/* Page Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <div className="inline-flex items-center gap-1.5 rounded-md bg-[#161D23] px-3 py-1 text-xs font-mono font-bold text-emerald-400 border border-[#222C35]">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>DOCUMENT INGESTION WORKSPACE</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-slate-100 uppercase">
          Upload Environmental Report
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed font-sans">
          Upload an Environmental Impact Assessment (EIA) PDF. GroundCheck extracts page-level text, decomposes atomic claims, and prepares the document for independent evidence verification.
        </p>
      </div>

      {/* Main Upload Box */}
      <div className="rounded-2xl border border-[#222C35] bg-[#11161B] p-6 sm:p-8 shadow-xl space-y-6">
        {/* Dropzone */}
        {!selectedFile ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 text-center cursor-pointer transition-all ${
              isDragging
                ? "border-emerald-500 bg-emerald-950/20"
                : "border-[#222C35] bg-[#0A0E11] hover:border-slate-700"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileInputChange}
              className="hidden"
            />
            <div className="w-12 h-12 rounded-lg bg-[#161D23] border border-[#222C35] flex items-center justify-center text-emerald-400 mb-4 shadow">
              <UploadCloud className="h-6 w-6" />
            </div>
            <p className="text-sm font-bold text-slate-200 font-sans">
              Drag and drop your environmental PDF here
            </p>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              or <span className="text-emerald-400 font-bold underline">browse file from disk</span>
            </p>
            <p className="text-[11px] text-slate-500 mt-3 font-mono">
              Accepted format: PDF (.pdf) · Maximum size: 50MB
            </p>
          </div>
        ) : (
          /* Selected File Preview Card */
          <div className="rounded-xl border border-emerald-500/40 bg-[#0A0E11] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-[#161D23] border border-[#222C35] flex items-center justify-center text-emerald-400">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-100 font-sans">{selectedFile.name}</p>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Ready for ingestion
                  </p>
                </div>
              </div>

              {!isUploading && (
                <button
                  onClick={handleRemoveFile}
                  className="rounded-lg p-2 text-slate-400 hover:bg-[#161D23] hover:text-rose-400 transition-colors"
                  title="Remove selected file"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/40 px-3 py-1.5 rounded-lg border border-emerald-500/20 font-mono">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>PDF format validated. Ready to process with PyMuPDF text extractor.</span>
            </div>
          </div>
        )}

        {/* Quick Sample Selector */}
        {!selectedFile && (
          <div className="flex flex-col sm:flex-row items-center justify-between p-3.5 rounded-xl bg-[#0A0E11] border border-[#222C35] font-mono text-xs gap-3">
            <span className="text-slate-400">Need a test document right now?</span>
            <button
              type="button"
              onClick={loadCanonicalSample}
              className="px-3.5 py-1.5 rounded-md bg-[#161D23] hover:bg-[#1E262C] border border-[#222C35] hover:border-emerald-500/40 text-emerald-300 font-bold flex items-center gap-1.5 transition-all"
            >
              <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
              <span>Load Canonical Apex Quartz EIA</span>
            </button>
          </div>
        )}

        {/* Error State */}
        {errorMessage && (
          <div className="flex items-start gap-3 rounded-xl bg-rose-950/50 border border-rose-500/30 p-4 text-xs text-rose-300 font-mono">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
            <div>
              <p className="font-bold text-rose-200">Connection or Validation Issue</p>
              <p className="mt-0.5 leading-relaxed">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Start Audit CTA Button */}
        <div>
          <button
            onClick={handleStartAudit}
            disabled={!selectedFile || isUploading}
            className={`w-full flex items-center justify-center gap-2 rounded-xl py-3.5 px-6 text-sm font-bold font-mono uppercase tracking-wider transition-all ${
              !selectedFile || isUploading
                ? "bg-[#161D23] text-slate-500 border border-[#222C35] cursor-not-allowed"
                : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-md"
            }`}
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Uploading and Ingesting Report...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="h-4 w-4" />
                <span>Start Audit</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Target Backend Notice */}
      <div className="rounded-xl border border-[#222C35] bg-[#11161B] p-4 text-xs font-mono text-slate-400 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Compass className="h-3.5 w-3.5 text-emerald-400" />
          <span>Active Backend Target: <span className="text-slate-200 font-bold">{apiTarget || "Same-Origin Proxy"}</span></span>
        </div>
        <Link href="/demo" className="text-emerald-400 hover:underline font-bold">
          View Canonical Benchmark Console →
        </Link>
      </div>
    </div>
  );
}

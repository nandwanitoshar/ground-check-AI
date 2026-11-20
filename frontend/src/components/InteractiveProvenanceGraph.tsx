"use client";

import React, { useState } from "react";
import { GitBranch, ShieldCheck, Database, FileText, CheckCircle2, Lock, ArrowRight, Info, Copy, Check } from "lucide-react";

interface NodeDetails {
  id: string;
  name: string;
  stage: string;
  source: string;
  timestamp: string;
  hash: string;
  method: string;
  calculation: string;
  result: string;
}

export default function InteractiveProvenanceGraph({ className = "" }: { className?: string }) {
  const [selectedNodeId, setSelectedNodeId] = useState<string>("verification");
  const [copiedHash, setCopiedHash] = useState<boolean>(false);

  const graphNodes: NodeDetails[] = [
    {
      id: "source",
      name: "SOURCE",
      stage: "External Authority",
      source: "USGS National Cadastre Database / OpenStreetMap Server",
      timestamp: "2026-11-18T10:15:30.412Z",
      hash: "8e9f2a1b4c6d8e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
      method: "Overpass API Query & Certified Open Data Mirror",
      calculation: "TLS 1.3 Certified Handshake with SHA-256 Certificate Check",
      result: "200 OK · Authoritative Cadastral WGS84 Boundary Vector",
    },
    {
      id: "evidence",
      name: "EVIDENCE",
      stage: "Raw Ingestion",
      source: "excavation_boundary.geojson (Evidence Workspace)",
      timestamp: "2026-11-18T10:18:22.109Z",
      hash: "450aa937609c2db04e8241416e99426f31bf9bb5039ebc57f7eb9b9961db1d72",
      method: "SHA-256 Deduplication & Planar Geometry Validation",
      calculation: "6 vertices validated: Self-intersection = False, Bowtie = None",
      result: "Ingested as Valid Polygon Geometry (2D Dimension)",
    },
    {
      id: "claim",
      name: "CLAIM",
      stage: "Extracted Target",
      source: "Apex_Quartz_Quarry_EIA_2024.pdf (Page 4, Paragraph 2)",
      timestamp: "2026-11-18T09:42:01.000Z",
      hash: "c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3",
      method: "Gemini OCR Extraction Assistant (AI Auxiliary Role)",
      calculation: 'Extracted: "The proposed excavation pit spans 12.5 hectares"',
      result: "Claim 02 Created (Category: Spatial Area, Importance: High)",
    },
    {
      id: "verification",
      name: "VERIFICATION",
      stage: "Deterministic Math",
      source: "GroundCheck Deterministic Python Geometric Engine",
      timestamp: "2026-11-18T10:18:25.044Z",
      hash: "5d2726a779ff2f42154da215bc551585ae8315ba7a9635d25558cc739bb80c7c",
      method: "Shoelace Formula (Gauss Area) on WGS84 Projected Coordinates",
      calculation: "Area = 0.5 * |Σ (x_i * y_{i+1} - x_{i+1} * y_i)| = 12.502 ha. Delta = +0.002 ha (0.016%) within 2% margin.",
      result: "VERIFIED · True Spatial Compatibility Confirmed",
    },
    {
      id: "finding",
      name: "FINDING",
      stage: "Audit Finding Item",
      source: "Audit Run Snapshot #1 (Version Immutable)",
      timestamp: "2026-11-18T10:18:25.500Z",
      hash: "b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2",
      method: "State Transition Evaluation & Materiality Ranking",
      calculation: "Transition: UNVERIFIABLE -> VERIFIED. Claim weight: 5.0 pts.",
      result: "Finding 02: Closed as Compliant with Document Assertion",
    },
    {
      id: "decision",
      name: "DECISION",
      stage: "Audit Package",
      source: "Final Report Section 1-17 & Reproducibility Package",
      timestamp: "2026-11-18T10:18:26.120Z",
      hash: "9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
      method: "Deterministic Risk Model & Monotonic Clamping",
      calculation: "Risk Score: 38 -> 33 / 100 (-5.0 pts). Verdict: PROCEED TO DRILLING",
      result: "Signed HMAC Audit Package Generated & Downloadable",
    },
  ];

  const activeNode = graphNodes.find((n) => n.id === selectedNodeId) || graphNodes[0];

  function copyHash(hash: string) {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  }

  return (
    <div className={`p-6 sm:p-8 rounded-2xl bg-[#0D1317] border border-slate-800 space-y-6 shadow-2xl relative ${className}`}>
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4 font-mono text-xs">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-purple-400" />
          <span className="font-bold text-slate-200">INTERACTIVE FORENSIC PROVENANCE GRAPH</span>
        </div>
        <span className="text-[11px] text-slate-500">
          Click any node below to inspect cryptographic lineage & calculation proof
        </span>
      </div>

      {/* The 6 Linear Graph Nodes with Connecting Signals */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {graphNodes.map((n, idx) => {
          const isSelected = n.id === selectedNodeId;

          return (
            <button
              key={n.id}
              onClick={() => setSelectedNodeId(n.id)}
              className={`p-3.5 rounded-xl border text-left transition-all duration-200 relative group flex flex-col justify-between min-h-[96px] ${
                isSelected
                  ? "bg-purple-950/40 border-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.3)] scale-[1.02]"
                  : "bg-[#080C0E] border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
              }`}
            >
              <div>
                <div className="flex items-center justify-between font-mono text-[9px] text-slate-500 mb-1">
                  <span>STEP 0{idx + 1}</span>
                  {isSelected && <span className="h-1.5 w-1.5 rounded-full bg-purple-400 animate-ping" />}
                </div>
                <p className={`font-mono text-xs font-black tracking-wider ${isSelected ? "text-purple-300" : "text-slate-300"}`}>
                  {n.name}
                </p>
              </div>

              <span className="font-mono text-[10px] text-slate-500 mt-2 block truncate">
                {n.stage}
              </span>

              {/* Selection indicator pill */}
              {isSelected && (
                <div className="absolute -bottom-1.5 inset-x-4 h-0.5 bg-purple-400 rounded-full" />
              )}
            </button>
          );
        })}
      </div>

      {/* Forensic Node Inspector Card */}
      <div className="bg-[#080C0E] border border-purple-500/30 rounded-xl p-5 font-mono text-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40 font-bold uppercase text-[10px]">
              NODE: {activeNode.name}
            </span>
            <span className="text-slate-300 font-bold">{activeNode.stage}</span>
          </div>
          <span className="text-slate-500 text-[11px]">{activeNode.timestamp}</span>
        </div>

        {/* Detailed Metadata Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1">
            <span className="text-slate-500 text-[10px] uppercase block">SOURCE ARTIFACT:</span>
            <p className="text-slate-200">{activeNode.source}</p>
          </div>

          <div className="space-y-1">
            <span className="text-slate-500 text-[10px] uppercase block">VALIDATION METHOD:</span>
            <p className="text-slate-200">{activeNode.method}</p>
          </div>

          <div className="space-y-1 md:col-span-2">
            <span className="text-slate-500 text-[10px] uppercase block">MATHEMATICAL CALCULATION / VERIFICATION FORMULA:</span>
            <p className="text-emerald-400 bg-[#0D1317] p-2.5 rounded-lg border border-slate-800 font-mono text-[11px]">
              {activeNode.calculation}
            </p>
          </div>

          <div className="space-y-1 md:col-span-2">
            <span className="text-slate-500 text-[10px] uppercase block">SHA-256 CRYPTOGRAPHIC INTEGRITY DIGEST:</span>
            <div className="flex items-center justify-between bg-[#0D1317] p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-300">
              <span className="truncate pr-2">{activeNode.hash}</span>
              <button
                onClick={() => copyHash(activeNode.hash)}
                className="shrink-0 flex items-center gap-1 text-slate-400 hover:text-slate-100 transition-colors"
                title="Copy hash to clipboard"
              >
                {copiedHash ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                <span className="text-[10px]">{copiedHash ? "Copied" : "Copy"}</span>
              </button>
            </div>
          </div>
        </div>

        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
          <span className="text-slate-500">NODE VERDICT:</span>
          <span className="text-emerald-400 font-bold">{activeNode.result}</span>
        </div>
      </div>
    </div>
  );
}


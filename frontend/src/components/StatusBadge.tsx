import React from "react";
import { CheckCircle2, AlertTriangle, HelpCircle, ShieldAlert } from "lucide-react";
import { VerificationStatus, EvidenceQuality } from "@/types/audit";

interface StatusBadgeProps {
  status: VerificationStatus;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
}

export function StatusBadge({ status, size = "md", showIcon = true }: StatusBadgeProps) {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs gap-1",
    md: "px-2.5 py-1 text-xs sm:text-sm gap-1.5 font-medium",
    lg: "px-3.5 py-1.5 text-sm sm:text-base gap-2 font-semibold"
  }[size];

  const iconSizes = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5"
  }[size];

  if (status === "VERIFIED") {
    return (
      <span
        className={`inline-flex items-center rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 ${sizeClasses} shadow-sm`}
      >
        {showIcon && <CheckCircle2 className={`${iconSizes} text-emerald-400`} />}
        <span>VERIFIED</span>
      </span>
    );
  }

  if (status === "POTENTIAL INCONSISTENCY") {
    return (
      <span
        className={`inline-flex items-center rounded-full bg-amber-950/70 text-amber-300 border border-amber-500/40 ${sizeClasses} shadow-sm animate-pulse-subtle`}
      >
        {showIcon && <AlertTriangle className={`${iconSizes} text-amber-400`} />}
        <span>POTENTIAL INCONSISTENCY</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center rounded-full bg-slate-800 text-slate-300 border border-slate-700 ${sizeClasses} shadow-sm`}
    >
      {showIcon && <HelpCircle className={`${iconSizes} text-slate-400`} />}
      <span>UNVERIFIABLE</span>
    </span>
  );
}

interface QualityBadgeProps {
  quality: EvidenceQuality;
}

export function QualityBadge({ quality }: QualityBadgeProps) {
  const styles = {
    "Strong evidence": "bg-teal-950/70 text-teal-300 border-teal-500/30",
    "Moderate evidence": "bg-blue-950/70 text-blue-300 border-blue-500/30",
    "Limited evidence": "bg-slate-800 text-slate-400 border-slate-700"
  }[quality] || "bg-slate-800 text-slate-400 border-slate-700";

  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium border ${styles}`}>
      {quality}
    </span>
  );
}

export function CategoryBadge({ category }: { category: string }) {
  const colors: Record<string, string> = {
    Water: "bg-cyan-950/60 text-cyan-300 border-cyan-500/20",
    Land: "bg-emerald-950/60 text-emerald-300 border-emerald-500/20",
    Biodiversity: "bg-green-950/60 text-green-300 border-green-500/20",
    Air: "bg-sky-950/60 text-sky-300 border-sky-500/20",
    Distance: "bg-indigo-950/60 text-indigo-300 border-indigo-500/20",
    Waste: "bg-orange-950/60 text-orange-300 border-orange-500/20",
    Compliance: "bg-purple-950/60 text-purple-300 border-purple-500/20",
    Infrastructure: "bg-slate-800 text-slate-300 border-slate-700"
  };

  const style = colors[category] || "bg-slate-800 text-slate-300 border-slate-700";

  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold border ${style}`}>
      {category}
    </span>
  );
}


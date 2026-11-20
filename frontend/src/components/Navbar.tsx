"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, FileSearch, Sparkles, Menu, X, Terminal, Activity, Settings, Check, RefreshCw } from "lucide-react";
import { checkBackendHealth, getApiBaseUrl } from "@/lib/api";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [customApiUrl, setCustomApiUrl] = useState("");
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    checkHealth();
    if (typeof window !== "undefined") {
      setCustomApiUrl(window.localStorage.getItem("groundcheck_api_url") || "");
    }
  }, []);

  async function checkHealth() {
    const ok = await checkBackendHealth();
    setBackendHealthy(ok);
  }

  function handleSaveApiUrl(e: React.FormEvent) {
    e.preventDefault();
    if (typeof window !== "undefined") {
      if (customApiUrl.trim()) {
        window.localStorage.setItem("groundcheck_api_url", customApiUrl.trim());
        setSavedMessage("Custom API URL saved.");
      } else {
        window.localStorage.removeItem("groundcheck_api_url");
        setSavedMessage("Reset to environment default.");
      }
      setTimeout(() => {
        setSavedMessage(null);
        setSettingsOpen(false);
        checkHealth();
      }, 1200);
    }
  }

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/audit", label: "Audit Console" },
    { href: "/demo", label: "Canonical Benchmark" },
    { href: "/about", label: "Methodology" },
  ];

  const currentApi = getApiBaseUrl();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#222C35] bg-[#0A0E11]/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 font-mono text-xs">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#161D23] border border-[#222C35] text-emerald-400 group-hover:border-emerald-400/80 transition-all">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-sans font-black tracking-tight text-slate-100 text-base">
                GroundCheck <span className="text-emerald-400">AI</span>
              </span>
              <span className="rounded bg-[#161D23] px-1.5 py-0.5 text-[9px] font-bold text-emerald-400 border border-[#222C35]">
                v1.0.0
              </span>
            </div>
            <p className="text-[10px] text-slate-400 hidden sm:block">
              Evidence Machine · Environmental Report Auditor
            </p>
          </div>
        </Link>

        {/* Center Navigation */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3.5 py-1.5 transition-all font-semibold ${
                  isActive
                    ? "bg-[#161D23] text-emerald-400 border border-[#222C35] shadow-sm"
                    : "text-slate-400 hover:bg-[#11161B] hover:text-slate-200"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Right Telemetry & Actions */}
        <div className="hidden sm:flex items-center gap-3">
          {/* Backend Connection Health Pill with Settings Drawer */}
          <div className="relative">
            <button
              onClick={() => setSettingsOpen(!settingsOpen)}
              className={`flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-md border transition-all ${
                backendHealthy
                  ? "bg-[#11161B] border-[#222C35] text-slate-300 hover:border-emerald-500/40"
                  : "bg-amber-950/40 border-amber-500/40 text-amber-300"
              }`}
              title="Click to inspect or change Backend API URL"
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  backendHealthy ? "bg-emerald-400" : "bg-amber-400 animate-pulse"
                }`}
              />
              <span className="font-bold uppercase">
                {backendHealthy ? "API READY" : "API OFFLINE"}
              </span>
            </button>

            {/* Quick API Config Popover */}
            {settingsOpen && (
              <div className="absolute right-0 mt-2 w-80 rounded-xl bg-[#11161B] border border-[#222C35] p-4 shadow-2xl z-50 space-y-3">
                <div className="flex items-center justify-between border-b border-[#222C35] pb-2">
                  <span className="font-bold text-slate-200">Backend API Destination</span>
                  <button onClick={() => setSettingsOpen(false)} className="text-slate-500 hover:text-slate-300">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="text-[11px] text-slate-400 space-y-1">
                  <div className="flex justify-between">
                    <span>Active Endpoint:</span>
                    <span className="text-slate-200 font-bold">{currentApi || "Same-Origin Proxy"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Health Status:</span>
                    <span className={backendHealthy ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>
                      {backendHealthy ? "200 OK" : "Unreachable"}
                    </span>
                  </div>
                </div>

                <form onSubmit={handleSaveApiUrl} className="space-y-2 pt-1 border-t border-[#222C35]">
                  <label className="text-[10px] text-slate-400 uppercase font-bold block">
                    Custom Backend URL (Override)
                  </label>
                  <input
                    type="text"
                    value={customApiUrl}
                    onChange={(e) => setCustomApiUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                    className="w-full px-2.5 py-1.5 rounded bg-[#0A0E11] border border-[#222C35] text-slate-200 text-xs focus:outline-none focus:border-emerald-500"
                  />
                  <div className="flex items-center justify-between pt-1">
                    <button
                      type="submit"
                      className="px-3 py-1 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-[11px] transition-all"
                    >
                      Save Override
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setCustomApiUrl("");
                        if (typeof window !== "undefined") window.localStorage.removeItem("groundcheck_api_url");
                        checkHealth();
                      }}
                      className="text-[10px] text-slate-500 hover:text-slate-300"
                    >
                      Reset Default
                    </button>
                  </div>
                  {savedMessage && (
                    <div className="text-[10px] text-emerald-400 flex items-center gap-1 mt-1">
                      <Check className="h-3 w-3" />
                      <span>{savedMessage}</span>
                    </div>
                  )}
                </form>
              </div>
            )}
          </div>

          <Link
            href="/audit"
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 px-3.5 py-1.5 text-xs font-bold text-slate-950 shadow transition-all uppercase tracking-wider"
          >
            <FileSearch className="h-3.5 w-3.5" />
            <span>Start Audit</span>
          </Link>
        </div>

        {/* Mobile menu button */}
        <div className="flex md:hidden">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="rounded-lg p-2 text-slate-400 hover:bg-[#161D23] hover:text-slate-200 border border-[#222C35]"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#222C35] bg-[#0A0E11] px-4 pt-3 pb-5 space-y-2 font-mono text-xs">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`block rounded-lg px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-[#161D23] text-emerald-400" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      )}
    </header>
  );
}

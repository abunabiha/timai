"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  Cpu,
  DollarSign,
  Play,
  Plus,
  RefreshCw,
  ShieldAlert,
  Zap,
} from "lucide-react";

interface ActiveAgent {
  project_id: string;
  agent_id: string;
  agent_name: string;
  role_name: string;
  task_id: string;
  pbi_title: string;
  state: "thinking" | "executing_tool" | "writing_artifact" | "in_review" | "revising" | "idle";
  current_tool?: string;
  tokens_used: number;
  cost_spent: number;
  updated_at: string;
}

interface BudgetStatus {
  project_id: string;
  currency: string;
  project_budget: number;
  total_spent: number;
  sprint_id?: string;
  sprint_budget: number;
  percent_used: number;
  status: "normal" | "warning_50" | "warning_80" | "exceeded_100";
  warning_message?: string;
  is_paused: boolean;
}

interface Props {
  projectId: string;
  sprintId?: string;
  token: string;
  userRole: string;
  onRefreshKanban?: () => void;
}

export default function ActiveAgentsPanel({
  projectId,
  sprintId,
  token,
  userRole,
  onRefreshKanban,
}: Props) {
  const [agents, setAgents] = useState<ActiveAgent[]>([]);
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExecutingAll, setIsExecutingAll] = useState(false);
  const [executionMessage, setExecutionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Increase Budget Dialog
  const [isIncreaseOpen, setIsIncreaseOpen] = useState(false);
  const [additionalAmount, setAdditionalAmount] = useState(5000000);
  const [isSavingBudget, setIsSavingBudget] = useState(false);

  const fetchStatus = async () => {
    if (!projectId || !token) return;
    try {
      // 1. Fetch active agents
      const aRes = await fetch(`http://localhost:8000/api/projects/${projectId}/active-agents`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (aRes.ok) {
        const aData = await aRes.json();
        setAgents(aData);
      }

      // 2. Fetch budget status
      const bUrl = sprintId
        ? `http://localhost:8000/api/projects/${projectId}/budget-status?sprint_id=${sprintId}`
        : `http://localhost:8000/api/projects/${projectId}/budget-status`;
      const bRes = await fetch(bUrl, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (bRes.ok) {
        const bData = await bRes.json();
        setBudget(bData);
      }
    } catch {
      // Ignore network errors in polling
    }
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 4000);
    return () => clearInterval(timer);
  }, [projectId, sprintId, token]);

  const handleExecuteAll = async () => {
    if (!sprintId || !token) return;
    setIsExecutingAll(true);
    setExecutionMessage(null);
    try {
      const res = await fetch(`http://localhost:8000/api/sprints/${sprintId}/execute-all`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setExecutionMessage({
          type: "success",
          text: `Eksekusi Runtime API selesai! ${data.tasks_executed} task berhasil dikerjakan dengan pemeriksaan mutu dan review silang.`,
        });
        fetchStatus();
        if (onRefreshKanban) onRefreshKanban();
      } else {
        const err = await res.json();
        setExecutionMessage({
          type: "error",
          text: err.detail || "Gagal menjalankan eksekusi agen.",
        });
      }
    } catch (exc: any) {
      setExecutionMessage({ type: "error", text: String(exc) });
    } finally {
      setIsExecutingAll(false);
    }
  };

  const handleIncreaseBudget = async () => {
    if (!projectId || !token) return;
    setIsSavingBudget(true);
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${projectId}/increase-budget`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          additional_budget: additionalAmount,
          sprint_id: sprintId || null,
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setBudget(updated);
        setIsIncreaseOpen(false);
        setExecutionMessage({
          type: "success",
          text: `Anggaran berhasil ditambah sebesar Rp ${additionalAmount.toLocaleString("id-ID")}. Eksekusi dilanjutkan!`,
        });
        if (onRefreshKanban) onRefreshKanban();
      }
    } catch {
      // Ignore
    } finally {
      setIsSavingBudget(false);
    }
  };

  const getStateBadge = (state: string) => {
    switch (state) {
      case "thinking":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 animate-pulse">
            <Zap className="w-2.5 h-2.5" /> Berpikir
          </span>
        );
      case "executing_tool":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 animate-pulse">
            <Activity className="w-2.5 h-2.5" /> Eksekusi Alat
          </span>
        );
      case "writing_artifact":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 animate-pulse">
            <Bot className="w-2.5 h-2.5" /> Menyusun Artefak
          </span>
        );
      case "in_review":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
            <ShieldAlert className="w-2.5 h-2.5" /> Review Silang
          </span>
        );
      case "revising":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300 animate-pulse">
            <RefreshCw className="w-2.5 h-2.5" /> Revisi Otomatis (1x)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            Siap Bekerja
          </span>
        );
    }
  };

  const getBudgetColor = () => {
    if (!budget) return "bg-emerald-500";
    if (budget.percent_used >= 100) return "bg-red-500";
    if (budget.percent_used >= 80) return "bg-amber-500";
    if (budget.percent_used >= 50) return "bg-yellow-500";
    return "bg-emerald-500";
  };

  return (
    <div className="space-y-4">
      {/* Execution feedback banner */}
      {executionMessage && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
            executionMessage.type === "success"
              ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200"
              : "bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-900 dark:text-red-200"
          }`}
        >
          <span>{executionMessage.text}</span>
          <button onClick={() => setExecutionMessage(null)} className="font-bold ml-4">
            ✕
          </button>
        </div>
      )}

      {/* Grid: Active Agents (Left) + Budget Guard (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Panel Agen Sekarang (2 cols) */}
        <div className="lg:col-span-2 p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              <h2 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                Panel Agen Sekarang (Observabilitas Real-time FR-11.4)
              </h2>
            </div>
            {sprintId && userRole !== "viewer" && (
              <button
                onClick={handleExecuteAll}
                disabled={isExecutingAll || (budget?.is_paused ?? false)}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                <Play className="w-3 h-3" />
                {isExecutingAll ? "Agen Sedang Mengerjakan..." : "Jalankan Runtime API Agen"}
              </button>
            )}
          </div>

          {agents.length === 0 ? (
            <div className="p-6 rounded-lg bg-slate-50 dark:bg-slate-900/40 border border-dashed border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500">
              Saat ini tidak ada agen yang sedang aktif di loop eksekusi. Klik <strong>&quot;Jalankan Runtime API Agen&quot;</strong> untuk menugaskan tim secara nyata.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {agents.map((ag) => (
                <div
                  key={ag.agent_id}
                  className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-bold text-xs text-slate-900 dark:text-white">
                        {ag.agent_name}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        {ag.role_name}
                      </div>
                    </div>
                    {getStateBadge(ag.state)}
                  </div>
                  <div className="text-[11px] text-slate-700 dark:text-slate-300 line-clamp-1">
                    🎯 {ag.pbi_title}
                  </div>
                  {ag.current_tool && (
                    <div className="text-[10px] font-mono text-purple-600 dark:text-purple-400">
                      Alat: {ag.current_tool}
                    </div>
                  )}
                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-200 dark:border-slate-800">
                    <span>{ag.tokens_used.toLocaleString()} token</span>
                    <span>Rp {ag.cost_spent.toLocaleString("id-ID")}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Budget Guard (1 col) */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <h2 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                Penjaga Anggaran (Budget Guard)
              </h2>
            </div>
            {userRole !== "viewer" && (
              <button
                onClick={() => setIsIncreaseOpen(true)}
                className="px-2 py-1 rounded text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 transition-colors flex items-center gap-1"
              >
                <Plus className="w-3 h-3" /> Tambah
              </button>
            )}
          </div>

          {budget ? (
            <div className="space-y-3">
              <div className="flex items-baseline justify-between">
                <span className="text-xl font-extrabold text-slate-900 dark:text-white">
                  Rp {budget.total_spent.toLocaleString("id-ID", { maximumFractionDigits: 0 })}
                </span>
                <span className="text-xs text-slate-500">
                  / Rp {budget.project_budget.toLocaleString("id-ID", { maximumFractionDigits: 0 })}
                </span>
              </div>

              {/* Progress bar */}
              <div className="space-y-1">
                <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${getBudgetColor()}`}
                    style={{ width: `${Math.min(100, budget.percent_used)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                  <span>{budget.percent_used.toFixed(1)}% Terpakai</span>
                  <span>Batas Kritis: 100%</span>
                </div>
              </div>

              {/* Warning box if active */}
              {budget.status !== "normal" && (
                <div
                  className={`p-2.5 rounded-lg border text-[11px] flex items-start gap-2 ${
                    budget.status === "exceeded_100"
                      ? "bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-900 dark:text-red-200 font-semibold"
                      : "bg-amber-50 dark:bg-amber-950/40 border-amber-300 dark:border-amber-800 text-amber-900 dark:text-amber-200"
                  }`}
                >
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    {budget.status === "exceeded_100" && (
                      <div className="font-bold uppercase text-[10px] tracking-wider mb-0.5">
                        [EKSEKUSI DIJEDA (100% LIMIT)]
                      </div>
                    )}
                    {budget.warning_message}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-xs text-slate-400">Memuat status anggaran...</div>
          )}
        </div>
      </div>

      {/* Increase Budget Modal */}
      {isIncreaseOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-5 max-w-sm w-full space-y-4 border border-slate-200 dark:border-slate-800 shadow-xl">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">
              Tambah Pagu Anggaran Proyek
            </h3>
            <p className="text-xs text-slate-500">
              Masukkan nominal tambahan anggaran untuk membuka kembali jeda eksekusi dan memberikan ruang token bagi agen.
            </p>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Nominal Tambahan (Rp)
              </label>
              <input
                type="number"
                value={additionalAmount}
                onChange={(e) => setAdditionalAmount(Number(e.target.value))}
                step={1000000}
                min={100000}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 font-bold"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setIsIncreaseOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-semibold"
              >
                Batal
              </button>
              <button
                onClick={handleIncreaseBudget}
                disabled={isSavingBudget}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold"
              >
                {isSavingBudget ? "Menyimpan..." : "Simpan Anggaran"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

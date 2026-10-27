"use client";

import React, { useState, useEffect } from "react";
import {
  Award,
  BookOpen,
  Check,
  CheckCircle2,
  Clock,
  EyeOff,
  Filter,
  GraduationCap,
  Layers,
  Plus,
  RefreshCw,
  Scale,
  Shield,
  Trash2,
} from "lucide-react";

interface LessonItem {
  id: string;
  layer: string;
  scope: string;
  content: string;
  evidence: string;
  status: "suggested" | "active" | "inactive";
  occurrence_count: number;
  project_id?: string;
  created_at: string;
  updated_at: string;
}

interface ModelScorecardItem {
  id: string;
  model_id?: string;
  model_name: string;
  role_name: string;
  profile_id: string;
  item_count: number;
  accepted_count: number;
  rejected_count: number;
  success_rate: number;
  avg_revisions: number;
  avg_cost: number;
}

interface CalibrationItem {
  profile_id: string;
  factor: number;
  status: string;
}

interface Props {
  token: string;
  userRole: string;
  projects: any[];
}

export default function LearningEnginePanel({ token, userRole }: Props) {
  const [lessons, setLessons] = useState<LessonItem[]>([]);
  const [scorecards, setScorecards] = useState<ModelScorecardItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [subTab, setSubTab] = useState<"lessons" | "scorecards">("lessons");
  const [isLoading, setIsLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // New Lesson Modal
  const [isNewOpen, setIsNewOpen] = useState(false);
  const [newContent, setNewContent] = useState("");
  const [newScope, setNewScope] = useState("global");
  const [newLayer, setNewLayer] = useState("preference");

  const loadData = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      // 1. Fetch lessons
      const lRes = await fetch("http://localhost:8000/api/learning/lessons", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (lRes.ok) {
        const lData = await lRes.json();
        setLessons(lData);
      }

      // 2. Fetch scorecards
      const sRes = await fetch("http://localhost:8000/api/learning/scorecards", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (sRes.ok) {
        const sData = await sRes.json();
        setScorecards(sData);
      }
    } catch {
      // Ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleApprove = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/learning/lessons/${id}/approve`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setActionMessage({ type: "success", text: "Aturan/pelajaran disetujui dan kini aktif disuntikkan ke prompt agen!" });
        loadData();
      }
    } catch {
      setActionMessage({ type: "error", text: "Gagal menyetujui pelajaran." });
    }
  };

  const handleDeactivate = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/learning/lessons/${id}/deactivate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setActionMessage({ type: "success", text: "Pelajaran dinonaktifkan." });
        loadData();
      }
    } catch {
      setActionMessage({ type: "error", text: "Gagal menonaktifkan pelajaran." });
    }
  };

  const handleActivate = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/learning/lessons/${id}/activate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setActionMessage({ type: "success", text: "Pelajaran diaktifkan kembali." });
        loadData();
      }
    } catch {
      setActionMessage({ type: "error", text: "Gagal mengaktifkan pelajaran." });
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/learning/lessons/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setActionMessage({ type: "success", text: "Pelajaran berhasil dihapus." });
        loadData();
      }
    } catch {
      setActionMessage({ type: "error", text: "Gagal menghapus pelajaran." });
    }
  };

  const handleCreate = async () => {
    if (!newContent.trim()) return;
    try {
      const res = await fetch("http://localhost:8000/api/learning/lessons", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: newContent,
          scope: newScope,
          layer: newLayer,
        }),
      });
      if (res.ok) {
        setIsNewOpen(false);
        setNewContent("");
        setActionMessage({ type: "success", text: "Pelajaran baru berhasil dicatat sebagai usulan." });
        loadData();
      }
    } catch {
      setActionMessage({ type: "error", text: "Gagal menambah pelajaran." });
    }
  };

  const filteredLessons = lessons.filter((l) => {
    if (statusFilter === "all") return true;
    return l.status === statusFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 mb-2">
            <GraduationCap className="w-3.5 h-3.5" />
            Learning Engine: Pembelajaran Berkelanjutan (FR-14)
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Yang Dipelajari Sistem
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            <strong>Prinsip Kejujuran:</strong> Bobot model tidak diubah; pembelajaran terjadi di tingkat sistem (memori preferensi PO, rapor kinerja per peran, kalibrasi estimasi) dan sepenuhnya terkendali oleh PO.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {userRole !== "viewer" && (
            <button
              onClick={() => setIsNewOpen(true)}
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" /> Tambah Aturan/Preferensi
            </button>
          )}
          <button
            onClick={loadData}
            disabled={isLoading}
            className="p-1.5 rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Action Notification */}
      {actionMessage && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
            actionMessage.type === "success"
              ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200"
              : "bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-900 dark:text-red-200"
          }`}
        >
          <span>{actionMessage.text}</span>
          <button onClick={() => setActionMessage(null)} className="font-bold ml-4">
            ✕
          </button>
        </div>
      )}

      {/* Tabs Switcher: Pelajaran vs Rapor Model */}
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSubTab("lessons")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              subTab === "lessons"
                ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" /> Aturan & Memori Preferensi ({lessons.length})
          </button>
          <button
            onClick={() => setSubTab("scorecards")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              subTab === "scorecards"
                ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <Award className="w-3.5 h-3.5" /> Rapor Kinerja Model ({scorecards.length})
          </button>
        </div>

        {subTab === "lessons" && (
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-medium"
            >
              <option value="all">Semua Status</option>
              <option value="active">Disetujui / Aktif</option>
              <option value="suggested">Usulan Baru</option>
              <option value="inactive">Nonaktif</option>
            </select>
          </div>
        )}
      </div>

      {/* Subtab 1: Lessons */}
      {subTab === "lessons" && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800 text-slate-500 font-medium">
                <tr>
                  <th className="px-4 py-3">Pelajaran / Preferensi</th>
                  <th className="px-4 py-3">Lapisan</th>
                  <th className="px-4 py-3">Cakupan (Scope)</th>
                  <th className="px-4 py-3">Kemunculan</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Kendali PO</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-850">
                {filteredLessons.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                      Belum ada aturan atau pelajaran yang terekam pada filter ini.
                    </td>
                  </tr>
                ) : (
                  filteredLessons.map((l) => (
                    <tr key={l.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900 dark:text-slate-100 mb-0.5">
                          {l.content}
                        </div>
                        {l.evidence && (
                          <div className="text-[10px] text-slate-500 italic">
                            Bukti: {l.evidence}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                          {l.layer}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                          {l.scope}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">
                        {l.occurrence_count}x
                      </td>
                      <td className="px-4 py-3">
                        {l.status === "active" ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                            <CheckCircle2 className="w-2.5 h-2.5" /> Disetujui (Aktif)
                          </span>
                        ) : l.status === "suggested" ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                            <Clock className="w-2.5 h-2.5" /> Usulan Baru
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                            <EyeOff className="w-2.5 h-2.5" /> Nonaktif
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {userRole !== "viewer" && (
                          <div className="flex items-center justify-end gap-1.5">
                            {l.status === "suggested" && (
                              <button
                                onClick={() => handleApprove(l.id)}
                                className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-semibold transition-colors flex items-center gap-1"
                              >
                                <Check className="w-3 h-3" /> Setujui
                              </button>
                            )}
                            {l.status === "active" && (
                              <button
                                onClick={() => handleDeactivate(l.id)}
                                className="px-2.5 py-1 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-100 text-[11px] font-semibold transition-colors"
                              >
                                Nonaktifkan
                              </button>
                            )}
                            {l.status === "inactive" && (
                              <button
                                onClick={() => handleActivate(l.id)}
                                className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] font-semibold transition-colors"
                              >
                                Aktifkan
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(l.id)}
                              className="p-1 rounded text-red-500 hover:bg-red-50 dark:hover:bg-red-950/40 transition-colors"
                              title="Hapus"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Subtab 2: Model Scorecards */}
      {subTab === "scorecards" && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800 text-slate-500 font-medium">
                <tr>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3">Peran</th>
                  <th className="px-4 py-3">Profil</th>
                  <th className="px-4 py-3">Total PBI</th>
                  <th className="px-4 py-3">Diterima / Ditolak</th>
                  <th className="px-4 py-3">Tingkat Keberhasilan</th>
                  <th className="px-4 py-3">Rata-rata Revisi</th>
                  <th className="px-4 py-3">Rata-rata Biaya</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-850">
                {scorecards.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                      Belum ada data eksekusi PBI untuk menyusun rapor model. Data akan terisi otomatis saat Sprint Review (G3) diselesaikan.
                    </td>
                  </tr>
                ) : (
                  scorecards.map((sc) => (
                    <tr key={sc.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                      <td className="px-4 py-3 font-bold text-slate-900 dark:text-white">
                        {sc.model_name}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-slate-600 dark:text-slate-400">
                        {sc.role_name}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 uppercase">
                          {sc.profile_id}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-semibold">{sc.item_count}</td>
                      <td className="px-4 py-3">
                        <span className="text-emerald-600 font-bold">{sc.accepted_count}</span>
                        {" / "}
                        <span className="text-red-500 font-bold">{sc.rejected_count}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-emerald-500 h-1.5 rounded-full"
                              style={{ width: `${sc.success_rate}%` }}
                            />
                          </div>
                          <span className="font-bold text-[11px]">{sc.success_rate}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-500">{sc.avg_revisions.toFixed(1)}x</td>
                      <td className="px-4 py-3 font-mono text-[11px] text-slate-500">
                        ${sc.avg_cost.toFixed(4)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* New Lesson Modal */}
      {isNewOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-5 max-w-md w-full space-y-4 border border-slate-200 dark:border-slate-800 shadow-xl">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">
              Tambah Aturan / Preferensi PO Baru
            </h3>
            <p className="text-xs text-slate-500">
              Aturan ini akan disimpan sebagai usulan yang bisa Anda setujui agar disuntikkan secara otomatis ke prompt agen.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Isi Aturan / Preferensi
              </label>
              <textarea
                rows={3}
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="Misal: 'Gunakan gaya sitasi APA 7 dan hindari kata transisi klise'..."
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Cakupan (Scope)
                </label>
                <select
                  value={newScope}
                  onChange={(e) => setNewScope(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                >
                  <option value="global">Global (Semua Proyek)</option>
                  <option value="proposal">Profil Proposal</option>
                  <option value="jurnal">Profil Jurnal</option>
                  <option value="software">Profil Software</option>
                  <option value="iot">Profil IoT</option>
                  <option value="buku">Profil Buku</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Lapisan Belajar
                </label>
                <select
                  value={newLayer}
                  onChange={(e) => setNewLayer(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                >
                  <option value="preference">Preferensi PO</option>
                  <option value="retro">Retrospektif</option>
                  <option value="role">Peran & Prompt</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setIsNewOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-semibold"
              >
                Batal
              </button>
              <button
                onClick={handleCreate}
                disabled={!newContent.trim()}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold disabled:opacity-50"
              >
                Simpan Usulan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

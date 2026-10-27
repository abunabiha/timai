"use client";

import React, { useState, useEffect } from "react";
import { useI18n } from "@/lib/i18n";
import { useTheme } from "@/lib/theme";
import {
  Moon,
  Sun,
  Globe,
  PlusCircle,
  Layers,
  CheckSquare,
  MessageSquare,
  BookOpen,
  Settings,
  ShieldCheck,
  User as UserIcon,
  LogOut,
  Lock,
  Mail,
  Cpu,
  Server,
  Activity,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: "admin" | "po" | "viewer";
}

interface ProjectItem {
  id: string;
  title: string;
  profile_id: string;
  brief: string;
  status: string;
  budget: number;
  currency: string;
}

interface ProviderItem {
  id: string;
  name: string;
  provider_type: string;
  base_url?: string;
  is_active: boolean;
  has_api_key: boolean;
  api_key_masked: string;
  created_at: string;
}

interface ModelItem {
  id: string;
  provider_id: string;
  name: string;
  model_identifier: string;
  context_window: number;
  input_price: number;
  output_price: number;
  supports_tools: boolean;
  supports_vision: boolean;
  competency_score: number;
  tier: string;
  is_active: boolean;
  created_at: string;
}

export default function HomePage() {
  const { t, locale, setLocale } = useI18n();
  const { theme, toggleTheme } = useTheme();

  const [isLoading, setIsLoading] = useState(true);
  const [isSetup, setIsSetup] = useState<boolean | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"dashboard" | "settings">("dashboard");

  // Providers and Models
  const [providers, setProviders] = useState<ProviderItem[]>([]);
  const [models, setModels] = useState<ModelItem[]>([]);
  const [providerTestResults, setProviderTestResults] = useState<Record<string, { success: boolean; message: string; latency?: number }>>({});
  const [modelHealthResults, setModelHealthResults] = useState<Record<string, { is_healthy: boolean; message: string }>>({});

  // Form states for Setup / Login
  const [adminName, setAdminName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form states for Provider
  const [provName, setProvName] = useState("");
  const [provType, setProvType] = useState("fake");
  const [provApiKey, setProvApiKey] = useState("");
  const [provBaseUrl, setProvBaseUrl] = useState("");
  const [isAddingProv, setIsAddingProv] = useState(false);

  // Form states for Model
  const [modProvId, setModProvId] = useState("");
  const [modName, setModName] = useState("");
  const [modIdentifier, setModIdentifier] = useState("");
  const [modTier, setModTier] = useState("medium");
  const [modScore, setModScore] = useState(4.0);
  const [modInputPrice, setModInputPrice] = useState(0.001);
  const [modOutputPrice, setModOutputPrice] = useState(0.002);
  const [isAddingModel, setIsAddingModel] = useState(false);

  // Check setup status and existing token
  useEffect(() => {
    async function checkAuthAndSetup() {
      setIsLoading(true);
      try {
        const res = await fetch("http://localhost:8000/api/auth/setup-status");
        if (res.ok) {
          const data = await res.json();
          setIsSetup(data.is_setup);
        } else {
          setIsSetup(false);
        }
      } catch {
        setIsSetup(false);
      }

      const savedToken = localStorage.getItem("timai_token");
      if (savedToken) {
        try {
          const meRes = await fetch("http://localhost:8000/api/auth/me", {
            headers: { Authorization: `Bearer ${savedToken}` },
          });
          if (meRes.ok) {
            const userData = await meRes.json();
            setUser(userData);
            setToken(savedToken);
            loadProjects(savedToken);
            loadProvidersAndModels(savedToken);
          } else {
            localStorage.removeItem("timai_token");
          }
        } catch {
          // Keep offline state
        }
      }
      setIsLoading(false);
    }

    checkAuthAndSetup();
  }, []);

  const loadProjects = async (authToken: string) => {
    try {
      const res = await fetch("http://localhost:8000/api/projects", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch {
      // Ignored
    }
  };

  const loadProvidersAndModels = async (authToken: string) => {
    try {
      const provRes = await fetch("http://localhost:8000/api/providers", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (provRes.ok) {
        const pData = await provRes.json();
        setProviders(pData);
        if (pData.length > 0 && !modProvId) {
          setModProvId(pData[0].id);
        }
      }

      const modRes = await fetch("http://localhost:8000/api/models", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (modRes.ok) {
        const mData = await modRes.json();
        setModels(mData);
      }
    } catch {
      // Ignored
    }
  };

  const handleSetupAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setIsSubmitting(true);
    try {
      const res = await fetch("http://localhost:8000/api/auth/setup-admin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: adminName, email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("timai_token", data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        setIsSetup(true);
        loadProvidersAndModels(data.access_token);
      } else {
        const err = await res.json();
        setErrorMsg(err.detail || "Setup failed");
      }
    } catch {
      setErrorMsg("Network error connecting to API server");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setIsSubmitting(true);
    try {
      const res = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("timai_token", data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        loadProjects(data.access_token);
        loadProvidersAndModels(data.access_token);
      } else {
        setErrorMsg(t.invalidCredentials);
      }
    } catch {
      setErrorMsg("Network error connecting to API server");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("timai_token");
    setToken(null);
    setUser(null);
    setProjects([]);
  };

  const handleCreateProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setIsAddingProv(true);
    try {
      const res = await fetch("http://localhost:8000/api/providers", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: provName,
          provider_type: provType,
          api_key: provApiKey,
          base_url: provBaseUrl || null,
        }),
      });
      if (res.ok) {
        setProvName("");
        setProvApiKey("");
        setProvBaseUrl("");
        loadProvidersAndModels(token);
      }
    } catch {
      // Ignored
    } finally {
      setIsAddingProv(false);
    }
  };

  const handleTestProvider = async (providerId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`http://localhost:8000/api/providers/${providerId}/test`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setProviderTestResults((prev) => ({
        ...prev,
        [providerId]: {
          success: data.success,
          message: data.message,
          latency: data.latency_ms,
        },
      }));
    } catch {
      setProviderTestResults((prev) => ({
        ...prev,
        [providerId]: {
          success: false,
          message: "Failed to reach backend test endpoint",
        },
      }));
    }
  };

  const handleCreateModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !modProvId) return;
    setIsAddingModel(true);
    try {
      const res = await fetch("http://localhost:8000/api/models", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          provider_id: modProvId,
          name: modName,
          model_identifier: modIdentifier,
          tier: modTier,
          competency_score: Number(modScore),
          input_price: Number(modInputPrice),
          output_price: Number(modOutputPrice),
        }),
      });
      if (res.ok) {
        setModName("");
        setModIdentifier("");
        loadProvidersAndModels(token);
      }
    } catch {
      // Ignored
    } finally {
      setIsAddingModel(false);
    }
  };

  const handleHealthCheckModel = async (modelId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`http://localhost:8000/api/models/${modelId}/health-check`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setModelHealthResults((prev) => ({
        ...prev,
        [modelId]: {
          is_healthy: data.is_healthy,
          message: data.message,
        },
      }));
    } catch {
      setModelHealthResults((prev) => ({
        ...prev,
        [modelId]: {
          is_healthy: false,
          message: "Failed to perform health check",
        },
      }));
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors">
      {/* Top Header */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              T
            </div>
            <div>
              <span className="font-bold text-xl tracking-tight text-slate-900 dark:text-white">
                {t.appName}
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs font-medium text-slate-500 dark:text-slate-400">
                v1.0 (Scrum AI)
              </span>
            </div>
          </div>

          {user && (
            <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
              <span
                onClick={() => setActiveTab("dashboard")}
                className={`cursor-pointer flex items-center gap-1.5 transition-colors ${
                  activeTab === "dashboard"
                    ? "text-indigo-600 dark:text-indigo-400 font-semibold"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <Layers className="w-4 h-4" /> {t.dashboard}
              </span>
              <span className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer flex items-center gap-1.5">
                <CheckSquare className="w-4 h-4" /> {t.confirmations}
              </span>
              <span className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer flex items-center gap-1.5">
                <MessageSquare className="w-4 h-4" /> {t.teamRoom}
              </span>
              <span className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer flex items-center gap-1.5">
                <BookOpen className="w-4 h-4" /> {t.systemLearning}
              </span>
              {user.role === "admin" && (
                <span
                  onClick={() => setActiveTab("settings")}
                  className={`cursor-pointer flex items-center gap-1.5 transition-colors ${
                    activeTab === "settings"
                      ? "text-indigo-600 dark:text-indigo-400 font-semibold"
                      : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  <Settings className="w-4 h-4" /> {t.settings}
                </span>
              )}
            </nav>
          )}

          <div className="flex items-center space-x-3">
            {/* User badge if logged in */}
            {user && (
              <div className="flex items-center gap-2 pr-2 border-r border-slate-200 dark:border-slate-800">
                <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs font-semibold">
                  <UserIcon className="w-4 h-4 text-slate-600 dark:text-slate-300" />
                </div>
                <div className="hidden sm:block text-left text-xs leading-tight">
                  <p className="font-semibold text-slate-800 dark:text-slate-200">{user.name}</p>
                  <span className="inline-block px-1.5 py-0.2 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                    {user.role}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors ml-1"
                  title={t.logoutButton}
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Language Switcher */}
            <button
              onClick={() => setLocale(locale === "id" ? "en" : "id")}
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 flex items-center gap-1 text-xs font-semibold"
              title={t.switchLang}
            >
              <Globe className="w-4 h-4" />
              <span>{locale.toUpperCase()}</span>
            </button>

            {/* Dark/Light Mode Switcher */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
              title={t.switchTheme}
            >
              {theme === "dark" ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col justify-start">
        {isLoading ? (
          <div className="text-center py-20 text-slate-400">Loading TimAI...</div>
        ) : !user ? (
          // AUTH & WIZARD SCREEN
          <div className="max-w-md w-full mx-auto space-y-6 my-auto">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-indigo-600 flex items-center justify-center text-white font-bold text-2xl shadow-md">
                T
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {isSetup ? t.loginTitle : t.setupAdminTitle}
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                {isSetup ? t.loginSubtitle : t.setupAdminSubtitle}
              </p>
            </div>

            {errorMsg && (
              <div className="p-3 text-xs rounded-lg bg-red-50 dark:bg-red-950/60 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-300 text-center">
                {errorMsg}
              </div>
            )}

            {!isSetup ? (
              // First-run Admin Wizard Form
              <form onSubmit={handleSetupAdmin} className="p-6 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-4">
                <div className="flex items-center gap-2 p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 text-xs font-medium">
                  <ShieldCheck className="w-4 h-4 shrink-0" />
                  <span>{t.setupAdminSubtitle}</span>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    {t.nameLabel}
                  </label>
                  <input
                    type="text"
                    required
                    value={adminName}
                    onChange={(e) => setAdminName(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Administrator"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    {t.emailLabel}
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="admin@example.com"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    {t.passwordLabel}
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="••••••••"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
                >
                  {isSubmitting ? "..." : t.setupButton}
                </button>
              </form>
            ) : (
              // Login Form
              <form onSubmit={handleLogin} className="p-6 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    {t.emailLabel}
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="user@example.com"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    {t.passwordLabel}
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
                >
                  {isSubmitting ? "..." : t.loginButton}
                </button>
              </form>
            )}
          </div>
        ) : activeTab === "settings" && user.role === "admin" ? (
          // ADMIN SETTINGS: PROVIDERS & MODEL CATALOG
          <div className="space-y-10">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                <Settings className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                {t.modelsAndProviders}
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Kelola kredensial penyedia model LLM (tersimpan dengan enkripsi AES-256-GCM) dan katalog model.
              </p>
            </div>

            {/* Providers Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <Server className="w-5 h-5 text-indigo-500" />
                  {t.providersTitle}
                </h2>
              </div>

              {/* Add Provider Form */}
              <form onSubmit={handleCreateProvider} className="p-4 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    {t.providerName}
                  </label>
                  <input
                    type="text"
                    required
                    value={provName}
                    onChange={(e) => setProvName(e.target.value)}
                    placeholder="e.g. OpenAI Main"
                    className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    {t.providerType}
                  </label>
                  <select
                    value={provType}
                    onChange={(e) => setProvType(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                  >
                    <option value="fake">Fake Provider (Test/Simulation)</option>
                    <option value="openai">OpenAI Compatible</option>
                    <option value="anthropic">Anthropic Claude</option>
                    <option value="google">Google Gemini</option>
                    <option value="openrouter">OpenRouter</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    {t.apiKey}
                  </label>
                  <input
                    type="password"
                    value={provApiKey}
                    onChange={(e) => setProvApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isAddingProv}
                  className="py-1.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium transition-colors"
                >
                  {isAddingProv ? "..." : t.addProvider}
                </button>
              </form>

              {/* Providers Table */}
              <div className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800 text-slate-500 font-medium">
                    <tr>
                      <th className="px-4 py-3">Penyedia</th>
                      <th className="px-4 py-3">Tipe</th>
                      <th className="px-4 py-3">Kunci Masked</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-850">
                    {providers.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                          Belum ada penyedia terdaftar. Silakan tambahkan Fake Provider atau penyedia LLM Anda.
                        </td>
                      </tr>
                    ) : (
                      providers.map((p) => {
                        const testInfo = providerTestResults[p.id];
                        return (
                          <tr key={p.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                            <td className="px-4 py-3 font-semibold text-slate-800 dark:text-slate-200">{p.name}</td>
                            <td className="px-4 py-3 font-mono text-[11px] uppercase text-indigo-600 dark:text-indigo-400">{p.provider_type}</td>
                            <td className="px-4 py-3 font-mono text-slate-500">{p.api_key_masked}</td>
                            <td className="px-4 py-3">
                              {testInfo ? (
                                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium ${
                                  testInfo.success ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
                                }`}>
                                  {testInfo.success ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                                  {testInfo.success ? `Connected (${testInfo.latency}ms)` : "Failed"}
                                </span>
                              ) : (
                                <span className="text-[10px] text-slate-400">Ready</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <button
                                onClick={() => handleTestProvider(p.id)}
                                className="px-2.5 py-1 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-[11px] font-medium transition-colors"
                              >
                                {t.testConnection}
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Model Catalog Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-indigo-500" />
                  {t.modelsCatalog}
                </h2>
              </div>

              {/* Add Model Form */}
              <form onSubmit={handleCreateModel} className="p-4 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm grid grid-cols-1 md:grid-cols-6 gap-3 items-end">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Penyedia</label>
                  <select
                    value={modProvId}
                    onChange={(e) => setModProvId(e.target.value)}
                    required
                    className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                  >
                    <option value="" disabled>Pilih Penyedia</option>
                    {providers.map((p) => (
                      <option key={p.id} value={p.id}>{p.name} ({p.provider_type})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{t.modelName}</label>
                  <input
                    type="text"
                    required
                    value={modName}
                    onChange={(e) => setModName(e.target.value)}
                    placeholder="e.g. GPT-4o Mini"
                    className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{t.modelIdentifier}</label>
                  <input
                    type="text"
                    required
                    value={modIdentifier}
                    onChange={(e) => setModIdentifier(e.target.value)}
                    placeholder="e.g. gpt-4o-mini"
                    className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{t.tier}</label>
                  <select
                    value={modTier}
                    onChange={(e) => setModTier(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                  >
                    <option value="low">Low (Hemat)</option>
                    <option value="medium">Medium (Standar)</option>
                    <option value="high">High (Cerdas)</option>
                    <option value="xhigh">XHigh (Terbaik)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{t.competencyScore}</label>
                  <input
                    type="number"
                    step="0.1"
                    min="1.0"
                    max="5.0"
                    value={modScore}
                    onChange={(e) => setModScore(parseFloat(e.target.value))}
                    className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isAddingModel || !modProvId}
                  className="py-1.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {isAddingModel ? "..." : t.addModel}
                </button>
              </form>

              {/* Model Catalog Table */}
              <div className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800 text-slate-500 font-medium">
                    <tr>
                      <th className="px-4 py-3">Nama Model</th>
                      <th className="px-4 py-3">Identifier</th>
                      <th className="px-4 py-3">Tier</th>
                      <th className="px-4 py-3">Kompetensi</th>
                      <th className="px-4 py-3">Konteks</th>
                      <th className="px-4 py-3">Health</th>
                      <th className="px-4 py-3 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-850">
                    {models.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-6 text-center text-slate-400">
                          Belum ada model dalam katalog. Silakan tambahkan model di atas.
                        </td>
                      </tr>
                    ) : (
                      models.map((m) => {
                        const hInfo = modelHealthResults[m.id];
                        return (
                          <tr key={m.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                            <td className="px-4 py-3 font-semibold text-slate-800 dark:text-slate-200">{m.name}</td>
                            <td className="px-4 py-3 font-mono text-[11px] text-slate-500">{m.model_identifier}</td>
                            <td className="px-4 py-3">
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                                {m.tier}
                              </span>
                            </td>
                            <td className="px-4 py-3 font-medium text-amber-600 dark:text-amber-400">{m.competency_score.toFixed(1)} / 5.0</td>
                            <td className="px-4 py-3 text-slate-500">{m.context_window.toLocaleString()} tok</td>
                            <td className="px-4 py-3">
                              {hInfo ? (
                                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium ${
                                  hInfo.is_healthy ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
                                }`}>
                                  <Activity className="w-3 h-3" />
                                  {hInfo.is_healthy ? "Healthy" : "Failed"}
                                </span>
                              ) : (
                                <span className="text-[10px] text-slate-400">Untested</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <button
                                onClick={() => handleHealthCheckModel(m.id)}
                                className="px-2.5 py-1 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-[11px] font-medium transition-colors"
                              >
                                {t.healthCheck}
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          // LOGGED IN DASHBOARD
          <div className="text-center max-w-2xl mx-auto space-y-4 my-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
              {t.loggedInAs} <strong className="uppercase">{user.role}</strong> ({user.name})
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              {t.welcomeTitle}
            </h1>
            <p className="text-base text-slate-600 dark:text-slate-300 leading-relaxed">
              {t.welcomeSubtitle}
            </p>

            <div className="pt-8">
              {projects.length === 0 ? (
                <div className="p-8 border-2 border-dashed border-slate-300 dark:border-slate-800 rounded-2xl bg-white/50 dark:bg-slate-950/40 space-y-4">
                  <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center text-slate-400">
                    <Layers className="w-6 h-6" />
                  </div>
                  <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
                    {t.emptyStateTitle}
                  </h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                    {t.emptyStateDesc}
                  </p>
                  {user.role !== "viewer" && (
                    <div className="pt-2">
                      <button className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-colors">
                        <PlusCircle className="w-4 h-4" />
                        {t.createProject}
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 text-left">
                  {projects.map((p) => (
                    <div
                      key={p.id}
                      className="p-5 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm space-y-2 hover:border-indigo-500 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 uppercase">
                          {p.profile_id}
                        </span>
                        <span className="text-xs text-indigo-600 dark:text-indigo-400 font-medium capitalize">
                          {p.status}
                        </span>
                      </div>
                      <h3 className="font-semibold text-base text-slate-900 dark:text-white">
                        {p.title}
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                        {p.brief}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-6 text-center text-xs text-slate-500 dark:text-slate-400">
        <p>TimAI &copy; 2026 &bull; {t.tagline}</p>
      </footer>
    </div>
  );
}

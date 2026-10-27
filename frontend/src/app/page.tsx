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
  ArrowRight,
  Sparkles,
  FileText,
  Shield,
  Play,
  Check,
  Clock,
  Compass,
  Download,
  ArrowUp,
  ArrowDown,
  RefreshCw,
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
  workspace_path?: string;
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

interface ClarificationQ {
  id: string;
  question: string;
  answer?: string;
  is_skipped?: boolean;
}

interface TeamAgent {
  role_id: string;
  role_name: string;
  role_version: number;
  tier: string;
  runtime: string;
  model_id?: string;
  model_name?: string;
  fallback_model_id?: string;
  fallback_model_name?: string;
  is_reviewer: boolean;
  reason: string;
}

interface ConfirmationItem {
  id: string;
  discussion_id: string;
  options: any[];
  selected_option?: string;
  po_feedback?: string;
  created_at: string;
  discussion?: {
    agenda: string;
    round_number: number;
    synthesis?: any;
    project?: {
      id: string;
      title: string;
    };
  };
}

interface ContributionItem {
  id: string;
  agent_id?: string;
  round_number: number;
  content: string;
  token_count: number;
  created_at: string;
}

interface DiscussionItem {
  id: string;
  project_id: string;
  agenda: string;
  round_number: number;
  status: string;
  synthesis?: any;
  cost: number;
  contributions: ContributionItem[];
  confirmations: ConfirmationItem[];
}

interface DecisionItem {
  id: string;
  project_id: string;
  summary: string;
  rationale: string;
  alternatives: any[];
  decided_by: string;
  created_at: string;
}

interface InceptionAgenda {
  agenda_number: string;
  title: string;
  description: string;
  lead_role: string;
  expected_output: string;
  discussion_id?: string;
  is_completed: boolean;
  selected_option?: string;
}

interface InceptionStatus {
  project_id: string;
  profile_id: string;
  agendas: InceptionAgenda[];
  is_ready_for_assembly: boolean;
  has_assembled: boolean;
  gate_g2_status?: string;
}

interface InceptionDoc {
  version: number;
  content: string;
  status: string;
  product_goal: string;
  gate_g2?: {
    decision: string;
    comments: string;
    decided_at?: string;
  };
}

interface BacklogItem {
  id: string;
  epic_id?: string;
  project_id: string;
  title: string;
  item_type: string;
  acceptance_criteria: string[];
  story_points: number;
  po_sort_order: number;
  status: string;
  source: string;
  is_po_task: boolean;
}

interface EpicWithItems {
  id: string;
  title: string;
  sort_order: number;
  items: BacklogItem[];
}

interface SprintItem {
  id: string;
  project_id: string;
  sprint_number: number;
  sprint_goal: string;
  start_date?: string;
  end_date?: string;
  budget_limit: number;
  status: string;
  velocity_achieved: number;
  created_at: string;
}

interface BurndownItem {
  day: string;
  ideal: number;
  actual: number;
}

interface BurndownData {
  sprint_number: number;
  total_planned_points: number;
  completed_points: number;
  remaining_points: number;
  velocity_achieved: number;
  burndown: BurndownItem[];
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
  const [activeTab, setActiveTab] = useState<"dashboard" | "settings" | "confirmations" | "teamRoom" | "inception" | "kanban">("dashboard");

  // Providers & Models
  const [providers, setProviders] = useState<ProviderItem[]>([]);
  const [models, setModels] = useState<ModelItem[]>([]);
  const [providerTestResults, setProviderTestResults] = useState<Record<string, { success: boolean; message: string; latency?: number }>>({});
  const [modelHealthResults, setModelHealthResults] = useState<Record<string, { is_healthy: boolean; message: string }>>({});

  // Auth Form
  const [adminName, setAdminName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Provider Form
  const [provName, setProvName] = useState("");
  const [provType, setProvType] = useState("fake");
  const [provApiKey, setProvApiKey] = useState("");
  const [provBaseUrl, setProvBaseUrl] = useState("");
  const [isAddingProv, setIsAddingProv] = useState(false);

  // Model Form
  const [modProvId, setModProvId] = useState("");
  const [modName, setModName] = useState("");
  const [modIdentifier, setModIdentifier] = useState("");
  const [modTier, setModTier] = useState("medium");
  const [modScore, setModScore] = useState(4.0);
  const [modInputPrice, setModInputPrice] = useState(0.001);
  const [modOutputPrice, setModOutputPrice] = useState(0.002);
  const [isAddingModel, setIsAddingModel] = useState(false);

  // Project Creation Wizard
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState<1 | 2 | 3 | 4>(1);
  const [currentProjId, setCurrentProjId] = useState<string>("");

  // Step 1: Brief
  const [pTitle, setPTitle] = useState("");
  const [pProfile, setPProfile] = useState("proposal");
  const [pBrief, setPBrief] = useState("");
  const [pBudget, setPBudget] = useState(50000000);
  const [pScheme, setPScheme] = useState("Fundamental");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Step 2: Clarification
  const [clarifyQuestions, setClarifyQuestions] = useState<ClarificationQ[]>([]);

  // Step 3: Team Composer
  const [proposedAgents, setProposedAgents] = useState<TeamAgent[]>([]);
  const [costRange, setCostRange] = useState<any>(null);
  const [durationRange, setDurationRange] = useState<any>(null);
  const [teamWarnings, setTeamWarnings] = useState<string[]>([]);
  const [hasReviewer, setHasReviewer] = useState(true);

  // Step 4: Approved Team
  const [approvedResult, setApprovedResult] = useState<any>(null);

  // Kotak Konfirmasi (Pending Confirmations)
  const [pendingConfirmations, setPendingConfirmations] = useState<ConfirmationItem[]>([]);
  const [poDirectionInputs, setPoDirectionInputs] = useState<Record<string, string>>({});

  // Ruang Tim (Team Room)
  const [selectedRoomProjId, setSelectedRoomProjId] = useState<string>("");
  const [roomDiscussions, setRoomDiscussions] = useState<DiscussionItem[]>([]);
  const [activeDiscussion, setActiveDiscussion] = useState<DiscussionItem | null>(null);
  const [newAgendaTitle, setNewAgendaTitle] = useState("");
  const [projectDecisions, setProjectDecisions] = useState<DecisionItem[]>([]);
  const [isRunningRound, setIsRunningRound] = useState(false);

  // Inception & G2 Gate
  const [selectedInceptionProjId, setSelectedInceptionProjId] = useState<string>("");
  const [inceptionStatus, setInceptionStatus] = useState<InceptionStatus | null>(null);
  const [inceptionDoc, setInceptionDoc] = useState<InceptionDoc | null>(null);
  const [backlogEpics, setBacklogEpics] = useState<EpicWithItems[]>([]);
  const [inceptionSubTab, setInceptionSubTab] = useState<"doc" | "backlog">("doc");
  const [isAssembling, setIsAssembling] = useState(false);
  const [poG2Comments, setPoG2Comments] = useState("");
  const [g2Message, setG2Message] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Sprint & Kanban
  const [selectedKanbanProjId, setSelectedKanbanProjId] = useState<string>("");
  const [projectSprints, setProjectSprints] = useState<SprintItem[]>([]);
  const [activeSprint, setActiveSprint] = useState<SprintItem | null>(null);
  const [kanbanCols, setKanbanCols] = useState<Record<string, BacklogItem[]>>({
    product_backlog: [],
    sprint_backlog: [],
    in_progress: [],
    in_review: [],
    waiting_po: [],
    done: [],
    blocked: [],
  });
  const [burndown, setBurndown] = useState<BurndownData | null>(null);
  const [isSimulatingWork, setIsSimulatingWork] = useState(false);
  const [dailyStandupResult, setDailyStandupResult] = useState<any>(null);
  const [pbiReviewDecisions, setPbiReviewDecisions] = useState<Record<string, { decision: "accept" | "reject"; notes: string }>>({});
  const [scrumMessage, setScrumMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [newPlanGoal, setNewPlanGoal] = useState("");

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
            loadConfirmations(savedToken);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadProjects = async (authToken: string) => {
    try {
      const res = await fetch("http://localhost:8000/api/projects", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        if (data.length > 0 && !selectedRoomProjId) {
          setSelectedRoomProjId(data[0].id);
          loadRoomData(data[0].id, authToken);
        }
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

  const loadConfirmations = async (authToken: string) => {
    try {
      const res = await fetch("http://localhost:8000/api/confirmations", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPendingConfirmations(data);
      }
    } catch {
      // Ignored
    }
  };

  const loadRoomData = async (projId: string, authToken: string) => {
    try {
      const decRes = await fetch(`http://localhost:8000/api/confirmations/projects/${projId}/decisions`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (decRes.ok) {
        const decData = await decRes.json();
        setProjectDecisions(decData);
      }
    } catch {
      // Ignored
    }
  };

  const loadInceptionData = async (projId: string, authToken: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/inceptions/projects/${projId}/status`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setInceptionStatus(data);
        if (data.has_assembled) {
          loadInceptionDoc(projId, authToken);
          loadInceptionBacklog(projId, authToken);
        } else {
          setInceptionDoc(null);
          setBacklogEpics([]);
        }
      }
    } catch {
      // Ignored
    }
  };

  const loadInceptionDoc = async (projId: string, authToken: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/inceptions/projects/${projId}/document`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setInceptionDoc(data);
      }
    } catch {
      // Ignored
    }
  };

  const loadInceptionBacklog = async (projId: string, authToken: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/inceptions/projects/${projId}/backlog`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setBacklogEpics(data);
      }
    } catch {
      // Ignored
    }
  };

  const handleInitInception = async (projId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`http://localhost:8000/api/inceptions/projects/${projId}/init`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        loadInceptionData(projId, token);
      }
    } catch {
      // Ignored
    }
  };

  const handleAssembleInception = async (projId: string) => {
    if (!token) return;
    setIsAssembling(true);
    try {
      const res = await fetch(`http://localhost:8000/api/inceptions/projects/${projId}/assemble`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        await loadInceptionData(projId, token);
        setInceptionSubTab("doc");
      }
    } finally {
      setIsAssembling(false);
    }
  };

  const handleDecideG2 = async (projId: string, decision: "approved" | "revision_requested" | "rejected") => {
    if (!token) return;
    setG2Message(null);
    try {
      const res = await fetch(`http://localhost:8000/api/inceptions/projects/${projId}/g2`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ decision, comments: poG2Comments }),
      });
      if (res.ok) {
        setG2Message({
          type: "success",
          text: decision === "approved"
            ? "Gerbang G2 berhasil disetujui! Proyek siap melangkah ke Sprint Planning."
            : decision === "revision_requested"
            ? "Permintaan revisi dikirim kembali ke tim. Putaran revisi telah disiapkan di Ruang Tim."
            : "Proyek dibatalkan.",
        });
        loadInceptionData(projId, token);
      } else {
        const err = await res.json();
        setG2Message({ type: "error", text: err.detail || "Gagal memproses keputusan G2." });
      }
    } catch {
      setG2Message({ type: "error", text: "Terjadi kesalahan jaringan." });
    }
  };

  const handleMoveBacklogItem = async (itemId: string, direction: "up" | "down") => {
    if (!token || !selectedInceptionProjId) return;
    const allItems = backlogEpics.flatMap((e) => e.items);
    const index = allItems.findIndex((it) => it.id === itemId);
    if (index === -1) return;
    if (direction === "up" && index === 0) return;
    if (direction === "down" && index === allItems.length - 1) return;

    const targetIndex = direction === "up" ? index - 1 : index + 1;
    const reordered = [...allItems];
    const [moved] = reordered.splice(index, 1);
    reordered.splice(targetIndex, 0, moved);

    try {
      const res = await fetch(`http://localhost:8000/api/inceptions/projects/${selectedInceptionProjId}/backlog/reorder`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ ordered_item_ids: reordered.map((it) => it.id) }),
      });
      if (res.ok) {
        loadInceptionBacklog(selectedInceptionProjId, token);
      }
    } catch {
      // Ignored
    }
  };

  const loadKanbanData = async (projId: string, authToken: string) => {
    try {
      const sprintsRes = await fetch(`http://localhost:8000/api/projects/${projId}/sprints`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (sprintsRes.ok) {
        const sData = await sprintsRes.json();
        setProjectSprints(sData);
        const act = sData.find((s: any) => s.status === "active" || s.status === "review" || s.status === "paused") || sData[sData.length - 1];
        setActiveSprint(act || null);
        if (act) {
          loadBurndown(act.id, authToken);
        }
      }

      const kRes = await fetch(`http://localhost:8000/api/projects/${projId}/kanban`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (kRes.ok) {
        const kData = await kRes.json();
        setKanbanCols(kData.columns);
      }
    } catch {
      // Ignored
    }
  };

  const loadBurndown = async (sprintId: string, authToken: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/sprints/${sprintId}/burndown`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const bData = await res.json();
        setBurndown(bData);
      }
    } catch {
      // Ignored
    }
  };

  const handlePlanSprint = async (projId: string) => {
    if (!token) return;
    try {
      const nextNumber = projectSprints.length + 1;
      const res = await fetch(`http://localhost:8000/api/projects/${projId}/sprints/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          sprint_number: nextNumber,
          sprint_goal: newPlanGoal || undefined,
        }),
      });
      if (res.ok) {
        setNewPlanGoal("");
        setScrumMessage({ type: "success", text: `Sprint ${nextNumber} berhasil direncanakan dan diaktifkan!` });
        loadKanbanData(projId, token);
      } else {
        const err = await res.json();
        setScrumMessage({ type: "error", text: err.detail || "Gagal merencanakan sprint." });
      }
    } catch {
      setScrumMessage({ type: "error", text: "Terjadi kesalahan jaringan." });
    }
  };

  const handleSimulateSprint = async (sprintId: string) => {
    if (!token) return;
    setIsSimulatingWork(true);
    try {
      const res = await fetch(`http://localhost:8000/api/sprints/${sprintId}/simulate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setScrumMessage({ type: "success", text: "Eksekusi simulasi selesai. PBI kini berada pada status Review untuk peninjauan PO (G3)." });
        loadKanbanData(selectedKanbanProjId, token);
      }
    } finally {
      setIsSimulatingWork(false);
    }
  };

  const handleDailyStandup = async (sprintId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`http://localhost:8000/api/sprints/${sprintId}/daily`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDailyStandupResult(data);
        setScrumMessage({ type: "success", text: `Laporan Daily Standup tanggal ${data.date} berhasil diterbitkan di workspace.` });
      }
    } catch {
      // Ignored
    }
  };

  const handleSprintReviewG3 = async (sprintId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`http://localhost:8000/api/sprints/${sprintId}/review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ decisions: pbiReviewDecisions }),
      });
      if (res.ok) {
        const data = await res.json();
        setScrumMessage({
          type: "success",
          text: `Sprint Review G3 selesai: ${data.accepted_count} PBI diterima (${data.velocity_achieved} poin velocity), ${data.rejected_count} PBI ditolak dan kembali ke Backlog.`,
        });
        loadKanbanData(selectedKanbanProjId, token);
      }
    } catch {
      // Ignored
    }
  };

  const handleSprintRetro = async (sprintId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`http://localhost:8000/api/sprints/${sprintId}/retro`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ action_item: "Perkuat koordinasi antar-agen sebelum draf diserahkan." }),
      });
      if (res.ok) {
        setScrumMessage({ type: "success", text: "Retrospektif selesai! Catatan dan usulan pelajaran telah dicatat." });
        loadKanbanData(selectedKanbanProjId, token);
      }
    } catch {
      // Ignored
    }
  };

  const handleSprintControl = async (sprintId: string, action: "pause" | "resume" | "cancel") => {
    if (!token) return;
    try {
      const res = await fetch(`http://localhost:8000/api/sprints/${sprintId}/${action}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setScrumMessage({ type: "success", text: `Sprint berhasil di-${action}.` });
        loadKanbanData(selectedKanbanProjId, token);
      }
    } catch {
      // Ignored
    }
  };

  const handleMoveKanbanCard = async (itemId: string, newStatus: string) => {
    if (!token) return;
    try {
      const res = await fetch(`http://localhost:8000/api/backlog/${itemId}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        loadKanbanData(selectedKanbanProjId, token);
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
        loadConfirmations(data.access_token);
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

  // Brief creation
  const handleCreateBrief = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setIsSubmitting(true);
    setErrorMsg("");
    try {
      const res = await fetch("http://localhost:8000/api/projects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: pTitle,
          profile_id: pProfile,
          brief: pBrief,
          budget: Number(pBudget),
          currency: "IDR",
          profile_fields: { scheme: pScheme },
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        setErrorMsg(err.detail || "Gagal membuat proyek");
        setIsSubmitting(false);
        return;
      }

      const proj = await res.json();
      setCurrentProjId(proj.id);

      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        await fetch(`http://localhost:8000/api/projects/${proj.id}/attachments`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
      }

      const clarRes = await fetch(`http://localhost:8000/api/projects/${proj.id}/clarify`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (clarRes.ok) {
        const questions = await clarRes.json();
        setClarifyQuestions(questions.map((q: any) => ({ ...q, answer: "", is_skipped: false })));
        setWizardStep(2);
      }
    } catch {
      setErrorMsg("Gagal menghubungi server");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit clarification
  const handleSubmitClarification = async () => {
    if (!token || !currentProjId) return;
    setIsSubmitting(true);
    try {
      await fetch(`http://localhost:8000/api/projects/${currentProjId}/clarify/answers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          answers: clarifyQuestions.map((q) => ({
            id: q.id,
            question: q.question,
            answer: q.answer || "",
            is_skipped: q.is_skipped || false,
          })),
        }),
      });

      const compRes = await fetch(`http://localhost:8000/api/projects/${currentProjId}/compose-team?package=balanced`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (compRes.ok) {
        const teamData = await compRes.json();
        setProposedAgents(teamData.agents);
        setCostRange(teamData.cost_range);
        setDurationRange(teamData.duration_range);
        setHasReviewer(teamData.has_reviewer);
        setTeamWarnings(teamData.warnings);
        setWizardStep(3);
      }
    } catch {
      setErrorMsg("Gagal memproses klarifikasi");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Dynamic recalculation
  const handleAgentTierOrModelChange = async (index: number, field: "tier" | "model_id", value: string) => {
    const updated = [...proposedAgents];
    updated[index] = { ...updated[index], [field]: value };
    setProposedAgents(updated);

    if (!token || !currentProjId) return;
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${currentProjId}/recalculate-estimate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          agents: updated,
          size: "M",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setCostRange(data.cost_range);
        setDurationRange(data.duration_range);
        setHasReviewer(data.has_reviewer);
        setTeamWarnings(data.warnings);
      }
    } catch {
      // Ignored
    }
  };

  // Approve G1
  const handleApproveTeamG1 = async () => {
    if (!token || !currentProjId) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${currentProjId}/approve-team`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          agents: proposedAgents,
          clarification_notes: "Klarifikasi dan asumsi telah disetujui bersama.",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setApprovedResult(data);
        setWizardStep(4);
        loadProjects(token);
      }
    } catch {
      setErrorMsg("Gagal menyetujui tim");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Decision point actions
  const handleDecide = async (
    confId: string,
    action: "approve_proposed" | "choose_option" | "redirect" | "continue_discussion",
    selectedOption?: string,
  ) => {
    if (!token) return;
    const poNotes = poDirectionInputs[confId] || "";
    try {
      const res = await fetch(`http://localhost:8000/api/confirmations/${confId}/decide`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          action,
          selected_option: selectedOption,
          po_notes: poNotes,
        }),
      });
      if (res.ok) {
        loadConfirmations(token);
        if (selectedRoomProjId) {
          loadRoomData(selectedRoomProjId, token);
        }
      }
    } catch {
      // Ignored
    }
  };

  const handleBatchApprove = async () => {
    if (!token || pendingConfirmations.length === 0) return;
    try {
      const decisions = pendingConfirmations.map((c) => ({
        confirmation_id: c.id,
        action: "approve_proposed",
      }));
      const res = await fetch("http://localhost:8000/api/confirmations/batch-decide", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ decisions }),
      });
      if (res.ok) {
        loadConfirmations(token);
        if (selectedRoomProjId) {
          loadRoomData(selectedRoomProjId, token);
        }
      }
    } catch {
      // Ignored
    }
  };

  // Ruang Tim actions
  const handleCreateNewDiscussion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedRoomProjId || !newAgendaTitle.trim()) return;
    try {
      const res = await fetch("http://localhost:8000/api/discussions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          project_id: selectedRoomProjId,
          agenda: newAgendaTitle,
          discussion_type: "inception",
        }),
      });
      if (res.ok) {
        const disc = await res.json();
        setActiveDiscussion(disc);
        setNewAgendaTitle("");
      }
    } catch {
      // Ignored
    }
  };

  const handleRunSingleRound = async (discId: string) => {
    if (!token) return;
    setIsRunningRound(true);
    try {
      const res = await fetch(`http://localhost:8000/api/discussions/${discId}/start`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const disc = await res.json();
        setActiveDiscussion(disc);
        loadConfirmations(token);
      }
    } catch {
      // Ignored
    } finally {
      setIsRunningRound(false);
    }
  };

  // Settings Handlers
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
                onClick={() => { setActiveTab("dashboard"); setIsWizardOpen(false); }}
                className={`cursor-pointer flex items-center gap-1.5 transition-colors ${
                  activeTab === "dashboard" && !isWizardOpen
                    ? "text-indigo-600 dark:text-indigo-400 font-semibold"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <Layers className="w-4 h-4" /> {t.dashboard}
              </span>
              <span
                onClick={() => { setActiveTab("confirmations"); setIsWizardOpen(false); loadConfirmations(token!); }}
                className={`cursor-pointer flex items-center gap-1.5 transition-colors ${
                  activeTab === "confirmations"
                    ? "text-indigo-600 dark:text-indigo-400 font-semibold"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <CheckSquare className="w-4 h-4" /> {t.confirmations}
                {pendingConfirmations.length > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-500 text-white">
                    {pendingConfirmations.length}
                  </span>
                )}
              </span>
              <span
                onClick={() => { setActiveTab("teamRoom"); setIsWizardOpen(false); }}
                className={`cursor-pointer flex items-center gap-1.5 transition-colors ${
                  activeTab === "teamRoom"
                    ? "text-indigo-600 dark:text-indigo-400 font-semibold"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <MessageSquare className="w-4 h-4" /> {t.teamRoom}
              </span>
              <span
                onClick={() => {
                  setActiveTab("inception");
                  setIsWizardOpen(false);
                  if (projects.length > 0) {
                    const targetId = selectedInceptionProjId || projects[0].id;
                    setSelectedInceptionProjId(targetId);
                    loadInceptionData(targetId, token!);
                  }
                }}
                className={`cursor-pointer flex items-center gap-1.5 transition-colors ${
                  activeTab === "inception"
                    ? "text-indigo-600 dark:text-indigo-400 font-semibold"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <Compass className="w-4 h-4" /> {t.inceptionTab}
              </span>
              <span
                onClick={() => {
                  setActiveTab("kanban");
                  setIsWizardOpen(false);
                  if (projects.length > 0) {
                    const targetId = selectedKanbanProjId || projects[0].id;
                    setSelectedKanbanProjId(targetId);
                    loadKanbanData(targetId, token!);
                  }
                }}
                className={`cursor-pointer flex items-center gap-1.5 transition-colors ${
                  activeTab === "kanban"
                    ? "text-indigo-600 dark:text-indigo-400 font-semibold"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <Layers className="w-4 h-4" /> {t.kanbanTab}
              </span>
              <span className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer flex items-center gap-1.5">
                <BookOpen className="w-4 h-4" /> {t.systemLearning}
              </span>
              {user.role === "admin" && (
                <span
                  onClick={() => { setActiveTab("settings"); setIsWizardOpen(false); }}
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

            <button
              onClick={() => setLocale(locale === "id" ? "en" : "id")}
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 flex items-center gap-1 text-xs font-semibold"
              title={t.switchLang}
            >
              <Globe className="w-4 h-4" />
              <span>{locale.toUpperCase()}</span>
            </button>

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
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col justify-start">
        {isLoading ? (
          <div className="text-center py-20 text-slate-400">Loading TimAI...</div>
        ) : !user ? (
          // ==================== AUTH & LOGIN ====================
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
              <div className="p-3 text-xs rounded-lg bg-red-50 dark:bg-red-950/60 border border-red-200 text-red-600 text-center">
                {errorMsg}
              </div>
            )}

            {!isSetup ? (
              <form onSubmit={handleSetupAdmin} className="p-6 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-4">
                <div className="flex items-center gap-2 p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 text-xs font-medium">
                  <ShieldCheck className="w-4 h-4 shrink-0" />
                  <span>{t.setupAdminSubtitle}</span>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t.nameLabel}</label>
                  <input
                    type="text"
                    required
                    value={adminName}
                    onChange={(e) => setAdminName(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                    placeholder="Administrator"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t.emailLabel}</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                    placeholder="admin@example.com"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t.passwordLabel}</label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
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
              <form onSubmit={handleLogin} className="p-6 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t.emailLabel}</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                      placeholder="user@example.com"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t.passwordLabel}</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
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
        ) : isWizardOpen ? (
          // ==================== PROJECT CREATION & TEAM COMPOSER WIZARD ====================
          <div className="max-w-4xl w-full mx-auto space-y-6">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
              <div className="flex items-center space-x-2 sm:space-x-4 text-xs font-semibold">
                <span className={`px-3 py-1 rounded-full ${wizardStep === 1 ? "bg-indigo-600 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-500"}`}>
                  {t.stepBrief}
                </span>
                <span className={`px-3 py-1 rounded-full ${wizardStep === 2 ? "bg-indigo-600 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-500"}`}>
                  {t.stepClarification}
                </span>
                <span className={`px-3 py-1 rounded-full ${wizardStep === 3 ? "bg-indigo-600 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-500"}`}>
                  {t.stepTeam}
                </span>
                <span className={`px-3 py-1 rounded-full ${wizardStep === 4 ? "bg-emerald-600 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-500"}`}>
                  {t.stepDone}
                </span>
              </div>
              <button
                onClick={() => setIsWizardOpen(false)}
                className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                Batal
              </button>
            </div>

            {errorMsg && (
              <div className="p-3 text-xs rounded-lg bg-red-50 dark:bg-red-950/60 border border-red-200 text-red-600">
                {errorMsg}
              </div>
            )}

            {wizardStep === 1 && (
              <form onSubmit={handleCreateBrief} className="p-6 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-4">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-500" />
                  Formulir Intake Brief Proyek
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t.projectTitle}</label>
                    <input
                      type="text"
                      required
                      value={pTitle}
                      onChange={(e) => setPTitle(e.target.value)}
                      placeholder="e.g. Proposal Hibah Deteksi Hama AI"
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t.selectProfile}</label>
                    <select
                      value={pProfile}
                      onChange={(e) => setPProfile(e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                    >
                      <option value="proposal">Proposal Penelitian (Hibah / Riset)</option>
                      <option value="jurnal">Artikel Jurnal Ilmiah (IMRaD)</option>
                      <option value="software">Software Development</option>
                      <option value="iot">Internet of Things (IoT)</option>
                      <option value="buku">Buku / Book Chapter</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Brief Proyek & Kriteria Sukses</label>
                  <textarea
                    required
                    rows={4}
                    value={pBrief}
                    onChange={(e) => setPBrief(e.target.value)}
                    placeholder="Jelaskan tujuan penelitian/pengembangan, latar belakang, metodologi, dan luaran target..."
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t.budget} (IDR)</label>
                    <input
                      type="number"
                      value={pBudget}
                      onChange={(e) => setPBudget(Number(e.target.value))}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      {pProfile === "proposal" ? "Skema Hibah" : pProfile === "jurnal" ? "Target Jurnal / Indeks" : "Spesifikasi Domain"}
                    </label>
                    <input
                      type="text"
                      value={pScheme}
                      onChange={(e) => setPScheme(e.target.value)}
                      placeholder="e.g. Fundamental Reguler Bima"
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">{t.uploadAttachment}</label>
                  <input
                    type="file"
                    accept=".pdf,.docx,.csv,.bib,.ris,.txt"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                  />
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? "Menganalisis..." : t.nextStep}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </form>
            )}

            {wizardStep === 2 && (
              <div className="p-6 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-indigo-500" />
                    Wawancara Klarifikasi oleh Agen Analis
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Agen Analis mengidentifikasi beberapa pertanyaan penting untuk memastikan tim dibentuk dengan akurat.
                  </p>
                </div>

                <div className="space-y-4">
                  {clarifyQuestions.map((q, idx) => (
                    <div key={q.id} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 space-y-2">
                      <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                        {idx + 1}. {q.question}
                      </p>
                      <input
                        type="text"
                        disabled={q.is_skipped}
                        value={q.answer}
                        onChange={(e) => {
                          const updated = [...clarifyQuestions];
                          updated[idx].answer = e.target.value;
                          setClarifyQuestions(updated);
                        }}
                        placeholder="Ketik jawaban Anda di sini..."
                        className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 disabled:opacity-40"
                      />
                      <label className="flex items-center gap-2 text-[11px] text-slate-500 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={q.is_skipped}
                          onChange={(e) => {
                            const updated = [...clarifyQuestions];
                            updated[idx].is_skipped = e.target.checked;
                            setClarifyQuestions(updated);
                          }}
                        />
                        {t.skipAsAssumption}
                      </label>
                    </div>
                  ))}
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={handleSubmitClarification}
                    disabled={isSubmitting}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? "Menyusun Tim..." : "Rancang Tim AI"}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {wizardStep === 3 && (
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <Cpu className="w-5 h-5 text-indigo-500" />
                      Rekomendasi Tim Agen AI (Team Composer)
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Ubah peran, tier, atau model agen. Estimasi biaya dan durasi diperbarui seketika.
                    </p>
                  </div>

                  {costRange && (
                    <div className="flex items-center gap-4 bg-indigo-50 dark:bg-indigo-950/50 p-3 rounded-xl border border-indigo-200 dark:border-indigo-800 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-500 block uppercase font-bold">{t.costRange}</span>
                        <span className="font-semibold text-indigo-700 dark:text-indigo-300">
                          {costRange.min_idr.toLocaleString()} – {costRange.max_idr.toLocaleString()} IDR
                        </span>
                      </div>
                      <div className="border-l border-indigo-200 dark:border-indigo-800 pl-4">
                        <span className="text-[10px] text-slate-500 block uppercase font-bold">{t.durationRange}</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          {durationRange?.label || "1–2 minggu"}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {teamWarnings.length > 0 && (
                  <div className="space-y-1">
                    {teamWarnings.map((w, i) => (
                      <div key={i} className="p-3 text-xs rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200 text-amber-800 dark:text-amber-300 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="grid gap-3 sm:grid-cols-2">
                  {proposedAgents.map((agent, idx) => (
                    <div key={idx} className="p-4 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm space-y-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="font-bold text-sm text-slate-900 dark:text-white block">{agent.role_name}</span>
                          <span className="text-[10px] font-mono text-slate-400">ID: {agent.role_id} &bull; Runtime: {agent.runtime}</span>
                        </div>
                        {agent.is_reviewer && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-200">
                            <Shield className="w-3 h-3" />
                            {t.reviewerBadge}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-500 dark:text-slate-400">{agent.reason}</p>

                      <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100 dark:border-slate-850">
                        <div>
                          <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">Tier</label>
                          <select
                            value={agent.tier}
                            onChange={(e) => handleAgentTierOrModelChange(idx, "tier", e.target.value)}
                            className="w-full px-2 py-1 text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 uppercase font-bold text-indigo-600 dark:text-indigo-400"
                          >
                            <option value="low">LOW</option>
                            <option value="medium">MEDIUM</option>
                            <option value="high">HIGH</option>
                            <option value="xhigh">XHIGH</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">Model</label>
                          <select
                            value={agent.model_id || ""}
                            onChange={(e) => handleAgentTierOrModelChange(idx, "model_id", e.target.value)}
                            className="w-full px-2 py-1 text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 truncate"
                          >
                            {models.map((m) => (
                              <option key={m.id} value={m.id}>{m.name} ({m.tier})</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="pt-4 flex justify-between items-center border-t border-slate-200 dark:border-slate-800">
                  <button
                    onClick={() => setWizardStep(2)}
                    className="px-4 py-2 text-xs font-semibold text-slate-500 hover:text-slate-800"
                  >
                    Kembali
                  </button>

                  <button
                    onClick={handleApproveTeamG1}
                    disabled={isSubmitting}
                    className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-colors shadow-md disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    {isSubmitting ? "Menginisialisasi Workspace..." : t.approveTeamG1}
                  </button>
                </div>
              </div>
            )}

            {wizardStep === 4 && (
              <div className="p-6 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm text-center space-y-4">
                <div className="w-12 h-12 mx-auto rounded-full bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center text-emerald-600">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                  Gerbang G1 Berhasil Disetujui!
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 max-w-lg mx-auto">
                  Tim agen sebanyak {approvedResult?.agent_count} anggota telah dibentuk. Workspace Git proyek telah diinisialisasi dan dokumen <code>team-charter.md</code> berhasil diterbitkan.
                </p>

                {approvedResult?.workspace_path && (
                  <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-xl font-mono text-xs text-slate-600 dark:text-slate-300 max-w-xl mx-auto break-all">
                    Workspace: {approvedResult.workspace_path}
                  </div>
                )}

                <div className="pt-4">
                  <button
                    onClick={() => { setIsWizardOpen(false); setWizardStep(1); }}
                    className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors"
                  >
                    Kembali ke Dashboard
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : activeTab === "confirmations" ? (
          // ==================== KOTAK KONFIRMASI (CONFIRMATION BOX) ====================
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                  <CheckSquare className="w-6 h-6 text-indigo-500" />
                  {t.pendingConfirmations}
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Daftar Titik Konfirmasi Scrum yang memerlukan persetujuan Product Owner sebelum tim dapat melanjutkan.
                </p>
              </div>

              {pendingConfirmations.length > 1 && (
                <button
                  onClick={handleBatchApprove}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors shrink-0"
                >
                  <Check className="w-4 h-4" />
                  {t.batchApprove} ({pendingConfirmations.length})
                </button>
              )}
            </div>

            {pendingConfirmations.length === 0 ? (
              <div className="p-12 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-950 text-center space-y-3">
                <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
                <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">
                  {t.noPendingConfirmations}
                </h3>
              </div>
            ) : (
              <div className="space-y-4">
                {pendingConfirmations.map((conf) => {
                  const synthesis = conf.discussion?.synthesis || {};
                  return (
                    <div key={conf.id} className="p-6 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300">
                          Menunggu Konfirmasi PO
                        </span>
                        <span className="text-xs text-slate-400">Putaran ke-{conf.discussion?.round_number || 1}</span>
                      </div>

                      <div>
                        <h3 className="font-bold text-lg text-slate-900 dark:text-white">
                          Agenda: {conf.discussion?.agenda || "Diskusi Tim"}
                        </h3>
                      </div>

                      {/* Synthesis Card */}
                      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 space-y-3 text-xs">
                        <div>
                          <span className="font-bold text-slate-600 dark:text-slate-400 uppercase text-[10px] block">Usulan Scrum Master</span>
                          <p className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                            {synthesis.proposed_decision || "Melanjutkan agenda dengan pendekatan standar."}
                          </p>
                        </div>

                        {synthesis.agreed_points && (
                          <div>
                            <span className="font-bold text-slate-600 dark:text-slate-400 uppercase text-[10px] block">Poin Disepakati</span>
                            <ul className="list-disc pl-4 mt-0.5 text-slate-600 dark:text-slate-300 space-y-0.5">
                              {synthesis.agreed_points.map((pt: string, i: number) => (
                                <li key={i}>{pt}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {synthesis.disagreements && (
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                            <div className="p-2.5 rounded-lg border border-indigo-200 dark:border-indigo-900 bg-indigo-50/50 dark:bg-indigo-950/20">
                              <strong className="text-indigo-700 dark:text-indigo-300 block mb-1">Opsi A:</strong>
                              <span>{synthesis.disagreements.option_a || conf.options[0]?.label}</span>
                            </div>
                            <div className="p-2.5 rounded-lg border border-purple-200 dark:border-purple-900 bg-purple-50/50 dark:bg-purple-950/20">
                              <strong className="text-purple-700 dark:text-purple-300 block mb-1">Opsi B:</strong>
                              <span>{synthesis.disagreements.option_b || conf.options[1]?.label}</span>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* PO Guidance Input */}
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1">
                          Catatan / Arahan PO (Opsional bila lanjut diskusi atau ubah arah):
                        </label>
                        <input
                          type="text"
                          value={poDirectionInputs[conf.id] || ""}
                          onChange={(e) => setPoDirectionInputs({ ...poDirectionInputs, [conf.id]: e.target.value })}
                          placeholder="Ketik arahan spesifik untuk tim..."
                          className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                        />
                      </div>

                      {/* Decision Buttons */}
                      <div className="pt-2 flex flex-wrap gap-2 items-center justify-end">
                        <button
                          onClick={() => handleDecide(conf.id, "choose_option", "A")}
                          className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-colors"
                        >
                          {t.optionA}
                        </button>
                        <button
                          onClick={() => handleDecide(conf.id, "choose_option", "B")}
                          className="px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold transition-colors"
                        >
                          {t.optionB}
                        </button>
                        <button
                          onClick={() => handleDecide(conf.id, "approve_proposed")}
                          className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-colors"
                        >
                          {t.approveProposed}
                        </button>
                        <button
                          onClick={() => handleDecide(conf.id, "continue_discussion")}
                          className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-medium transition-colors"
                        >
                          {t.continueDiscussion}
                        </button>
                        <button
                          onClick={() => handleDecide(conf.id, "redirect")}
                          className="px-3 py-1.5 rounded-lg border border-amber-300 dark:border-amber-800 hover:bg-amber-50 dark:hover:bg-amber-950/40 text-amber-700 dark:text-amber-300 text-xs font-medium transition-colors"
                        >
                          {t.redirect}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : activeTab === "teamRoom" ? (
          // ==================== RUANG TIM (TEAM ROOM) ====================
          <div className="space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                  <MessageSquare className="w-6 h-6 text-indigo-500" />
                  {t.teamRoom}
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  {t.singleRoundNotice}
                </p>
              </div>

              {/* Project selector dropdown */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Proyek:</span>
                <select
                  value={selectedRoomProjId}
                  onChange={(e) => {
                    setSelectedRoomProjId(e.target.value);
                    loadRoomData(e.target.value, token!);
                  }}
                  className="px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.title}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Start New Discussion Form */}
            <form onSubmit={handleCreateNewDiscussion} className="p-4 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm flex flex-col sm:flex-row items-end gap-3">
              <div className="flex-1 w-full">
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Topik Agenda Baru (Satu Putaran)
                </label>
                <input
                  type="text"
                  required
                  value={newAgendaTitle}
                  onChange={(e) => setNewAgendaTitle(e.target.value)}
                  placeholder="e.g. Pembahasan Metodologi Eksperimen dan Validasi Statistik"
                  className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                />
              </div>
              <button
                type="submit"
                disabled={!selectedRoomProjId}
                className="py-1.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium transition-colors shrink-0 disabled:opacity-50"
              >
                {t.startDiscussion}
              </button>
            </form>

            {/* Active Discussion View */}
            {activeDiscussion && (
              <div className="p-6 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase text-slate-400 block">Agenda Diskusi</span>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">{activeDiscussion.agenda}</h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 capitalize">
                      Status: {activeDiscussion.status}
                    </span>
                    {activeDiscussion.status === "draft" && (
                      <button
                        onClick={() => handleRunSingleRound(activeDiscussion.id)}
                        disabled={isRunningRound}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-colors disabled:opacity-50"
                      >
                        <Play className="w-3.5 h-3.5" />
                        {isRunningRound ? "Menjalankan Putaran..." : t.runRound}
                      </button>
                    )}
                  </div>
                </div>

                {/* Contributions list */}
                <div className="space-y-3 pt-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase block">Kontribusi Peserta:</span>
                  {activeDiscussion.contributions.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">Belum ada pembicara. Klik Jalankan Putaran untuk memulai diskusi satu putaran.</p>
                  ) : (
                    activeDiscussion.contributions.map((c, i) => (
                      <div key={c.id || i} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 space-y-1">
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span className="font-semibold text-indigo-600 dark:text-indigo-400">Pembicara ke-{i + 1}</span>
                          <span>{c.token_count} token</span>
                        </div>
                        <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">{c.content}</p>
                      </div>
                    ))
                  )}
                </div>

                {/* Synthesis view if available */}
                {activeDiscussion.synthesis && activeDiscussion.synthesis.proposed_decision && (
                  <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 space-y-2 text-xs">
                    <span className="font-bold text-indigo-700 dark:text-indigo-300 block">Sintesis Scrum Master:</span>
                    <p className="text-slate-800 dark:text-slate-200">{activeDiscussion.synthesis.proposed_decision}</p>
                  </div>
                )}
              </div>
            )}

            {/* Decision Log Table */}
            <div className="space-y-3">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Compass className="w-5 h-5 text-indigo-500" />
                {t.decisionLog}
              </h3>
              <div className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800 text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Waktu</th>
                      <th className="px-4 py-3">Keputusan</th>
                      <th className="px-4 py-3">Alasan PO</th>
                      <th className="px-4 py-3">Pemutus</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-850">
                    {projectDecisions.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                          Belum ada keputusan tercatat dalam Decision Log.
                        </td>
                      </tr>
                    ) : (
                      projectDecisions.map((d) => (
                        <tr key={d.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                          <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">
                            {new Date(d.created_at).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 font-semibold text-slate-800 dark:text-slate-200">{d.summary}</td>
                          <td className="px-4 py-3 text-slate-500">{d.rationale}</td>
                          <td className="px-4 py-3 text-slate-600">{d.decided_by}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : activeTab === "settings" && user.role === "admin" ? (
          // ==================== ADMIN SETTINGS ====================
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
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Server className="w-5 h-5 text-indigo-500" />
                {t.providersTitle}
              </h2>

              <form onSubmit={handleCreateProvider} className="p-4 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{t.providerName}</label>
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
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{t.providerType}</label>
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
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{t.apiKey}</label>
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
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Cpu className="w-5 h-5 text-indigo-500" />
                {t.modelsCatalog}
              </h2>

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
        ) : activeTab === "inception" ? (
          // ==================== INCEPTION & G2 GATE ====================
          <div className="space-y-6">
            {/* Header & Project Selector */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 mb-2">
                  <Compass className="w-3.5 h-3.5" />
                  Tahap 3: Inception (PRD / Rencana & Backlog)
                </div>
                <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                  Tinjau PRD, Rencana & Gerbang G2
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Dari diskusi agenda terstruktur menuju Product Goal, Epik, Backlog terukur, Definition of Done, dan persetujuan PO.
                </p>
              </div>

              {projects.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">Pilih Proyek:</span>
                  <select
                    value={selectedInceptionProjId}
                    onChange={(e) => {
                      const pid = e.target.value;
                      setSelectedInceptionProjId(pid);
                      if (token) loadInceptionData(pid, token);
                    }}
                    className="px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-medium"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.title} ({p.profile_id})
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Notification alert */}
            {g2Message && (
              <div
                className={`p-4 rounded-xl border flex items-center justify-between text-xs ${
                  g2Message.type === "success"
                    ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200"
                    : "bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-800 dark:text-red-200"
                }`}
              >
                <span>{g2Message.text}</span>
                <button onClick={() => setG2Message(null)} className="font-bold ml-4">
                  ✕
                </button>
              </div>
            )}

            {!selectedInceptionProjId ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                Silakan buat atau pilih proyek terlebih dahulu.
              </div>
            ) : (
              <div className="space-y-6">
                {/* Status Bar */}
                <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                      <Layers className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-800 dark:text-slate-200">
                          {projects.find((p) => p.id === selectedInceptionProjId)?.title}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                          {inceptionStatus?.profile_id || "proposal"}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">
                        Status Gerbang G2:{" "}
                        <strong
                          className={
                            inceptionStatus?.gate_g2_status === "approved"
                              ? "text-emerald-600 dark:text-emerald-400 font-semibold"
                              : inceptionStatus?.gate_g2_status === "revision_requested"
                              ? "text-amber-600 dark:text-amber-400 font-semibold"
                              : "text-slate-600 dark:text-slate-400"
                          }
                        >
                          {inceptionStatus?.gate_g2_status === "approved"
                            ? "Disetujui PO (Lanjut Sprint)"
                            : inceptionStatus?.gate_g2_status === "revision_requested"
                            ? "Revisi Diminta PO"
                            : "Menunggu Peninjauan PO"}
                        </strong>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {(!inceptionStatus || inceptionStatus.agendas.length === 0) ? (
                      <button
                        onClick={() => handleInitInception(selectedInceptionProjId)}
                        className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors"
                      >
                        Inisialisasi Agenda Inception
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAssembleInception(selectedInceptionProjId)}
                        disabled={isAssembling}
                        className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-50 flex items-center gap-1.5"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${isAssembling ? "animate-spin" : ""}`} />
                        {isAssembling ? "Merakit Dokumen..." : "Rakit Dokumen Inception"}
                      </button>
                    )}
                  </div>
                </div>

                {/* Section A: Inception Agendas */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                      Agenda Pembahasan Inception (1 Putaran + Keputusan PO)
                    </h2>
                    <span className="text-xs text-slate-500">
                      {inceptionStatus?.agendas.filter((a) => a.is_completed).length || 0} dari{" "}
                      {inceptionStatus?.agendas.length || 0} Selesai
                    </span>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {inceptionStatus?.agendas.map((ag) => (
                      <div
                        key={ag.agenda_number}
                        className={`p-4 rounded-xl border transition-all ${
                          ag.is_completed
                            ? "bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800"
                            : "bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                            Agenda {ag.agenda_number}
                          </span>
                          <span className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400">
                            {ag.lead_role}
                          </span>
                        </div>
                        <h3 className="font-semibold text-xs text-slate-800 dark:text-slate-100 mb-1">
                          {ag.title}
                        </h3>
                        <p className="text-[11px] text-slate-500 line-clamp-2 mb-3">
                          {ag.description}
                        </p>
                        <div className="pt-2 border-t border-slate-100 dark:border-slate-850 flex items-center justify-between">
                          {ag.is_completed ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Opsi {ag.selected_option} Terpilih
                            </span>
                          ) : (
                            <span className="text-[11px] font-medium text-slate-400">Belum diputuskan</span>
                          )}
                          <button
                            onClick={() => {
                              setSelectedRoomProjId(selectedInceptionProjId);
                              setActiveTab("teamRoom");
                            }}
                            className="text-[11px] text-indigo-600 dark:text-indigo-400 font-semibold hover:underline"
                          >
                            Ruang Tim &rarr;
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Section B: Inception Documents & Backlog (if assembled) */}
                {inceptionDoc && (
                  <div className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm space-y-4 p-5">
                    {/* Sub tabs & Export buttons */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setInceptionSubTab("doc")}
                          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                            inceptionSubTab === "doc"
                              ? "bg-indigo-600 text-white"
                              : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                          }`}
                        >
                          Dokumen Lengkap (PRD/Rencana)
                        </button>
                        <button
                          onClick={() => setInceptionSubTab("backlog")}
                          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                            inceptionSubTab === "backlog"
                              ? "bg-indigo-600 text-white"
                              : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                          }`}
                        >
                          Product Backlog ({backlogEpics.flatMap((e) => e.items).length} Item)
                        </button>
                      </div>

                      <div className="flex items-center gap-2">
                        <a
                          href={`http://localhost:8000/api/inceptions/projects/${selectedInceptionProjId}/export/docx`}
                          download
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" /> Ekspor DOCX
                        </a>
                        <a
                          href={`http://localhost:8000/api/inceptions/projects/${selectedInceptionProjId}/export/pdf`}
                          download
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" /> Ekspor PDF
                        </a>
                      </div>
                    </div>

                    {/* Sub Tab: Document Content */}
                    {inceptionSubTab === "doc" ? (
                      <div className="space-y-4">
                        <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
                          <div className="font-bold text-slate-800 dark:text-slate-200 mb-1">
                            Product Goal:
                          </div>
                          <p className="text-slate-600 dark:text-slate-400 italic">
                            &ldquo;{inceptionDoc.product_goal}&rdquo;
                          </p>
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-xs leading-relaxed bg-white dark:bg-slate-950 p-4 rounded-lg border border-slate-100 dark:border-slate-850 font-mono whitespace-pre-wrap max-h-96 overflow-y-auto">
                          {inceptionDoc.content}
                        </div>
                      </div>
                    ) : (
                      /* Sub Tab: Product Backlog */
                      <div className="space-y-4">
                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <span>
                            Urutan prioritas Product Backlog ditentukan oleh Product Owner (FR-7.4 & PRD 5.1).
                          </span>
                          {user.role === "viewer" && (
                            <span className="text-amber-500 font-medium">
                              (Mode Viewer: Hanya PO yang dapat mengubah urutan)
                            </span>
                          )}
                        </div>

                        {backlogEpics.map((epic) => (
                          <div
                            key={epic.id}
                            className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden"
                          >
                            <div className="bg-slate-50 dark:bg-slate-900/60 px-4 py-2.5 font-bold text-xs text-slate-800 dark:text-slate-200 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                              <span>Epik: {epic.title}</span>
                              <span className="text-[11px] font-normal text-slate-500">
                                {epic.items.length} User Story / Task
                              </span>
                            </div>
                            <div className="divide-y divide-slate-100 dark:divide-slate-850">
                              {epic.items.map((item, idx) => (
                                <div
                                  key={item.id}
                                  className="p-3.5 flex items-start justify-between gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors"
                                >
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                      <span className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-800 text-[10px] font-bold flex items-center justify-center">
                                        {item.po_sort_order + 1}
                                      </span>
                                      <h4 className="font-semibold text-xs text-slate-800 dark:text-slate-200">
                                        {item.title}
                                      </h4>
                                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                                        {item.story_points} Poin
                                      </span>
                                      {item.is_po_task && (
                                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300">
                                          Tugas PO
                                        </span>
                                      )}
                                    </div>
                                    {item.acceptance_criteria && item.acceptance_criteria.length > 0 && (
                                      <div className="pl-7 text-[11px] text-slate-500 space-y-0.5">
                                        {item.acceptance_criteria.map((ac: any, i: number) => (
                                          <div key={i} className="flex items-center gap-1.5">
                                            <span className="w-1 h-1 rounded-full bg-slate-400"></span>
                                            <span>{ac}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>

                                  {user.role !== "viewer" && (
                                    <div className="flex items-center gap-1 shrink-0">
                                      <button
                                        onClick={() => handleMoveBacklogItem(item.id, "up")}
                                        disabled={idx === 0}
                                        className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 disabled:opacity-20"
                                        title="Pindah ke Atas"
                                      >
                                        <ArrowUp className="w-3.5 h-3.5" />
                                      </button>
                                      <button
                                        onClick={() => handleMoveBacklogItem(item.id, "down")}
                                        disabled={idx === epic.items.length - 1}
                                        className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 disabled:opacity-20"
                                        title="Pindah ke Bawah"
                                      >
                                        <ArrowDown className="w-3.5 h-3.5" />
                                      </button>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* PO Decision Box for Gate G2 */}
                    {user.role !== "viewer" && (
                      <div className="mt-6 pt-5 border-t border-slate-200 dark:border-slate-800 space-y-3">
                        <div className="flex items-center gap-2">
                          <ShieldCheck className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                          <h3 className="font-bold text-xs text-slate-800 dark:text-slate-200">
                            Titik Konfirmasi PO: Keputusan Gerbang G2 (Persetujuan Inception & Rencana)
                          </h3>
                        </div>
                        <p className="text-[11px] text-slate-500">
                          Persetujuan G2 menandai berakhirnya tahap Inception dan mengunci ruang lingkup awal untuk masuk ke Sprint Planning.
                        </p>
                        <textarea
                          rows={2}
                          value={poG2Comments}
                          onChange={(e) => setPoG2Comments(e.target.value)}
                          placeholder="Catatan atau arahan PO untuk tim (opsional saat menyetujui, wajib diisi jika minta revisi)..."
                          className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:ring-1 focus:ring-indigo-500"
                        />
                        <div className="flex items-center justify-end gap-2 pt-1">
                          <button
                            onClick={() => handleDecideG2(selectedInceptionProjId, "rejected")}
                            className="px-3 py-1.5 rounded-lg bg-red-50 dark:bg-red-950/60 text-red-700 dark:text-red-300 hover:bg-red-100 text-xs font-semibold transition-colors"
                          >
                            Batalkan Proyek
                          </button>
                          <button
                            onClick={() => handleDecideG2(selectedInceptionProjId, "revision_requested")}
                            className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-xs font-semibold transition-colors"
                          >
                            Minta Revisi Tim
                          </button>
                          <button
                            onClick={() => handleDecideG2(selectedInceptionProjId, "approved")}
                            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5"
                          >
                            <Check className="w-3.5 h-3.5" /> Setujui Rencana (G2)
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : activeTab === "kanban" ? (
          // ==================== KANBAN & SPRINT ENGINE ====================
          <div className="space-y-6">
            {/* Header & Controls */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 mb-2">
                  <Layers className="w-3.5 h-3.5" />
                  Scrum Engine: Kanban & Manajemen Sprint
                </div>
                <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                  Papan Kanban & Eksekusi Sprint
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Pantau alur kerja agen, Daily Standup, pengujian DoD, review increment G3, dan retrospektif.
                </p>
              </div>

              {projects.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">Pilih Proyek:</span>
                  <select
                    value={selectedKanbanProjId}
                    onChange={(e) => {
                      const pid = e.target.value;
                      setSelectedKanbanProjId(pid);
                      if (token) loadKanbanData(pid, token);
                    }}
                    className="px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-medium"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.title} ({p.profile_id})
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Notification alert */}
            {scrumMessage && (
              <div
                className={`p-4 rounded-xl border flex items-center justify-between text-xs ${
                  scrumMessage.type === "success"
                    ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200"
                    : "bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-800 dark:text-red-200"
                }`}
              >
                <span>{scrumMessage.text}</span>
                <button onClick={() => setScrumMessage(null)} className="font-bold ml-4">
                  ✕
                </button>
              </div>
            )}

            {!selectedKanbanProjId ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                Silakan pilih proyek terlebih dahulu.
              </div>
            ) : (
              <div className="space-y-6">
                {/* Sprint Action & Status Bar */}
                <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-sm text-slate-800 dark:text-slate-200">
                          {activeSprint ? `Sprint ${String(activeSprint.sprint_number).padStart(2, "0")}` : "Belum Ada Sprint Aktif"}
                        </span>
                        {activeSprint && (
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            activeSprint.status === "active"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                              : activeSprint.status === "review"
                              ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                              : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300"
                          }`}>
                            {activeSprint.status}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 line-clamp-1">
                        Goal: <strong className="text-slate-700 dark:text-slate-300">{activeSprint?.sprint_goal || "Direncanakan oleh Product Owner dan Scrum Master"}</strong>
                      </p>
                    </div>

                    {user.role !== "viewer" && (
                      <div className="flex flex-wrap items-center gap-2">
                        {(!activeSprint || activeSprint.status === "completed" || activeSprint.status === "cancelled") ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              value={newPlanGoal}
                              onChange={(e) => setNewPlanGoal(e.target.value)}
                              placeholder="Sprint Goal (opsional)..."
                              className="px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 w-48 sm:w-64"
                            />
                            <button
                              onClick={() => handlePlanSprint(selectedKanbanProjId)}
                              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors"
                            >
                              Rencanakan Sprint Baru
                            </button>
                          </div>
                        ) : (
                          <>
                            <button
                              onClick={() => handleDailyStandup(activeSprint.id)}
                              className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-semibold transition-colors"
                            >
                              Laporan Daily Standup
                            </button>
                            <button
                              onClick={() => handleSimulateSprint(activeSprint.id)}
                              disabled={isSimulatingWork}
                              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
                            >
                              {isSimulatingWork ? "Mensimulasikan..." : "Simulasi Eksekusi Kerja"}
                            </button>
                            {activeSprint.status === "review" && (
                              <button
                                onClick={() => handleSprintRetro(activeSprint.id)}
                                className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold transition-colors"
                              >
                                Jalankan Retro
                              </button>
                            )}
                            {activeSprint.status === "active" ? (
                              <button
                                onClick={() => handleSprintControl(activeSprint.id, "pause")}
                                className="px-2.5 py-1.5 rounded-lg text-slate-500 hover:bg-slate-100 text-xs font-medium"
                              >
                                Jeda
                              </button>
                            ) : activeSprint.status === "paused" ? (
                              <button
                                onClick={() => handleSprintControl(activeSprint.id, "resume")}
                                className="px-2.5 py-1.5 rounded-lg text-emerald-600 hover:bg-emerald-50 text-xs font-medium"
                              >
                                Lanjut
                              </button>
                            ) : null}
                          </>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Review G3 Decision Box if Sprint is in Review */}
                  {activeSprint?.status === "review" && user.role !== "viewer" && (
                    <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-amber-900 dark:text-amber-200">
                          Sprint Review (Gerbang G3): Tinjau dan Putuskan PBI
                        </span>
                        <button
                          onClick={() => handleSprintReviewG3(activeSprint.id)}
                          className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-sm transition-colors"
                        >
                          Kunci Keputusan G3 (Terima / Tolak)
                        </button>
                      </div>
                      <div className="space-y-2">
                        {kanbanCols["in_review"]?.map((pbi) => (
                          <div
                            key={pbi.id}
                            className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-amber-200 dark:border-amber-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                          >
                            <div>
                              <span className="font-semibold text-slate-800 dark:text-slate-200">
                                {pbi.title}
                              </span>{" "}
                              <span className="text-[10px] text-slate-400">({pbi.story_points} Poin)</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <select
                                value={pbiReviewDecisions[pbi.id]?.decision || "accept"}
                                onChange={(e) =>
                                  setPbiReviewDecisions((prev) => ({
                                    ...prev,
                                    [pbi.id]: {
                                      decision: e.target.value as "accept" | "reject",
                                      notes: prev[pbi.id]?.notes || "",
                                    },
                                  }))
                                }
                                className="px-2 py-1 text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-medium"
                              >
                                <option value="accept">Terima PBI (Done)</option>
                                <option value="reject">Tolak PBI (Kembali ke Backlog)</option>
                              </select>
                              <input
                                type="text"
                                placeholder="Catatan review..."
                                value={pbiReviewDecisions[pbi.id]?.notes || ""}
                                onChange={(e) =>
                                  setPbiReviewDecisions((prev) => ({
                                    ...prev,
                                    [pbi.id]: {
                                      decision: prev[pbi.id]?.decision || "accept",
                                      notes: e.target.value,
                                    },
                                  }))
                                }
                                className="px-2 py-1 text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 w-44"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Burndown & Velocity Metrics Cards */}
                {burndown && (
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-sm">
                      <span className="text-xs text-slate-500 font-medium">Velocity Tercapai</span>
                      <p className="text-2xl font-extrabold text-indigo-600 dark:text-indigo-400 mt-1">
                        {burndown.velocity_achieved} Poin
                      </p>
                      <span className="text-[11px] text-slate-400">Poin PBI yang disetujui PO</span>
                    </div>
                    <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-sm">
                      <span className="text-xs text-slate-500 font-medium">Poin Selesai</span>
                      <p className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1">
                        {burndown.completed_points} / {burndown.total_planned_points} Poin
                      </p>
                      <span className="text-[11px] text-slate-400">Kemajuan pekerjaan sprint</span>
                    </div>
                    <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-sm">
                      <span className="text-xs text-slate-500 font-medium">Sisa Poin Backlog</span>
                      <p className="text-2xl font-extrabold text-amber-600 dark:text-amber-400 mt-1">
                        {burndown.remaining_points} Poin
                      </p>
                      <span className="text-[11px] text-slate-400">Estimasi sisa pekerjaan</span>
                    </div>
                  </div>
                )}

                {/* Burndown Data Table */}
                {burndown && burndown.burndown.length > 0 && (
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-sm">
                    <h3 className="font-bold text-xs text-slate-800 dark:text-slate-200 mb-3">
                      Burndown Sprint (Ideal vs Aktual)
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-400 font-medium">
                            <th className="pb-2">Garis Metrik</th>
                            {burndown.burndown.map((b) => (
                              <th key={b.day} className="pb-2 text-center">{b.day}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-850">
                          <tr>
                            <td className="py-2 font-semibold text-slate-500">Ideal</td>
                            {burndown.burndown.map((b, i) => (
                              <td key={i} className="py-2 text-center text-slate-400">{b.ideal}</td>
                            ))}
                          </tr>
                          <tr>
                            <td className="py-2 font-semibold text-indigo-600 dark:text-indigo-400">Aktual</td>
                            {burndown.burndown.map((b, i) => (
                              <td key={i} className="py-2 text-center font-bold text-indigo-600 dark:text-indigo-400">{b.actual}</td>
                            ))}
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Kanban 7 Columns */}
                <div>
                  <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-3">
                    Papan Kanban 7 Kolom (FR-10.1)
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-7 gap-3 overflow-x-auto pb-4">
                    {[
                      { key: "product_backlog", label: "Product Backlog", color: "bg-slate-100 dark:bg-slate-900 border-slate-300" },
                      { key: "sprint_backlog", label: "Sprint Backlog", color: "bg-indigo-50/50 dark:bg-indigo-950/20 border-indigo-200" },
                      { key: "in_progress", label: "In Progress", color: "bg-blue-50/50 dark:bg-blue-950/20 border-blue-200" },
                      { key: "in_review", label: "In Review", color: "bg-amber-50/50 dark:bg-amber-950/20 border-amber-200" },
                      { key: "waiting_po", label: "Waiting PO", color: "bg-purple-50/50 dark:bg-purple-950/20 border-purple-200" },
                      { key: "done", label: "Done", color: "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200" },
                      { key: "blocked", label: "Blocked", color: "bg-red-50/50 dark:bg-red-950/20 border-red-200" },
                    ].map((col) => {
                      const items = kanbanCols[col.key] || [];
                      return (
                        <div
                          key={col.key}
                          className={`rounded-xl border p-3 min-h-[300px] flex flex-col space-y-2 ${col.color} dark:border-slate-800`}
                        >
                          <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
                            <span className="font-bold text-[11px] text-slate-700 dark:text-slate-300">
                              {col.label}
                            </span>
                            <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                              {items.length}
                            </span>
                          </div>

                          <div className="flex-1 space-y-2 overflow-y-auto max-h-[500px]">
                            {items.map((item) => (
                              <div
                                key={item.id}
                                className="p-3 bg-white dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm space-y-2 hover:border-indigo-400 transition-colors"
                              >
                                <div className="flex items-start justify-between gap-1">
                                  <h4 className="font-semibold text-xs text-slate-800 dark:text-slate-200 line-clamp-2">
                                    {item.title}
                                  </h4>
                                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 shrink-0">
                                    {item.story_points}p
                                  </span>
                                </div>

                                {item.is_po_task && (
                                  <span className="inline-block px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300">
                                    Tugas PO
                                  </span>
                                )}

                                {user.role !== "viewer" && (
                                  <div className="pt-2 border-t border-slate-100 dark:border-slate-850 flex items-center justify-between text-[10px]">
                                    <span className="text-slate-400">Pindah:</span>
                                    <select
                                      value={item.status}
                                      onChange={(e) => handleMoveKanbanCard(item.id, e.target.value)}
                                      className="px-1.5 py-0.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[10px]"
                                    >
                                      <option value="product_backlog">Backlog</option>
                                      <option value="sprint_backlog">Sprint B.</option>
                                      <option value="in_progress">Progress</option>
                                      <option value="in_review">Review</option>
                                      <option value="waiting_po">Wait PO</option>
                                      <option value="done">Done</option>
                                      <option value="blocked">Blocked</option>
                                    </select>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          // ==================== DASHBOARD HOME ====================
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 mb-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
                  {t.loggedInAs} <strong className="uppercase">{user.role}</strong> ({user.name})
                </div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                  {t.welcomeTitle}
                </h1>
                <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                  {t.welcomeSubtitle}
                </p>
              </div>

              {user.role !== "viewer" && (
                <button
                  onClick={() => { setIsWizardOpen(true); setWizardStep(1); }}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs sm:text-sm shadow-md transition-colors shrink-0"
                >
                  <PlusCircle className="w-4 h-4" />
                  {t.createProject}
                </button>
              )}
            </div>

            {/* Project List */}
            <div>
              {projects.length === 0 ? (
                <div className="p-12 border-2 border-dashed border-slate-300 dark:border-slate-800 rounded-2xl bg-white/50 dark:bg-slate-950/40 text-center space-y-4 my-8">
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
                      <button
                        onClick={() => { setIsWizardOpen(true); setWizardStep(1); }}
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-colors"
                      >
                        <PlusCircle className="w-4 h-4" />
                        {t.createProject}
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {projects.map((p) => (
                    <div
                      key={p.id}
                      className="p-5 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm space-y-3 hover:border-indigo-500 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 uppercase">
                          {p.profile_id}
                        </span>
                        <span className="text-[11px] font-semibold text-slate-500 capitalize">
                          Status: <strong className="text-indigo-600 dark:text-indigo-400">{p.status}</strong>
                        </span>
                      </div>
                      <h3 className="font-semibold text-base text-slate-900 dark:text-white line-clamp-1">
                        {p.title}
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                        {p.brief}
                      </p>
                      <div className="pt-2 border-t border-slate-100 dark:border-slate-850 flex items-center justify-between text-xs text-slate-500">
                        <span>Pagu: {p.budget.toLocaleString()} {p.currency}</span>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedInceptionProjId(p.id);
                          setActiveTab("inception");
                          if (token) loadInceptionData(p.id, token);
                        }}
                        className="w-full inline-flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 font-medium text-xs transition-colors"
                      >
                        <Compass className="w-3.5 h-3.5" /> Tinjau Inception & Rencana (G2)
                      </button>
                      <button
                        onClick={() => {
                          setSelectedKanbanProjId(p.id);
                          setActiveTab("kanban");
                          if (token) loadKanbanData(p.id, token);
                        }}
                        className="w-full mt-1.5 inline-flex items-center justify-center gap-1.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 font-medium text-xs transition-colors"
                      >
                        <Layers className="w-3.5 h-3.5 text-indigo-500" /> Buka Kanban & Sprint
                      </button>
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

# SDLC Fase 3: Desain Arsitektur Sistem & Spesifikasi Teknis (System Design & Architecture)

Dokumen ini menjelaskan arsitektur tingkat tinggi (*High-Level Design* - HLD) dan desain terperinci (*Low-Level Design* - LLD) platform TimAI.

---

## 1. Arsitektur Tingkat Tinggi (High-Level Architecture)

Platform TimAI mengadopsi arsitektur *Modular Layered Monolith* dengan kontainerisasi Docker:

```mermaid
flowchart TD
    subgraph ClientLayer ["Lapisan Klien (Frontend)"]
        UI["Next.js 14 Web UI\n(React, TypeScript, Tailwind)"]
        SSE_Client["SSE Event Stream Consumer\n(Ruang Tim & Live Status)"]
    end

    subgraph ApiGatewayLayer ["Lapisan API & Orkestrasi (Backend)"]
        FastAPI["FastAPI Application Server (Python 3.12)\nUvicorn Asynchronous Workers"]
        AuthRBAC["Auth & RBAC Middleware\n(Argon2 + JWT Bearer)"]
        Routers["REST API Routers\n(/projects, /sprints, /discussions, /learning)"]
        Orchestrator["Orchestrator Engines:\n- Team Composer\n- Meeting Engine (K5)\n- Inception Engine\n- Scrum Engine\n- Agent Runtime & Quality Checker\n- Budget Guard\n- Learning Engine"]
    end

    subgraph GatewayLayer ["Lapisan Model Gateway"]
        MGW["Model Gateway (Uniform Abstraction)"]
        Crypto["Crypto Module\n(AES-256-GCM)"]
        Adapters["Provider Adapters:\n- FakeProvider (Offline/Testing)\n- Anthropic (Claude 3.5/3.7)\n- OpenAI (GPT-4o, o1)\n- Google Gemini\n- Ollama Local"]
    end

    subgraph DataLayer ["Lapisan Persistensi & Pesan"]
        PG[("PostgreSQL 16 + pgvector\n(ACID State, 24 Tabel, Vektor)")]
        Redis[("Redis 7 Alpine\n(Pub/Sub, SSE Buffer, Caching)")]
        GitFS[("Workspaces File System\n(Git Repositories, Dokumen, ZIP)")]
    end

    subgraph WorkerLayer ["Lapisan Pekerja Latar Belakang (Worker)"]
        Worker["Background Python Worker\n(Event Consumer, Batch Processing)"]
    end

    UI -->|HTTP / JSON| FastAPI
    SSE_Client -->|EventStream / SSE| FastAPI
    FastAPI --> AuthRBAC --> Routers --> Orchestrator
    Orchestrator --> MGW
    MGW --> Crypto
    MGW --> Adapters
    Orchestrator --> PG
    Orchestrator --> Redis
    Orchestrator --> GitFS
    Worker --> Redis
    Worker --> PG
```

---

## 2. Desain Basis Data Relasional (ERD & 24 Entitas)

Basis data PostgreSQL dirancang dengan normalisasi tingkat 3 (3NF) dan integritas referensial penuh:

```mermaid
erDiagram
    User ||--o{ Project : owns
    User ||--o{ Gate : decides
    ProjectProfile ||--o{ Project : defines
    Project ||--o{ Attachment : stores
    Project ||--o{ Agent : contains
    Project ||--o{ Discussion : conducts
    Project ||--o{ Artifact : produces
    Project ||--o{ ProductGoal : sets
    Project ||--o{ Epic : organizes
    Project ||--o{ BacklogItem : holds
    Project ||--o{ Sprint : plans
    Project ||--o{ Gate : evaluates
    Project ||--o{ UsageRecord : logs
    Project ||--o{ Lesson : learns

    Provider ||--o{ Model : catalogs
    Model ||--o{ Agent : powers
    RoleTemplate ||--o{ Agent : templates

    Discussion ||--o{ Contribution : records
    Discussion ||--o{ Confirmation : initiates
    Confirmation ||--o{ Decision : finalizes

    Epic ||--o{ BacklogItem : breaks_down
    Sprint ||--o{ BacklogItem : includes
    BacklogItem ||--o{ Task : tasks
    Agent ||--o{ Task : assigned_to

    Model ||--o{ ModelScorecard : evaluated
```

### Rincian 24 Tabel Utama:
1. `users`: Akun pengguna dengan password hash Argon2id dan peran RBAC (`admin`, `po`, `viewer`).
2. `project_profiles`: Definisi 5 profil baku (`proposal`, `jurnal`, `buku`, `software`, `iot`) beserta default agenda & DoD.
3. `projects`: Data proyek (judul, brief, anggaran, mata uang, bahasa, status, dan flag `is_secret`).
4. `attachments`: Lampiran berkas (PDF, DOCX, CSV, BibTeX) dan intisari hasil ekstraksi teks.
5. `role_templates`: Definisi 25 peran spesialis (nama, kompetensi, tier minimum, izin alat, prompt, DoD).
6. `providers`: Kredensial penyedia model LLM (kunci API tersimpan terenkripsi dengan AES-256-GCM).
7. `models`: Katalog model AI (tier, harga input/output per 1M token, skor kompetensi, status aktif).
8. `agents`: Instansiasi agen virtual untuk proyek tertentu, terikat ke RoleTemplate dan Model.
9. `discussions`: Sesi rapat terstruktur (tipe: `general`, `inception`, `standup`, `review`, `retro`).
10. `contributions`: Kontribusi pesan agen pada putaran rapat (K5: 1 pesan per peserta per putaran).
11. `confirmations`: Titik Konfirmasi Scrum Master untuk persetujuan PO (Opsi A vs Opsi B).
12. `decisions`: Catatan keputusan resmi PO yang mengikat arah tim.
13. `artifacts`: Berkas keluaran bernilai (dokumen Inception, laporan sprint, paket naskah).
14. `product_goals`: Sasaran utama produk proyek.
15. `epics`: Kelompok fitur besar proyek.
16. `backlog_items`: Product Backlog Items (PBI) ber-story points, acceptance criteria, dan urutan PO (`po_sort_order`).
17. `sprints`: Siklus sprint (nomor sprint, sprint goal, budget limit, status, velocity tercapai).
18. `tasks`: Tugas kerja turunan PBI (langkah `execute` untuk writer, langkah `verify` untuk reviewer).
19. `increments`: Kumpulan deliverable yang disetujui pada akhir sprint.
20. `gates`: Catatan keputusan pada gerbang strategis (`G1`, `G2`, `G3`, `G4`).
21. `usage_records`: Pencatatan konsumsi token dan biaya tiap pemanggilan model AI.
22. `lessons`: Pengetahuan preferensi PO dan pelajaran retro (`suggested` -> `active` -> `inactive`).
23. `model_scorecards`: Rekam jejak rasio keberhasilan dan biaya model per peran dan profil.
24. `example_libraries`: Pustaka contoh acuan berkualitas tinggi.

---

## 3. Arsitektur Model Gateway & Abstraksi Penyedia

Untuk mencegah *vendor lock-in* dan mengoptimalkan biaya, seluruh pemanggilan LLM dialihkan melalui `ModelGateway`:

```mermaid
flowchart LR
    Orchestrator["Agent Runtime / Engines"] --> Gateway["ModelGateway.complete()"]
    Gateway --> Guard["Budget Guard Pre-Flight"]
    Guard --> Selector["Adapter Registry"]
    Selector --> FakeAdapter["FakeProviderAdapter\n(Local Offline, Mock Responses)"]
    Selector --> OpenAIAdapter["OpenAIAdapter\n(gpt-4o, gpt-4o-mini)"]
    Selector --> AnthropicAdapter["AnthropicAdapter\n(claude-3-5-sonnet, haiku)"]
    Selector --> GeminiAdapter["GeminiAdapter\n(gemini-1.5-pro, flash)"]
    Selector --> OllamaAdapter["OllamaAdapter\n(local Llama3, DeepSeek)"]
    Gateway --> Usage["UsageRecord Logger\n(Tokens, Latency, Cost IDR/USD)"]
```

### Mekanisme Kunci:
1. **Fallback Model Otomatis:** Jika model primer mengalami *rate-limit* atau error jaringan, gateway otomatis mencoba *fallback model* yang telah ditentukan pada profil peran.
2. **Kalkulasi Biaya Real-time:** Setiap respons mencatat token input dan output serta menghitung biaya dalam mata uang proyek (USD atau IDR).
3. **Penyembunyian Kredensial:** Kunci API didekripsi hanya di dalam memori saat pemanggilan HTTP keluar, dan tidak pernah dicetak di log aplikasi.

---

## 4. Arsitektur Keamanan & Kriptografi

```mermaid
flowchart TD
    subgraph DataAtRest ["Keamanan Data Tersimpan (At Rest)"]
        AES["Kunci API Pihak Ketiga:\nAES-256-GCM (Authenticated Encryption)\nMaster Key dari Environtment"]
        Argon2["Kata Sandi Pengguna:\nArgon2id Hash (Memory-Hard, Anti-GPU Cracking)"]
        GitIsolate["Workspace Proyek:\nDirektori Lokal Terisolasi per project_id"]
    end

    subgraph DataInTransit ["Keamanan Data Berjalan (In Transit)"]
        JWT["Autentikasi Stateless:\nJWT Bearer Token dengan Masa Aktif 8 Jam"]
        RBAC["Otorisasi Hak Akses:\nRole Guard FastAPI (Admin, PO, Viewer)"]
        UploadSanitizer["Sanitasi Berkas Unggahan:\n- Ekstensi whitelist (PDF, DOCX, CSV, BibTeX)\n- Batas 50 MB\n- os.path.basename (Cegah Path Traversal '../')"]
    end
```

---

## 5. Mesin Orkestrasi Agen (Agent Runtime & Scrum Flow)

1. **Prinsip Izin Minimal (*Least Privilege*):** Agen hanya dapat mengeksekusi alat (*tools*) yang terdaftar pada `permissions` perannya:
   - Agen Penulis (*Writer*): `write_workspace_file`, `search_literature`, `post_message_to_team_room`.
   - Agen Peninjau (*Reviewer*): `read_workspace_file`, `review_card`, `post_message_to_team_room` (DILARANG menulis berkas draf kerja).
2. **Review Silang Wajib & Siklus Revisi Maksimal 1x (FR-9.5):**
   - Agen Penulis menyusun draf deliverable.
   - Quality Checker memvalidasi batas kata dan sitasi DOI.
   - Agen Peninjau memberikan penilaian (*Approved* atau *Needs Revision*).
   - Jika *Needs Revision*, sistem melakukan maksimal 1 revisi otomatis. Jika masih belum sesuai, kartu berpindah ke *Waiting PO* agar PO memberikan arahan.
3. **Penjaga Anggaran (*Budget Guard*):**
   - Ambang 50%: Peringatan visual di UI.
   - Ambang 80%: Notifikasi peringatan kritis.
   - Ambang 100%: Jeda otomatis (*pause*) eksekusi agen. Proyek tidak dapat dieksekusi lebih lanjut hingga PO menyetujui penambahan pagu anggaran.

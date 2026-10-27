# Dokumentasi Lengkap Siklus Hidup Pengembangan Perangkat Lunak (SDLC)
## Platform TimAI — Scrum-Based Autonomous AI Agent Team Platform

Dokumen ini merupakan indeks utama dokumentasi **Software Development Life Cycle (SDLC)** untuk platform **TimAI**, disusun mengikuti standar rekayasa perangkat lunak internasional (IEEE/ISO/IEC 12207) yang disesuaikan dengan kerangka kerja Scrum dan sistem multi-agen AI.

---

## Peta Dokumen SDLC TimAI

```
docs/sdlc/
├── README.md                                  # Indeks Master & Tata Kelola SDLC
├── 01_PLANNING_AND_FEASIBILITY.md            # Fase 1: Perencanaan, Studi Kelayakan & Piagam Proyek
├── 02_REQUIREMENTS_SPECIFICATION.md          # Fase 2: Analisis Kebutuhan Perangkat Lunak (SRS/PRD)
├── 03_SYSTEM_DESIGN_AND_ARCHITECTURE.md       # Fase 3: Desain Arsitektur Sistem, ERD & Spesifikasi API
├── 04_IMPLEMENTATION_AND_DEVELOPMENT.md       # Fase 4: Panduan Implementasi, Standar Kode & Git
├── 05_TESTING_AND_QUALITY_ASSURANCE.md        # Fase 5: Rencana & Laporan Pengujian (STP & STR)
├── 06_DEPLOYMENT_AND_DEVOPS.md                # Fase 6: DevOps, Kontainerisasi & Pipeline CI/CD
└── 07_OPERATIONS_AND_MAINTENANCE.md           # Fase 7: Pemeliharaan, Observabilitas & Disaster Recovery
```

---

## Ringkasan Eksekutif Tiap Tahapan SDLC

| Fase | Dokumen | Penanggung Jawab | Status | Keluaran Utama |
|---|---|---|---|---|
| **1. Perencanaan** | [01_PLANNING_AND_FEASIBILITY.md](file:///d:/Project/timai/docs/sdlc/01_PLANNING_AND_FEASIBILITY.md) | Product Owner / Tech Lead | Disetujui | Analisis TELOS, WBS 10 Milestone MVP, Anggaran |
| **2. Kebutuhan** | [02_REQUIREMENTS_SPECIFICATION.md](file:///d:/Project/timai/docs/sdlc/02_REQUIREMENTS_SPECIFICATION.md) | Analis Sistem / PO | Disetujui | SRS (FR-1 s.d. FR-14, NFR-1 s.d. NFR-5), User Stories |
| **3. Perancangan** | [03_SYSTEM_DESIGN_AND_ARCHITECTURE.md](file:///d:/Project/timai/docs/sdlc/03_SYSTEM_DESIGN_AND_ARCHITECTURE.md) | Software Architect | Disetujui | Arsitektur Multi-Tier, ERD 24 Entitas, AES-256, API |
| **4. Implementasi** | [04_IMPLEMENTATION_AND_DEVELOPMENT.md](file:///d:/Project/timai/docs/sdlc/04_IMPLEMENTATION_AND_DEVELOPMENT.md) | Tim Pengembang Backend/Frontend | Selesai | FastAPI, Next.js 14, Agent Runtime, Least Privilege |
| **5. Pengujian** | [05_TESTING_AND_QUALITY_ASSURANCE.md](file:///d:/Project/timai/docs/sdlc/05_TESTING_AND_QUALITY_ASSURANCE.md) | QA Engineer / Test Lead | Lolos (100%) | 34 Test Suite, E2E Scrum Cycle, Crash Resilience |
| **6. Penerapan** | [06_DEPLOYMENT_AND_DEVOPS.md](file:///d:/Project/timai/docs/sdlc/06_DEPLOYMENT_AND_DEVOPS.md) | DevOps Engineer | Aktif | Docker Compose, GitHub Actions CI/CD Pipeline |
| **7. Pemeliharaan** | [07_OPERATIONS_AND_MAINTENANCE.md](file:///d:/Project/timai/docs/sdlc/07_OPERATIONS_AND_MAINTENANCE.md) | Site Reliability Engineer (SRE) | Siap Operasi | Skrip Backup/Restore, Runbook Troubleshooting |

---

## Keterkaitan dengan Kerangka Kerja Scrum

TimAI tidak hanya dibangun *menggunakan* prinsip agile, tetapi inti platformnya adalah *mengotomatisasi siklus Scrum* bagi agen AI:

```
[Brief PO] 
   └──> [G1 Persetujuan Tim]
           └──> [Inception & Titik Konfirmasi]
                   └──> [G2 Persetujuan Backlog & DoD]
                           └──> [Sprint Planning -> Eksekusi -> Review Silang]
                                   └──> [G3 Sprint Review & Retro]
                                           └──> [G4 Penutupan Proyek & Rilis]
```

Seluruh artefak yang dihasilkan agen pada setiap fase memiliki metadata baku yang dapat dilacak (PRD Bagian 5.2d), tersimpan dalam Git workspace, dan dikawal ketat oleh Product Owner manusia.

# Status Perkembangan TimAI

## Milestone 1: Kerangka Proyek dan Docker Compose
- **Apa yang jadi**: Monorepo siap dengan FastAPI backend (/health dan /version), worker loop yang terhubung ke PostgreSQL pgvector & Redis, frontend Next.js (TypeScript, Tailwind, i18n ID/EN, dark/light theme), migrasi Alembic, serta konfigurasi Docker Compose dan Makefile/make.bat.
- **Perintah menjalankan**: `docker compose up -d` atau `make up` (uji via `make test` dan `make lint`).
- **Hal yang belum**: Skema entitas bisnis basis data, autentikasi pengguna (Admin/PO/Viewer), dan seed profile (dikerjakan di Milestone 2).

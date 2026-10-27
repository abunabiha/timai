# Status Perkembangan TimAI

## Milestone 1: Kerangka Proyek dan Docker Compose
- **Apa yang jadi**: Monorepo siap dengan FastAPI backend (/health dan /version), worker loop yang terhubung ke PostgreSQL pgvector & Redis, frontend Next.js (TypeScript, Tailwind, i18n ID/EN, dark/light theme), migrasi Alembic, serta konfigurasi Docker Compose dan Makefile/make.bat.
- **Perintah menjalankan**: `docker compose up -d` atau `make up` (uji via `make test` dan `make lint`).
- **Hal yang belum**: Skema entitas bisnis basis data, autentikasi pengguna (Admin/PO/Viewer), dan seed profile (dikerjakan di Milestone 2).

## Milestone 2: Model Data, Autentikasi, Peran Pengguna
- **Apa yang jadi**: 24 entitas model data inti sesuai PRD Bagian 12, migrasi Alembic dua arah yang bersih, 5 seed ProjectProfile, autentikasi Argon2 + JWT untuk peran Admin, PO, dan Viewer dengan penegakan hak akses & isolasi proyek, wizard Admin awal dan form login di antarmuka web.
- **Perintah menjalankan**: `docker compose up -d` (akses web di `http://localhost:3001` dan API di `http://localhost:8000`), uji via `make test` dan `make lint`.
- **Hal yang belum**: Model Gateway, katalog model, enkripsi kunci API penyedia model, dan FakeProvider (dikerjakan di Milestone 3).

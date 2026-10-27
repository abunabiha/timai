# Status Perkembangan TimAI

## Milestone 1: Kerangka Proyek dan Docker Compose
- **Apa yang jadi**: Monorepo siap dengan FastAPI backend (/health dan /version), worker loop yang terhubung ke PostgreSQL pgvector & Redis, frontend Next.js (TypeScript, Tailwind, i18n ID/EN, dark/light theme), migrasi Alembic, serta konfigurasi Docker Compose dan Makefile/make.bat.
- **Perintah menjalankan**: `docker compose up -d` atau `make up` (uji via `make test` dan `make lint`).
- **Hal yang belum**: Skema entitas bisnis basis data, autentikasi pengguna (Admin/PO/Viewer), dan seed profile (dikerjakan di Milestone 2).

## Milestone 2: Model Data, Autentikasi, Peran Pengguna
- **Apa yang jadi**: 24 entitas model data inti sesuai PRD Bagian 12, migrasi Alembic dua arah yang bersih, 5 seed ProjectProfile, autentikasi Argon2 + JWT untuk peran Admin, PO, dan Viewer dengan penegakan hak akses & isolasi proyek, wizard Admin awal dan form login di antarmuka web.
- **Perintah menjalankan**: `docker compose up -d` (akses web di `http://localhost:3001` dan API di `http://localhost:8000`), uji via `make test` dan `make lint`.
- **Hal yang belum**: Model Gateway, katalog model, enkripsi kunci API penyedia model, dan FakeProvider (dikerjakan di Milestone 3).


## Milestone 3: Model Gateway, Katalog Model, FakeProvider
- **Apa yang jadi**: Model Gateway terpadu (`ModelGateway.complete`) dengan adaptor LiteLLM (OpenAI, Anthropic, Google, OpenRouter) dan FakeProvider untuk pengujian deterministik, enkripsi AES-256-GCM kunci API penyedia dengan masking penuh, CRUD katalog model dan verifikasi tier fallback (>= tier awal), pencatatan otomatis tabel UsageRecord dengan peringatan ketidaksesuaian model aktual, serta UI pengaturan penyedia dan katalog model.
- **Perintah menjalankan**: Uji via `make test` dan `make lint`, atau akses menu Pengaturan di antarmuka web `http://localhost:3001`.
- **Hal yang belum**: Alur brief proyek, form brief spesifik profil, ekstraksi lampiran, wawancara klarifikasi, katalog peran (RoleTemplate), dan Team Composer (dikerjakan di Milestone 4).


## Milestone 4: Brief, Klarifikasi, Katalog Peran, Team Composer
- **Apa yang jadi**: Formulir intake brief dengan kolom profil khusus dan ekstraksi lampiran (PDF, DOCX, CSV, BibTeX), wawancara klarifikasi agen Analis (maks. 7 pertanyaan dengan pencatatan asumsi ke `00-brief/klarifikasi.md`), katalog lengkap RoleTemplate 25 peran lintas 5 profil proyek, Team Composer berbasis PRD Bagian 10 dengan rekomendasi tim, pembaruan seketika estimasi biaya/durasi saat tier/model diubah, validasi keberadaan reviewer, serta persetujuan gerbang G1 yang membuat entitas Agent, Gate G1, workspace Git sesuai struktur PRD 5.2c, dan penerbitan `01-tim/team-charter.md` berformat metadata PRD 5.2d.
- **Perintah menjalankan**: Uji via `make test` dan `make lint`, atau buka wizard Buat Proyek Baru di UI `http://localhost:3001`.
- **Hal yang belum**: Meeting Engine (satu putaran, state machine diskusi di Postgres, sintesis Scrum Master, Titik Konfirmasi PO, SSE/WebSocket) (dikerjakan di Milestone 5).

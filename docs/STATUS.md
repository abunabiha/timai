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

## Milestone 5: Meeting Engine, Satu Putaran, Titik Konfirmasi
- **Apa yang jadi**: Engine diskusi Scrum terstruktur dengan penegakan aturan tepat satu putaran bicara per peserta (maksimal 400 kata), penghentian otomatis saat plafon token tercapai, sintesis ringkas Scrum Master beserta usulan opsi keputusan (A/B), penanganan Titik Konfirmasi oleh PO (pemberian pilihan opsi tunggal atau batch), pencatatan otomatis ke `02-inception/decision-log.md` dan `notulen/agenda-NN.md`, SSE streaming untuk event diskusi, serta UI Kotak Konfirmasi dan Ruang Tim.
- **Perintah menjalankan**: Uji via `make test` dan `make lint`, atau buka menu Ruang Tim dan Kotak Konfirmasi di antarmuka web `http://localhost:3001`.
- **Hal yang belum**: Alur Inception lengkap (agenda otomatis per profil Proposal/Jurnal, perakitan dokumen Inception, ekstraksi Product Backlog/Epics/DoD/Rencana Rilis/Risiko, gerbang G2, dan ekspor DOCX/PDF) (dikerjakan di Milestone 6).

## Milestone 6: Inception, Perakitan PRD, Product Backlog, G2
- **Apa yang jadi**: Alur Inception lengkap berbasis profil proyek (Proposal, Jurnal, Software, IoT, Buku) dengan inisialisasi agenda diskusi terstruktur, perakitan otomatis dokumen Inception (`02-inception/dokumen-inception.md`) dari notulen dan keputusan yang dilengkapi blok metadata PRD 5.2d, pembuatan otomatis Product Goal, Epik, Product Backlog Items dengan story points & kriteria penerimaan, DoD (`dod.md`), Rencana Rilis (`rencana-rilis.md`), Risk Register (`risiko.md`), kontrol hak akses ketat di mana reordering backlog hanya bisa dilakukan PO, persetujuan gerbang G2 (Setuju/Revisi/Batal), ekspor dokumen Inception ke format DOCX (`python-docx`) dan PDF (`reportlab`), serta antarmuka UI Inception & Gerbang G2.
- **Perintah menjalankan**: Uji via `docker compose exec -T backend pytest` atau `make test`, dan akses tab Inception di web `http://localhost:3001`.
- **Hal yang belum**: Scrum Engine dan Kanban (Sprint Planning, Sprint Backlog, Daily Standup report, Sprint Review G3 terima/tolak PBI, Retrospective usulan pelajaran, Burndown & Velocity) (dikerjakan di Milestone 7).

## Milestone 7: Scrum Engine dan Kanban
- **Apa yang jadi**: Mesin Scrum lengkap yang mencakup Sprint Planning dengan penguncian Sprint Goal dan pemecahan PBI menjadi Task ber-DoD (`sprint-NN/sprint-plan.md`), laporan Daily Standup otomatis per agen yang dirangkum Scrum Master (`sprint-NN/daily/YYYY-MM-DD.md`), simulasi eksekusi kerja agen, Sprint Review (Gerbang G3) dengan keputusan terima/tolak per PBI di mana PBI yang ditolak dikembalikan secara aman ke Product Backlog, penerbitan paket review dan laporan sprint (`review.md`, `laporan-sprint.md`), Sprint Retrospective satu putaran yang mencatat usulan pelajaran ke tabel Lesson dan `retro.md`, metrik Burndown dan kalkulasi Velocity, kendali jeda/lanjut/batal sprint oleh PO, serta antarmuka Papan Kanban 7 kolom interaktif.
- **Perintah menjalankan**: Uji via `docker compose exec -T backend pytest` atau `make test`, dan akses tab Papan Kanban & Sprint di web `http://localhost:3001`.
- **Hal yang belum**: Eksekusi agen sesungguhnya (Agent Runtime API, loop model + least privilege tools, review silang wajib, perbaikan otomatis maks 1 kali, dan Budget Guard pembatas anggaran 50%/80%/100%) (dikerjakan di Milestone 8).



## Milestone 8: Eksekusi Agen, Review Silang, Penjaga Anggaran
- **Apa yang jadi**: Agent Runtime API terstruktur dengan penegakan izin alat berbasis peran (*least privilege*) dan perakitan konteks terfokus hemat token (Task, kriteria penerimaan, DoD, serta potongan relevan dari workspace); pemeriksaan otomatis khusus profil Proposal & Jurnal (verifikasi DOI/sitasi, batas kata, dan pelabelan klaim tanpa rujukan sebagai `[perlu sumber]`); sistem review silang wajib oleh agen reviewer dengan pembatasan perbaikan otomatis maksimal 1 kali sebelum dipindahkan ke kolom Waiting PO beserta ringkasan masalah; penjaga anggaran (*Budget Guard*) dengan pemantauan ambang 50%, 80%, dan penghentian otomatis pada 100% pagu anggaran serta penjagaan tindakan berisiko (penghapusan berkas, akses domain baru); panel "Agen Sekarang" observabilitas real-time di UI; serta eksekusi proyek proposal end-to-end terverifikasi.
- **Perintah menjalankan**: Uji via `docker compose exec -T backend pytest tests/test_agent_runtime.py` atau `make test`, jalankan eksekusi agen nyata lewat tombol "Jalankan Runtime API Agen" di tab Kanban `http://localhost:3001`.
- **Hal yang belum**: Learning Engine dasar (memori preferensi PO, promosi pelajaran retro usulan -> aktif -> nonaktif, injeksi pelajaran aktif ke prompt agen, ModelScorecard per peran, dan kalibrasi estimasi) (dikerjakan di Milestone 9).


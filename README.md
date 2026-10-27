# TimAI — Platform Tim AI Berbasis Scrum

TimAI adalah platform perangkat lunak inovatif di mana pengguna bertindak sebagai **Product Owner (PO)** dan tugas-tugas diselesaikan oleh **tim agen AI otonom** melalui siklus terstruktur kerangka kerja Scrum (PRD TimAI v1.0).

---

## 1. Arsitektur & Teknologi

- **Backend**: FastAPI (Python 3.12, Uvicorn, SQLAlchemy 2.0 Async, Pydantic v2)
- **Basis Data**: PostgreSQL 16 + pgvector (vektor semantik untuk pencarian pustaka & memori sistem)
- **Cache / Message Queue**: Redis 7 Alpine
- **Worker**: Proses terpisah Python (Async Event Loop + SSE Streaming)
- **Frontend**: Next.js 14 (React, TypeScript, Tailwind CSS, Lucide Icons, Bilingual ID/EN)
- **Model Gateway**: Adapter seragam untuk FakeProvider (pengujian offline tanpa biaya), OpenAI, Anthropic Claude, Google Gemini, OpenRouter, dan Ollama lokal. Kunci API disimpan terenkripsi dengan AES-256-GCM.
- **Orkestrasi**: Docker Compose & Makefile

---

## 2. Prasyarat Sistem

1. [Docker](https://www.docker.com/) (v24+) & Docker Compose (v2.20+)
2. Git (v2.30+)
3. Python 3.12+ (opsional untuk menjalankan skrip CLI di luar container)
4. Node.js 20+ (opsional untuk pengembangan frontend lokal)

---

## 3. Instalasi Cepat (Quickstart dari Nol)

### Langkah 1: Kloning Repositori & Persiapan Lingkungan
```bash
git clone <url-repositori-timai>
cd timai

# Salin berkas lingkungan
cp .env.example .env
```

Pastikan variabel penting di `.env` telah sesuai:
```ini
APP_ENV=development
SECRET_KEY=timai-rahasia-super-aman-ganti-di-produksi
MASTER_ENCRYPTION_KEY=0123456789abcdef0123456789abcdef
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=timai
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/timai
REDIS_URL=redis://redis:6379/0
```

### Langkah 2: Jalankan Layanan dengan Docker Compose
```bash
docker compose up -d
# atau menggunakan Makefile:
make up
```

Layanan akan berjalan pada port berikut:
- **Frontend Web UI**: [http://localhost:3000](http://localhost:3000) (atau port 3001 jika port 3000 terpakai)
- **Backend API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Langkah 3: Akun Default Awal
Saat migrasi awal dijalankan, sistem secara otomatis menyediakan akun default:
- **Admin**: `admin@timai.local` (Kata Sandi: `adminpass123`)
- **Product Owner (PO)**: `po@timai.local` (Kata Sandi: `popass123`)
- **Viewer**: `viewer@timai.local` (Kata Sandi: `viewerpass123`)

---

## 4. Konfigurasi Penyedia Model AI (LLM Providers)

1. Masuk ke aplikasi sebagai **Admin** di [http://localhost:3000](http://localhost:3000).
2. Buka menu **Penyedia Model** (`/providers`).
3. Anda dapat menggunakan:
   - **FakeProvider** (Bawaan / Default): Tidak memerlukan koneksi internet atau kuota berbayar; cocok untuk demo, simulasi, dan pengujian.
   - **OpenAI / Anthropic / Gemini / OpenRouter**: Masukkan API Key Anda. Sistem akan mengenkripsi kunci dengan AES-256-GCM. Kunci asli tidak akan pernah dikembalikan ke respons API atau ditulis ke berkas log.
   - **Ollama**: Masukkan URL Ollama lokal (misal: `http://host.docker.internal:11434`).
4. Klik tombol **Uji Koneksi** untuk memvalidasi status koneksi.

---

## 5. Alur Penggunaan Lengkap (End-to-End Walkthrough)

Alur kerja Scrum terpadu di TimAI mengikuti 8 tahap (PRD Bagian 5.2a):

```
[1. Brief Intake] -> [2. Gerbang G1] -> [3. Inception] -> [4. Gerbang G2]
      -> [5. Sprint Planning] -> [6. Eksekusi Agen & Review Silang]
      -> [7. Gerbang G3 Review & Retro] -> [8. Gerbang G4 Penutupan Proyek]
```

### 1. Brief Intake & Ekstraksi Lampiran
- Masuk sebagai **Product Owner (PO)**.
- Klik **Buat Proyek Baru**. Pilih salah satu dari 5 profil:
  - `Proposal Penelitian` (Kemendikbudristek, Kedaireka, LPDP, BRIN)
  - `Artikel Jurnal` (Scopus, WoS, Sinta)
  - `Buku / Bab Buku`
  - `Perangkat Lunak (Software)`
  - `Sistem IoT Terpadu`
- Tuliskan brief proyek, anggaran, tenggat waktu, dan unggah berkas pendukung (PDF panduan, CSV data, BibTeX rujukan).

### 2. Sesi Klarifikasi & Gerbang G1 (Persetujuan Tim)
- Scrum Master mengajukan pertanyaan klarifikasi jika ada ambiguitas pada brief.
- **Team Composer** merancang proposal tim agen berdasarkan profil dan pagu anggaran, lengkap dengan peran penulis, editor, dan reviewer independen.
- PO meninjau estimasi biaya dan menyetujui Gerbang G1. Sistem menginisialisasi repositori Git dan dokumen `01-tim/team-charter.md`.

### 3. Tahap Inception & Titik Konfirmasi
- Tim agen menjalankan agenda rapat Inception (misal: Gap Riset, Desain Metodologi, Struktur Proposal).
- Scrum Master menyintesis hasil rapat dan mengajukan **Titik Konfirmasi (Opsi A vs Opsi B)** kepada PO.
- Keputusan PO dicatat ke dalam `01-tim/decision-log.md`.
- Sistem menyusun naskah `02-inception/dokumen-inception.md`, Product Goal, Epik, Product Backlog Item (PBI), Definition of Done (DoD), Rencana Rilis, dan Daftar Risiko.

### 4. Gerbang G2 (Persetujuan Inception)
- PO meninjau draf dokumen Inception, dapat mengubah urutan prioritas PBI di Product Backlog, dan menandatangani Gerbang G2.

### 5. Sprint Planning & Eksekusi Agen Otonom
- **Sprint Planning**: PBI teratas dialokasikan ke Sprint dengan Sprint Goal terukur.
- **Agent Runtime**:
  - Agen bekerja otonom menggunakan Tool Loop dengan prinsip izin terendah (*least privilege*).
  - Pengecekan mutu otomatis (*Quality Checker*): memverifikasi batas kata, struktur format, dan validitas sitasi DOI rujukan (mencegah halusinasi atau klaim palsu).
  - Review silang independen (*Cross-Review*): Agen Reviewer menilai draf. Jika terdapat catatan, agen penulis melakukan maksimal 1 revisi otomatis sebelum menyerahkan kartu ke PO.
  - Penjaga Anggaran (*Budget Guard*): Memantau token dan biaya secara real-time. Peringatan pada 50% dan 80%, serta jeda otomatis (*pause*) pada 100% pagu hingga PO menyetujui penambahan.

### 6. Gerbang G3 (Sprint Review) & Retrospektif
- **Sprint Review (Gerbang G3)**: PO meninjau deliverable tiap PBI:
  - PBI yang disetujui berstatus `done` dan story points dihitung ke *velocity*.
  - PBI yang ditolak dikembalikan ke Product Backlog untuk disempurnakan di sprint berikutnya.
- **Sprint Retrospective**: Tim mencatat evaluasi dan menghasilkan usulan pelajaran baru (*Lesson*).

### 7. Gerbang G4 (Penutupan Proyek & Paket Hasil Akhir)
- Setelah seluruh sprint selesai, PO menutup proyek pada Gerbang G4.
- Sistem menerbitkan:
  - `final/laporan-penutupan.md` (dan ekspor `.pdf` serta `.docx`) berisi ringkasan eksekutif, metrik kecepatan, total biaya, dan capaian luaran.
  - `final/paket-hasil-akhir.zip` berisi seluruh artefak naskah final.
  - Tag rilis permanen pada Git: `final-release`.

### 8. Yang Dipelajari Sistem (Continuous Learning Engine)
- Buka menu **Yang Dipelajari Sistem** (`/learning`).
- Menampilkan aturan preferensi PO dan memori yang dipelajari dari Titik Konfirmasi dan catatan penolakan review.
- Pembelajaran berstatus `usulan` -> `aktif` (disetujui PO atau muncul >= 2 kali berulang) -> `nonaktif`.
- Pelajaran aktif disuntikkan secara dinamis ke prompt agen terkait. Proyek rahasia (`is_secret=True`) terkunci pada lingkup proyek dan tidak bocor lintas proyek.

---

## 6. Pencadangan & Pemulihan (Backup & Restore)

TimAI menyertakan utilitas pencadangan basis data dan berkas workspace secara utuh:

### Pencadangan (Backup)
```bash
# Menjalankan pencadangan otomatis (DB + Workspaces)
python scripts/backup.py

# Hasil backup tersimpan di folder backups/ (misal: backups/timai_backup_20261027_032422.zip)
```

### Pemulihan (Restore)
```bash
# Mengembalikan data dari berkas arsip ZIP
python scripts/restore.py -i backups/timai_backup_20261027_032422.zip
```

---

## 7. Pengujian & Penjaminan Kualitas (Testing & Verification)

Jalankan seluruh rangkaian uji terotomatisasi:
```bash
# Menjalankan 34+ unit & integration test backend (menggunakan FakeProvider)
docker compose exec backend pytest

# Menjalankan linter backend (Ruff)
docker compose exec backend ruff check .

# Membangun frontend Next.js untuk memastikan bebas error tipe/sintaks
docker compose exec frontend npm run build
```

---

## 8. Pemecahan Masalah (Troubleshooting)

| Masalah | Penyebab Umum | Solusi |
|---|---|---|
| Port 3000 atau 8000 sudah terpakai | Aplikasi lokal lain menggunakan port tersebut | Ganti pemetaan port host di `docker-compose.yml` (misal: `"3002:3000"` atau `"8001:8000"`) |
| `/health` melaporkan redis `disconnected` | Container Redis belum selesai booting | Tunggu 5-10 detik atau periksa status dengan `docker compose ps` |
| Pagu Anggaran 100% tercapai (Proyek Paused) | Biaya token model mencapai batas pagu brief | Masuk ke detail proyek dan klik **Tambah Pagu Anggaran** |
| Unggahan berkas ditolak (400 Bad Request) | Format berkas tidak didukung atau ukuran > 50MB | Pastikan format adalah PDF, DOCX, CSV, BibTeX, RIS, atau TXT |
| Ingin mereset data ke kondisi awal | Pengujian lokal selesai dan ingin data bersih | Jalankan `docker compose down -v` lalu jalankan kembali `docker compose up -d` |

---

## 9. Lisensi
Hak Cipta © 2026 TimAI Team. Hak cipta dilindungi undang-undang.

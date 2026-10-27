# TimAI — Platform Tim AI Berbasis Scrum

TimAI adalah platform kolaboratif di mana pengguna bertindak sebagai **Product Owner (PO)** dan tugas-tugas diselesaikan oleh **tim agen AI otonom** melalui siklus terstruktur kerangka kerja Scrum.

## Arsitektur Singkat
- **Backend**: FastAPI (Python 3.12)
- **Basis Data**: PostgreSQL 16 + pgvector
- **Cache / PubSub**: Redis 7
- **Worker**: Proses Python terpisah
- **Frontend**: Next.js (TypeScript + Tailwind CSS + i18n ID/EN)
- **Orkestrasi**: Docker Compose

## Prasyarat
- [Docker](https://www.docker.com/) & Docker Compose
- (Opsional untuk pengembangan lokal) Python 3.12, Node.js 20+

## Instalasi & Menjalankan

1. **Salin berkas konfigurasi lingkungan:**
   ```bash
   cp .env.example .env
   ```

2. **Jalankan seluruh layanan:**
   ```bash
   make up
   # atau:
   docker compose up -d
   ```

3. **Periksa status layanan:**
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - Backend Health Check: [http://localhost:8000/health](http://localhost:8000/health)
   - Backend Version: [http://localhost:8000/version](http://localhost:8000/version)

4. **Menjalankan Pengujian (Testing):**
   ```bash
   make test
   ```

5. **Menjalankan Linter:**
   ```bash
   make lint
   ```

6. **Menghentikan Layanan:**
   ```bash
   make down
   ```

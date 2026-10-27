# SDLC Fase 6: Penerapan & DevOps (Deployment & DevOps Guide)

Dokumen ini menjelaskan strategi penerapan, konfigurasi kontainerisasi Docker, arsitektur pipeline CI/CD GitHub Actions, dan manajemen rahasia untuk platform TimAI.

---

## 1. Arsitektur Kontainerisasi Docker

Platform TimAI dikemas sepenuhnya ke dalam 5 layanan mandiri terorkestrasi melalui `docker-compose.yml`:

```mermaid
flowchart TD
    subgraph Host ["Host Server / Cloud VM (Docker Engine)"]
        subgraph Net ["timai-net (Bridge Network)"]
            Frontend["timai-frontend (Port 3000)\nNext.js 14 Production Server"]
            Backend["timai-backend (Port 8000)\nFastAPI / Uvicorn Server"]
            Worker["timai-worker\nPython Background Event Consumer"]
            Postgres[("timai-postgres (Port 5432)\npgvector/pgvector:pg16")]
            Redis[("timai-redis (Port 6379)\nredis:7-alpine")]
        end
        VolPG[("pgdata Volume")]
        VolRedis[("redisdata Volume")]
        VolWS[("./workspaces Bind Mount")]
    end

    Postgres --- VolPG
    Redis --- VolRedis
    Backend --- VolWS
    Worker --- VolWS
    Frontend -->|Internal Proxy| Backend
    Backend --> Postgres
    Backend --> Redis
    Worker --> Postgres
    Worker --> Redis
```

---

## 2. Pipeline CI/CD GitHub Actions (`.github/workflows/ci.yml`)

Pipeline CI/CD terintegrasi secara otomatis dipicu pada setiap `push` dan `pull_request` ke cabang `master` dan `main`:

```mermaid
flowchart LR
    Push["Git Push / PR\n(master / main)"] --> CI_Start["CI Pipeline Started"]
    
    subgraph ParallelJobs ["Pemeriksaan Paralel"]
        Job1["Backend Quality & Tests:\n- Setup Python 3.12\n- Service: Postgres & Redis\n- Ruff Linting Check\n- Pytest (34 Test Skenario)"]
        Job2["Frontend Quality & Build:\n- Setup Node.js 20\n- npm test (i18n & Integrity)\n- Next.js Production Build"]
    end
    
    CI_Start --> Job1
    CI_Start --> Job2
    
    Job1 --> Job3["Docker Build Validation:\n- docker compose config\n- docker compose build images"]
    Job2 --> Job3
    
    Job3 --> Success["Semua Pemeriksaan Hijau\nSiap Deploy ke Server"]
```

### Konfigurasi Kunci Pipeline:
- **Concurrency Control:** `cancel-in-progress: true` membatalkan build lama jika ada commit baru pada cabang yang sama untuk menghemat kuota runner.
- **Service Containers:** PostgreSQL 16 dengan ekstensi `pgvector` dan Redis 7 aktif sebagai kontainer pendukung pengujian di runner GitHub.
- **Isolasi Lingkungan Pengujian:** Pengujian menggunakan variabel lingkungan *mock* yang aman, tanpa membocorkan kunci API produksi.

---

## 3. Manajemen Variabel Lingkungan & Rahasia (Secrets Management)

Variabel lingkungan didefinisikan pada `.env` dengan pemisahan peran yang tegas:

```ini
# Status Lingkungan
APP_ENV=production
APP_NAME="TimAI Platform"
APP_VERSION="1.0.0"

# Kriptografi & Token Keamanan (Wajib 32+ Karakter Acak)
SECRET_KEY=kunci-jwt-super-aman-acak-dan-panjang-min-32-karakter
MASTER_ENCRYPTION_KEY=0123456789abcdef0123456789abcdef

# Kredensial Basis Data (Diisolasi dalam Docker Network)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password-kuat-produksi-disini
POSTGRES_DB=timai
DATABASE_URL=postgresql+asyncpg://postgres:password-kuat-produksi-disini@postgres:5432/timai
SYNC_DATABASE_URL=postgresql://postgres:password-kuat-produksi-disini@postgres:5432/timai

# Kredensial Redis
REDIS_URL=redis://redis:6379/0
```

> [!CAUTION]
> Jangan pernah menambahkan berkas `.env` ke Git. Di server produksi, simpan rahasia di sistem manajemen rahasia seperti *GitHub Repository Secrets*, *HashiCorp Vault*, atau *AWS Secrets Manager*.

---

## 4. Prosedur Penerapan ke Server (Deployment Playbook)

### Penerapan Pertama Kali (Initial Setup):
```bash
# 1. Kloning repositori
git clone https://github.com/abunabiha/timai.git
cd timai

# 2. Siapkan berkas konfigurasi
cp .env.example .env
nano .env  # Masukkan password database dan kunci kriptografi produksi

# 3. Bangun dan jalankan kontainer
docker compose up -d --build

# 4. Jalankan migrasi basis data awal
docker compose exec backend alembic upgrade head

# 5. Periksa status kesehatan sistem
curl http://localhost:8000/health
```

### Pembaruan Rilis Baru (Zero-Downtime Rolling Update):
```bash
# 1. Tarik perubahan terbaru dari Git
git pull origin master

# 2. Bangun image baru tanpa mematikan layanan
docker compose build backend worker frontend

# 3. Jalankan migrasi basis data (jika ada)
docker compose exec backend alembic upgrade head

# 4. Restart kontainer secara berurutan
docker compose up -d --no-deps backend
docker compose up -d --no-deps worker
docker compose up -d --no-deps frontend
```

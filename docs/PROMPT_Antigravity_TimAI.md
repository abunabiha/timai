# Panduan & Prompt Membangun TimAI di Google Antigravity

Dokumen pendamping `PRD_TimAI_Scrum.md` (v1.3). Cara pakai: salin prompt satu per satu, **satu prompt = satu percakapan baru** di Agent Manager.

---

## 0. Cara kerja yang disarankan

1. **PRD jadi sumber kebenaran.** Taruh `PRD_TimAI_Scrum.md` di folder `docs/` proyek. Setiap prompt merujuk ke bagian PRD yang relevan, jadi agen tidak perlu menerima PRD utuh berulang-ulang (hemat kuota).
2. **Pakai Planning mode** untuk semua prompt di bawah. Minta agen menyerahkan *implementation plan* lebih dulu. Baca, koreksi, baru setujui. Fast mode hanya untuk perbaikan kecil.
3. **Satu milestone, satu percakapan, satu commit.** Setelah hasilnya lolos uji, commit. Percakapan berikutnya memulai dari kondisi bersih.
4. **Uji dengan model palsu dulu.** Prompt 3 membuat `FakeProvider` yang membalas teks tetap. Semua uji otomatis memakainya, jadi pengembangan tidak menghabiskan token API sungguhan.
5. **Jaga cakupan.** Setiap prompt memuat bagian "Jangan dikerjakan". Itu mencegah agen melebar ke fitur milestone berikutnya.

### Stack bawaan (usulan, bisa diganti sebelum Prompt 1)
| Lapisan | Pilihan | Alasan singkat |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Ekosistem LLM terkuat |
| Basis data | PostgreSQL + pgvector | Satu DB untuk data relasional dan pencarian semantik |
| Antrean/pub-sub | Redis | Status agen real-time |
| Worker | Proses Python terpisah dengan state machine di PostgreSQL | Tahan restart tanpa menambah infrastruktur |
| Gateway model | LiteLLM sebagai pustaka (di balik adaptor sendiri) | Banyak penyedia, harga dan token tercatat |
| Frontend | Next.js + TypeScript + Tailwind | Papan Kanban dan dashboard interaktif |
| Deploy | Docker Compose | Sesuai keputusan K3 |

---

## 1. Persiapan satu kali

### 1a. Struktur awal
```
timai/
├─ docs/PRD_TimAI_Scrum.md
├─ .agents/rules/timai.md      ← isi di 1b
└─ (kode dibuat oleh prompt-prompt di bawah)
```

### 1b. File aturan proyek (salin ke `.agents/rules/timai.md`)

```markdown
# Aturan proyek TimAI

## Sumber kebenaran
- Spesifikasi ada di docs/PRD_TimAI_Scrum.md. Jika instruksi bertentangan dengan PRD, berhenti dan tanyakan.
- Jangan menambah fitur di luar milestone yang sedang dikerjakan.

## Cara kerja
- Selalu buat implementation plan dan tunggu persetujuan sebelum menulis kode.
- Satu milestone selesai hanya jika: kode jalan, tes lolos, dan README bagian terkait diperbarui.
- Tulis tes untuk setiap logika bisnis. Tes tidak boleh memanggil API LLM sungguhan; gunakan FakeProvider.
- Jangan pernah menulis kunci API, token, atau kata sandi ke kode, log, atau commit. Baca dari variabel lingkungan.

## Kode
- Python: type hints wajib, ruff + mypy harus bersih. TypeScript: strict mode.
- Nama kode, komentar, dan pesan commit dalam bahasa Inggris. Teks antarmuka lewat file i18n (Indonesia default, Inggris).
- Setiap pemanggilan model wajib lewat ModelGateway dan tercatat di tabel usage (model aktual, token, biaya).
- Jangan menelan error. Error model/alat harus dicatat dan diteruskan ke status tugas.

## Aturan produk yang tidak boleh dilanggar
- Setiap diskusi antaragen = SATU putaran (tiap peserta bicara sekali), lalu sintesis Scrum Master, lalu Titik Konfirmasi PO.
- Hanya PO (manusia) yang mengubah urutan Product Backlog dan menyetujui gerbang G1–G4.
- Agen dilarang mengarang sumber, data, atau hasil penelitian. Klaim tanpa rujukan terverifikasi ditandai "perlu sumber".
- Batas anggaran (token/biaya) ditegakkan di orkestrator, bukan hanya ditampilkan.
```

### 1c. Rekomendasi pengaturan Antigravity
- Buka folder `timai/` sebagai workspace.
- Aktifkan **Planning mode** sebagai default untuk percakapan baru.
- Bila ada pilihan tingkat izin eksekusi terminal, gunakan mode yang **meminta persetujuan** untuk perintah yang menghapus berkas atau mengakses jaringan.
- Letak folder aturan, workflow, dan skill bisa berbeda antarversi. Sumber yang saya baca menyebut `.agent/rules/` pada satu panduan dan `.agents/rules/` pada panduan lain. Cek panel *Customizations* di aplikasi Anda dan tambahkan aturan lewat panel itu bila perlu.

---

## 2. Prompt per milestone

### Template (kerangka semua prompt)

```
KONTEKS: <1–2 kalimat, rujuk bagian PRD>
TUJUAN: <hasil yang harus ada setelah selesai>
CAKUPAN: <daftar yang dikerjakan>
JANGAN DIKERJAKAN: <fitur milestone lain>
KRITERIA SELESAI: <uji/perintah yang harus lolos>
LANGKAH PERTAMA: Buat implementation plan dan berhenti untuk persetujuan saya.
```

---

### Prompt 1 — Kerangka proyek dan Docker Compose

```
KONTEKS
Kita membangun TimAI, platform tim agen AI berbasis Scrum. Baca docs/PRD_TimAI_Scrum.md Bagian 8 (NFR) dan Bagian 9 (Arsitektur), serta .agents/rules/timai.md.

TUJUAN
Kerangka monorepo yang bisa dijalankan dengan satu perintah `docker compose up`.

CAKUPAN
- Folder: backend/ (FastAPI), worker/ (proses worker), frontend/ (Next.js), docker/, docs/.
- docker-compose.yml: postgres (pgvector), redis, backend, worker, frontend. Semua konfigurasi dari .env; sediakan .env.example tanpa rahasia.
- Backend: endpoint GET /health dan GET /version.
- Frontend: halaman beranda kosong dengan layout, dukungan i18n ID/EN, tema terang/gelap.
- Worker: loop yang mencetak "worker alive" tiap 10 detik dan terhubung ke Redis + Postgres.
- Migrasi basis data memakai Alembic (belum ada tabel bisnis).
- Makefile: make up, make down, make test, make lint.
- README: cara instalasi dan menjalankan.

JANGAN DIKERJAKAN
Autentikasi, tabel bisnis, integrasi model, logika Scrum.

KRITERIA SELESAI
- `docker compose up` menjalankan semua layanan tanpa error.
- /health mengembalikan status database dan redis.
- `make test` dan `make lint` lolos (minimal satu tes per layanan).

LANGKAH PERTAMA
Buat implementation plan dan berhenti untuk persetujuan saya.
```

### Prompt 2 — Model data, autentikasi, peran pengguna

```
KONTEKS
Lanjutan Prompt 1. Baca PRD Bagian 2.2 (pengguna), Bagian 12 (model data), FR-15.

TUJUAN
Skema basis data inti dan login untuk peran Admin, PO, Viewer.

CAKUPAN
- Migrasi Alembic untuk entitas: User, Project, ProjectProfile, Attachment, RoleTemplate, Provider, Model, Agent, Discussion, Contribution, Confirmation, Decision, Artifact, ProductGoal, Epic, BacklogItem, Sprint, Task, Increment, Gate, UsageRecord, Lesson, ModelScorecard. Ikuti atribut di PRD Bagian 12.
- Autentikasi email + kata sandi (hash argon2), sesi/JWT, tiga peran dengan pemeriksaan hak akses di setiap endpoint.
- Wizard pengguna pertama: instalasi baru membuat akun Admin.
- Seed data: 5 ProjectProfile (software, iot, proposal, jurnal, buku) dengan data kosong yang dapat diisi prompt berikutnya.
- Tes: hak akses (Viewer tidak bisa menulis, PO hanya melihat proyeknya sendiri).

JANGAN DIKERJAKAN
Penyedia model, logika diskusi, UI Kanban.

KRITERIA SELESAI
- Migrasi naik dan turun bersih.
- Tes hak akses lolos.
- Halaman login dan wizard Admin berfungsi.
```

### Prompt 3 — Model Gateway, katalog model, FakeProvider

```
KONTEKS
Baca PRD FR-4 (penyedia dan katalog model) dan NFR "Hemat token".

TUJUAN
Satu pintu untuk semua pemanggilan model, dengan pencatatan biaya dan model aktual.

CAKUPAN
- Antarmuka ModelGateway.complete(agent_context, messages, tools, limits) di backend.
- Adaptor: (a) endpoint OpenAI-compatible, (b) Anthropic, (c) Google, (d) OpenRouter, (e) FakeProvider yang membalas teks deterministik untuk tes. Gunakan LiteLLM di dalam adaptor, bukan di seluruh kode.
- Halaman Admin: tambah/uji koneksi penyedia, kunci API disimpan terenkripsi (AES-256-GCM, kunci induk dari .env), kunci tidak pernah dikirim kembali ke klien.
- Katalog model (CRUD): penyedia, nama, konteks, harga input/output, dukungan tool use/vision, skor kompetensi 1–5, tier (low/medium/high/xhigh) yang bisa diedit.
- Setiap panggilan mencatat UsageRecord: model yang diminta DAN model aktual dari metadata respons, token masuk/keluar, biaya, latensi, error. Beri peringatan bila model aktual berbeda dari yang diminta.
- Health check model berkala.
- Fallback ke model cadangan dengan tier setara atau lebih tinggi; tiap pergantian tercatat.
- Tes memakai FakeProvider saja.

JANGAN DIKERJAKAN
Runtime agen, Team Composer, diskusi.

KRITERIA SELESAI
- Admin bisa menambah penyedia, menguji koneksi, dan melihat daftar model.
- Tes membuktikan: model aktual tercatat, fallback bekerja, kunci tidak bocor di log atau respons API.
```

### Prompt 4 — Brief, klarifikasi, katalog peran, Team Composer

```
KONTEKS
Baca PRD FR-1, FR-2, FR-3, Bagian 6.2 (tim default per profil), Bagian 10 (spesifikasi Team Composer).

TUJUAN
PO membuat proyek dari brief dan menerima usulan tim yang bisa diubah dan disetujui (gerbang G1).

CAKUPAN
- Form brief + kolom tambahan per profil (FR-1.3), unggah lampiran (PDF, DOCX, CSV, BibTeX) dengan ekstraksi teks dan ringkasan.
- Wawancara klarifikasi: agen Analis mengajukan maksimal 7 pertanyaan; jawaban dan asumsi disimpan ke klarifikasi.md di workspace.
- Katalog RoleTemplate dengan seluruh peran di PRD 6.2 (prompt peran, tier minimum/default, alat, kompetensi, kriteria selesai). Peran berversi.
- Team Composer sesuai Bagian 10: mulai dari tim default profil, sesuaikan dengan analisis brief, hitung estimasi biaya dan durasi sebagai RENTANG, tampilkan alasan per agen, validasi (ada reviewer, biaya <= anggaran).
- Layar "Rancang Tim": kartu agen, ganti peran/model/tier/runtime, estimasi biaya diperbarui seketika, tombol Setujui Tim (G1). Setelah G1, buat record Agent dan workspace Git proyek dengan struktur folder PRD Bagian 5.2c.
- Team Charter disimpan sebagai team-charter.md dengan metadata PRD 5.2d.
- Tes memakai FakeProvider; analisis brief diuji dengan respons JSON tetap.

JANGAN DIKERJAKAN
Diskusi antaragen, backlog, sprint, runtime CLI. Hanya profil Proposal dan Jurnal yang perlu lengkap; profil lain cukup terdaftar.

KRITERIA SELESAI
- Alur dari brief sampai G1 berjalan di UI dan menghasilkan team-charter.md.
- Mengubah model/tier di UI memperbarui estimasi biaya.
```

### Prompt 5 — Meeting Engine: satu putaran + Titik Konfirmasi

```
KONTEKS
Ini inti produk. Baca PRD FR-6 dengan teliti, Bagian 11 (contoh Titik Konfirmasi), dan aturan K5: setiap diskusi hanya SATU putaran.

TUJUAN
Mesin diskusi antaragen yang hemat token, berhenti di Titik Konfirmasi, dan menunggu keputusan PO.

CAKUPAN
- Entitas dan state machine Discussion: draf -> berjalan -> sintesis -> menunggu PO -> selesai. State disimpan di Postgres sehingga tahan restart dan bisa menunggu PO berhari-hari.
- Satu putaran: Scrum Master menentukan urutan peserta; tiap agen bicara TEPAT SATU KALI, wajib membaca kontribusi sebelumnya; panjang kontribusi dibatasi (default 400 kata, bisa diatur); plafon token per putaran.
- Sintesis Scrum Master: usulan keputusan, poin setuju, beda pendapat sebagai opsi A/B, pertanyaan untuk PO, perkiraan biaya bila dilanjutkan.
- Titik Konfirmasi di UI dengan tombol: Setuju (atau pilih opsi A/B langsung), Lanjut diskusi (+ arahan PO, satu putaran lagi), Ubah arah (PO menulis keputusan sendiri).
- Decision Log otomatis; notulen disimpan sebagai notulen/agenda-NN.md.
- Kotak Konfirmasi: daftar semua konfirmasi yang menunggu, bisa diputuskan sekaligus (FR-6.9).
- Tampilan langsung putaran lewat SSE/WebSocket; PO bisa menyela.
- Pengingat bila PO belum menjawab; tim tidak melanjutkan diskusi itu tanpa jawaban.
- Setiap kontribusi dicatat ke UsageRecord lewat ModelGateway.
- Tes (FakeProvider): satu putaran tepat satu kontribusi per peserta; tidak ada putaran kedua tanpa klik PO; restart worker di tengah diskusi tidak menggandakan kontribusi; plafon token menghentikan putaran.

JANGAN DIKERJAKAN
Backlog, sprint, eksekusi tugas, mode persetujuan otomatis.

KRITERIA SELESAI
- Demo: diskusi dengan 3 agen palsu -> sintesis -> PO memilih opsi B -> keputusan masuk Decision Log.
- Semua tes di atas lolos.
```

### Prompt 6 — Inception: dari diskusi menjadi PRD/Rencana dan Product Backlog

```
KONTEKS
Baca PRD FR-7, Bagian 5.1 (kerangka Scrum), Bagian 5.2 (keluaran tahapan), dan Bagian 6.1 untuk profil Proposal penelitian dan Artikel jurnal.

TUJUAN
Setelah G1, tim menjalankan agenda Inception dan menghasilkan dokumen rencana, Product Goal, Product Backlog, DoD, rencana rilis, dan risk register, lalu PO memutuskan G2.

CAKUPAN
- Agenda Inception per profil (FR-7.1) untuk Proposal dan Jurnal; tiap agenda memakai Meeting Engine dari Prompt 5.
- Setelah seluruh agenda terkonfirmasi, agen Analis/Research Lead merakit Dokumen Inception dari notulen dan keputusan (bukan menulis ulang dari nol), memakai templat profil.
- Hasilkan Product Goal, Epik, Product Backlog Item (kriteria penerimaan, estimasi poin, urutan usulan), Definition of Done, Rencana Rilis (rentang tanggal dan biaya), Risk Register.
- Layar Tinjau PRD/Rencana: komentar per bagian, diff antarversi, tombol Setujui / Minta revisi / Batalkan (G2). Revisi mengirim komentar kembali ke tim dan membuka diskusi satu putaran baru.
- Simpan semua keluaran dengan metadata PRD 5.2d dan versi.
- Ekspor dokumen Inception ke DOCX dan PDF.

JANGAN DIKERJAKAN
Sprint, Kanban, eksekusi.

KRITERIA SELESAI
- Dari proyek proposal sampai G2 dengan FakeProvider: semua berkas keluaran ada di workspace dengan metadata benar.
- Mengubah urutan Product Backlog hanya bisa dilakukan PO.
```

### Prompt 7 — Scrum Engine dan Kanban

```
KONTEKS
Baca PRD Bagian 5.1, FR-8, FR-10, dan Lampiran keluaran 5.2.

TUJUAN
Sprint berjalan dari Planning sampai Review, dan PO memantaunya di Kanban.

CAKUPAN
- Kanban: kolom Product Backlog, Sprint Backlog, In Progress, In Review, Waiting PO, Done, Blocked. Tampilan Board dan List, filter, pencarian, kartu dengan semua kolom FR-10.2, penanda "Tugas PO".
- Sprint Planning: satu putaran diskusi; Scrum Master mengusulkan Sprint Goal, PBI terpilih dari urutan teratas sesuai velocity, pemecahan Task, dan penugasan agen. Titik Konfirmasi PO. Hasil menjadi Sprint Backlog dan sprint-plan.md.
- Aturan backlog PRD 5.1: hanya PO mengubah urutan; Sprint Goal terkunci selama sprint; PBI usulan tim berlabel "usulan tim".
- Daily Scrum sebagai laporan (bukan diskusi): tiap agen menulis selesai/sedang/hambatan, Scrum Master merangkum.
- Sprint Review: paket review per PBI, tombol Terima/Tolak dengan catatan per PBI (G3). PBI ditolak kembali ke Product Backlog. Buat laporan-sprint.md.
- Retrospective satu putaran menghasilkan usulan pelajaran (belum perlu Learning Engine penuh, cukup tersimpan sebagai Lesson berstatus "usulan").
- Dashboard: progres sprint, burndown, velocity, biaya vs batas, jumlah konfirmasi menunggu.
- Jeda, lanjut, dan hentikan sprint oleh PO.

JANGAN DIKERJAKAN
Eksekusi sungguhan oleh agen (Prompt 8). Pada milestone ini, eksekusi Task disimulasikan oleh FakeProvider yang menandai Task selesai.

KRITERIA SELESAI
- Simulasi satu sprint penuh: Planning -> Eksekusi (palsu) -> Review -> Retro, dengan G3 menolak satu PBI dan PBI itu kembali ke backlog.
- Burndown dan velocity terhitung benar pada data simulasi.
```

### Prompt 8 — Eksekusi agen, review silang, penjaga anggaran

```
KONTEKS
Baca PRD FR-5, FR-9, FR-11, dan NFR Keamanan/Kendali biaya.

TUJUAN
Agen benar-benar mengerjakan Task (runtime API), diperiksa reviewer, dan dibatasi anggaran.

CAKUPAN
- Agent Runtime API: loop model + alat dengan izin per peran (least privilege). Alat: baca/tulis berkas workspace, cari di workspace, pencarian literatur/web (dapat dimatikan), kirim pesan ke Ruang Tim, ajukan pertanyaan ke PO, ubah kartu miliknya.
- Konteks agen hanya berisi Task, kriteria penerimaan, DoD, dan potongan relevan dari workspace (pencarian semantik), bukan seluruh riwayat.
- Review silang wajib: reviewer ditautkan ke peran pelaksana; perbaikan otomatis hanya 1 kali; bila masih gagal, kartu ke Waiting PO dengan ringkasan masalah.
- Pemeriksaan otomatis untuk profil Proposal dan Jurnal: batas kata/halaman, format sitasi, verifikasi DOI/rujukan, konsistensi istilah. Klaim tanpa rujukan terverifikasi ditandai "perlu sumber".
- Budget Guard di orkestrator: batas per diskusi, sprint, proyek; peringatan 50/80/100%; pada 100% eksekusi dijeda sampai PO menambah anggaran.
- Tindakan berisiko (akses domain baru, hapus berkas) menunggu persetujuan PO.
- Panel "Agen Sekarang" real-time.
- Tes (FakeProvider): batas anggaran benar-benar menghentikan eksekusi; izin peran ditegakkan; perbaikan otomatis tidak lebih dari 1 kali.

JANGAN DIKERJAKAN
Runtime CLI/sandbox, profil Software/IoT/Buku, Learning Engine.

KRITERIA SELESAI
- Satu proyek proposal berjalan end-to-end memakai FakeProvider dengan hasil artefak, review, dan penghentian anggaran yang terverifikasi.
- Uji manual singkat dengan satu model nyata murah (tier low) pada satu Task.
```

### Prompt 9 — Learning Engine dasar

```
KONTEKS
Baca PRD FR-14, termasuk paragraf "Prinsip kejujuran": sistem tidak melatih bobot model; belajar terjadi di tingkat sistem dan sepenuhnya terkendali PO.

TUJUAN
Sistem mengingat preferensi PO dan mencatat kinerja model per peran, dengan halaman kendali untuk PO.

CAKUPAN
- Pengambilan pelajaran dari: keputusan di Titik Konfirmasi, alasan penolakan di Sprint Review, suntingan PO pada artefak, catatan retro.
- Lesson berstatus usulan -> aktif -> nonaktif; aktif hanya setelah PO menyetujui, atau muncul berulang (>= 2 kali).
- Lesson aktif disuntikkan ke prompt agen yang relevan sesuai cakupan (global, per profil, per proyek) dengan batas ukuran.
- ModelScorecard: setiap PBI mencatat model, peran, diterima/ditolak, jumlah perbaikan, biaya. Team Composer memakai skor ini sesuai rumus PRD Bagian 10 langkah 6.
- Kalibrasi estimasi: rasio estimasi vs aktual per profil mengoreksi estimasi berikutnya.
- Halaman "Yang Dipelajari Sistem": daftar aturan/memori/skor model dengan aksi setujui, edit, nonaktifkan, hapus. Proyek berpenanda rahasia tidak berbagi contoh lintas proyek.
- Tes: Lesson usulan tidak mempengaruhi prompt; Lesson aktif mempengaruhi; nonaktif tidak.

JANGAN DIKERJAKAN
Penyempurnaan prompt peran otomatis, ekspor dataset fine-tuning, pustaka contoh (v1.2).

KRITERIA SELESAI
- Demo dua proyek berurutan: koreksi PO di proyek 1 muncul sebagai usulan, disetujui, lalu terlihat mempengaruhi prompt di proyek 2.
```

### Prompt 10 — Pengerasan MVP dan uji menyeluruh

```
KONTEKS
Seluruh milestone MVP selesai. Baca PRD Bagian 14 (kriteria selesai MVP) dan Bagian 8 (NFR).

TUJUAN
MVP stabil dan siap dipakai untuk satu proposal dan satu manuskrip nyata.

CAKUPAN
- Tes end-to-end otomatis (FakeProvider) untuk alur lengkap: brief -> G1 -> Inception -> G2 -> dua sprint -> G3 -> penutupan G4.
- Uji ketahanan: matikan worker di tengah diskusi dan tengah sprint, lalu hidupkan lagi; tidak ada kontribusi ganda atau state hilang.
- Audit keamanan dasar: kunci API tidak muncul di log/respons, hak akses, validasi unggahan berkas, batasan ukuran.
- Backup/restore sederhana (skrip) untuk database dan berkas.
- Perbaiki semua lint/type error; lengkapi README (instalasi, konfigurasi penyedia, alur penggunaan, pemecahan masalah).
- Buat daftar periksa pilot: apa yang harus saya siapkan (kunci API, templat skema hibah, jurnal target) sebelum menjalankan proyek nyata pertama.

JANGAN DIKERJAKAN
Fitur baru di luar PRD.

KRITERIA SELESAI
- `make test` hijau; skenario end-to-end lolos; README bisa diikuti dari nol.
```

---

## 3. Setelah MVP

| Versi | Prompt berikutnya (gunakan templat yang sama) |
|---|---|
| v1.1 | Runtime CLI + sandbox + toolchain firmware; profil Software dan IoT; Tugas PO; rapor model penuh |
| v1.2 | Profil Buku dwibahasa; pustaka contoh; paket Hemat/Maksimal; laporan penutupan |

Untuk tiap versi, ulangi pola: *baca bagian PRD yang relevan -> implementation plan -> persetujuan -> bangun -> uji dengan FakeProvider -> commit*.

## 4. Jika agen melenceng atau macet

| Gejala | Tindakan |
|---|---|
| Agen menambah fitur di luar cakupan | Balas: "Kembalikan ke cakupan prompt. Hapus yang tidak diminta." |
| Rencana terlalu besar | Minta: "Pecah menjadi dua milestone, kerjakan bagian pertama dulu." |
| Tes lolos tapi perilaku salah | Minta tes baru yang gagal terhadap perilaku yang salah, baru perbaiki kodenya |
| Agen mengubah PRD | Tolak. PRD hanya diubah oleh Anda; usulan perubahan ditulis sebagai catatan terpisah |
| Kuota habis di tengah milestone | Minta ringkasan status ke `docs/STATUS.md`, lalu lanjutkan di percakapan baru dengan merujuk berkas itu |

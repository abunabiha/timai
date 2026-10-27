# PRD — Platform Tim AI Berbasis Scrum (nama kerja: **TimAI**)

| | |
|---|---|
| **Versi** | 1.3 |
| **Tanggal** | 27 Oktober 2026 |
| **Pemilik produk & penggagas ide** | Imam |
| **Status** | Untuk ditinjau |

### Riwayat perubahan
| Versi | Perubahan |
|---|---|
| 1.0 | Draf awal |
| 1.1 | Lima profil proyek prioritas; diskusi **satu putaran** lalu konfirmasi PO; modul **pembelajaran berkelanjutan**; rujukan ke aplikasi lain dihapus |
| 1.2 | Bagian 5.1 **Kerangka Scrum**: peran, artefak + komitmen (Product Goal, Sprint Goal, DoD), hierarki Product Backlog → Sprint Backlog → Increment, aturan backlog |
| 1.3 | Bagian 5.2 **Keluaran setiap tahapan**: dokumen per tahap, isi minimal, format, penyetuju, matriks per profil, struktur folder workspace, metadata dokumen |

### Keputusan yang sudah ditetapkan PO
| # | Keputusan | Pilihan |
|---|---|---|
| K1 | Jenis proyek | Lima profil prioritas: **(1) Software, (2) IoT (perangkat keras + firmware + software), (3) Proposal penelitian, (4) Artikel jurnal, (5) Buku / book chapter (Indonesia dan Inggris)**. Jenis lain menyusul memakai profil "Umum" |
| K2 | Akses model | **API dan CLI**: API untuk diskusi, perencanaan, dan penulisan; CLI agen coding untuk eksekusi teknis |
| K3 | Bentuk aplikasi | **Web app self-hosted** dengan Docker Compose |
| K4 | Persetujuan hasil kerja | Di setiap **sprint review**, ditambah persetujuan tim dan PRD di awal |
| K5 | Aturan diskusi | **Setiap diskusi hanya satu putaran.** Setelah itu Scrum Master bertanya ke PO: *setuju* atau *lanjut diskusi* |
| K6 | Kecerdasan sistem | Aplikasi **terus belajar** dari setiap proyek supaya rekomendasi dan hasilnya makin baik |

Butir bertanda **[U]** adalah usulan desain penyusun dan masih bisa diubah PO.

---

## 1. Ringkasan

TimAI adalah platform tempat pengguna berperan sebagai **Product Owner (PO)**. Pekerjaannya dikerjakan oleh **tim agen AI**. Setiap agen memegang satu peran dan dijalankan oleh model AI yang tingkat kecerdasannya sesuai beratnya peran itu.

Alur kerjanya:
1. PO memberi brief proyek.
2. Sistem mengusulkan susunan tim: jumlah anggota, peran, tier kecerdasan, dan model.
3. Setelah tim disetujui, agen berdiskusi menyusun PRD atau rencana kerja.
4. Setiap diskusi berlangsung satu putaran. Setelah itu PO memutuskan apakah hasilnya diterima atau diskusi dilanjutkan.
5. Begitu rencana disetujui, tim bekerja dalam sprint Scrum sampai proyek selesai. PO memantau lewat Kanban, timeline, dan perkiraan tanggal selesai.

Setiap proyek yang selesai menjadi bahan belajar sistem. Usulan tim berikutnya lebih tepat, gaya tulisan makin sesuai selera PO, dan estimasi makin akurat.

## 2. Masalah dan pengguna

### 2.1 Masalah
1. Satu chatbot untuk proyek besar membuat konteks cepat penuh, peran bercampur, dan tidak ada pemeriksaan silang.
2. Model termahal untuk semua pekerjaan memboroskan biaya. Model termurah untuk semua pekerjaan menurunkan mutu.
3. Pengguna tidak selalu tahu berapa "orang" dan keahlian apa yang dibutuhkan sebuah proyek.
4. Diskusi antar-AI yang dibiarkan berjalan sendiri cenderung berputar dan menghabiskan token.
5. Pelajaran dari proyek sebelumnya (koreksi, preferensi gaya, kesalahan berulang) hilang begitu percakapan selesai.

### 2.2 Pengguna
| Peran | Deskripsi | Hak akses |
|---|---|---|
| **Product Owner (PO)** | Pemilik proyek | Membuat proyek, menyetujui tim, hasil diskusi, PRD, dan hasil sprint; mengatur prioritas backlog |
| **Admin** | Pengelola instalasi self-hosted (bisa orang yang sama dengan PO) | Penyedia model, katalog model, pengguna, anggaran, backup |
| **Viewer** [U] | Rekan, mahasiswa, atau pembimbing | Melihat dashboard dan artefak, memberi komentar |

## 3. Tujuan dan non-tujuan

**Tujuan**
- G1. Mengubah brief menjadi tim AI yang tepat ukuran dan tepat biaya.
- G2. Diskusi antaragen yang hemat token: satu putaran, lalu PO memutuskan.
- G3. Mengeksekusi proyek dalam sprint dengan pemeriksaan silang antaragen.
- G4. PO memegang kendali penuh di setiap titik keputusan dan bisa melihat semua yang terjadi di antaranya.
- G5. Sistem makin cerdas dari proyek ke proyek tanpa mengorbankan kendali PO.
- G6. Semua data, kunci API, dan artefak tetap di server milik pengguna.

**Non-tujuan v1** [U]
- Melatih model AI dari nol.
- Bertindak di dunia nyata atas nama PO (mengirim email ke pihak luar, membayar, submit ke jurnal atau portal hibah) tanpa persetujuan eksplisit.
- Kolaborasi banyak PO secara real-time dalam satu proyek.

## 4. Konsep inti (glosarium)

| Istilah | Arti di TimAI |
|---|---|
| **Proyek** | Satu tujuan yang dikerjakan satu tim, dengan workspace, backlog, dan anggaran sendiri |
| **Profil proyek** | Paket bawaan per jenis proyek: tim default, templat artefak, Definition of Done, dan pemeriksaan otomatis |
| **Brief** | Masukan awal PO: tujuan, konteks, batasan, tenggat, anggaran, lampiran |
| **Agen** | Satu anggota tim: peran + model + instruksi + izin alat |
| **Peran** | Templat tanggung jawab, misalnya Scrum Master, Researcher, Firmware Engineer |
| **Tier kecerdasan** | Kelas kemampuan model: `low`, `medium`, `high`, `xhigh` |
| **Runtime** | **API** (pemanggilan model langsung) atau **CLI** (agen coding di dalam sandbox) |
| **Ruang Tim** | Tempat diskusi antaragen, dimoderasi Scrum Master |
| **Putaran** | Setiap peserta rapat berbicara **satu kali**, lalu Scrum Master menyusun sintesis |
| **Titik Konfirmasi** | Pertanyaan Scrum Master ke PO di akhir setiap putaran: setuju atau lanjut diskusi |
| **Gerbang** | Keputusan besar PO: setujui tim, PRD, hasil sprint, penutupan |
| **Sprint** | Satu siklus kerja dengan cakupan, batas waktu, dan batas biaya |
| **Pelajaran** | Pengetahuan yang diambil sistem dari proyek (preferensi, aturan, pola sukses/gagal) dan dipakai lagi |

## 5. Siklus hidup proyek

```
[0 Brief] → [1 Klarifikasi] → [2 Usulan Tim] ══G1══▶ [3 Inception]
                                                       │
                     ┌─────────────────────────────────┘
                     ▼
        ┌──▶ Diskusi 1 putaran → Sintesis Scrum Master → TITIK KONFIRMASI PO
        │                                                  │        │
        └──────────── "lanjut diskusi" (+ arahan PO) ──────┘        │ "setuju"
                                                                     ▼
                                                     PRD/Rencana ══G2══▶ Sprint
                                                                     │
   ┌── [4 Planning: 1 putaran + konfirmasi] → [5 Eksekusi + Daily] → [6 Review ══G3══]
   │                                                                     │
   └──────────────── [7 Retrospective → Pelajaran] ◀─────────────────────┘
                              │ backlog habis / PO menutup
                              ▼
                  [8 Penutupan + konsolidasi pelajaran] ══G4══▶ Selesai
```

| Fase | Pelaku | Keluaran | Keputusan PO |
|---|---|---|---|
| 0 Brief | PO | Brief | — |
| 1 Klarifikasi | Agen Analis | Pertanyaan dan jawaban | PO menjawab (boleh dilewati) |
| 2 Usulan tim | Team Composer | Rancangan tim + estimasi biaya | **G1 Setujui tim** |
| 3 Inception | Seluruh tim | Agenda Inception dibahas satu per satu | **Titik Konfirmasi** tiap agenda, lalu **G2 Setujui PRD/Rencana** |
| 4 Sprint Planning | Tim | Sprint backlog, pembagian tugas | **Titik Konfirmasi** (satu putaran) |
| 5 Eksekusi | Agen pelaksana + reviewer | Artefak per item | Hanya bila agen bertanya atau ada hambatan |
| 6 Sprint Review | Tim → PO | Hasil sprint + bukti | **G3 Terima/tolak per item** |
| 7 Retrospective | Tim | Pelajaran usulan | PO menyetujui pelajaran yang disimpan |
| 8 Penutupan | Tim | Paket hasil akhir, laporan | **G4 Tutup proyek** |

### 5.1 Kerangka Scrum di TimAI

TimAI menerapkan Scrum secara utuh: ada tiga peran (*accountabilities*), tiga artefak beserta komitmennya, dan lima event. Satu-satunya penyesuaian adalah aturan diskusi satu putaran yang diakhiri konfirmasi PO.

**Peran**
| Scrum | Di TimAI |
|---|---|
| Product Owner | **Pengguna (manusia)**. Satu-satunya pihak yang mengurutkan Product Backlog dan menerima hasil |
| Scrum Master | **Agen Scrum Master**: memoderasi event, menjaga aturan, menghapus hambatan, menjadi penghubung ke PO |
| Developers | **Semua agen pelaksana dan reviewer** (developer, firmware engineer, writer, researcher, editor, dst.) yang membangun Increment |

**Artefak dan komitmen**
| Artefak | Komitmen | Siapa menetapkan | Keterangan |
|---|---|---|---|
| **Product Backlog** | **Product Goal** | PO (diusulkan tim saat Inception) | Daftar seluruh pekerjaan proyek, diurutkan PO |
| **Sprint Backlog** | **Sprint Goal** | Tim saat Sprint Planning, dikonfirmasi PO | Item yang dipilih untuk sprint + rencana tugas untuk menyelesaikannya |
| **Increment** | **Definition of Done** | DoD disepakati saat Inception | Hasil nyata yang lolos DoD dan siap ditunjukkan di Sprint Review |

**Hierarki dan alur penurunan**
```
Product Goal
  └─ Epik
       └─ Product Backlog Item (PBI) ── diurutkan PO, berestimasi, punya kriteria penerimaan
             │   (Sprint Planning: pilih PBI teratas sesuai kapasitas/velocity)
             ▼
        Sprint Backlog = Sprint Goal + PBI terpilih + Task per PBI
             │   (Eksekusi → Review silang → lolos DoD)
             ▼
        Increment ── ditunjukkan di Sprint Review (G3)
             │
             ├─ diterima PO → Done
             └─ ditolak / belum Done → kembali ke Product Backlog (diurutkan ulang)
```

Bentuk PBI mengikuti profil proyek: *user story* (Software/IoT), bagian proposal (Proposal), bagian manuskrip (Jurnal), bab/subbab (Buku). Task adalah langkah kerja di bawah PBI, misalnya "susun draf", "verifikasi rujukan", "review", "perbaikan".

**Event**
| Event Scrum | Di TimAI | Keputusan PO |
|---|---|---|
| Sprint | Wadah semua event; dibatasi waktu + biaya | — |
| Sprint Planning | Satu putaran: pilih PBI, rumuskan Sprint Goal, pecah jadi Task, tugaskan per agen | Titik Konfirmasi |
| Daily Scrum | Laporan per agen (selesai/sedang/hambatan) + rangkuman Scrum Master | Tidak perlu |
| Sprint Review | Tim menunjukkan Increment beserta bukti | **G3** terima/tolak per PBI |
| Sprint Retrospective | Satu putaran: apa yang perlu diperbaiki | Setujui pelajaran (FR-14) |
| Backlog Refinement (aktivitas berkelanjutan) | Tim memecah, mengestimasi, memperjelas PBI; PO mengurutkan | Urutan oleh PO |

**Aturan backlog**
1. Hanya PO yang mengubah **urutan** Product Backlog. Tim boleh mengusulkan PBI baru. PBI usulan tim masuk dengan label *usulan tim* sampai diterima PO saat refinement atau review.
2. **Sprint Backlog milik tim.** Tim boleh menambah atau mengubah Task selama sprint. Perubahan isi PBI dikabarkan ke PO.
3. **Sprint Goal tidak berubah** selama sprint. Bila goal menjadi tidak relevan, hanya PO yang boleh membatalkan sprint.
4. PBI yang tidak lolos DoD tidak boleh ditunjukkan sebagai Increment. Saat sprint berakhir, PBI itu kembali ke Product Backlog.
5. **Velocity** (jumlah poin PBI yang diterima per sprint) dipakai untuk Sprint Planning berikutnya dan untuk perkiraan tanggal selesai (FR-10.5).

**Contoh singkat: profil Artikel jurnal**
| Lapisan | Isi |
|---|---|
| Product Goal | Manuskrip siap submit ke jurnal target dalam 3 sprint |
| Epik | Pendahuluan & tinjauan pustaka; Metode; Hasil & pembahasan; Finalisasi |
| PBI (contoh) | "Pendahuluan memuat gap penelitian dengan ≥ 15 rujukan terverifikasi, ≤ 900 kata" (5 poin) |
| Sprint Goal (Sprint 1) | Pendahuluan dan Metode lengkap, lolos review Journal-Fit Reviewer |
| Task untuk PBI di atas | Research Lead memetakan gap → Academic Writer menyusun draf → Fact Checker memverifikasi rujukan → Language Editor menyunting → Journal-Fit Reviewer meninjau |
| Increment | Bagian Pendahuluan + Metode yang memenuhi DoD (rujukan terverifikasi, batas kata, gaya sitasi jurnal) |

### 5.2 Keluaran setiap tahapan

Setiap tahap **wajib** menghasilkan dokumen yang tersimpan di workspace proyek. Sebuah tahap tidak dianggap selesai sebelum keluarannya ada dan, bila ada penyetuju, sudah disetujui.

#### a. Keluaran umum (semua profil)

| Tahap | Keluaran | Isi minimal | Format | Disetujui |
|---|---|---|---|---|
| 0 Brief | **Brief Proyek** | Tujuan, latar, hasil yang diharapkan, kriteria sukses, tenggat, anggaran, bahasa, profil, daftar lampiran | Form → `brief.md` + JSON | — |
| 1 Klarifikasi | **Catatan Klarifikasi & Asumsi** | Pertanyaan agen, jawaban PO, asumsi untuk pertanyaan yang dilewati | `klarifikasi.md` | PO (menjawab) |
| 2 Usulan Tim | **Team Charter** | Daftar agen: peran, tier, model, runtime, alasan; relasi reviewer; estimasi biaya dan durasi (rentang); paket | `team-charter.md` + JSON | **G1** |
| 3 Inception, per agenda | **Notulen + Sintesis** | Kontribusi tiap agen (1 putaran), sintesis Scrum Master, opsi A/B, pertanyaan, keputusan PO | `notulen/agenda-NN.md` | Titik Konfirmasi |
| | **Decision Log** | Keputusan, alasan, alternatif, pemutus, tanggal | `decision-log.md` (bertambah terus) | — |
| 3 Inception, akhir | **Dokumen Inception** (PRD/Rencana sesuai profil, lihat 5.2b) | Isi sesuai templat profil | `.md` → DOCX/PDF | **G2** |
| | **Product Goal** | Satu pernyataan tujuan produk | di dokumen Inception | **G2** |
| | **Product Backlog** | Epik → PBI dengan kriteria penerimaan, estimasi, urutan | Board + `product-backlog.json` | **G2** |
| | **Definition of Done** | Kriteria umum + per jenis PBI | `dod.md` | **G2** |
| | **Rencana Rilis** | Jumlah sprint, cakupan per sprint, perkiraan tanggal dan biaya | `rencana-rilis.md` | **G2** |
| | **Risk Register** | Risiko, dampak, kemungkinan, mitigasi | `risiko.md` | **G2** |
| 4 Sprint Planning | **Sprint Plan** | Sprint Goal, PBI terpilih, Task per PBI, penugasan agen, batas waktu dan biaya | `sprint-NN/sprint-plan.md` + board | Titik Konfirmasi |
| 5 Eksekusi | **Artefak kerja** per Task | Draf, kode, gambar, tabel, dsb. | Berkas di `sprint-NN/kerja/` + commit Git | Reviewer agen |
| | **Catatan Review** | Temuan reviewer, keputusan lolos/perbaiki, hasil pemeriksaan otomatis | Komentar di kartu + `review-notes` | Reviewer agen |
| | **Laporan Daily** | Per agen: selesai, sedang, hambatan; rangkuman Scrum Master | `sprint-NN/daily/YYYY-MM-DD.md` | — |
| | **Lembar Tugas PO** (bila ada) | Panduan langkah + isian hasil dari PO | Form + lampiran PO | PO (mengisi) |
| 6 Sprint Review | **Paket Sprint Review** | Daftar PBI, bukti per PBI (tautan artefak, hasil uji/pemeriksaan), status DoD | `sprint-NN/review.md` | **G3** per PBI |
| | **Increment** | PBI yang diterima, digabung ke cabang utama workspace | Tag Git `sprint-NN` | **G3** |
| | **Laporan Sprint** | Sprint Goal tercapai/tidak, PBI diterima/ditolak, burndown, velocity, biaya vs batas | `sprint-NN/laporan-sprint.md` + grafik | — |
| 7 Retrospective | **Catatan Retro** | Yang berjalan baik, yang perlu diperbaiki, tindakan | `sprint-NN/retro.md` | — |
| | **Usulan Pelajaran** | Aturan/memori baru beserta bukti | Antrean "Yang Dipelajari Sistem" | PO |
| 8 Penutupan | **Paket Hasil Akhir** | Semua keluaran akhir profil (5.2b) | `final/` + ZIP | **G4** |
| | **Laporan Penutupan** | Ringkasan proyek, keluaran, keputusan penting, total biaya, velocity rata-rata, pelajaran | `laporan-penutupan.md` → PDF | **G4** |

#### b. Keluaran spesifik per profil

| Tahap | Software | IoT | Proposal penelitian | Artikel jurnal | Buku / book chapter |
|---|---|---|---|---|---|
| **3 Dokumen Inception** | PRD, arsitektur sistem, desain data & API, rencana uji | PRD sistem, arsitektur perangkat (sensor–MCU–jaringan–cloud), BOM, diagram koneksi, spesifikasi protokol & payload, rencana uji | Kerangka sesuai skema hibah, analisis gap & state of the art, rancangan metode, peta luaran & TKT, jadwal, draf RAB | Jurnal target + gaya selingkung, pernyataan kontribusi, kerangka IMRaD, peta bukti (klaim → sumber), rencana gambar/tabel | Outline buku/bab, profil pembaca, panduan gaya, glosarium istilah (ID–EN bila dwibahasa), pembagian bab ke penulis |
| **Bentuk PBI** | User story | User story + tugas perangkat | Bagian proposal | Bagian manuskrip | Bab / subbab |
| **5 Artefak kerja** | Kode + tes per story | Firmware, kode backend/dashboard, skema rangkaian, panduan perakitan & lembar uji (Tugas PO) | Draf bagian, tabel RAB, daftar pustaka terverifikasi | Draf bagian, tabel/gambar, daftar rujukan terverifikasi | Draf bab, catatan cek fakta, versi terjemahan |
| **6 Bukti Increment** | Fitur berjalan, hasil tes, catatan rilis | Hasil kompilasi, uji fungsi (simulasi atau data uji dari PO), validasi payload | Bagian lolos cek kelengkapan panduan, batas halaman, konsistensi angka | Bagian lolos review Journal-Fit, format sitasi sesuai jurnal | Bab lolos cek konsistensi istilah, gaya, dan proofread |
| **8 Hasil akhir** | Repo, dokumentasi, panduan deploy | Paket firmware + backend + dashboard, BOM, skema, panduan perakitan & uji, laporan uji | Naskah proposal DOCX/PDF sesuai templat + lampiran | Manuskrip siap submit, cover letter, highlight, berkas gambar, daftar periksa jurnal | Naskah lengkap per bab, daftar pustaka, indeks istilah, versi bahasa kedua (bila dwibahasa) |

#### c. Struktur folder workspace (templat)

```
proyek-<nama>/
├─ 00-brief/          brief.md · klarifikasi.md · lampiran/
├─ 01-tim/            team-charter.md
├─ 02-inception/      notulen/agenda-01.md … · decision-log.md · dokumen-inception.md
│                     product-backlog.json · dod.md · rencana-rilis.md · risiko.md
├─ sprints/
│  └─ sprint-01/      sprint-plan.md · daily/ · kerja/ · review.md
│                     laporan-sprint.md · retro.md
├─ final/             keluaran akhir sesuai profil · laporan-penutupan.md
└─ pembelajaran/      pelajaran-usulan.md · pelajaran-disetujui.md
```

#### d. Metadata wajib setiap dokumen

Setiap dokumen keluaran diawali blok metadata, sehingga asal-usulnya selalu bisa dilacak (NFR Ketertelusuran):

```yaml
proyek: <nama proyek>
tahap: <0–8 / nama tahap>
sprint: <nomor, bila ada>
dokumen: <jenis keluaran>
versi: <n>
dibuat_oleh: <agen · peran · model aktual>
direview_oleh: <agen reviewer>
status: draf | menunggu PO | disetujui | ditolak
disetujui_oleh: <PO> · <tanggal>
```

## 6. Lima profil proyek

Setiap profil menentukan tim default, artefak Inception, struktur backlog, Definition of Done (DoD), dan pemeriksaan otomatis. PO tetap bisa mengubah semuanya.

### 6.1 Ringkasan per profil

| Profil | Artefak Inception | Satuan backlog | Pemeriksaan otomatis | Keluaran akhir |
|---|---|---|---|---|
| **1. Software** | PRD, arsitektur, desain data/API, rencana uji | User story + kriteria penerimaan | Build, tes unit/integrasi, lint, pemindaian keamanan dasar | Repo kode, dokumentasi, panduan deploy |
| **2. IoT** | PRD sistem, arsitektur perangkat (sensor–MCU–jaringan–cloud), daftar komponen (BOM), diagram koneksi, protokol data | User story + tugas perangkat (firmware, rangkaian, integrasi, dashboard) | Kompilasi firmware (misal ESP32/Arduino), simulasi bila tersedia, validasi skema payload (MQTT/HTTP), tes backend | Kode firmware + backend + dashboard, BOM, skema rangkaian, panduan perakitan dan uji |
| **3. Proposal penelitian** | Kerangka proposal sesuai skema hibah (diunggah PO), analisis gap, metodologi, rencana luaran, jadwal, draf RAB | Bagian/bab proposal | Kelengkapan sesuai panduan skema, batas kata/halaman, cek sitasi dan rujukan, konsistensi angka RAB | Naskah proposal (DOCX/PDF) sesuai templat, lampiran |
| **4. Artikel jurnal** | Target jurnal dan gaya selingkung, kerangka IMRaD, peta bukti (klaim → sumber), rencana gambar/tabel | Bagian manuskrip (Abstrak, Pendahuluan, Metode, Hasil, Pembahasan, Kesimpulan) | Format referensi sesuai gaya jurnal, verifikasi DOI/rujukan, batas kata, konsistensi istilah, keterbacaan | Manuskrip siap submit, cover letter, highlight, tabel/gambar |
| **5. Buku / book chapter** | Outline buku/bab, sasaran pembaca, glosarium, panduan gaya, **bahasa** (Indonesia, Inggris, atau dwibahasa) | Bab / subbab | Konsistensi istilah dan gaya antarbab, cek rujukan, ejaan (PUEBI/KBBI untuk Indonesia, gaya akademik untuk Inggris), keselarasan terjemahan | Naskah per bab, daftar pustaka, indeks istilah |

### 6.2 Tim default per profil (paket Seimbang)

Tier di bawah adalah titik awal. Team Composer menyesuaikannya dengan kompleksitas brief (Bagian 10).

| Profil | Anggota default (peran · tier · runtime) |
|---|---|
| **Software** | Scrum Master · high · API — Business Analyst · high · API — Solution Architect · high · API — Backend Developer · medium · CLI — Frontend Developer · medium · CLI — QA Engineer · medium · CLI — Technical Writer · low · API |
| **IoT** | Scrum Master · high · API — Systems Analyst · high · API — Hardware/Electronics Designer · high · API — Embedded Firmware Engineer · medium · CLI — Backend & Dashboard Developer · medium · CLI — IoT Integration & QA Engineer · medium · CLI — Technical Writer · low · API |
| **Proposal penelitian** | Scrum Master · medium · API — Research Lead (gap & novelty) · high · API — Reviewer Metodologi · high · API — Grant Writer · medium · API — Budget Planner (RAB) · medium · API — Fact Checker · medium · API — Editor · low · API |
| **Artikel jurnal** | Scrum Master · medium · API — Research Lead · high · API — Statistician/Data Analyst · high · API — Academic Writer · medium · API — Journal-Fit Reviewer (meniru reviewer jurnal) · high · API — Fact Checker · medium · API — Language Editor · low · API |
| **Buku / book chapter** | Scrum Master · medium · API — Book Editor (penjaga outline & gaya) · high · API — Subject Matter Writer (1–3 agen) · medium · API — Fact Checker · medium · API — Translator/Bilingual Editor (bila dwibahasa) · high · API — Proofreader · low · API |

**Catatan IoT.** Agen tidak bisa menyentuh perangkat fisik. Hasil yang bergantung pada perangkat keras (perakitan, kalibrasi sensor, uji lapangan) masuk backlog sebagai **tugas PO/manusia** dan ditandai berbeda di Kanban. Agen menyiapkan panduan langkah dan lembar isian hasil uji. PO mengunggah hasilnya kembali (angka, foto, log serial) supaya tim bisa melanjutkan.

**Catatan akademik.** Agen dilarang mengarang sumber, data, atau hasil penelitian. Klaim tanpa rujukan yang terverifikasi ditandai **"perlu sumber"**. Data hasil eksperimen hanya berasal dari unggahan PO.

## 7. Kebutuhan fungsional

Prioritas: **P0** MVP, **P1** rilis kedua, **P2** lanjutan [U].

### FR-1 Intake brief

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-1.1 | Form brief: judul, tujuan, latar, hasil yang diharapkan, kriteria sukses, tenggat, anggaran biaya maksimum, bahasa keluaran | P0 |
| FR-1.2 | Pilih **profil proyek** (Software, IoT, Proposal penelitian, Artikel jurnal, Buku/book chapter, Umum) atau "deteksi otomatis" | P0 |
| FR-1.3 | Kolom tambahan per profil, misalnya: IoT (MCU, sensor, konektivitas, platform cloud); Proposal (skema hibah, unggah panduan & templat resmi, TKT awal/akhir, luaran wajib); Jurnal (target jurnal, gaya sitasi, batas kata, data/hasil yang dimiliki); Buku (judul, jumlah bab, bahasa, penerbit/gaya) | P0 |
| FR-1.4 | Unggah lampiran: PDF, DOCX, gambar, CSV/XLSX, ZIP/repo Git, BibTeX/RIS | P0 |
| FR-1.5 | **Wawancara klarifikasi**: agen Analis mengajukan ≤ 7 pertanyaan bila brief ambigu. Pertanyaan yang dilewati dicatat sebagai asumsi | P0 |

### FR-2 Team Composer (rekomendasi tim)

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-2.1 | Sistem menghasilkan daftar peran, jumlah agen per peran, tier kecerdasan, model yang disarankan, dan runtime, berangkat dari tim default profil (6.2) lalu disesuaikan dengan brief | P0 |
| FR-2.2 | Setiap rekomendasi disertai alasan singkat | P0 |
| FR-2.3 | Estimasi biaya dan durasi sebagai **rentang** | P0 |
| FR-2.4 | Paket **Hemat / Seimbang / Maksimal** | P1 |
| FR-2.5 | PO bebas menambah/menghapus agen, mengganti peran, model, tier, runtime. Estimasi diperbarui seketika | P0 |
| FR-2.6 | Peringatan konfigurasi berisiko: tanpa reviewer, tier peran kritis terlalu rendah, model tidak mendukung alat yang dibutuhkan | P0 |
| FR-2.7 | Simpan susunan tim sebagai templat pribadi | P1 |
| FR-2.8 | **G1**: PO menyetujui tim, lalu agen dibuat dan Inception dimulai | P0 |
| FR-2.9 | Rekomendasi memanfaatkan **riwayat kinerja** model per peran dari proyek-proyek sebelumnya (FR-14) | P1 |

### FR-3 Katalog peran

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-3.1 | Peran didefinisikan oleh: nama, deskripsi, tanggung jawab, artefak, kompetensi (penalaran, menulis akademik, coding, embedded, elektronika, riset, statistik, penerjemahan, review), tier minimum/default, alat yang diizinkan, templat prompt, kriteria selesai | P0 |
| FR-3.2 | **Scrum Master** selalu ada sebagai moderator dan satu-satunya agen yang bertanya langsung ke PO soal kelanjutan diskusi | P0 |
| FR-3.3 | Pustaka peran bawaan mencakup semua peran di 6.2 dan dapat diubah/ditambah | P0 |
| FR-3.4 | Peran **Reviewer** dapat ditautkan ke peran lain | P0 |
| FR-3.5 | Setiap peran berversi. Perubahan peran hasil pembelajaran (FR-14) membuat versi baru yang bisa dibandingkan dan dikembalikan | P1 |

### FR-4 Penyedia model dan katalog model

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-4.1 | **Koneksi API**: Anthropic, OpenAI, Google, OpenRouter, endpoint OpenAI-compatible (termasuk gateway/router buatan sendiri), model lokal (Ollama/vLLM) | P0 |
| FR-4.2 | **Koneksi CLI**: agen coding (Claude Code, Codex, Gemini CLI, OpenCode, dsb.) di kontainer sandbox | P1 |
| FR-4.3 | **Katalog model**: penyedia, nama, panjang konteks, harga input/output, dukungan tool use, vision, keluaran terstruktur, bahasa, skor kompetensi (1–5) | P0 |
| FR-4.4 | **Pemetaan tier** dapat diedit Admin; tidak ada model yang dikunci di kode | P0 |
| FR-4.5 | Health check berkala dan status model | P0 |
| FR-4.6 | **Fallback** per agen ke model cadangan dengan tier setara atau lebih tinggi; setiap pergantian dicatat | P1 |
| FR-4.7 | **Verifikasi identitas model**: catat model yang benar-benar menjawab (metadata respons) dan beri peringatan bila gateway mengganti model atau menyembunyikan error | P1 |
| FR-4.8 | Kunci API terenkripsi, tidak pernah terlihat oleh agen | P0 |

### FR-5 Runtime dan izin agen

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-5.1 | **Runtime API** (default untuk diskusi, perencanaan, riset, penulisan) | P0 |
| FR-5.2 | **Runtime CLI** di sandbox per tugas, bekerja di branch Git sendiri (default untuk kode software, firmware, dan backend IoT) | P1 |
| FR-5.3 | Alat bawaan: baca/tulis berkas workspace, cari di workspace, pencarian web dan pencarian literatur ilmiah (bisa dimatikan), eksekusi kode di sandbox, toolchain firmware (kompilasi), ubah kartu Kanban miliknya, kirim pesan ke Ruang Tim, ajukan pertanyaan ke PO | P0 |
| FR-5.4 | Izin per peran (*least privilege*) | P0 |
| FR-5.5 | Tindakan berisiko (akses domain baru, hapus berkas, push ke repo luar) menunggu persetujuan PO | P0 |

### FR-6 Ruang Tim: diskusi satu putaran

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-6.1 | Setiap diskusi punya agenda, peserta, moderator (Scrum Master), dan keluaran yang diharapkan | P0 |
| FR-6.2 | **Satu putaran**: setiap peserta yang relevan berbicara **tepat satu kali** dengan urutan yang ditentukan moderator. Peserta wajib membaca kontribusi sebelumnya dan menanggapi, tidak sekadar mengulang | P0 |
| FR-6.3 | Setelah putaran, Scrum Master menulis **sintesis**: usulan keputusan, poin setuju, poin beda pendapat (dengan opsi A/B), pertanyaan untuk PO, perkiraan biaya bila diskusi dilanjutkan | P0 |
| FR-6.4 | **Titik Konfirmasi PO** dengan tiga pilihan: **Setuju** (keputusan dicatat, lanjut ke langkah berikutnya), **Lanjut diskusi** (satu putaran lagi; PO boleh menambah arahan atau memilih peserta), **Ubah arah** (PO menulis keputusan sendiri; tim menyesuaikan) | P0 |
| FR-6.5 | Bila ada beda pendapat, PO dapat langsung memilih opsi A atau B tanpa putaran tambahan | P0 |
| FR-6.6 | Panjang kontribusi tiap agen dibatasi (default ≤ 400 kata [U]) dan setiap putaran memiliki plafon token | P0 |
| FR-6.7 | Keputusan masuk **Decision Log** (keputusan, alasan, alternatif, siapa memutuskan) | P0 |
| FR-6.8 | PO dapat menonton putaran secara langsung dan menyela kapan saja | P0 |
| FR-6.9 | **Pengelompokan konfirmasi**: bila beberapa diskusi selesai bersamaan, PO menerima satu layar berisi semua Titik Konfirmasi yang bisa diputuskan sekaligus | P1 |
| FR-6.10 | **Persetujuan otomatis opsional** per jenis diskusi (misalnya pembagian tugas teknis kecil) untuk PO yang ingin lebih sedikit interupsi. Mati secara default | P1 |
| FR-6.11 | Bila PO tidak merespons, sistem mengirim pengingat (in-app, email/webhook). Tim tidak melanjutkan diskusi tanpa jawaban; tim boleh mengerjakan item lain yang tidak terblokir | P0 |

### FR-7 Inception (menuju PRD/rencana)

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-7.1 | Agenda Inception per profil, misalnya: Software/IoT: tujuan → lingkup → kebutuhan → arsitektur → risiko → rencana sprint; Proposal: kesesuaian skema → gap & novelty → metodologi → luaran & TKT → jadwal & RAB; Jurnal: target jurnal → kontribusi → kerangka & peta bukti → rencana analisis; Buku: sasaran pembaca → outline → panduan gaya & glosarium → pembagian bab | P0 |
| FR-7.2 | Setiap agenda = satu diskusi satu putaran + Titik Konfirmasi (FR-6) | P0 |
| FR-7.3 | Hasil yang sudah dikonfirmasi digabung menjadi artefak Inception sesuai profil (6.1) | P0 |
| FR-7.4 | **Product Backlog** awal: epik → item dengan kriteria penerimaan, estimasi, prioritas usulan, peran pelaksana; tugas fisik ditandai "Tugas PO" | P0 |
| FR-7.5 | **Definition of Done** proyek dan per jenis item | P0 |
| FR-7.6 | **Rencana rilis**: jumlah sprint, cakupan per sprint, perkiraan tanggal dan biaya (rentang) | P0 |
| FR-7.7 | **G2**: Setujui / Minta revisi (komentar per bagian) / Batalkan | P0 |
| FR-7.8 | Artefak berversi dengan diff antarversi | P0 |

### FR-8 Mesin Scrum

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-8.1 | Sprint ditentukan oleh cakupan + batas waktu + batas biaya | P0 |
| FR-8.2 | **Sprint Planning**: satu putaran diskusi; Scrum Master mengusulkan **Sprint Goal**, PBI terpilih dari urutan teratas Product Backlog sesuai velocity, pemecahan Task, dan pembagian ke agen, lalu Titik Konfirmasi PO. Hasilnya menjadi **Sprint Backlog** (5.1) | P0 |
| FR-8.3 | **Daily Stand-up** sebagai *laporan*, bukan diskusi: tiap agen menulis selesai/sedang/hambatan; Scrum Master merangkum untuk PO. Tidak memerlukan konfirmasi | P0 |
| FR-8.4 | **Hambatan**: Scrum Master mengalihkan tugas atau mengeskalasi ke PO. Bila perlu diskusi, berlaku aturan satu putaran | P0 |
| FR-8.5 | **Sprint Review (G3)**: tim menyajikan item selesai beserta bukti; PO **Terima** / **Tolak dengan catatan** per item | P0 |
| FR-8.6 | **Retrospective**: satu putaran; keluarannya usulan pelajaran (FR-14) yang disetujui PO | P1 |
| FR-8.7 | **Backlog refinement**: PO mengubah prioritas (drag-and-drop), menambah item, meminta pemecahan item besar | P0 |
| FR-8.8 | PO dapat menjeda, melanjutkan, menghentikan sprint | P0 |

### FR-9 Eksekusi dan kendali mutu

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-9.1 | Workspace proyek berupa repo Git internal; semua artefak berversi | P0 |
| FR-9.2 | Setiap tugas di branch sendiri, digabung setelah lolos review | P0 |
| FR-9.3 | **Review silang wajib** oleh agen reviewer sebelum item masuk Done | P0 |
| FR-9.4 | Pemeriksaan otomatis sesuai profil (6.1) | P1 |
| FR-9.5 | Perbaikan otomatis setelah review dibatasi **1 kali** [U] demi hemat token. Bila masih gagal, item masuk kolom **Waiting PO** dengan ringkasan masalah | P0 |
| FR-9.6 | Agen menyatakan ketidakpastian ("tidak tahu", "data tidak tersedia"), dilarang mengarang sumber atau data; Fact Checker memverifikasi rujukan | P0 |
| FR-9.7 | **Tugas PO** (pekerjaan fisik/manusia) punya form isian hasil; tim baru melanjutkan setelah hasil diunggah | P0 |

### FR-10 Kanban dan manajemen proyek

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-10.1 | Kolom bawaan: **Product Backlog · Sprint Backlog · In Progress · In Review · Waiting PO · Done · Blocked**. Bisa diatur | P0 |
| FR-10.2 | Kartu: judul, deskripsi, kriteria, agen pelaksana, reviewer, estimasi, prioritas, label, sprint, sub-tugas, dependensi, tautan artefak, aktivitas, komentar; penanda **Tugas PO** | P0 |
| FR-10.3 | Tampilan Board, List (P0), Timeline/Gantt, Kalender (P1) | P0/P1 |
| FR-10.4 | Burndown sprint, burnup rilis, velocity | P1 |
| FR-10.5 | **Perkiraan tanggal selesai** berbasis velocity nyata, ditampilkan sebagai rentang; sprint pertama berlabel "estimasi awal" | P1 |
| FR-10.6 | Filter dan pencarian | P0 |
| FR-10.7 | Milestone dan tenggat, misalnya tanggal tutup hibah atau deadline call for chapter; peringatan bila perkiraan melewati tenggat | P1 |
| FR-10.8 | PO mengubah kartu langsung; perubahan saat sprint berjalan dikabarkan ke Scrum Master | P0 |

### FR-11 Dashboard, biaya, dan observabilitas

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-11.1 | Dashboard: fase, progres sprint, **jumlah Titik Konfirmasi menunggu**, hambatan, biaya vs anggaran, perkiraan selesai | P0 |
| FR-11.2 | Token dan biaya per agen, peran, diskusi, sprint, proyek | P0 |
| FR-11.3 | Batas anggaran dengan peringatan 50/80/100% [U]; pada 100% eksekusi dijeda | P0 |
| FR-11.4 | Panel "Agen Sekarang" | P0 |
| FR-11.5 | Log lengkap pemanggilan model dan alat | P0 |

### FR-12 Notifikasi

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-12.1 | Kejadian: Titik Konfirmasi menunggu, gerbang menunggu, Tugas PO, anggaran, sprint selesai, item Blocked, kegagalan model | P0 |
| FR-12.2 | Kanal: in-app (P0), email dan webhook ke Telegram/n8n (P1) | P0/P1 |
| FR-12.3 | Ringkasan harian | P2 |

### FR-13 Hasil dan integrasi

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-13.1 | Unduh: Markdown, DOCX (mengikuti templat yang diunggah PO), PDF, ZIP workspace, BibTeX/RIS | P0 |
| FR-13.2 | Push ke GitHub/GitLab dengan persetujuan PO | P1 |
| FR-13.3 | Laporan penutupan: ringkasan, keluaran, keputusan penting, biaya, pelajaran | P1 |
| FR-13.4 | Webhook/API keluar untuk otomasi | P2 |

### FR-14 Pembelajaran berkelanjutan

**Prinsip kejujuran.** Model AI tidak bertambah cerdas hanya karena dipakai. Bobotnya tidak berubah setelah percakapan, dan ini juga berlaku untuk asisten AI seperti Claude, yang "mengingat" lewat catatan memori terpisah, bukan karena modelnya berubah. Karena itu, kecerdasan TimAI tumbuh di **tingkat sistem**: apa yang diingat, aturan yang dipakai, cara memilih model, dan contoh terbaik yang diberikan ke agen. Semua yang dipelajari bisa dilihat, diedit, dan dihapus PO.

| ID | Lapisan belajar | Cara kerja | Prio |
|---|---|---|---|
| FR-14.1 | **Memori preferensi PO** | Diambil dari keputusan di Titik Konfirmasi, alasan penolakan di Sprint Review, dan suntingan PO pada artefak, misalnya "PO tidak suka kalimat transisi klise" atau "gaya sitasi default APA 7". Disimpan sebagai aturan usulan, aktif setelah disetujui PO | P0 |
| FR-14.2 | **Pustaka pengalaman** | Artefak yang diterima PO (bab proposal, firmware, manuskrip) diindeks dan dijadikan **contoh rujukan** (*few-shot*) untuk proyek sejenis berikutnya | P1 |
| FR-14.3 | **Pelajaran retrospektif** | Hasil retro ("Fact Checker harus dilibatkan sebelum Writer menyelesaikan bab") menjadi aturan tim per profil | P1 |
| FR-14.4 | **Rapor kinerja model per peran** | Setiap item mencatat model, peran, diterima/ditolak, jumlah perbaikan, biaya. Skor kompetensi di katalog diperbarui otomatis sehingga Team Composer memilih model yang terbukti berhasil untuk peran itu | P1 |
| FR-14.5 | **Penyempurnaan peran dan prompt** | Sistem mengusulkan perubahan instruksi peran berdasarkan pola penolakan; versi baru diuji pada proyek berikutnya dan bisa dikembalikan | P2 |
| FR-14.6 | **Kalibrasi estimasi** | Rasio estimasi vs aktual (token, waktu) per profil dipakai untuk mengoreksi estimasi berikutnya | P1 |
| FR-14.7 | **Ekspor dataset** | Pasangan instruksi–hasil yang diterima PO dapat diekspor untuk *fine-tuning* model lokal, bila PO menginginkannya | P2 |
| FR-14.8 | **Kendali PO** | Halaman "Yang Dipelajari Sistem": daftar aturan, memori, contoh rujukan, dan skor model, dengan aksi setujui/edit/nonaktifkan/hapus. Cakupan: global, per profil, atau per proyek | P0 |
| FR-14.9 | **Pengaman** | Pelajaran dari satu kejadian tidak langsung jadi aturan permanen; perlu persetujuan PO atau muncul berulang (≥ 2 kali [U]). Data rahasia proyek tidak dipakai sebagai contoh lintas proyek bila proyek ditandai "rahasia" | P0 |

### FR-15 Administrasi self-hosted

| ID | Kebutuhan | Prio |
|---|---|---|
| FR-15.1 | Instalasi `docker compose up`, konfigurasi `.env` dan wizard awal | P0 |
| FR-15.2 | Pengguna (Admin, PO, Viewer), login email+password; SSO di P2 | P0 |
| FR-15.3 | Penyedia, katalog model, tier, harga | P0 |
| FR-15.4 | Batas sumber daya: agen paralel global, CPU/RAM sandbox | P0 |
| FR-15.5 | Backup/restore (database, berkas, basis pembelajaran) | P1 |
| FR-15.6 | Pembaruan versi dengan migrasi otomatis | P1 |

## 8. Kebutuhan non-fungsional

| Area | Kebutuhan |
|---|---|
| **Hemat token** | Satu putaran per diskusi; batas kata per kontribusi; ringkasan konteks bergulir; agen hanya menerima konteks yang relevan dengan tugasnya (diambil lewat pencarian semantik), bukan seluruh riwayat |
| **Keamanan** | Kunci API terenkripsi; sandbox per tugas tanpa akses host; egress jaringan sandbox dibatasi daftar izin |
| **Kendali biaya** | Batas per diskusi, sprint, dan proyek ditegakkan di orkestrator |
| **Keandalan** | Checkpoint per langkah; restart server melanjutkan dari langkah terakhir; proyek bisa menunggu jawaban PO berhari-hari tanpa kehilangan state |
| **Ketertelusuran** | Setiap artefak terlacak ke tugas, agen, model, dan diskusi yang menghasilkannya |
| **Kejujuran keluaran** | Ketidakpastian wajib dinyatakan; rujukan diverifikasi sebelum diterima |
| **Kinerja** | Interaksi UI < 300 ms [U]; status agen real-time (WebSocket/SSE) |
| **Skalabilitas** | ≥ 5 proyek aktif dan ≥ 20 agen paralel per instalasi [U] |
| **Privasi** | Semua data di server pengguna; tidak ada telemetri ke luar secara default |
| **Bahasa** | Antarmuka Indonesia dan Inggris; keluaran mengikuti brief, termasuk dwibahasa untuk buku |
| **Portabilitas** | Linux x86_64/ARM64 dengan Docker; Windows lewat Docker Desktop/WSL2 |

## 9. Arsitektur usulan [U]

```
                    ┌─────────────── Browser PO / Viewer ───────────────┐
                    │ Dashboard · Ruang Tim · Konfirmasi · Kanban ·      │
                    │ Review · Yang Dipelajari Sistem                    │
                    └──────────────▲──────────────────┬──────────────────┘
                                   │ WebSocket/SSE    │ REST
┌──────────────────────────────────┴──────────────────▼──────────────────────────┐
│ API Server: auth, proyek, Kanban, artefak, gerbang & konfirmasi                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Orchestrator (state machine tahan restart)                                      │
│ Team Composer · Meeting Engine (1 putaran) · Scrum Engine · Budget Guard ·      │
│ Learning Engine (memori, rapor model, kalibrasi, pustaka contoh)                │
├─────────────────────────┬──────────────────────────┬────────────────────────────┤
│ Agent Runtime (API)      │ Sandbox Runner (CLI,     │ Model Gateway              │
│                          │ firmware toolchain, Git) │ routing, harga, fallback,  │
│                          │                          │ verifikasi model aktual    │
├─────────────────────────┴──────────────────────────┴────────────────────────────┤
│ PostgreSQL + pgvector │ Redis (antrean, pub/sub) │ MinIO (berkas) │ Git internal │
└─────────────────────────────────────────────────────────────────────────────────┘
```

- **Orchestrator**: mesin workflow tahan restart (misalnya Temporal), atau tabel state + worker antrean.
- **Model Gateway**: pustaka gateway yang sudah ada atau buatan sendiri. Wajib mencatat model aktual yang menjawab dan error yang terjadi, karena gateway yang diam-diam mengganti model sulit dilacak.
- **Sandbox**: Docker dengan profil terbatas. Untuk IoT, sertakan image toolchain (misalnya PlatformIO/Arduino CLI untuk ESP32).
- **Learning Engine**: tabel aturan/memori berversi, indeks vektor untuk pustaka contoh, tabel statistik kinerja model per peran.

## 10. Spesifikasi Team Composer

**Masukan**: brief, profil proyek, jawaban klarifikasi, tenggat, anggaran, paket, katalog peran, katalog model, rapor kinerja model (FR-14.4).

**Langkah**
1. **Mulai dari tim default profil** (6.2).
2. **Analisis brief** (model tier `high`), dengan keluaran terstruktur:
   - kompetensi tambahan beserta bobotnya;
   - kompleksitas (1–5);
   - ukuran (S/M/L/XL);
   - risiko domain.
3. **Penyesuaian peran**: tambah peran untuk kompetensi berbobot ≥ 3 yang belum tertutup, dan hapus peran yang tidak relevan. Contoh: proposal tanpa RAB menghapus Budget Planner; buku dwibahasa menambah Translator.
4. **Jumlah agen**: S = 1 per peran pelaksana; M = 1–2; L/XL = 2–3 untuk pelaksana utama. Peran koordinasi selalu 1 [U].
5. **Tier**: tier = max(tier minimum peran, f(kompleksitas, risiko)).
6. **Model**: di antara model aktif pada tier itu, pilih skor tertinggi:
   `0,4×kecocokan kompetensi + 0,3×rapor kinerja di peran ini + 0,3×(1 − biaya ternormalisasi)`.
   Syarat wajib (tool use, vision, konteks, bahasa) diperiksa lebih dulu. Bila belum ada riwayat, bobot rapor dialihkan ke kecocokan kompetensi.
7. **Estimasi**: jumlah item × token per item per peran × harga, ditambah biaya diskusi satu putaran. Hasilnya dikoreksi faktor kalibrasi (FR-14.6).
8. **Validasi**: reviewer tersedia, biaya ≤ anggaran, model sehat.

## 11. Contoh alur: Titik Konfirmasi

> **Proyek**: Artikel jurnal, "Deteksi bau TPS berbasis ESP32 dan K-Means"
> **Agenda Inception 2 dari 4**: Kontribusi dan target jurnal
>
> *Putaran (masing-masing 1 kali bicara)*: Research Lead → Journal-Fit Reviewer → Statistician
>
> **Sintesis Scrum Master**
> - Usulan keputusan: kontribusi utama = pipeline edge-clustering berbiaya rendah dengan validasi lapangan.
> - Beda pendapat:
>   - **A**: target jurnal IoT terapan (Research Lead);
>   - **B**: target jurnal sensor/instrumentasi (Journal-Fit Reviewer).
> - Pertanyaan untuk PO: berapa jumlah titik pengambilan data lapangan yang Anda miliki?
> - Bila diskusi dilanjutkan: ±1 putaran, perkiraan biaya Rp X.
>
> **[Setuju dengan A]  [Setuju dengan B]  [Lanjut diskusi + arahan]  [Ubah arah]**

## 12. Model data inti [U]

| Entitas | Atribut utama |
|---|---|
| **User** | id, nama, email, peran sistem |
| **Project** | id, PO, judul, profil, brief, kolom profil, status/fase, tenggat, anggaran, bahasa, rahasia? |
| **ProjectProfile** | id, nama, tim default, agenda Inception, templat artefak, DoD, pemeriksaan |
| **Attachment** | id, proyek, berkas, ringkasan, embedding |
| **RoleTemplate** | id, versi, nama, kompetensi{}, tier_min, tier_default, tools[], prompt, DoD |
| **Provider / Model** | koneksi, kapabilitas, harga, skor kompetensi, tier, status |
| **Agent** | id, proyek, peran (versi), model, cadangan, runtime, izin |
| **Discussion** | id, proyek, jenis, agenda, peserta, urutan, putaran ke-n, status, sintesis, biaya |
| **Contribution** | id, diskusi, agen, isi, token |
| **Confirmation** | id, diskusi, opsi, pilihan PO, arahan PO, waktu |
| **Decision** | id, diskusi, keputusan, alasan, alternatif, pemutus |
| **Artifact** | id, proyek, jenis, path, versi, pembuat, status review |
| **ProductGoal** | id, proyek, pernyataan, status, tanggal disetujui |
| **Epic** | id, proyek, judul, urutan |
| **BacklogItem (PBI)** | id, epik, judul, jenis (story/bagian/bab), kriteria penerimaan, estimasi poin, **urutan PO**, status, asal (PO/usulan tim), sprint, penanda `po_task` |
| **Sprint** | id, proyek, nomor, **Sprint Goal**, mulai, selesai, batas biaya, status, velocity tercapai |
| **Task** | id, PBI, agen, jenis langkah, branch, status, percobaan |
| **Increment** | id, sprint, PBI yang lolos DoD, artefak, keputusan PO per PBI |
| **Gate** | id, jenis (G1–G4), objek, keputusan, komentar |
| **UsageRecord** | agen, model aktual, token, biaya, waktu |
| **Lesson** | id, lapisan (preferensi/retro/peran), cakupan, isi, sumber bukti, status (usulan/aktif/nonaktif), jumlah kemunculan |
| **ModelScorecard** | model, peran, profil, item, diterima, ditolak, rata-rata perbaikan, biaya rata-rata |
| **ExampleLibrary** | id, profil, jenis artefak, artefak sumber, embedding, izin lintas proyek |

## 13. Layar utama [U]

1. **Beranda**: proyek, status, jumlah konfirmasi menunggu.
2. **Buat Proyek**: pilih profil → brief → klarifikasi.
3. **Rancang Tim**: kartu agen, paket, estimasi, *Setujui Tim*.
4. **Ruang Tim**: putaran langsung, sintesis, tombol konfirmasi.
5. **Kotak Konfirmasi**: semua Titik Konfirmasi dan gerbang yang menunggu, bisa diputuskan sekaligus.
6. **Tinjau PRD/Rencana**: komentar per bagian, diff versi.
7. **Kanban**: board/list/timeline/kalender.
8. **Sprint Review**: terima/tolak per item.
9. **Dashboard**: progres, burndown, biaya, perkiraan selesai.
10. **Artefak**: workspace dan pratinjau.
11. **Yang Dipelajari Sistem**: aturan, memori, contoh rujukan, rapor model.
12. **Pengaturan**: penyedia, model & tier, peran, profil proyek, notifikasi, pengguna.

## 14. Rencana rilis [U]

| Fase | Cakupan | Kriteria selesai |
|---|---|---|
| **MVP** | Profil **Proposal penelitian** dan **Artikel jurnal** (runtime API saja, paling cepat memberi manfaat); Team Composer (Seimbang); Ruang Tim satu putaran + Titik Konfirmasi; Inception → rencana + backlog; G1–G3; Scrum dasar; Kanban Board/List; biaya + batas anggaran; memori preferensi PO + halaman "Yang Dipelajari Sistem"; unduh DOCX/MD; Docker Compose | Satu proposal dan satu manuskrip selesai end-to-end |
| **v1.1** | Profil **Software** dan **IoT** (runtime CLI + sandbox + toolchain firmware); Tugas PO; review silang otomatis; retrospektif; rapor kinerja model; kalibrasi estimasi; Timeline/Kalender; notifikasi email/webhook | Satu proyek IoT selesai dengan firmware yang dapat dikompilasi dan Tugas PO tercatat |
| **v1.2** | Profil **Buku/book chapter** dwibahasa; pustaka pengalaman (contoh rujukan); paket Hemat/Maksimal; verifikasi model aktual; laporan penutupan; Viewer | Satu book chapter dwibahasa selesai dengan konsistensi istilah lolos pemeriksaan |
| **Lanjutan** | Penyempurnaan prompt otomatis, ekspor dataset fine-tuning, profil "Umum", SSO | — |

Urutan MVP di atas adalah usulan: profil penulisan akademik tidak memerlukan sandbox, sehingga lebih cepat dibangun dan diuji. Bila PO lebih membutuhkan profil Software/IoT terlebih dahulu, urutan dapat ditukar.

## 15. Metrik keberhasilan [U]

Target awal, ditinjau ulang setelah pilot.

| Metrik | Target awal |
|---|---|
| Usulan tim disetujui dengan ≤ 2 perubahan | ≥ 70% |
| Titik Konfirmasi yang langsung "Setuju" (tanpa putaran tambahan) | ≥ 60%, **naik** dari proyek ke proyek |
| Item diterima PO pada review pertama | ≥ 75%, **naik** dari proyek ke proyek |
| Rata-rata token per diskusi | turun ≥ 20% dibanding diskusi multi-putaran |
| Selisih biaya aktual vs estimasi | ≤ ±30%, menyempit seiring kalibrasi |
| Waktu PO per sprint | ≤ 20 menit |
| Pelajaran usulan yang disetujui PO | ≥ 40% |

Tren "naik dari proyek ke proyek" adalah ukuran utama untuk tujuan G5 (sistem makin cerdas).

## 16. Risiko dan mitigasi

| Risiko | Mitigasi |
|---|---|
| PO terlalu sering diminta konfirmasi | Konfirmasi dikelompokkan, opsi A/B langsung, persetujuan otomatis opsional untuk diskusi kecil, Daily bukan diskusi |
| Satu putaran terlalu dangkal untuk topik sulit | Sintesis wajib memuat beda pendapat dan perkiraan biaya putaran berikutnya, sehingga PO bisa memilih melanjutkan secara sadar |
| Halusinasi fakta dan rujukan | Fact Checker, larangan mengarang, verifikasi rujukan, data eksperimen hanya dari PO |
| Agen saling setuju tanpa kritik | Peran reviewer wajib; reviewer memakai model dari penyedia berbeda bila memungkinkan [U] |
| Sistem "belajar" hal yang keliru | Pelajaran perlu persetujuan PO atau kemunculan berulang; semua bisa dinonaktifkan dan dihapus |
| Kebocoran data antarproyek lewat pustaka contoh | Penanda proyek rahasia; izin lintas proyek per artefak |
| Gateway mengganti model atau menyembunyikan error | Log model aktual, peringatan ketidakcocokan |
| Tugas IoT bergantung perangkat fisik | Tugas PO terpisah dengan form hasil uji |
| Estimasi meleset | Rentang, label "estimasi awal", kalibrasi |

## 17. Pertanyaan terbuka

1. Satuan sprint yang paling nyaman: jam, hari, atau jumlah item?
2. Berapa lama sistem menunggu jawaban Titik Konfirmasi sebelum mengirim pengingat?
3. Untuk proposal penelitian, apakah templat dan panduan skema selalu diunggah PO per proyek, atau disimpan sebagai pustaka templat di aplikasi?
4. Untuk buku dwibahasa: ditulis dalam satu bahasa lalu diterjemahkan, atau ditulis paralel di dua bahasa?
5. Apakah PO ingin bisa ikut "berbicara" dalam putaran sebagai peserta, selain memutuskan di akhir?
6. Profil mana yang paling mendesak untuk MVP: akademik (usulan) atau Software/IoT?
7. Distribusi aplikasi: pemakaian pribadi, institusi (misalnya kampus), atau produk komersial?

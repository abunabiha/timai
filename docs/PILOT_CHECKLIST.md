# Daftar Periksa Pilot Proyek Nyata (Pilot Checklist) TimAI

Panduan persiapan bagi **Product Owner (PO)** sebelum menjalankan proyek nyata pertama (proposal penelitian hibah atau artikel manuskrip jurnal) di platform TimAI.

---

## 1. Penyedia Model AI & Kunci API (LLM Providers)

Pastikan minimal satu penyedia model AI siap digunakan. Untuk hasil optimal dengan biaya hemat (skema tiering PRD TimAI), siapkan kunci API berikut:

- [ ] **Kunci API Penyedia Aktif:**
  - **Anthropic Claude** (Direkomendasikan untuk peran Tier High/XHigh seperti *Research Lead*, *Reviewer Metodologi*, dan *Grant Writer*):
    - Dapatkan API key dari [console.anthropic.com](https://console.anthropic.com).
    - Model yang didukung: `claude-3-5-sonnet`, `claude-3-7-sonnet`, `claude-3-5-haiku`.
  - **OpenAI** (Direkomendasikan untuk Tier Med/High):
    - Dapatkan API key dari [platform.openai.com](https://platform.openai.com).
    - Model yang didukung: `gpt-4o`, `gpt-4o-mini`, `o1-mini`.
  - **Google Gemini** (Opsi ekonomis dengan konteks panjang):
    - Dapatkan API key dari [aistudio.google.com](https://aistudio.google.com).
    - Model yang didukung: `gemini-1.5-pro`, `gemini-2.0-flash`.
  - **Ollama / Local LLM** (Opsional untuk lingkungan lokal offline/bebas biaya):
    - Model lokal: `llama3.3:70b`, `deepseek-r1:8b`, `qwen2.5:14b`.
- [ ] **Cek Saldo / Pagu Kredit API:**
  - Pastikan akun penyedia memiliki saldo kredit aktif (minimal \$10 - \$25 untuk 1 proyek proposal lengkap 2-3 sprint).
  - Batas pengeluaran (spending limits) di dasbor penyedia telah diatur agar tidak terjadi penagihan berlebih.
- [ ] **Daftarkan Penyedia di TimAI:**
  - Masuk sebagai Admin (`admin@timai.local`).
  - Masuk ke menu **Penyedia Model** (`/providers`).
  - Tambahkan penyedia dan masukkan API Key. Kunci API akan otomatis dienkripsi dengan standar militer AES-256-GCM dan termasker aman.
  - Klik **Uji Koneksi** untuk memastikan status penyedia `online`.

---

## 2. Dokumen Panduan Skema Hibah (Untuk Profil Proposal Penelitian)

Jika proyek pertama adalah penyusunan proposal penelitian hibah (misal: Kemendikbudristek Bima, Kedaireka Matching Fund, LPDP RISPRO, BRIN, atau internal universitas):

- [ ] **Buku Panduan Resmi Skema (PDF):**
  - Siapkan berkas panduan edisi terbaru (misal: *Panduan Penelitian dan Pengabdian kepada Masyarakat Edisi XV*).
  - Format yang didukung untuk diunggah: `.pdf` atau `.docx`.
- [ ] **Templat Format Proposal Baku (.docx):**
  - Siapkan templat resmi bab proposal (Judul, Ringkasan, Latar Belakang, Tinjauan Pustaka, Metodologi, Jadwal, Justifikasi Anggaran).
- [ ] **Standar Biaya Masukan (SBM) Terbaru:**
  - Catatan batas honorarium, biaya bahan habis pakai, sewa alat laboratorium, dan biaya perjalanan dinas sesuai pagu skema.
- [ ] **Target Tingkat Kesiapterapan Teknologi (TKT):**
  - Tentukan TKT awal dan target TKT akhir proyek (misal: TKT 1-3 untuk riset dasar, TKT 4-6 untuk riset terapan).

---

## 3. Pedoman Jurnal Sasaran (Untuk Profil Artikel Jurnal)

Jika proyek pertama adalah penulisan manuskrip artikel jurnal ilmiah bereputasi (Scopus / WoS / Sinta):

- [ ] **Author Guidelines / Pedoman Penulis Jurnal Sasaran:**
  - Simpan teks pedoman penulisan jurnal sasaran (nama jurnal, penerbit: Elsevier, IEEE, Springer, dsb.).
  - Batasan jumlah kata (misal: 6.000 - 8.000 kata).
  - Format sitasi dan daftar pustaka yang diwajibkan (misal: IEEE, APA 7th Edition, Harvard, Vancouver).
- [ ] **Kumpulan Makalah Rujukan / State-of-the-Art:**
  - Siapkan 10 - 20 berkas referensi utama dalam format PDF atau ekspor pustaka (`.bib` / BibTeX atau `.ris`).
  - Unggah ke tab lampiran brief proyek agar diekstrak otomatis oleh sistem.
- [ ] **Data Hasil Eksperimen / Pengujian:**
  - Siapkan berkas tabel data hasil pengujian dalam format `.csv` atau ringkasan temuan empiris.

---

## 4. Parameter Anggaran & Waktu (Project Parameters)

- [ ] **Tenggat Waktu (Target Deadline):**
  - Tentukan tanggal tenggat penyelesaian draf akhir (disarankan minimal 7 - 14 hari kerja untuk 2-3 sprint).
- [ ] **Pagu Anggaran Maksimum Proyek (Budget Ceiling):**
  - Tetapkan anggaran biaya pemanggilan model dalam IDR (misal: Rp 2.000.000 - Rp 5.000.000).
  - TimAI akan secara otomatis menghentikan sementara (pause) eksekusi agen jika mencapai 100% pagu hingga PO menyetujui penambahan pagu.
- [ ] **Penanda Kerahasiaan (Secret Project):**
  - Jika proposal atau artikel mengandung paten/kekayaan intelektual sensitif, aktifkan toggle **Proyek Rahasia (is_secret = True)** saat pembuatan brief.
  - Penanda ini mengunci seluruh memori dan pelajaran sistem agar tidak bocor lintas proyek.

---

## 5. Kesiapan Peran Product Owner (PO Availability)

Dalam metode Scrum yang diadaptasi oleh TimAI, agen AI bekerja mandiri namun PO memegang kendali penuh pada gerbang strategis:

- [ ] **Gerbang G1 (Persetujuan Tim):** PO meninjau komposisi tim agen, tier model, estimasi biaya, dan menandatangani *Team Charter*.
- [ ] **Titik Konfirmasi Inception:** PO memilih arahan saat Scrum Master mengajukan Opsi A vs Opsi B pada sintesis agenda.
- [ ] **Gerbang G2 (Persetujuan Dokumen Inception & Backlog):** PO menyetujui Product Goal, DoD, dan urutan Product Backlog sebelum sprint dimulai.
- [ ] **Gerbang G3 (Sprint Review):** PO menerima (accept) atau menolak (reject) draf tiap PBI. Item yang ditolak otomatis kembali ke Product Backlog untuk diperbaiki pada sprint berikutnya.
- [ ] **Gerbang G4 (Penutupan Proyek):** PO menerima paket hasil akhir (`paket-hasil-akhir.zip` dan `laporan-penutupan.md/pdf`).

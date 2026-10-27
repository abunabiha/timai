# Checklist Milestone TimAI (Prompt 1 - 10)

- [x] **Prompt 1: Kerangka proyek dan Docker Compose**
  - Kriteria Selesai:
    - `docker compose up` menjalankan semua layanan tanpa error.
    - `/health` mengembalikan status database dan redis.
    - `make test` dan `make lint` lolos (minimal satu tes per layanan).

- [x] **Prompt 2: Model data, autentikasi, peran pengguna**
  - Kriteria Selesai:
    - Migrasi naik dan turun bersih.
    - Tes hak akses lolos.
    - Halaman login dan wizard Admin berfungsi.

- [x] **Prompt 3: Model Gateway, katalog model, FakeProvider**
  - Kriteria Selesai:
    - Admin bisa menambah penyedia, menguji koneksi, dan melihat daftar model.
    - Tes membuktikan: model aktual tercatat, fallback bekerja, kunci tidak bocor di log atau respons API.

- [x] **Prompt 4: Brief, klarifikasi, katalog peran, Team Composer**
  - Kriteria Selesai:
    - Alur dari brief sampai G1 berjalan di UI dan menghasilkan `team-charter.md`.
    - Mengubah model/tier di UI memperbarui estimasi biaya.

- [x] **Prompt 5: Meeting Engine: satu putaran + Titik Konfirmasi**
  - Kriteria Selesai:
    - Demo: diskusi dengan 3 agen palsu -> sintesis -> PO memilih opsi B -> keputusan masuk Decision Log.
    - Semua tes lolos: satu putaran tepat satu kontribusi per peserta, tidak ada putaran kedua tanpa klik PO, restart worker di tengah diskusi tidak menggandakan kontribusi, plafon token menghentikan putaran.

- [x] **Prompt 6: Inception: dari diskusi menjadi PRD/Rencana dan Product Backlog**
  - Kriteria Selesai:
    - Dari proyek proposal sampai G2 dengan FakeProvider: semua berkas keluaran ada di workspace dengan metadata benar.
    - Mengubah urutan Product Backlog hanya bisa dilakukan PO.

- [x] **Prompt 7: Scrum Engine dan Kanban**
  - Kriteria Selesai:
    - Simulasi satu sprint penuh: Planning -> Eksekusi (palsu) -> Review -> Retro, dengan G3 menolak satu PBI dan PBI itu kembali ke backlog.
    - Burndown dan velocity terhitung benar pada data simulasi.

- [x] **Prompt 8: Eksekusi agen, review silang, penjaga anggaran**
  - Kriteria Selesai:
    - Satu proyek proposal berjalan end-to-end memakai FakeProvider dengan hasil artefak, review, dan penghentian anggaran yang terverifikasi.
    - Uji manual singkat dengan satu model nyata murah (tier low) pada satu Task.

- [/] **Prompt 9: Learning Engine dasar** [SEDANG DIKERJAKAN]
  - Kriteria Selesai:
    - Demo dua proyek berurutan: koreksi PO di proyek 1 muncul sebagai usulan, disetujui, lalu terlihat mempengaruhi prompt di proyek 2.

- [ ] **Prompt 10: Pengerasan MVP dan uji menyeluruh**
  - Kriteria Selesai:
    - `make test` hijau; skenario end-to-end lolos; README bisa diikuti dari nol.

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

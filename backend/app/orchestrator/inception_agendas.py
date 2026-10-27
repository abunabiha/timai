"""Inception Agendas per Profile according to PRD FR-7.1 and Section 6.1."""

INCEPTION_AGENDAS_BY_PROFILE: dict[str, list[dict[str, str]]] = {
    "proposal": [
        {
            "agenda_number": "01",
            "title": "Kesesuaian Skema Hibah & Ruang Lingkup",
            "description": "Evaluasi kesesuaian brief dengan panduan skema hibah resmi, batasan administratif, dan luaran wajib.",
            "lead_role": "Scrum Master",
            "expected_output": "Persetujuan ruang lingkup dan kepatuhan syarat administratif skema hibah.",
        },
        {
            "agenda_number": "02",
            "title": "Analisis Gap, State of the Art & Novelty",
            "description": "Pemetaan penelitian terdahulu, identifikasi research gap yang jelas, dan perumusan nilai kebaruan (novelty).",
            "lead_role": "Research Lead",
            "expected_output": "Pernyataan gap riset dan kebaruan proposal yang kokoh dengan rujukan ilmiah.",
        },
        {
            "agenda_number": "03",
            "title": "Rancangan Metodologi Penelitian",
            "description": "Perancangan tahapan riset, desain eksperimen/studi, variabel, instrumen, dan rencana analisis data.",
            "lead_role": "Reviewer Metodologi",
            "expected_output": "Alur metodologi penelitian yang sistematis, valid, dan dapat direplikasi.",
        },
        {
            "agenda_number": "04",
            "title": "Target Luaran, Indikator Capaian & Target TKT",
            "description": "Penetapan luaran wajib (artikel jurnal, paten/HKI, prosiding) dan target Tingkat Kesiapterapan Teknologi (TKT).",
            "lead_role": "Grant Writer",
            "expected_output": "Daftar luaran terukur beserta baseline dan target TKT awal hingga akhir.",
        },
        {
            "agenda_number": "05",
            "title": "Rencana Jadwal Kerja & Draf Rancang Anggaran Biaya (RAB)",
            "description": "Penyusunan jadwal pelaksanaan per bulan/sprint dan draf RAB sesuai standar biaya masukan (SBM).",
            "lead_role": "Budget Planner",
            "expected_output": "Matriks jadwal kegiatan dan rincian alokasi anggaran biaya penelitian.",
        },
    ],
    "jurnal": [
        {
            "agenda_number": "01",
            "title": "Target Jurnal, Cakupan (Aims & Scope) & Gaya Selingkung",
            "description": "Pemilihan jurnal target bereputasi, kesesuaian aims & scope, batas kata, dan panduan bagi penulis (author guidelines).",
            "lead_role": "Scrum Master",
            "expected_output": "Keputusan jurnal target dan acuan gaya selingkung penulisan.",
        },
        {
            "agenda_number": "02",
            "title": "Pernyataan Kontribusi Utama (Novelty & Contribution)",
            "description": "Perumusan kontribusi ilmiah utama artikel dan keunggulan komparatif terhadap publikasi terkini.",
            "lead_role": "Research Lead",
            "expected_output": "Rumusan kontribusi utama dan positioning artikel jurnal.",
        },
        {
            "agenda_number": "03",
            "title": "Kerangka IMRaD & Peta Bukti (Klaim -> Sumber/Data)",
            "description": "Penyusunan outline IMRaD (Introduction, Methods, Results, and Discussion) dan pemetaan klaim ke data eksperimen.",
            "lead_role": "Academic Writer",
            "expected_output": "Struktur IMRaD lengkap dan peta keterikatan klaim dengan bukti empiris.",
        },
        {
            "agenda_number": "04",
            "title": "Rencana Analisis Statistik, Gambar & Tabel",
            "description": "Rencana pengolahan data, pengujian statistik, serta tata letak visual grafik dan tabel hasil temuan.",
            "lead_role": "Statistician",
            "expected_output": "Protokol analisis statistik dan spesifikasi gambar/tabel manuskrip.",
        },
    ],
    "software": [
        {
            "agenda_number": "01",
            "title": "Tujuan Produk & Batasan Lingkup Sistem",
            "description": "Penyelarasan Product Goal, target pengguna, skenario utama, dan batasan di luar lingkup (out of scope).",
            "lead_role": "Scrum Master",
            "expected_output": "Pernyataan Product Goal dan batasan fungsional sistem.",
        },
        {
            "agenda_number": "02",
            "title": "Kebutuhan Fungsional & Kriteria Penerimaan",
            "description": "Perumusan epik dan kebutuhan fungsional (user stories) serta kriteria penerimaan awal.",
            "lead_role": "Business Analyst",
            "expected_output": "Katalog user stories awal dan kriteria penerimaan.",
        },
        {
            "agenda_number": "03",
            "title": "Arsitektur Sistem, Desain Data & Kontrak API",
            "description": "Pemilihan arsitektur teknis, diagram entitas basis data, dan spesifikasi antarmuka API.",
            "lead_role": "Solution Architect",
            "expected_output": "Desain arsitektur perangkat lunak dan skema data.",
        },
        {
            "agenda_number": "04",
            "title": "Rencana Rilis, Strategi Uji & Mitigasi Risiko",
            "description": "Penetapan rencana rilis sprint, strategi pengujian otomatis (DoD), dan mitigasi risiko teknis.",
            "lead_role": "QA Engineer",
            "expected_output": "Rencana rilis sprint dan matriks manajemen risiko perangkat lunak.",
        },
    ],
    "iot": [
        {
            "agenda_number": "01",
            "title": "Tujuan Sistem & Arsitektur Perangkat (Sensor-MCU-Cloud)",
            "description": "Perancangan topologi IoT dari sensor, mikrokontroler (MCU), protokol jaringan, hingga cloud backend.",
            "lead_role": "Systems Analyst",
            "expected_output": "Diagram arsitektur perangkat keras dan komunikasi data IoT.",
        },
        {
            "agenda_number": "02",
            "title": "Daftar Komponen (BOM) & Spesifikasi Payload Data",
            "description": "Penyusunan Bill of Materials (BOM) perangkat keras dan skema format payload (MQTT/HTTP JSON).",
            "lead_role": "Hardware Designer",
            "expected_output": "BOM terverifikasi dan spesifikasi kontrak payload telemetri.",
        },
        {
            "agenda_number": "03",
            "title": "Skema Rangkaian & Rencana Uji Firmware/Hardware",
            "description": "Perancangan skema rangkaian elektronik, logika firmware dasar, dan panduan perakitan fisik.",
            "lead_role": "Embedded Firmware Engineer",
            "expected_output": "Desain rangkaian dan panduan tugas fisik untuk PO (Tugas PO).",
        },
        {
            "agenda_number": "04",
            "title": "Rencana Rilis & Integrasi Dashboard Monitoring",
            "description": "Perencanaan sprint integrasi dashboard web, pengujian end-to-end, dan rencana rilis prototipe.",
            "lead_role": "Scrum Master",
            "expected_output": "Rencana rilis sistem IoT dan strategi validasi fisik.",
        },
    ],
    "buku": [
        {
            "agenda_number": "01",
            "title": "Sasaran Pembaca, Posisi Pasar & Outline Buku",
            "description": "Penetapan profil audiens pembaca, daya tarik unik buku, dan struktur garis besar bab.",
            "lead_role": "Book Editor",
            "expected_output": "Outline buku terstruktur dan profil pembaca sasaran.",
        },
        {
            "agenda_number": "02",
            "title": "Panduan Gaya Selingkung, Nada Tulisan & Glosarium",
            "description": "Penyusunan panduan gaya bahasa (PUEBI/KBBI atau akademik), nada penulisan, dan glosarium istilah bilingual.",
            "lead_role": "Book Editor",
            "expected_output": "Panduan gaya penulisan dan daftar istilah baku.",
        },
        {
            "agenda_number": "03",
            "title": "Pembagian Bab ke Penulis & Rencana Jadwal Sprint",
            "description": "Pembagian penugasan bab ke penulis, alokasi per sprint, dan kriteria penyuntingan antarbab.",
            "lead_role": "Scrum Master",
            "expected_output": "Matriks penugasan bab dan jadwal penulisan per sprint.",
        },
    ],
}


def get_agendas_for_profile(profile_code: str) -> list[dict[str, str]]:
    """Return the list of inception agendas for a given profile code, defaulting to software if not found."""
    return INCEPTION_AGENDAS_BY_PROFILE.get(profile_code, INCEPTION_AGENDAS_BY_PROFILE["software"])

"""Inception Engine: Manages Inception agendas, document assembly, backlog generation, and Gate G2."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Artifact,
    BacklogItem,
    Discussion,
    Epic,
    Gate,
    ProductGoal,
    Project,
    User,
)
from app.orchestrator.inception_agendas import get_agendas_for_profile
from app.orchestrator.meeting import meeting_engine


def get_project_workspace_path(project: Project) -> Path:
    if project.workspace_path and Path(project.workspace_path).exists():
        return Path(project.workspace_path)
    workspaces_root = Path("workspaces")
    if workspaces_root.exists():
        for p in workspaces_root.iterdir():
            if p.is_dir() and project.id[:8] in p.name:
                return p
    return workspaces_root / f"proyek-{project.id[:8]}"


def get_git_executable() -> str:
    candidates = [
        r"C:\Users\ROG\AppData\Local\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd\git.exe",
        "git",
    ]
    for c in candidates:
        try:
            res = subprocess.run([c, "--version"], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                return c
        except Exception:
            continue
    return "git"


async def init_inception_agendas(project: Project, db: AsyncSession) -> list[Discussion]:
    """Ensure all required Inception agendas exist as discussions for the project."""
    profile_code = project.profile_id or "proposal"
    agendas = get_agendas_for_profile(profile_code)

    # Fetch existing inception discussions
    stmt = (
        select(Discussion)
        .where(Discussion.project_id == project.id, Discussion.discussion_type == "inception")
        .order_by(Discussion.created_at.asc())
    )
    res = await db.execute(stmt)
    existing_discussions = list(res.scalars().all())

    existing_agendas = {d.agenda for d in existing_discussions}
    new_discussions = []

    for item in agendas:
        agenda_title = f"Agenda {item['agenda_number']}: {item['title']}"
        if agenda_title not in existing_agendas:
            disc = await meeting_engine.create_discussion(
                db=db,
                project_id=project.id,
                agenda=agenda_title,
                discussion_type="inception",
            )
            new_discussions.append(disc)

    # Return all current inception discussions
    stmt = (
        select(Discussion)
        .where(Discussion.project_id == project.id, Discussion.discussion_type == "inception")
        .options(selectinload(Discussion.contributions), selectinload(Discussion.confirmations))
        .order_by(Discussion.created_at.asc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def assemble_inception_document(
    project_id: str,
    db: AsyncSession,
    current_user: User | None = None,
) -> dict[str, Any]:
    """Assemble Inception Document from meeting notes and decisions, and generate the Product Backlog."""
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.agents),
            selectinload(Project.discussions).selectinload(Discussion.contributions),
            selectinload(Project.discussions).selectinload(Discussion.confirmations),
        )
    )
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    profile_code = project.profile_id or "proposal"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Read decision log if exists in workspace
    workspace_path = get_project_workspace_path(project)
    decision_log_path = workspace_path / "02-inception" / "decision-log.md"
    decision_log_content = ""
    if decision_log_path.exists():
        decision_log_content = decision_log_path.read_text(encoding="utf-8")

    # Check previous version if any
    artifact_stmt = (
        select(Artifact)
        .where(Artifact.project_id == project_id, Artifact.artifact_type == "dokumen_inception")
        .order_by(Artifact.version.desc())
    )
    art_res = await db.execute(artifact_stmt)
    latest_artifact = art_res.scalar_one_or_none()
    new_version = (latest_artifact.version + 1) if latest_artifact else 1

    # 1. Product Goal formulation
    product_goal_stmt = select(ProductGoal).where(ProductGoal.project_id == project_id)
    pg_res = await db.execute(product_goal_stmt)
    product_goal = pg_res.scalar_one_or_none()

    default_goal_statement = f"Menghasilkan naskah lengkap dan terverifikasi untuk {project.title} yang memenuhi seluruh standar keunggulan profil {profile_code}."
    if not product_goal:
        product_goal = ProductGoal(
            project_id=project.id,
            statement=default_goal_statement,
            status="active",
        )
        db.add(product_goal)
        await db.flush()

    # 2. Epics & Backlog Items generation
    epics_stmt = select(Epic).where(Epic.project_id == project_id).order_by(Epic.sort_order.asc())
    existing_epics_res = await db.execute(epics_stmt)
    existing_epics = list(existing_epics_res.scalars().all())

    if not existing_epics:
        existing_epics = await _generate_default_epics_and_backlog(project, db)

    deadline_str = project.deadline.strftime("%Y-%m-%d") if project.deadline else "30 hari kalender"
    budget_val = project.budget if project.budget else 25000000.0

    # 3. Assemble Dokumen Inception Markdown
    doc_frontmatter = f"""---
proyek: {project.title}
tahap: 3 Inception
sprint: null
dokumen: Dokumen Inception (PRD/Rencana)
versi: {new_version}
dibuat_oleh: Analis · Research Lead · FakeProvider
direview_oleh: Scrum Master
status: menunggu PO
disetujui_oleh: null
---
"""

    doc_body = f"""
# Dokumen Inception: {project.title}

## 1. Ringkasan Eksekutif & Product Goal
**Product Goal:**
> {product_goal.statement}

- **Profil Proyek:** {profile_code.capitalize()}
- **Tenggat Target:** {deadline_str}
- **Batas Anggaran:** Rp {budget_val:,.0f}
- **Bahasa Keluaran:** {project.language.upper()}

## 2. Sintesis Hasil Agenda Inception
Berikut adalah rangkuman kesepakatan tim berdasarkan agenda Inception yang telah dibahas:
"""
    for disc in project.discussions:
        if disc.discussion_type == "inception":
            latest_conf = disc.confirmations[-1] if disc.confirmations else None
            status_text = "Terkonfirmasi" if (latest_conf and latest_conf.selected_option) else "Dalam Proses"
            choice = f" (Opsi terpilih: {latest_conf.selected_option})" if (latest_conf and latest_conf.selected_option) else ""
            doc_body += f"\n### {disc.agenda}\n- **Status:** {status_text}{choice}\n"
            if latest_conf and latest_conf.po_feedback:
                doc_body += f"- **Catatan PO:** {latest_conf.po_feedback}\n"

    doc_body += f"""
## 3. Log Keputusan Terpilih
```markdown
{decision_log_content if decision_log_content else "Belum ada entri catatan keputusan resmi."}
```

## 4. Struktur Product Backlog
Product Backlog disusun dalam bentuk Epik dan Product Backlog Item (PBI) yang terukur dan memiliki kriteria penerimaan yang jelas:
"""
    # Fetch all backlog items for inclusion
    bi_stmt = (
        select(BacklogItem)
        .where(BacklogItem.project_id == project.id)
        .order_by(BacklogItem.po_sort_order.asc())
    )
    bi_res = await db.execute(bi_stmt)
    all_backlog_items = list(bi_res.scalars().all())

    for item in all_backlog_items:
        po_tag = " [TUGAS PO]" if item.is_po_task else ""
        doc_body += f"\n- **[{item.po_sort_order + 1}] {item.title}** ({item.story_points} Poin){po_tag}\n"
        if item.acceptance_criteria:
            doc_body += "  *Kriteria Penerimaan:*\n"
            for ac in item.acceptance_criteria:
                doc_body += f"  - {ac}\n"

    full_inception_doc = doc_frontmatter + doc_body

    # 4. Write output files to workspace with PRD 5.2d metadata
    inception_dir = workspace_path / "02-inception"
    inception_dir.mkdir(parents=True, exist_ok=True)

    # 4a. dokumen-inception.md
    doc_file_path = inception_dir / "dokumen-inception.md"
    doc_file_path.write_text(full_inception_doc, encoding="utf-8")

    # 4b. product-backlog.json
    backlog_json_data = {
        "metadata": {
            "proyek": project.title,
            "tahap": "3 Inception",
            "sprint": None,
            "dokumen": "Product Backlog",
            "versi": new_version,
            "dibuat_oleh": "Scrum Master · Team · FakeProvider",
            "direview_oleh": "PO",
            "status": "menunggu PO",
            "disetujui_oleh": None,
        },
        "product_goal": product_goal.statement,
        "items": [
            {
                "id": it.id,
                "epic_id": it.epic_id,
                "title": it.title,
                "story_points": it.story_points,
                "po_sort_order": it.po_sort_order,
                "acceptance_criteria": it.acceptance_criteria,
                "status": it.status,
                "source": it.source,
                "is_po_task": it.is_po_task,
            }
            for it in all_backlog_items
        ],
    }
    backlog_file_path = inception_dir / "product-backlog.json"
    backlog_file_path.write_text(json.dumps(backlog_json_data, indent=2), encoding="utf-8")

    # 4c. Definition of Done (dod.md)
    dod_content = f"""---
proyek: {project.title}
tahap: 3 Inception
sprint: null
dokumen: Definition of Done (DoD)
versi: {new_version}
dibuat_oleh: QA Engineer · Reviewer · FakeProvider
direview_oleh: Scrum Master
status: menunggu PO
disetujui_oleh: null
---

# Definition of Done (DoD) - {project.title}

## 1. Kriteria Umum (Semua PBI)
- [ ] Draf atau keluaran memenuhi kriteria penerimaan spesifik pada PBI.
- [ ] Lolos review silang oleh peran Reviewer yang ditugaskan (tanpa temuan kritis).
- [ ] Bebas dari fabrikasi sumber, data palsu, atau klaim tanpa sitasi rujukan terverifikasi.
- [ ] Semua berkas keluaran tersimpan di direktori sprint terkait dengan metadata PRD 5.2d.
- [ ] Riwayat perubahan tercatat dalam commit Git workspace proyek.

## 2. Kriteria Spesifik Profil ({profile_code.upper()})
- [ ] Format dokumen dan struktur penulisan sesuai dengan gaya panduan resmi ({profile_code}).
- [ ] Keterbacaan dan konsistensi terminologi terverifikasi oleh Editor.
- [ ] Batas jumlah kata/halaman tidak melampaui toleransi yang ditetapkan brief.
"""
    dod_file_path = inception_dir / "dod.md"
    dod_file_path.write_text(dod_content, encoding="utf-8")

    # 4d. Rencana Rilis (rencana-rilis.md)
    release_content = f"""---
proyek: {project.title}
tahap: 3 Inception
sprint: null
dokumen: Rencana Rilis
versi: {new_version}
dibuat_oleh: Scrum Master · FakeProvider
direview_oleh: PO
status: menunggu PO
disetujui_oleh: null
---

# Rencana Rilis - {project.title}

- **Jumlah Sprint Direncanakan:** 2 - 3 Sprint (Durasi 1 minggu per sprint)
- **Rentang Estimasi Biaya:** Rp {budget_val * 0.35:,.0f} - Rp {budget_val * 0.85:,.0f}
- **Target Penyelesaian:** {deadline_str}

## Rincian Alokasi Sprint
| Sprint | Fokus / Cakupan Utama | Target Poin | Estimasi Tanggal |
|---|---|---|---|
| Sprint 1 | Fondasi, Kajian Pustaka & Desain Metodologi Utama | 12 - 16 Poin | Minggu 1 |
| Sprint 2 | Pengembangan Isi Pokok, Analisis & Draf Lengkap | 14 - 18 Poin | Minggu 2 |
| Sprint 3 | Review Silang, Finalisasi Format & Uji Kelayakan Akhir | 8 - 12 Poin | Minggu 3 |
"""
    release_file_path = inception_dir / "rencana-rilis.md"
    release_file_path.write_text(release_content, encoding="utf-8")

    # 4e. Risk Register (risiko.md)
    risk_content = f"""---
proyek: {project.title}
tahap: 3 Inception
sprint: null
dokumen: Risk Register
versi: {new_version}
dibuat_oleh: Solution Architect · Research Lead · FakeProvider
direview_oleh: Scrum Master
status: menunggu PO
disetujui_oleh: null
---

# Risk Register - {project.title}

| ID | Deskripsi Risiko | Dampak | Kemungkinan | Strategi Mitigasi |
|---|---|---|---|---|
| R-01 | Ketidaksesuaian dengan format panduan skema terbaru | Tinggi | Sedang | Fact Checker memverifikasi checklist panduan resmi pada setiap draf PBI. |
| R-02 | Kekurangan rujukan primer terindeks bereputasi (5 tahun terakhir) | Sedang | Sedang | Prioritaskan pencarian literatur terakreditasi sebelum penulisan draf dimulai. |
| R-03 | Pelampauan pagu anggaran API token | Tinggi | Rendah | Penegakan plafon token per diskusi dan peringatan dini pada 50% & 80% anggaran. |
| R-04 | Keterlambatan umpan balik PO pada Titik Konfirmasi | Sedang | Sedang | Sistem notifikasi berkala dan delegasi item pekerjaan yang tidak terblokir. |
"""
    risk_file_path = inception_dir / "risiko.md"
    risk_file_path.write_text(risk_content, encoding="utf-8")

    # Record Artifact in DB
    artifact = Artifact(
        project_id=project.id,
        artifact_type="dokumen_inception",
        file_path=str(doc_file_path),
        version=new_version,
        review_status="under_review",
        metadata_json={
            "product_goal": product_goal.statement,
            "backlog_items_count": len(all_backlog_items),
            "generated_at": now_iso,
        },
    )
    db.add(artifact)

    # Ensure Gate G2 is initialized in DB
    gate_stmt = select(Gate).where(Gate.project_id == project.id, Gate.gate_type == "G2")
    gate_res = await db.execute(gate_stmt)
    gate_g2 = gate_res.scalar_one_or_none()
    if not gate_g2:
        gate_g2 = Gate(
            project_id=project.id,
            gate_type="G2",
            target_id=artifact.id,
            decision="pending",
        )
        db.add(gate_g2)

    await db.commit()

    # Commit to Git workspace
    git_bin = get_git_executable()
    try:
        subprocess.run([git_bin, "add", "."], cwd=str(workspace_path), check=False, capture_output=True)
        subprocess.run(
            [git_bin, "commit", "-m", f"Inception: Dokumen Inception dan Backlog v{new_version} dihasilkan"],
            cwd=str(workspace_path),
            check=False,
            capture_output=True,
        )
    except Exception:
        pass

    return {
        "artifact_id": artifact.id,
        "version": new_version,
        "product_goal": product_goal.statement,
        "backlog_count": len(all_backlog_items),
        "files_generated": [
            "02-inception/dokumen-inception.md",
            "02-inception/product-backlog.json",
            "02-inception/dod.md",
            "02-inception/rencana-rilis.md",
            "02-inception/risiko.md",
        ],
    }


async def _generate_default_epics_and_backlog(project: Project, db: AsyncSession) -> list[Epic]:
    """Generate default Epics and PBIs according to the project profile."""
    profile_code = project.profile_id or "proposal"

    epics_data: list[dict[str, Any]] = []

    if profile_code == "proposal":
        epics_data = [
            {
                "title": "Kajian Pustaka & Analisis Gap",
                "sort_order": 0,
                "items": [
                    {
                        "title": "Pemetaan State of the Art dan Gap Riset",
                        "story_points": 5,
                        "criteria": ["Minimal 15 rujukan bereputasi 5 tahun terakhir", "Gap riset terdefinisi secara eksplisit", "Matriks komparasi studi terdahulu"],
                    },
                    {
                        "title": "Perumusan Novelty dan Kontribusi Utama Penelitian",
                        "story_points": 3,
                        "criteria": ["Klaim kebaruan terhubung dengan gap riset", "Manfaat teoritis dan praktis diuraikan"],
                    },
                ],
            },
            {
                "title": "Metodologi & Desain Eksperimen",
                "sort_order": 1,
                "items": [
                    {
                        "title": "Rancangan Metodologi dan Alur Eksperimen",
                        "story_points": 5,
                        "criteria": ["Diagram alir penelitian lengkap", "Tahapan replikatif dan parameter terukur"],
                    },
                    {
                        "title": "Protokol Pengumpulan Data dan Instrumen Validasi",
                        "story_points": 3,
                        "criteria": ["Rancangan instrumen data", "Metode pengujian signifikansi dan validitas"],
                    },
                ],
            },
            {
                "title": "Jadwal, Luaran & Draf RAB",
                "sort_order": 2,
                "items": [
                    {
                        "title": "Penyusunan Rencana Jadwal, Matriks Luaran & Target TKT",
                        "story_points": 3,
                        "criteria": ["Tabel jadwal kegiatan per bulan", "Target TKT awal dan akhir terdefinisi"],
                    },
                    {
                        "title": "Draf Rincian Anggaran Biaya (RAB) sesuai SBM",
                        "story_points": 3,
                        "criteria": ["RAB terstruktur sesuai kategori SBM resmi", "Total anggaran berada dalam batas pagu brief"],
                    },
                ],
            },
            {
                "title": "Finalisasi Naskah Proposal",
                "sort_order": 3,
                "items": [
                    {
                        "title": "Penyusunan Draf Lengkap Naskah Proposal dan Lampiran Wajib",
                        "story_points": 8,
                        "criteria": ["Naskah lengkap format skema hibah", "Semua lampiran administratif tersedia", "Lolos uji plagiarisme dan konsistensi sitasi"],
                    },
                ],
            },
        ]
    elif profile_code == "jurnal":
        epics_data = [
            {
                "title": "Aims & Scope dan Pendahuluan",
                "sort_order": 0,
                "items": [
                    {
                        "title": "Penetapan Target Jurnal dan Penulisan Pendahuluan Berorientasi Gap",
                        "story_points": 5,
                        "criteria": ["Sesuai author guidelines jurnal target", "Pendahuluan ≤ 900 kata", "15 rujukan bereputasi"],
                    },
                ],
            },
            {
                "title": "Metodologi dan Protokol Data",
                "sort_order": 1,
                "items": [
                    {
                        "title": "Penyusunan Bagian Metode dengan Protokol Replikasi Lengkap",
                        "story_points": 5,
                        "criteria": ["Metode detail dan transparan", "Deskripsi dataset dan perangkat lunak analisis"],
                    },
                ],
            },
            {
                "title": "Hasil dan Pembahasan (IMRaD)",
                "sort_order": 2,
                "items": [
                    {
                        "title": "Analisis Statistik, Penyajian Gambar, Tabel & Hasil Temuan",
                        "story_points": 8,
                        "criteria": ["Visualisasi data beresolusi tinggi", "Tabel ringkasan metrik evaluasi", "P-value atau confidence interval jelas"],
                    },
                    {
                        "title": "Pembahasan Komparatif terhadap Literatur Terkini",
                        "story_points": 5,
                        "criteria": ["Analisis perbandingan dengan riset terkini", "Keterbatasan riset diuraikan jujur"],
                    },
                ],
            },
            {
                "title": "Finalisasi Manuskrip",
                "sort_order": 3,
                "items": [
                    {
                        "title": "Penyuntingan Gaya Selingkung, Verifikasi Rujukan & Kesimpulan",
                        "story_points": 3,
                        "criteria": ["Format referensi 100% konsisten", "Abstrak dan kata kunci lengkap", "Highlight dan cover letter siap"],
                    },
                ],
            },
        ]
    elif profile_code == "iot":
        epics_data = [
            {
                "title": "Perangkat Keras dan Skema",
                "sort_order": 0,
                "items": [
                    {
                        "title": "Desain Skema Rangkaian dan Validasi BOM Komponen",
                        "story_points": 5,
                        "criteria": ["Skema pinout mikrokontroler", "Daftar BOM komponen terverifikasi ketersediaannya"],
                        "is_po_task": False,
                    },
                    {
                        "title": "Panduan Perakitan Fisik dan Kalibrasi Sensor di Lapangan",
                        "story_points": 3,
                        "criteria": ["Panduan perakitan langkah demi langkah", "Lembar pencatatan kalibrasi PO"],
                        "is_po_task": True,  # PO Physical task
                    },
                ],
            },
            {
                "title": "Firmware dan Komunikasi",
                "sort_order": 1,
                "items": [
                    {
                        "title": "Implementasi Firmware Mikrokontroler dan Protokol Telemetri",
                        "story_points": 8,
                        "criteria": ["Kode firmware modular", "Format payload JSON via MQTT/HTTP", "Penanganan reconnections"],
                        "is_po_task": False,
                    },
                ],
            },
            {
                "title": "Integrasi Cloud dan Dashboard",
                "sort_order": 2,
                "items": [
                    {
                        "title": "Integrasi Telemetri Backend dan Dashboard Monitoring Real-Time",
                        "story_points": 5,
                        "criteria": ["Endpoint ingesti data aktif", "Widget visualisasi grafik sensor", "Notifikasi ambang batas"],
                        "is_po_task": False,
                    },
                    {
                        "title": "Uji Lapangan dan Pengujian Konektivitas Nyata",
                        "story_points": 5,
                        "criteria": ["Uji transmisi 24 jam", "Catatan log serial pengujian diunggah PO"],
                        "is_po_task": True,  # PO Physical task
                    },
                ],
            },
        ]
    else:  # software / buku / default
        epics_data = [
            {
                "title": "Arsitektur dan Desain Sistem",
                "sort_order": 0,
                "items": [
                    {
                        "title": "Desain Skema Basis Data dan Kontrak REST API",
                        "story_points": 5,
                        "criteria": ["ERD lengkap", "Spesifikasi OpenAPI / endpoint", "Data migration scripts"],
                    },
                ],
            },
            {
                "title": "Modul Inti dan Layanan Bisnis",
                "sort_order": 1,
                "items": [
                    {
                        "title": "Implementasi Manajemen Pengguna dan RBAC",
                        "story_points": 5,
                        "criteria": ["Autentikasi aman JWT/Argon2", "Pemisahan hak akses peran PO/Admin/Viewer"],
                    },
                    {
                        "title": "Implementasi Alur Kerja Utama Sistem",
                        "story_points": 8,
                        "criteria": ["Fitur inti berjalan sesuai kriteria penerimaan", "Validasi input dan penanganan error"],
                    },
                ],
            },
            {
                "title": "Pengujian dan Penjaminan Mutu",
                "sort_order": 2,
                "items": [
                    {
                        "title": "Pengujian Unit, Integrasi, dan Otomasi CI",
                        "story_points": 5,
                        "criteria": ["Cakupan tes memadai", "Linting dan type check lolos tanpa error"],
                    },
                ],
            },
        ]

    created_epics = []
    global_sort = 0

    for epic_dict in epics_data:
        epic = Epic(
            project_id=project.id,
            title=epic_dict["title"],
            sort_order=epic_dict["sort_order"],
        )
        db.add(epic)
        await db.flush()
        created_epics.append(epic)

        for item_dict in epic_dict["items"]:
            bi = BacklogItem(
                epic_id=epic.id,
                project_id=project.id,
                title=item_dict["title"],
                item_type="story",
                acceptance_criteria=item_dict.get("criteria", []),
                story_points=item_dict.get("story_points", 3),
                po_sort_order=global_sort,
                status="product_backlog",
                source="team_proposed",
                is_po_task=item_dict.get("is_po_task", False),
            )
            db.add(bi)
            global_sort += 1

    await db.flush()
    return created_epics


async def review_gate_g2(
    project_id: str,
    decision: str,
    comments: str,
    current_user: User,
    db: AsyncSession,
) -> dict[str, Any]:
    """Handle PO decision for Gate G2 (approved, revision_requested, rejected)."""
    # Verify user permission: only PO or ADMIN can decide Gate G2
    if current_user.role not in ["po", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya Product Owner (PO) yang berhak memutuskan Gerbang G2.")

    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    gate_stmt = select(Gate).where(Gate.project_id == project_id, Gate.gate_type == "G2")
    gate_res = await db.execute(gate_stmt)
    gate_g2 = gate_res.scalar_one_or_none()
    if not gate_g2:
        gate_g2 = Gate(project_id=project_id, gate_type="G2")
        db.add(gate_g2)

    gate_g2.decision = decision
    gate_g2.comments = comments
    gate_g2.decided_by_user_id = current_user.id
    gate_g2.decided_at = datetime.now(timezone.utc)

    workspace_path = get_project_workspace_path(project)
    doc_path = workspace_path / "02-inception" / "dokumen-inception.md"

    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if decision == "approved":
        # Update metadata in dokumen-inception.md
        if doc_path.exists():
            text = doc_path.read_text(encoding="utf-8")
            text = text.replace("status: menunggu PO", "status: disetujui")
            text = text.replace("disetujui_oleh: null", f"disetujui_oleh: {current_user.name} · {now_date}")
            doc_path.write_text(text, encoding="utf-8")

        # Update ProductGoal status
        pg_stmt = select(ProductGoal).where(ProductGoal.project_id == project_id)
        pg_res = await db.execute(pg_stmt)
        product_goal = pg_res.scalar_one_or_none()
        if product_goal:
            product_goal.approved_at = datetime.now(timezone.utc)

        # Update project status to inception_approved
        project.status = "inception_approved"

        # Commit to Git
        git_bin = get_git_executable()
        try:
            subprocess.run([git_bin, "add", "."], cwd=str(workspace_path), check=False, capture_output=True)
            subprocess.run(
                [git_bin, "commit", "-m", f"G2 approved: Dokumen Inception disetujui oleh {current_user.name}"],
                cwd=str(workspace_path),
                check=False,
                capture_output=True,
            )
        except Exception:
            pass

    elif decision == "revision_requested":
        if doc_path.exists():
            text = doc_path.read_text(encoding="utf-8")
            text = text.replace("status: menunggu PO", "status: draf (revisi diminta)")
            doc_path.write_text(text, encoding="utf-8")

        # Create a revision discussion for the team
        rev_disc = Discussion(
            project_id=project.id,
            discussion_type="inception_revision",
            agenda=f"Revisi Inception G2: {comments[:80]}",
            status="draft",
        )
        db.add(rev_disc)

    elif decision == "rejected":
        project.status = "cancelled"

    await db.commit()
    return {
        "gate": "G2",
        "decision": decision,
        "comments": comments,
        "decided_by": current_user.name,
        "decided_at": gate_g2.decided_at.isoformat(),
    }


async def reorder_backlog_items(
    project_id: str,
    ordered_item_ids: list[str],
    current_user: User,
    db: AsyncSession,
) -> list[BacklogItem]:
    """Reorder Product Backlog items strictly restricted to PO (FR-7.4 & PRD 5.1)."""
    # Strict permission check: only PO or ADMIN can reorder!
    if current_user.role not in ["po", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Hanya Product Owner (PO) yang berhak mengubah urutan Product Backlog.",
        )

    stmt = select(BacklogItem).where(BacklogItem.project_id == project_id)
    res = await db.execute(stmt)
    items_by_id = {item.id: item for item in res.scalars().all()}

    updated_items = []
    for order_idx, item_id in enumerate(ordered_item_ids):
        if item_id in items_by_id:
            item = items_by_id[item_id]
            item.po_sort_order = order_idx
            updated_items.append(item)

    await db.commit()

    # Update product-backlog.json in workspace
    project_stmt = select(Project).where(Project.id == project_id)
    p_res = await db.execute(project_stmt)
    project = p_res.scalar_one_or_none()

    if project:
        workspace_path = get_project_workspace_path(project)
        backlog_file = workspace_path / "02-inception" / "product-backlog.json"
        if backlog_file.exists():
            try:
                data = json.loads(backlog_file.read_text(encoding="utf-8"))
                item_order_map = {item.id: item.po_sort_order for item in updated_items}
                for it in data.get("items", []):
                    if it["id"] in item_order_map:
                        it["po_sort_order"] = item_order_map[it["id"]]
                data["items"] = sorted(data.get("items", []), key=lambda x: x.get("po_sort_order", 0))
                backlog_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                pass

    return updated_items

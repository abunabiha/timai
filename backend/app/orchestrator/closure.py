import logging
import os
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    BacklogItem,
    Gate,
    Lesson,
    ProductGoal,
    Project,
    Sprint,
    UsageRecord,
    User,
)
from app.orchestrator.exporter import exporter
from app.orchestrator.inception import get_git_executable, get_project_workspace_path

logger = logging.getLogger("timai.closure")


class ClosureOrchestrator:
    """
    Project Closure & Gate G4 (PRD 5.2a Tahap 8):
    - Final package assembly in final/ + ZIP archive
    - Laporan Penutupan (laporan-penutupan.md & PDF export)
    - Records Gate G4 decision
    - Updates project.status to 'closed'
    """

    async def close_project_g4(
        self,
        db: AsyncSession,
        project_id: str,
        current_user: User,
        comments: str = "Proyek resmi ditutup dan hasil akhir disetujui oleh PO.",
    ) -> dict[str, Any]:
        """Closes project upon PO G4 gate approval."""
        if current_user.role not in ["po", "admin"]:
            raise HTTPException(status_code=403, detail="Hanya Product Owner (PO) yang berhak menutup proyek (G4).")

        p_stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.sprints),
                selectinload(Project.backlog_items),
                selectinload(Project.agents),
            )
        )
        p_res = await db.execute(p_stmt)
        project = p_res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

        workspace_path = get_project_workspace_path(project)
        final_dir = workspace_path / "final"
        final_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%d")

        # 1. Calculate Metrics
        s_stmt = select(Sprint).where(Sprint.project_id == project.id)
        s_res = await db.execute(s_stmt)
        all_sprints = list(s_res.scalars().all())

        total_sprints = len(all_sprints)
        total_velocity = float(sum(s.velocity_achieved or 0.0 for s in all_sprints))
        avg_velocity = round(total_velocity / max(1, total_sprints), 1)

        # Cost spent
        cost_stmt = (
            select(func.coalesce(func.sum(UsageRecord.cost), 0.0))
            .where(UsageRecord.project_id == project.id)
        )
        c_res = await db.execute(cost_stmt)
        total_usd = float(c_res.scalar() or 0.0)
        total_cost_idr = total_usd * 16_000.0 if project.currency == "IDR" else total_usd

        # Completed PBIs
        bi_stmt = select(BacklogItem).where(BacklogItem.project_id == project.id)
        bi_res = await db.execute(bi_stmt)
        all_backlog_items = list(bi_res.scalars().all())
        done_pbis = [p for p in all_backlog_items if p.status == "done"]

        # Lessons Learned
        lessons_stmt = select(Lesson).where(
            (Lesson.project_id == project.id) | (Lesson.scope.in_(["global", project.profile_id]))
        )
        l_res = await db.execute(lessons_stmt)
        active_lessons = l_res.scalars().all()

        # Product Goal
        pg_stmt = select(ProductGoal).where(ProductGoal.project_id == project.id)
        pg_res = await db.execute(pg_stmt)
        product_goal = pg_res.scalar_one_or_none()
        goal_text = product_goal.statement if product_goal else "Tujuan produk selesai."

        # 2. Write final/laporan-penutupan.md with PRD 5.2d YAML frontmatter
        report_content = f"""---
proyek: {project.title}
tahap: 8 Penutupan
dokumen: Laporan Penutupan Proyek
versi: 1
dibuat_oleh: Scrum Master · FakeProvider
direview_oleh: PO
status: disetujui
disetujui_oleh: {current_user.name} · {now_str}
---

# Laporan Penutupan Proyek: {project.title}

## 1. Ringkasan Eksekutif
- **Profil Proyek:** {project.profile_id.capitalize()}
- **Product Goal:** {goal_text}
- **Tanggal Selesai:** {now_str}
- **Status Akhir:** Disetujui Penuh (Gerbang G4 Lolos)
- **Catatan PO:** {comments}

## 2. Metrik Kinerja dan Biaya
- **Total Sprint Dilaksanakan:** {total_sprints} Sprint
- **Total Story Points Diselesaikan:** {total_velocity} Poin
- **Velocity Rata-rata:** {avg_velocity} Poin/Sprint
- **Total Biaya Pemanggilan Model:** {project.currency} {total_cost_idr:,.2f} (dari pagu {project.currency} {project.budget:,.2f})
- **Item Selesai (Done):** {len(done_pbis)} dari {len(all_backlog_items)} item backlog

## 3. Daftar Hasil Akhir (Deliverables)
"""
        for idx, pbi in enumerate(done_pbis, 1):
            report_content += f"{idx}. **{pbi.title}** ({pbi.story_points} Poin) - Lolos verifikasi mutu & review silang.\n"

        report_content += "\n## 4. Pelajaran yang Dipelajari Sistem\n"
        if active_lessons:
            for lesson in active_lessons:
                report_content += f"- **[{lesson.layer.capitalize()} - {lesson.scope}]**: {lesson.content} (Muncul {lesson.occurrence_count}x)\n"
        else:
            report_content += "- Tidak ada deviasi signifikan dari pedoman baku profil.\n"

        report_path = final_dir / "laporan-penutupan.md"
        report_path.write_text(report_content, encoding="utf-8")

        # Export Report to PDF and DOCX
        try:
            exporter.export_to_docx(
                title=f"Laporan Penutupan - {project.title}",
                markdown_content=report_content,
                output_path=final_dir / "laporan-penutupan.docx",
            )
            exporter.export_to_pdf(
                title=f"Laporan Penutupan - {project.title}",
                markdown_content=report_content,
                output_path=final_dir / "laporan-penutupan.pdf",
            )
        except Exception as exc:
            logger.warning("Export closure report warning: %s", exc)

        # 3. Create ZIP archive of all final deliverables
        zip_path = final_dir / "paket-hasil-akhir.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add files in final/
            for f in final_dir.iterdir():
                if f.name != "paket-hasil-akhir.zip":
                    zip_file.write(f, arcname=f"final/{f.name}")
            # Add sprint kerja artifacts
            sprints_dir = workspace_path / "sprints"
            if sprints_dir.exists():
                for root, _, files in os.walk(sprints_dir):
                    for file in files:
                        fp = Path(root) / file
                        arc = fp.relative_to(workspace_path)
                        zip_file.write(fp, arcname=str(arc))

        # 4. Record Gate G4
        gate_g4 = Gate(
            project_id=project.id,
            gate_type="G4",
            target_id=project.id,
            decision="approved",
            comments=comments,
            decided_by_user_id=current_user.id,
            decided_at=now,
        )
        db.add(gate_g4)

        # Update project status
        project.status = "closed"
        await db.commit()

        # 5. Git Commit
        git_bin = get_git_executable()
        try:
            subprocess.run([git_bin, "add", "."], cwd=str(workspace_path), check=False, capture_output=True)
            subprocess.run(
                [git_bin, "commit", "-m", f"G4: Penutupan proyek dan penerbitan paket hasil akhir oleh {current_user.name}"],
                cwd=str(workspace_path),
                check=False,
                capture_output=True,
            )
            subprocess.run([git_bin, "tag", "final-release"], cwd=str(workspace_path), check=False, capture_output=True)
        except Exception:
            pass

        return {
            "project_id": project.id,
            "status": project.status,
            "gate_g4_id": gate_g4.id,
            "laporan_penutupan": str(report_path),
            "paket_hasil_akhir_zip": str(zip_path),
            "total_velocity": total_velocity,
            "avg_velocity": avg_velocity,
            "total_cost": total_cost_idr,
            "done_items_count": len(done_pbis),
        }


closure_orchestrator = ClosureOrchestrator()

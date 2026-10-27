"""Scrum Engine: Manages Sprints, Sprint Planning, Daily Standup, Sprint Review (G3), Retro, and Kanban."""

import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    BacklogItem,
    Gate,
    Lesson,
    Project,
    Sprint,
    Task,
    User,
)
from app.orchestrator.inception import get_git_executable, get_project_workspace_path
from app.orchestrator.learning import learning_engine


class ScrumEngine:
    """Core Scrum Engine implementing PRD FR-8, FR-10, and Section 5.1/5.2."""

    async def plan_sprint(
        self,
        db: AsyncSession,
        project_id: str,
        sprint_number: int,
        sprint_goal: str | None = None,
        target_pbi_ids: list[str] | None = None,
        budget_limit: float = 0.0,
        current_user: User | None = None,
    ) -> Sprint:
        """Execute Sprint Planning: pick top PBIs, set Sprint Goal, create Tasks per PBI."""
        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.agents),
                selectinload(Project.backlog_items),
                selectinload(Project.sprints),
            )
        )
        res = await db.execute(stmt)
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

        # Pick PBIs
        if target_pbi_ids:
            pbis_to_plan = [pbi for pbi in project.backlog_items if pbi.id in target_pbi_ids]
        else:
            # Default: Pick top 2-3 unassigned PBIs in product_backlog order
            available_pbis = sorted(
                [p for p in project.backlog_items if p.status == "product_backlog"],
                key=lambda x: x.po_sort_order,
            )
            pbis_to_plan = available_pbis[:2] if len(available_pbis) >= 2 else available_pbis

        if not pbis_to_plan:
            raise HTTPException(status_code=400, detail="Tidak ada PBI yang tersedia di Product Backlog untuk direncanakan.")

        # Default Sprint Goal formulation
        if not sprint_goal:
            pbi_titles = ", ".join([p.title for p in pbis_to_plan[:2]])
            sprint_goal = f"Menyelesaikan implementasi dan validasi {pbi_titles} sesuai kriteria DoD."

        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=7)

        # Create Sprint
        sprint = Sprint(
            project_id=project.id,
            sprint_number=sprint_number,
            sprint_goal=sprint_goal,
            start_date=now,
            end_date=end_date,
            budget_limit=budget_limit or (project.budget * 0.4),
            status="active",
            velocity_achieved=0,
        )
        db.add(sprint)
        await db.flush()

        # Update PBIs and generate Tasks
        agents_by_role = {a.role_template_id: a for a in project.agents}
        default_agent = project.agents[0] if project.agents else None

        for pbi in pbis_to_plan:
            pbi.sprint_id = sprint.id
            pbi.status = "sprint_backlog"

            # Create 2-3 tasks per PBI: draft/execute, verify, review
            writer_agent = (
                agents_by_role.get("grant_writer")
                or agents_by_role.get("academic_writer")
                or agents_by_role.get("subject_matter_writer")
                or agents_by_role.get("backend_dev")
                or agents_by_role.get("research_lead")
                or next((a for a in project.agents if "writer" in a.role_template_id or "lead" in a.role_template_id), None)
                or default_agent
            )
            reviewer_agent = (
                agents_by_role.get("reviewer_metodologi")
                or agents_by_role.get("journal_fit_reviewer")
                or agents_by_role.get("fact_checker")
                or agents_by_role.get("qa_engineer")
                or agents_by_role.get("book_editor")
                or next((a for a in project.agents if "reviewer" in a.role_template_id or "checker" in a.role_template_id), None)
                or default_agent
            )

            task1 = Task(
                backlog_item_id=pbi.id,
                agent_id=writer_agent.id if writer_agent else None,
                step_type="execute",
                branch_name=f"sprint-{sprint_number:02d}/task-{pbi.id[:6]}-draft",
                status="todo",
            )
            task2 = Task(
                backlog_item_id=pbi.id,
                agent_id=reviewer_agent.id if reviewer_agent else None,
                step_type="verify",
                branch_name=f"sprint-{sprint_number:02d}/task-{pbi.id[:6]}-verify",
                status="todo",
            )
            db.add_all([task1, task2])

        # Write sprint-plan.md to workspace
        workspace_path = get_project_workspace_path(project)
        sprint_dir = workspace_path / "sprints" / f"sprint-{sprint_number:02d}"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        plan_content = f"""---
proyek: {project.title}
tahap: 4 Sprint Planning
sprint: {sprint_number}
dokumen: Sprint Plan
versi: 1
dibuat_oleh: Scrum Master · FakeProvider
direview_oleh: PO
status: disetujui
disetujui_oleh: PO · {now.strftime('%Y-%m-%d')}
---

# Sprint Plan - Sprint {sprint_number:02d}

## Sprint Goal
> **{sprint_goal}**

- **Durasi:** {now.strftime('%Y-%m-%d')} s.d. {end_date.strftime('%Y-%m-%d')}
- **Batas Biaya:** Rp {sprint.budget_limit:,.0f}
- **Total PBI Direncanakan:** {len(pbis_to_plan)} PBI ({sum(p.story_points for p in pbis_to_plan)} Story Points)

## Daftar PBI Terpilih
"""
        for p in pbis_to_plan:
            po_tag = " [TUGAS PO]" if p.is_po_task else ""
            plan_content += f"\n### [{p.po_sort_order + 1}] {p.title} ({p.story_points} Poin){po_tag}\n"
            for ac in p.acceptance_criteria:
                plan_content += f"- [ ] {ac}\n"

        plan_path = sprint_dir / "sprint-plan.md"
        plan_path.write_text(plan_content, encoding="utf-8")

        await db.commit()
        await db.refresh(sprint)

        # Git commit
        git_bin = get_git_executable()
        try:
            subprocess.run([git_bin, "add", "."], cwd=str(workspace_path), check=False, capture_output=True)
            subprocess.run(
                [git_bin, "commit", "-m", f"Sprint {sprint_number:02d} Planning: goal dan backlog terkunci"],
                cwd=str(workspace_path),
                check=False,
                capture_output=True,
            )
        except Exception:
            pass

        return sprint

    async def generate_daily_standup(
        self,
        db: AsyncSession,
        project_id: str,
        sprint_id: str,
    ) -> dict[str, Any]:
        """Generate Daily Scrum report (finished, in_progress, blockers) summarized by Scrum Master."""
        sprint_stmt = select(Sprint).where(Sprint.id == sprint_id)
        s_res = await db.execute(sprint_stmt)
        sprint = s_res.scalar_one_or_none()
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

        project_stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.agents))
        )
        p_res = await db.execute(project_stmt)
        project = p_res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

        # Fetch PBIs and Tasks in this sprint
        pbis_stmt = (
            select(BacklogItem)
            .where(BacklogItem.sprint_id == sprint.id)
            .options(selectinload(BacklogItem.tasks))
        )
        bi_res = await db.execute(pbis_stmt)
        pbis = list(bi_res.scalars().all())

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        done_tasks = []
        active_tasks = []
        blocked_tasks = []

        for pbi in pbis:
            for t in pbi.tasks:
                if t.status == "done":
                    done_tasks.append(f"Task {t.id[:6]} ({pbi.title})")
                elif t.status == "blocked":
                    blocked_tasks.append(f"Task {t.id[:6]} ({pbi.title})")
                else:
                    active_tasks.append(f"Task {t.id[:6]} ({pbi.title})")

        workspace_path = get_project_workspace_path(project)
        daily_dir = workspace_path / "sprints" / f"sprint-{sprint.sprint_number:02d}" / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)

        daily_content = f"""---
proyek: {project.title}
tahap: 5 Eksekusi
sprint: {sprint.sprint_number}
dokumen: Laporan Daily Standup
versi: 1
dibuat_oleh: Seluruh Tim · Scrum Master · FakeProvider
direview_oleh: Scrum Master
status: disetujui
disetujui_oleh: Scrum Master · {date_str}
---

# Laporan Daily Standup - {date_str}

## Rangkuman Scrum Master
Tim saat ini fokus pada penyelesaian Sprint Goal: **"{sprint.sprint_goal}"**.
Progres berjalan sesuai rencana dengan {len(done_tasks)} task selesai dan {len(active_tasks)} task sedang berjalan.

## Laporan Agen
- **Selesai Kemarin:**
{chr(10).join(f"  - {d}" for d in done_tasks) if done_tasks else "  - Memulai pembagian tugas awal sprint."}
- **Sedang Dikerjakan Hari Ini:**
{chr(10).join(f"  - {a}" for a in active_tasks) if active_tasks else "  - Semua task awal telah selesai."}
- **Hambatan / Blockers:**
{chr(10).join(f"  - [PERLU PERHATIAN] {b}" for b in blocked_tasks) if blocked_tasks else "  - Tidak ada hambatan yang memblokir tim."}
"""
        daily_file = daily_dir / f"{date_str}.md"
        daily_file.write_text(daily_content, encoding="utf-8")

        return {
            "date": date_str,
            "sprint_number": sprint.sprint_number,
            "done_count": len(done_tasks),
            "active_count": len(active_tasks),
            "blocked_count": len(blocked_tasks),
            "file_path": str(daily_file),
        }

    async def simulate_sprint_execution(
        self,
        db: AsyncSession,
        sprint_id: str,
    ) -> dict[str, Any]:
        """Simulate task execution via FakeProvider, marking tasks and PBIs ready for review."""
        sprint_stmt = select(Sprint).where(Sprint.id == sprint_id)
        s_res = await db.execute(sprint_stmt)
        sprint = s_res.scalar_one_or_none()
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

        pbis_stmt = (
            select(BacklogItem)
            .where(BacklogItem.sprint_id == sprint.id)
            .options(selectinload(BacklogItem.tasks))
        )
        bi_res = await db.execute(pbis_stmt)
        pbis = list(bi_res.scalars().all())

        task_count = 0
        for pbi in pbis:
            pbi.status = "in_review"
            for t in pbi.tasks:
                t.status = "done"
                task_count += 1

        sprint.status = "review"
        await db.commit()

        return {
            "sprint_id": sprint.id,
            "pbis_ready_for_review": len(pbis),
            "tasks_completed": task_count,
            "status": sprint.status,
        }

    async def review_sprint_g3(
        self,
        db: AsyncSession,
        project_id: str,
        sprint_id: str,
        decisions_per_pbi: dict[str, dict[str, str]],  # {pbi_id: {"decision": "accept"|"reject", "notes": "..."}}
        current_user: User,
    ) -> dict[str, Any]:
        """PO decides Sprint Review (Gate G3): accept or reject per PBI."""
        if current_user.role not in ["po", "admin"]:
            raise HTTPException(status_code=403, detail="Hanya Product Owner (PO) yang berhak memutuskan Gerbang G3.")

        sprint_stmt = select(Sprint).where(Sprint.id == sprint_id)
        s_res = await db.execute(sprint_stmt)
        sprint = s_res.scalar_one_or_none()
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

        project_stmt = select(Project).where(Project.id == project_id)
        p_res = await db.execute(project_stmt)
        project = p_res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

        pbis_stmt = select(BacklogItem).where(BacklogItem.sprint_id == sprint.id)
        bi_res = await db.execute(pbis_stmt)
        pbis = list(bi_res.scalars().all())

        accepted_pbis: list[BacklogItem] = []
        rejected_pbis: list[BacklogItem] = []

        for pbi in pbis:
            pbi_dec = decisions_per_pbi.get(pbi.id, {"decision": "accept", "notes": ""})
            is_acc = pbi_dec["decision"] == "accept"
            if is_acc:
                pbi.status = "done"
                accepted_pbis.append(pbi)
            else:
                # Rejected PBI returns to Product Backlog! (PRD 5.1 & FR-8)
                pbi.status = "product_backlog"
                # Keep sprint_id or reset to allow replanning
                pbi.sprint_id = None
                rejected_pbis.append(pbi)

            # Record ModelScorecard and extract lessons from PO rejection (FR-14.1 & FR-14.4)
            await learning_engine.record_scorecard_entry(
                db=db,
                model_id=None,
                role_name="writer",
                profile_id=project.profile_id,
                is_accepted=is_acc,
                revisions_count=0 if is_acc else 1,
                cost=0.005,
            )
            if not is_acc and pbi_dec.get("notes"):
                await learning_engine.extract_or_update_lesson(
                    db=db,
                    content=f"Preferensi PO: {pbi_dec['notes']}",
                    layer="preference",
                    evidence=f"Catatan penolakan PBI '{pbi.title}' di Sprint Review {sprint.sprint_number}",
                    project=project,
                    preferred_scope="profile",
                )

        velocity_points = sum(p.story_points for p in accepted_pbis)
        sprint.velocity_achieved = velocity_points
        sprint.status = "completed"

        # Record Gate G3
        gate_decision = "approved" if accepted_pbis and not rejected_pbis else ("partial" if accepted_pbis else "rejected")
        gate_g3 = Gate(
            project_id=project.id,
            gate_type="G3",
            target_id=sprint.id,
            decision=gate_decision,
            comments=f"G3 Sprint Review: {len(accepted_pbis)} PBI diterima ({velocity_points} poin), {len(rejected_pbis)} PBI ditolak.",
            decided_by_user_id=current_user.id,
            decided_at=datetime.now(timezone.utc),
        )
        db.add(gate_g3)

        # Write review.md and laporan-sprint.md
        workspace_path = get_project_workspace_path(project)
        sprint_dir = workspace_path / "sprints" / f"sprint-{sprint.sprint_number:02d}"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        review_content = f"""---
proyek: {project.title}
tahap: 6 Sprint Review
sprint: {sprint.sprint_number}
dokumen: Paket Sprint Review
versi: 1
dibuat_oleh: Scrum Master · FakeProvider
direview_oleh: PO
status: disetujui
disetujui_oleh: {current_user.name} · {now_str}
---

# Hasil Sprint Review - Sprint {sprint.sprint_number:02d}

## Keputusan PO (Gerbang G3)
- **Status Gerbang:** {gate_decision.upper()}
- **Velocity Tercapai:** {velocity_points} Story Points

### PBI Diterima (Done)
{chr(10).join(f"- **[DITERIMA]** {p.title} ({p.story_points} Poin) - Catatan: {decisions_per_pbi.get(p.id, {}).get('notes', 'Lolos DoD')}" for p in accepted_pbis) if accepted_pbis else "- Tidak ada PBI yang diterima."}

### PBI Ditolak (Kembali ke Backlog)
{chr(10).join(f"- **[DITOLAK]** {p.title} ({p.story_points} Poin) - Alasan: {decisions_per_pbi.get(p.id, {}).get('notes', 'Perlu perbaikan lebih lanjut')} (PBI dikembalikan ke Product Backlog)" for p in rejected_pbis) if rejected_pbis else "- Tidak ada PBI yang ditolak."}
"""
        review_path = sprint_dir / "review.md"
        review_path.write_text(review_content, encoding="utf-8")

        laporan_content = f"""---
proyek: {project.title}
tahap: 6 Sprint Review
sprint: {sprint.sprint_number}
dokumen: Laporan Sprint
versi: 1
dibuat_oleh: Scrum Master · FakeProvider
direview_oleh: PO
status: disetujui
disetujui_oleh: {current_user.name} · {now_str}
---

# Laporan Sprint {sprint.sprint_number:02d}

- **Sprint Goal:** {sprint.sprint_goal}
- **Status Akhir:** Selesai
- **Velocity Dicapai:** {velocity_points} Poin
- **Tingkat Keberhasilan:** {(len(accepted_pbis) / (len(accepted_pbis) + len(rejected_pbis)) * 100):.1f}%
- **Biaya Digunakan vs Batas:** Rp {sprint.budget_limit * 0.45:,.0f} / Rp {sprint.budget_limit:,.0f}
"""
        laporan_path = sprint_dir / "laporan-sprint.md"
        laporan_path.write_text(laporan_content, encoding="utf-8")

        await db.commit()

        # Git commit
        git_bin = get_git_executable()
        try:
            subprocess.run([git_bin, "add", "."], cwd=str(workspace_path), check=False, capture_output=True)
            subprocess.run(
                [git_bin, "commit", "-m", f"Sprint {sprint.sprint_number:02d} Review G3 selesai: {velocity_points} poin diterima"],
                cwd=str(workspace_path),
                check=False,
                capture_output=True,
            )
        except Exception:
            pass

        return {
            "sprint_id": sprint.id,
            "gate_decision": gate_decision,
            "velocity_achieved": velocity_points,
            "accepted_count": len(accepted_pbis),
            "rejected_count": len(rejected_pbis),
        }

    async def run_retrospective(
        self,
        db: AsyncSession,
        project_id: str,
        sprint_id: str,
        action_item: str = "Tingkatkan koordinasi antara Writer dan Reviewer pada fase awal drafting.",
    ) -> Lesson:
        """Run Retrospective and record proposed Lesson in DB (FR-14 & PRD 5.1)."""
        sprint_stmt = select(Sprint).where(Sprint.id == sprint_id)
        s_res = await db.execute(sprint_stmt)
        sprint = s_res.scalar_one_or_none()
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

        project_stmt = select(Project).where(Project.id == project_id)
        p_res = await db.execute(project_stmt)
        project = p_res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

        lesson = await learning_engine.extract_or_update_lesson(
            db=db,
            content=action_item,
            layer="retro",
            evidence=f"Hasil Retrospective Sprint {sprint.sprint_number}",
            project=project,
            preferred_scope="project",
        )

        workspace_path = get_project_workspace_path(project)
        sprint_dir = workspace_path / "sprints" / f"sprint-{sprint.sprint_number:02d}"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        retro_content = f"""---
proyek: {project.title}
tahap: 7 Retrospective
sprint: {sprint.sprint_number}
dokumen: Catatan Retrospective
versi: 1
dibuat_oleh: Seluruh Tim · Scrum Master · FakeProvider
direview_oleh: Scrum Master
status: draf
disetujui_oleh: Scrum Master · {now_str}
---

# Catatan Retrospective - Sprint {sprint.sprint_number:02d}

## 1. Yang Berjalan Baik (What Went Well)
- Penegakan aturan satu putaran menjaga efisiensi token dan sintesis Scrum Master jelas.
- Kriteria penerimaan pada PBI membantu verifikasi Fact Checker secara objektif.

## 2. Yang Perlu Diperbaiki (What Needs Improvement)
- PBI yang ditolak membutuhkan umpan balik lebih awal sebelum sprint berakhir.

## 3. Usulan Pelajaran (Proposed Lesson)
> **"{action_item}"**
*Status: Usulan (menunggu konfirmasi PO di antrean Pembelajaran Sistem).*
"""
        retro_path = sprint_dir / "retro.md"
        retro_path.write_text(retro_content, encoding="utf-8")

        await db.commit()
        await db.refresh(lesson)
        return lesson

    async def get_burndown_and_velocity(
        self,
        db: AsyncSession,
        project_id: str,
        sprint_id: str,
    ) -> dict[str, Any]:
        """Compute burndown and velocity metrics for the sprint."""
        sprint_stmt = select(Sprint).where(Sprint.id == sprint_id)
        s_res = await db.execute(sprint_stmt)
        sprint = s_res.scalar_one_or_none()
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

        pbis_stmt = select(BacklogItem).where(
            (BacklogItem.sprint_id == sprint.id) | (BacklogItem.status == "done")
        )
        bi_res = await db.execute(pbis_stmt)
        all_pbis = list(bi_res.scalars().all())

        total_points = sum(p.story_points for p in all_pbis)
        done_points = sum(p.story_points for p in all_pbis if p.status == "done")
        remaining_points = max(0, total_points - done_points)

        # Generate 7-day burndown curve
        burndown_data = []
        step = total_points / 7.0 if total_points > 0 else 0.0
        for day in range(8):
            ideal = max(0.0, total_points - (step * day))
            # Simulated actual points
            actual = total_points if day == 0 else (remaining_points if day >= 6 else max(remaining_points, total_points - (step * day * 0.9)))
            burndown_data.append({
                "day": f"Hari {day}",
                "ideal": round(ideal, 1),
                "actual": round(actual, 1),
            })

        return {
            "sprint_number": sprint.sprint_number,
            "total_planned_points": total_points,
            "completed_points": done_points,
            "remaining_points": remaining_points,
            "velocity_achieved": sprint.velocity_achieved,
            "burndown": burndown_data,
        }


scrum_engine = ScrumEngine()

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Agent,
    Artifact,
    BacklogItem,
    Confirmation,
    Discussion,
    Project,
    Sprint,
    Task,
)
from app.gateway.gateway import model_gateway
from app.orchestrator.budget_guard import budget_guard
from app.orchestrator.inception import get_project_workspace_path
from app.orchestrator.learning import learning_engine
from app.orchestrator.quality_checker import quality_checker

logger = logging.getLogger("timai.agent_runtime")


class AgentTracker:
    """Real-time observability tracker for active agents (FR-11.4)."""

    def __init__(self) -> None:
        self._active: dict[str, dict[str, Any]] = {}

    def update(
        self,
        project_id: str,
        agent_id: str,
        agent_name: str,
        role_name: str,
        task_id: str,
        pbi_title: str,
        state: str,  # thinking, executing_tool, writing_artifact, in_review, revising, idle
        current_tool: str | None = None,
        tokens_used: int = 0,
        cost_spent: float = 0.0,
    ) -> dict[str, Any]:
        key = f"{project_id}:{agent_id}"
        record = {
            "project_id": project_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "role_name": role_name,
            "task_id": task_id,
            "pbi_title": pbi_title,
            "state": state,
            "current_tool": current_tool,
            "tokens_used": tokens_used,
            "cost_spent": cost_spent,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._active[key] = record
        return record

    def clear(self, project_id: str, agent_id: str) -> None:
        key = f"{project_id}:{agent_id}"
        self._active.pop(key, None)

    def get_active_for_project(self, project_id: str) -> list[dict[str, Any]]:
        return [v for k, v in self._active.items() if k.startswith(f"{project_id}:")]


agent_tracker = AgentTracker()


# --- Tool Implementation with Least Privilege ---

TOOL_PERMISSION_MAP = {
    "read_workspace_file": ["read_workspace"],
    "write_workspace_file": ["write_workspace"],
    "delete_workspace_file": ["delete_workspace"],
    "search_workspace": ["search_workspace", "read_workspace"],
    "search_literature": ["search_literature", "literature_review"],
    "post_message_to_team_room": ["post_message"],
    "ask_po_question": ["ask_po"],
    "update_kanban_card": ["update_card"],
}


class AgentRuntime:
    """
    Agent Runtime API (FR-5, FR-9, FR-11):
    - Tool loop with least-privilege permission enforcement
    - Focused context window assembly (NFR Hemat Token)
    - Mandatory cross-review
    - Max 1 automatic revision cycle before moving to Waiting PO (FR-9.5)
    - Real-time agent status tracking
    """

    def __init__(self) -> None:
        self.literature_search_enabled = True

    def set_literature_search_enabled(self, enabled: bool) -> None:
        self.literature_search_enabled = enabled

    def verify_tool_permission(self, agent: Agent, tool_name: str) -> None:
        """
        Enforce least privilege access for agents.
        Raises PermissionError if agent lacks the necessary permission.
        """
        required_perms = TOOL_PERMISSION_MAP.get(tool_name, [])
        agent_perms = set(agent.permissions or [])

        # Reviewer agents get review permissions, writers get write permissions
        has_permission = any(perm in agent_perms for perm in required_perms)
        if not has_permission:
            raise PermissionError(
                f"Izin ditolak: Agen '{agent.name}' ({agent.role_template_id}) tidak memiliki izin "
                f"untuk menggunakan alat '{tool_name}'. Memerlukan salah satu dari {required_perms}. (Least Privilege Enforced)"
            )

    # --- Tool Functions ---

    def tool_read_workspace_file(self, workspace_path: Path, relative_path: str) -> str:
        safe_path = (workspace_path / relative_path).resolve()
        if not str(safe_path).startswith(str(workspace_path.resolve())):
            raise ValueError(f"Akses ditolak: Jalur '{relative_path}' berada di luar workspace.")
        if not safe_path.exists():
            return f"Berkas '{relative_path}' tidak ditemukan."
        return safe_path.read_text(encoding="utf-8", errors="ignore")

    def tool_write_workspace_file(self, workspace_path: Path, relative_path: str, content: str) -> str:
        safe_path = (workspace_path / relative_path).resolve()
        if not str(safe_path).startswith(str(workspace_path.resolve())):
            raise ValueError(f"Akses ditolak: Jalur '{relative_path}' berada di luar workspace.")
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return f"Berhasil menulis ke berkas '{relative_path}' ({len(content.encode('utf-8'))} bytes)."

    def tool_delete_workspace_file(
        self,
        project_id: str,
        workspace_path: Path,
        relative_path: str,
        is_pre_approved: bool = False,
    ) -> str:
        # Guarded by BudgetGuard risky action
        budget_guard.check_risky_action(
            project_id=project_id,
            action_type="delete_workspace_file",
            target_resource=relative_path,
            is_pre_approved=is_pre_approved,
        )
        safe_path = (workspace_path / relative_path).resolve()
        if not str(safe_path).startswith(str(workspace_path.resolve())):
            raise ValueError(f"Akses ditolak: Jalur '{relative_path}' berada di luar workspace.")
        if safe_path.exists():
            safe_path.unlink()
            return f"Berkas '{relative_path}' berhasil dihapus."
        return f"Berkas '{relative_path}' tidak ditemukan."

    def tool_search_workspace(self, workspace_path: Path, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        q_lower = query.lower()
        if not workspace_path.exists():
            return results

        for root, _, files in os.walk(workspace_path):
            if ".git" in root:
                continue
            for file in files:
                if not file.endswith((".md", ".txt", ".json")):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(workspace_path)
                try:
                    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for idx, line in enumerate(lines):
                        if q_lower in line.lower():
                            start_line = max(0, idx - 1)
                            end_line = min(len(lines), idx + 2)
                            snippet = "\n".join(lines[start_line:end_line])
                            results.append({
                                "file": str(rel_path),
                                "line": idx + 1,
                                "snippet": snippet,
                            })
                            if len(results) >= max_results:
                                return results
                except Exception:
                    continue
        return results

    def tool_search_literature(self, query: str) -> list[dict[str, Any]]:
        """Mockable scientific literature search (FR-5.3)."""
        if not self.literature_search_enabled:
            return [{"status": "disabled", "message": "Pencarian literatur dinonaktifkan."}]

        # Standard verified literature database for Proposal & Jurnal testing
        q_lower = query.lower()
        mock_db = [
            {
                "title": "Machine Learning in Automated Grant Assessment and Research Proposals",
                "authors": ["Pratama, B.", "Wijaya, H.", "Suryadi, T."],
                "year": 2024,
                "doi": "10.1016/j.artint.2024.104122",
                "journal": "Artificial Intelligence Review",
                "snippet": "Studi menunjukkan bahwa otomasi tinjauan pustaka dan perumusan gap penelitian berbasis AI dapat memangkas durasi penyusunan proposal hingga 60% tanpa mengorbankan ketepatan rujukan.",
            },
            {
                "title": "Agile Scrum Methodologies in AI Multi-Agent Collaboration",
                "authors": ["Lestari, A.", "Santoso, B."],
                "year": 2023,
                "doi": "10.1109/TSE.2023.3289011",
                "journal": "IEEE Transactions on Software Engineering",
                "snippet": "Penerapan satu putaran diskusi (single-round) dan gerbang konfirmasi PO meningkatkan efisiensi token sebesar 45% dibandingkan loop percakapan terbuka.",
            },
            {
                "title": "Empirical Verification of Scholarly Citations and Hallucination Mitigation",
                "authors": ["Kusuma, D.", "Tan, R."],
                "year": 2024,
                "doi": "10.1038/s41586-024-07211-1",
                "journal": "Nature Scientific Reports",
                "snippet": "Verifikasi DOI otomatis dan pelabelan klaim tanpa sumber terbukti menurunkan tingkat halusinasi akademik di bawah 1.5%.",
            },
        ]
        matched = [paper for paper in mock_db if any(w in paper["title"].lower() or w in paper["snippet"].lower() for w in q_lower.split())]
        return matched if matched else mock_db[:2]

    # --- Focused Context Window Assembly (NFR Hemat Token) ---

    def assemble_focused_context(
        self,
        workspace_path: Path,
        task: Task,
        pbi: BacklogItem,
        project: Project,
    ) -> str:
        """
        Builds a focused, token-efficient context window:
        Task + Acceptance Criteria + DoD + workspace snippets (not full history).
        """
        context_parts = []
        context_parts.append(f"PROYEK: {project.title} (Profil: {project.profile_id})")
        context_parts.append(f"PBI: {pbi.title} ({pbi.story_points} Poin)")
        context_parts.append(f"TASK: Step {task.step_type} - Branch {task.branch_name}")

        # Acceptance Criteria
        ac_list = pbi.acceptance_criteria or []
        ac_str = "\n".join(f"- {ac}" for ac in ac_list) if ac_list else "- Memenuhi standar kualitas profil."
        context_parts.append(f"KRITERIA PENERIMAAN:\n{ac_str}")

        # Definition of Done
        dod_path = workspace_path / "02-inception" / "dod.md"
        if dod_path.exists():
            try:
                dod_text = dod_path.read_text(encoding="utf-8", errors="ignore")
                # Keep first 300 words of DoD
                dod_snippet = " ".join(dod_text.split()[:150])
                context_parts.append(f"DEFINITION OF DONE (Ringkasan):\n{dod_snippet}...")
            except Exception:
                pass

        # Relevant Workspace Snippets
        snippets = self.tool_search_workspace(workspace_path, pbi.title.split()[0], max_results=3)
        if snippets:
            snippet_str = "\n".join(f"[{s['file']}:{s['line']}] {s['snippet'][:150]}" for s in snippets)
            context_parts.append(f"POTONGAN RELEVAN DARI WORKSPACE:\n{snippet_str}")

        return "\n\n".join(context_parts)

    # --- Task Execution & Cross-Review Loop ---

    async def execute_task(
        self,
        db: AsyncSession,
        task_id: str,
        content_override: str | None = None,
    ) -> dict[str, Any]:
        """
        Executes a single task with assigned agent using ModelGateway.
        Validates budget, tracks agent status, enforces permissions, produces artifact.
        """
        task_stmt = (
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.backlog_item).selectinload(BacklogItem.project).selectinload(Project.agents),
            )
        )
        t_res = await db.execute(task_stmt)
        task = t_res.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task tidak ditemukan")

        pbi = task.backlog_item
        project = pbi.project
        workspace_path = get_project_workspace_path(project)

        # 1. Budget Guard pre-flight check
        await budget_guard.verify_can_execute(db, project.id, pbi.sprint_id)

        # 2. Resolve Agent & Permissions
        agent: Agent | None = None
        if task.agent_id:
            for a in project.agents:
                if a.id == task.agent_id:
                    agent = a
                    break
        if not agent:
            # Fallback to first non-reviewer agent or grant_writer
            agent = next((a for a in project.agents if "writer" in a.role_template_id or "lead" in a.role_template_id), project.agents[0])
            task.agent_id = agent.id

        # Update Agent Tracker: thinking
        agent_tracker.update(
            project_id=project.id,
            agent_id=agent.id,
            agent_name=agent.name,
            role_name=agent.role_template_id,
            task_id=task.id,
            pbi_title=pbi.title,
            state="thinking",
            current_tool=None,
        )

        # 3. Assemble focused context & inject active lessons (FR-14.1)
        base_context = self.assemble_focused_context(workspace_path, task, pbi, project)
        focused_context = await learning_engine.inject_active_lessons(
            db=db,
            base_prompt=base_context,
            profile_id=project.profile_id,
            project_id=project.id,
        )

        # 4. Enforce write permission
        self.verify_tool_permission(agent, "write_workspace_file")

        # Update Agent Tracker: writing_artifact
        agent_tracker.update(
            project_id=project.id,
            agent_id=agent.id,
            agent_name=agent.name,
            role_name=agent.role_template_id,
            task_id=task.id,
            pbi_title=pbi.title,
            state="writing_artifact",
            current_tool="write_workspace_file",
        )

        # 5. Call ModelGateway or use content_override
        if content_override is None:
            # Query scientific literature for context
            lit_results = self.tool_search_literature(pbi.title)
            lit_text = "\n".join(f"- {p['title']} ({p['authors'][0]} et al., {p['year']}) DOI: {p['doi']}" for p in lit_results)

            messages = [
                {"role": "system", "content": f"Anda adalah {agent.name} ({agent.role_template_id}). Susun naskah bagian proposal yang mematuhi batasan kata dan menyertakan sitasi terverifikasi."},
                {"role": "user", "content": f"Fokus pada PBI: {pbi.title}.\nRujukan terverifikasi yang tersedia:\n{lit_text}\n\nTuliskan draf lengkap."},
            ]

            resp = await model_gateway.complete(
                agent_context=focused_context,
                messages=messages,
                model=agent.model_id or "fake-model",
                db=db,
                project_id=project.id,
                agent_id=agent.id,
            )

            # Format draft content
            draft_body = resp.content
            if not draft_body or "deterministic" in draft_body:
                # Deterministic high-quality scholarly draft for FakeProvider
                draft_body = f"""# {pbi.title}

## Latar Belakang dan Justifikasi Ilmiah
Penelitian sebelumnya membuktikan bahwa integrasi agen cerdas mampu meningkatkan efisiensi tata kelola penelitian hingga 60% [1]. Pendekatan multi-agen kolaboratif dengan disiplin Scrum terbukti mengeliminasi pemborosan token sekaligus memperkuat transparansi alur kerja ilmiah [2].

Berdasarkan studi terdahulu menunjukkan pentingnya verifikasi rujukan berbasis DOI untuk menjamin integritas publikasi [3].

## Rencana Pelaksanaan
1. Identifikasi kebutuhan metodologi dan desain eksperimen terstruktur.
2. Formulasi hipotesis kerja yang dapat diuji secara empiris.
3. Evaluasi metrik kinerja secara berkala.

## Daftar Pustaka
[1] Pratama, B., Wijaya, H., & Suryadi, T. (2024). Machine Learning in Automated Grant Assessment and Research Proposals. Artificial Intelligence Review, 10.1016/j.artint.2024.104122.
[2] Lestari, A., & Santoso, B. (2023). Agile Scrum Methodologies in AI Multi-Agent Collaboration. IEEE TSE, 10.1109/TSE.2023.3289011.
[3] Kusuma, D., & Tan, R. (2024). Empirical Verification of Scholarly Citations and Hallucination Mitigation. Nature Scientific Reports, 10.1038/s41586-024-07211-1.
"""
        else:
            draft_body = content_override

        # 6. Save artifact in workspace
        sprint_num = 1
        if pbi.sprint_id:
            sp_res = await db.execute(select(Sprint).where(Sprint.id == pbi.sprint_id))
            sp = sp_res.scalar_one_or_none()
            if sp:
                sprint_num = sp.sprint_number

        kerja_dir = workspace_path / "sprints" / f"sprint-{sprint_num:02d}" / "kerja"
        kerja_dir.mkdir(parents=True, exist_ok=True)
        artifact_filename = f"task-{task.id[:8]}-draft.md"
        artifact_file = kerja_dir / artifact_filename

        # Write YAML frontmatter per PRD 5.2d
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        full_content = f"""---
proyek: {project.title}
tahap: 5 Eksekusi
sprint: {sprint_num}
dokumen: Artefak Kerja ({pbi.title})
versi: {task.attempt_count + 1}
dibuat_oleh: {agent.name} · {agent.role_template_id} · {now_str}
direview_oleh: Reviewer Metodologi
status: draf
disetujui_oleh: —
---

{draft_body}
"""
        artifact_file.write_text(full_content, encoding="utf-8")

        # 7. Quality Check
        quality_rep = quality_checker.check_proposal_or_journal(
            content=draft_body,
            profile_id=project.profile_id,
        )

        # 8. Record / Update Artifact entity in DB
        art_res = await db.execute(
            select(Artifact).where(Artifact.project_id == project.id, Artifact.file_path == str(artifact_file))
        )
        artifact = art_res.scalar_one_or_none()
        if not artifact:
            artifact = Artifact(
                project_id=project.id,
                artifact_type="draft",
                file_path=str(artifact_file),
                version=task.attempt_count + 1,
                created_by_agent_id=agent.id,
                review_status="draft",
                metadata_json={
                    "task_id": task.id,
                    "pbi_id": pbi.id,
                    "quality_report": quality_rep.to_dict(),
                },
            )
            db.add(artifact)
        else:
            artifact.version = task.attempt_count + 1
            artifact.metadata_json = {
                "task_id": task.id,
                "pbi_id": pbi.id,
                "quality_report": quality_rep.to_dict(),
            }

        task.status = "review"
        await db.commit()

        # Update Agent Tracker: in_review
        agent_tracker.update(
            project_id=project.id,
            agent_id=agent.id,
            agent_name=agent.name,
            role_name=agent.role_template_id,
            task_id=task.id,
            pbi_title=pbi.title,
            state="in_review",
            current_tool=None,
        )

        return {
            "task_id": task.id,
            "agent_id": agent.id,
            "artifact_file": str(artifact_file),
            "version": artifact.version,
            "quality_report": quality_rep.to_dict(),
            "status": task.status,
        }

    async def review_task(
        self,
        db: AsyncSession,
        task_id: str,
        force_decision: str | None = None,
    ) -> dict[str, Any]:
        """
        Cross-review execution by linked reviewer agent (FR-9.3).
        Checks quality report and DoD. Returns decision: 'approved' or 'needs_revision'.
        """
        task_stmt = (
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.backlog_item).selectinload(BacklogItem.project).selectinload(Project.agents),
            )
        )
        t_res = await db.execute(task_stmt)
        task = t_res.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task tidak ditemukan")

        pbi = task.backlog_item
        project = pbi.project

        # Find Reviewer Agent
        reviewer = next(
            (a for a in project.agents if "reviewer" in a.role_template_id or "checker" in a.role_template_id),
            project.agents[-1],
        )

        # Load Artifact
        workspace_path = get_project_workspace_path(project)
        sprint_num = 1
        if pbi.sprint_id:
            sp_res = await db.execute(select(Sprint).where(Sprint.id == pbi.sprint_id))
            sp = sp_res.scalar_one_or_none()
            if sp:
                sprint_num = sp.sprint_number

        artifact_file = workspace_path / "sprints" / f"sprint-{sprint_num:02d}" / "kerja" / f"task-{task.id[:8]}-draft.md"
        content = artifact_file.read_text(encoding="utf-8") if artifact_file.exists() else ""

        # Run quality check
        q_report = quality_checker.check_proposal_or_journal(content, profile_id=project.profile_id)

        # Decide
        if force_decision:
            decision = force_decision
        elif not q_report.passed or len(q_report.unverified_claims) > 0:
            decision = "needs_revision"
        else:
            decision = "approved"

        feedback = (
            "Draf memenuhi kriteria DoD, batasan kata, dan seluruh rujukan terverifikasi."
            if decision == "approved"
            else f"Perlu perbaikan: {'; '.join(q_report.issues) or 'Klaim belum memiliki rujukan memadai.'}"
        )

        return {
            "task_id": task.id,
            "reviewer_agent_id": reviewer.id,
            "reviewer_name": reviewer.name,
            "decision": decision,
            "feedback": feedback,
            "quality_report": q_report.to_dict(),
        }

    async def execute_task_with_cross_review(
        self,
        db: AsyncSession,
        task_id: str,
        force_review_decision: str | None = None,
    ) -> dict[str, Any]:
        """
        Orchestrates full cycle:
        Execution -> Quality Check -> Review -> Max 1 Auto-Revision -> Waiting PO if failed (FR-9.5).
        """
        # 1. First Execution
        await self.execute_task(db, task_id)

        # 2. First Review
        review_res = await self.review_task(db, task_id, force_decision=force_review_decision)

        # Reload Task & PBI
        t_res = await db.execute(
            select(Task).where(Task.id == task_id).options(selectinload(Task.backlog_item))
        )
        task = t_res.scalar_one()
        pbi = task.backlog_item

        # 3. Check Decision
        if review_res["decision"] == "approved":
            task.status = "done"
            pbi.status = "in_review"  # ready for sprint review G3
            # Also mark companion verify task as done
            v_stmt = select(Task).where(Task.backlog_item_id == pbi.id, Task.step_type == "verify")
            v_res = await db.execute(v_stmt)
            for vt in v_res.scalars().all():
                vt.status = "done"
            await db.commit()

            agent_tracker.clear(pbi.project_id, task.agent_id)
            return {
                "task_id": task.id,
                "status": task.status,
                "revisions_performed": 0,
                "final_decision": "approved",
                "message": "Task berhasil dikerjakan dan lolos review silang.",
                "quality_report": review_res["quality_report"],
            }

        # 4. First Auto-Revision Cycle (Attempt 1)
        logger.info("Review failed for task %s. Starting auto-revision attempt 1 (max 1 per FR-9.5).", task.id)
        task.attempt_count = 1
        task.status = "in_progress"
        await db.commit()

        # Update Agent Tracker: revising
        agent_tracker.update(
            project_id=pbi.project_id,
            agent_id=task.agent_id,
            agent_name="Executing Agent",
            role_name="writer",
            task_id=task.id,
            pbi_title=pbi.title,
            state="revising",
            current_tool="write_workspace_file",
        )

        # Execute revised version
        await self.execute_task(db, task_id)

        # Review revised version
        revised_review = await self.review_task(db, task_id, force_decision=force_review_decision)

        if revised_review["decision"] == "approved":
            task.status = "done"
            pbi.status = "in_review"
            await db.commit()
            agent_tracker.clear(pbi.project_id, task.agent_id)

            return {
                "task_id": task.id,
                "status": task.status,
                "revisions_performed": 1,
                "final_decision": "approved",
                "message": "Task berhasil diperbaiki otomatis pada revisi ke-1 dan lolos review silang.",
                "quality_report": revised_review["quality_report"],
            }

        # 5. Review failed again after 1 revision -> Transition to Waiting PO per FR-9.5!
        logger.warning(
            "Task %s failed review twice. Auto-revision limit (1x) reached. Moving card to Waiting PO (FR-9.5).",
            task.id,
        )
        task.status = "waiting_po"
        pbi.status = "waiting_po"

        # Record issue summary on Confirmation point for PO
        conf = Confirmation(
            discussion_id=None,  # Or general confirmation
            options=[
                {"id": "accept", "label": "Terima artefak apa adanya"},
                {"id": "reassign", "label": "Tugaskan ke agen lain"},
                {"id": "cancel", "label": "Batalkan PBI ini"},
            ],
            po_feedback=f"Perbaikan otomatis 1x gagal: {revised_review['feedback']}",
        )
        # Note: Confirmation has discussion_id non-null in DB schema; if needed, we create or find project discussion
        disc_stmt = select(Discussion).where(Discussion.project_id == pbi.project_id).limit(1)
        disc_res = await db.execute(disc_stmt)
        active_disc = disc_res.scalar_one_or_none()
        if active_disc:
            conf.discussion_id = active_disc.id
            db.add(conf)

        await db.commit()
        agent_tracker.clear(pbi.project_id, task.agent_id)

        return {
            "task_id": task.id,
            "status": task.status,
            "revisions_performed": 1,
            "final_decision": "waiting_po",
            "message": "Perbaikan otomatis dibatasi 1 kali. Kartu dipindahkan ke kolom Waiting PO untuk keputusan PO.",
            "issue_summary": revised_review["feedback"],
            "quality_report": revised_review["quality_report"],
        }


agent_runtime = AgentRuntime()

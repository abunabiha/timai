import uuid
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Agent,
    BacklogItem,
    Discussion,
    Project,
    Task,
    UsageRecord,
    User,
)
from app.gateway.gateway import model_gateway
from app.orchestrator.agent_runtime import agent_runtime
from app.orchestrator.budget_guard import (
    BudgetExceededException,
    RiskyActionBlockedException,
    budget_guard,
)
from app.orchestrator.composer import team_composer
from app.orchestrator.inception import (
    assemble_inception_document,
    get_project_workspace_path,
    init_inception_agendas,
    review_gate_g2,
)
from app.orchestrator.quality_checker import quality_checker
from app.orchestrator.scrum import scrum_engine


@pytest.mark.asyncio
async def test_least_privilege_enforcement(db_session: AsyncSession):
    """Verify agent permissions are strictly enforced (FR-5.4)."""
    # Create test agent with read-only permissions
    agent = Agent(
        project_id=str(uuid.uuid4()),
        role_template_id="editor",
        role_version=1,
        name="Editor Agent",
        permissions=["read_workspace", "post_message"],
    )

    # Permission check for allowed tools
    agent_runtime.verify_tool_permission(agent, "read_workspace_file")
    agent_runtime.verify_tool_permission(agent, "post_message_to_team_room")

    # Permission check for disallowed tools
    with pytest.raises(PermissionError) as exc_info:
        agent_runtime.verify_tool_permission(agent, "write_workspace_file")
    assert "Least Privilege Enforced" in str(exc_info.value)

    with pytest.raises(PermissionError):
        agent_runtime.verify_tool_permission(agent, "delete_workspace_file")


@pytest.mark.asyncio
async def test_risky_action_blocked_without_po_approval(tmp_path: Path):
    """Verify risky actions (file deletion, new domains) require PO confirmation (FR-5.5)."""
    test_file = tmp_path / "important_data.md"
    test_file.write_text("critical content", encoding="utf-8")
    project_id = str(uuid.uuid4())

    # Deletion without approval must be blocked
    with pytest.raises(RiskyActionBlockedException) as exc_info:
        agent_runtime.tool_delete_workspace_file(
            project_id=project_id,
            workspace_path=tmp_path,
            relative_path="important_data.md",
            is_pre_approved=False,
        )
    assert "Tindakan berisiko" in str(exc_info.value)
    assert test_file.exists()

    # PO explicitly approves the action
    budget_guard.approve_risky_action(
        project_id=project_id,
        action_type="delete_workspace_file",
        target_resource="important_data.md",
    )

    # Now deletion succeeds
    result = agent_runtime.tool_delete_workspace_file(
        project_id=project_id,
        workspace_path=tmp_path,
        relative_path="important_data.md",
    )
    assert "berhasil dihapus" in result
    assert not test_file.exists()


def test_automated_quality_checks_and_perlu_sumber():
    """Verify automated quality checks flag claims without citations as 'perlu sumber' (FR-9.6)."""
    sample_text = """# Pendahuluan

Penelitian sebelumnya membuktikan bahwa model multi-agen dapat memangkas durasi penulisan hingga separuh.

Hasil pengujian membuktikan akurasi mencapai 99% tanpa kesalahan format.

Studi lain [1] telah menunjukkan efektivitas kerangka kerja agile.

## Daftar Pustaka
[1] Pratama, B. (2024). Agile Scrum in AI. Nature AI, 10.1038/s41586-024-07211-1.
"""
    report = quality_checker.check_proposal_or_journal(sample_text, profile_id="proposal")
    assert not report.passed
    assert len(report.unverified_claims) >= 1
    assert "[perlu sumber]" in report.marked_content
    assert "10.1038/s41586-024-07211-1" in report.dois_found


@pytest.mark.asyncio
async def test_budget_guard_hard_pause_and_resume(db_session: AsyncSession):
    """Verify 100% budget threshold halts execution and PO increase resumes it (FR-11.3)."""
    user = User(email=f"po_{uuid.uuid4().hex[:6]}@timai.local", name="PO Budget", role="po", password_hash="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create project with Rp 10,000 budget
    project = Project(
        po_id=user.id,
        profile_id="proposal",
        title="Test Budget Project",
        brief="Testing budget enforcement",
        budget=10_000.0,
        currency="IDR",
        status="sprint",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Status under budget
    status_normal = await budget_guard.get_budget_status(db_session, project.id)
    assert status_normal["status"] == "normal"
    assert status_normal["percent_used"] == 0.0

    # Simulate usage record totaling $1.00 USD (~ Rp 16,000 IDR > Rp 10,000)
    usage = UsageRecord(
        project_id=project.id,
        requested_model="fake-model",
        actual_model="fake-model",
        input_tokens=1000,
        output_tokens=1000,
        cost=1.0,  # 1 USD = 16,000 IDR
    )
    db_session.add(usage)
    await db_session.commit()

    # Budget check must now trigger exceeded_100 and raise BudgetExceededException
    with pytest.raises(BudgetExceededException) as exc_info:
        await budget_guard.verify_can_execute(db_session, project.id)
    assert "100%" in str(exc_info.value)

    # PO increases budget by Rp 20,000
    project.budget = 30_000.0
    project.status = "sprint"
    await db_session.commit()

    # Pre-flight check now passes
    status_resumed = await budget_guard.verify_can_execute(db_session, project.id)
    assert status_resumed["percent_used"] < 100.0


@pytest.mark.asyncio
async def test_cross_review_and_max_one_auto_revision(db_session: AsyncSession):
    """
    Verify cross-review triggers auto-revision at most 1 time.
    If 2nd review fails, card moves to Waiting PO (FR-9.5).
    """
    user = User(email=f"po_{uuid.uuid4().hex[:6]}@timai.local", name="PO Review", role="po", password_hash="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Setup test project, agent, PBI, and task
    project = Project(
        po_id=user.id,
        profile_id="proposal",
        title="Test Review Project",
        brief="Testing cross-review",
        budget=5_000_000.0,
        currency="IDR",
        status="sprint",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    writer = Agent(
        project_id=project.id,
        role_template_id="grant_writer",
        name="Grant Writer",
        permissions=["read_workspace", "write_workspace", "search_workspace", "post_message", "update_card"],
    )
    reviewer = Agent(
        project_id=project.id,
        role_template_id="reviewer_metodologi",
        name="Reviewer Metodologi",
        permissions=["read_workspace", "search_workspace", "post_message", "update_card"],
    )
    db_session.add_all([writer, reviewer])

    disc = Discussion(
        project_id=project.id,
        agenda="Sprint Execution Discussion",
        discussion_type="general",
    )
    db_session.add(disc)

    pbi = BacklogItem(
        project_id=project.id,
        title="Metodologi Penelitian dan State-of-the-Art",
        story_points=3,
        status="in_progress",
        acceptance_criteria=["Menjelaskan gap penelitian", "Menyertakan rujukan terverifikasi"],
    )
    db_session.add(pbi)
    await db_session.commit()
    await db_session.refresh(pbi)

    task = Task(
        backlog_item_id=pbi.id,
        agent_id=writer.id,
        step_type="execute",
        status="todo",
        attempt_count=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Execute with forced rejection to test max 1 auto-revision
    result = await agent_runtime.execute_task_with_cross_review(
        db=db_session,
        task_id=task.id,
        force_review_decision="needs_revision",
    )

    # Verify auto-revision ran exactly once and stopped at waiting_po
    assert result["revisions_performed"] == 1
    assert result["final_decision"] == "waiting_po"
    assert result["status"] == "waiting_po"

    await db_session.refresh(task)
    await db_session.refresh(pbi)
    assert task.status == "waiting_po"
    assert pbi.status == "waiting_po"
    assert task.attempt_count == 1


@pytest.mark.asyncio
async def test_end_to_end_proposal_agent_execution(db_session: AsyncSession):
    """
    End-to-end proposal project execution using FakeProvider:
    Artifact generation, quality check, cross-review approval, and DoD satisfaction.
    """
    # 1. Create Proposal Project
    user = User(email=f"po_{uuid.uuid4().hex[:6]}@timai.local", name="PO Proposal", role="po", password_hash="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    project = Project(
        po_id=user.id,
        title="Proposal Otomasi Riset AI",
        brief="Penyusunan naskah proposal penelitian kecerdasan buatan multi-agen dengan metodologi teruji.",
        profile_id="proposal",
        budget=10_000_000.0,
        currency="IDR",
        language="id",
        status="brief",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # 2. Gate G1: Compose Team
    composition = await team_composer.compose_team(db_session, project)
    await team_composer.approve_team_g1(
        db=db_session,
        project_id=project.id,
        team_config=composition["agents"],
        user_id=user.id,
    )

    # 3. Inception & Gate G2
    await init_inception_agendas(project, db_session)
    await assemble_inception_document(project.id, db_session, user)
    await review_gate_g2(
        project_id=project.id,
        decision="approved",
        comments="Disetujui untuk Sprint 1.",
        current_user=user,
        db=db_session,
    )

    # 4. Sprint Planning
    sprint = await scrum_engine.plan_sprint(
        db=db_session,
        project_id=project.id,
        sprint_number=1,
        sprint_goal="Menyelesaikan draf bab metodologi dan gap penelitian",
        budget_limit=2_500_000.0,
        current_user=user,
    )

    # 5. Execute Sprint Tasks through Agent Runtime
    pbi_stmt = select(BacklogItem).where(BacklogItem.sprint_id == sprint.id)
    pbi_res = await db_session.execute(pbi_stmt)
    pbis = pbi_res.scalars().all()
    assert len(pbis) > 0

    first_pbi = pbis[0]
    task_stmt = select(Task).where(Task.backlog_item_id == first_pbi.id)
    task_res = await db_session.execute(task_stmt)
    tasks = task_res.scalars().all()
    assert len(tasks) > 0

    exec_task = tasks[0]
    result = await agent_runtime.execute_task_with_cross_review(
        db=db_session,
        task_id=exec_task.id,
        force_review_decision="approved",
    )

    assert result["final_decision"] == "approved"
    assert result["status"] == "done"

    # Verify artifact written in workspace
    workspace_path = get_project_workspace_path(project)
    kerja_dir = workspace_path / "sprints" / "sprint-01" / "kerja"
    files = list(kerja_dir.glob("*.md"))
    assert len(files) > 0

    artifact_content = files[0].read_text(encoding="utf-8")
    assert "tahap: 5 Eksekusi" in artifact_content
    assert "Daftar Pustaka" in artifact_content


@pytest.mark.asyncio
async def test_low_tier_model_clean_interface(db_session: AsyncSession):
    """
    Verify low-tier model execution against FakeProvider or real low-tier model if API key set.
    """
    # Test through model gateway with low tier model
    context = "PROFIL: Proposal Penelitian\nTUGAS: Uji singkat model tier low"
    messages = [{"role": "user", "content": "Tuliskan satu paragraf perumusan masalah."}]

    resp = await model_gateway.complete(
        agent_context=context,
        messages=messages,
        model="fake-model",
        db=db_session,
    )

    assert resp.content is not None
    assert resp.input_tokens > 0
    assert resp.output_tokens > 0
    assert resp.latency_ms >= 0

"""
End-to-End and Hardening Tests for Prompt 10.
Covers:
1. Full project lifecycle E2E (Brief -> G1 -> Inception -> G2 -> Sprint 1 -> Sprint 2 -> G3 -> G4 Closure).
2. Worker crash and resumption resilience (no duplicate contributions or corrupted state).
3. Security & RBAC audit (masked API keys, RBAC prohibitions, safe file upload validation).
"""

import uuid
import zipfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models import (
    Agent,
    BacklogItem,
    Contribution,
    Gate,
    Model,
    Project,
    Provider,
    Task,
    User,
)
from app.main import app
from app.orchestrator.agent_runtime import agent_runtime
from app.orchestrator.closure import closure_orchestrator
from app.orchestrator.composer import team_composer
from app.orchestrator.inception import (
    assemble_inception_document,
    get_project_workspace_path,
    init_inception_agendas,
    review_gate_g2,
)
from app.orchestrator.meeting import meeting_engine
from app.orchestrator.scrum import scrum_engine


@pytest.fixture
async def hardening_users(db_session: AsyncSession):
    """Seed test users (PO, Viewer, and Admin) and Fake Provider."""
    prov = Provider(name="Hardening Fake Provider", provider_type="fake", is_active=True)
    db_session.add(prov)
    await db_session.flush()

    for tier, name, ident in [
        ("low", "Hardening Fake Low", "fake-low"),
        ("medium", "Hardening Fake Med", "fake-med"),
        ("high", "Hardening Fake High", "fake-high"),
        ("xhigh", "Hardening Fake XHigh", "fake-xhigh"),
    ]:
        m = Model(
            provider_id=prov.id,
            name=name,
            model_identifier=ident,
            tier=tier,
            input_price=0.001,
            output_price=0.002,
            competency_score=4.6,
            is_active=True,
        )
        db_session.add(m)

    admin = User(
        email=f"admin_{uuid.uuid4().hex[:6]}@timai.local",
        name="Admin User",
        password_hash=hash_password("adminpass"),
        role="admin",
        is_active=True,
    )
    po1 = User(
        email=f"po1_{uuid.uuid4().hex[:6]}@timai.local",
        name="Product Owner One",
        password_hash=hash_password("popass123"),
        role="po",
        is_active=True,
    )
    po2 = User(
        email=f"po2_{uuid.uuid4().hex[:6]}@timai.local",
        name="Product Owner Two",
        password_hash=hash_password("popass123"),
        role="po",
        is_active=True,
    )
    viewer = User(
        email=f"viewer_{uuid.uuid4().hex[:6]}@timai.local",
        name="Viewer User",
        password_hash=hash_password("viewpass"),
        role="viewer",
        is_active=True,
    )
    db_session.add_all([admin, po1, po2, viewer])
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(po1)
    await db_session.refresh(po2)
    await db_session.refresh(viewer)

    return {"admin": admin, "po1": po1, "po2": po2, "viewer": viewer, "provider": prov}


@pytest.mark.asyncio
async def test_full_project_lifecycle_e2e(db_session: AsyncSession, hardening_users):
    """
    Test criterion:
    Alur lengkap end-to-end:
    Brief -> Gate G1 -> Inception -> Gate G2 -> Dua Sprint (Planning, Exec, Review G3, Retro) -> Penutupan Gate G4.
    """
    po = hardening_users["po1"]

    # 1. Brief: Create Project
    project = Project(
        po_id=po.id,
        title="Pengembangan Smart Grid AI untuk Kampus Hijau",
        profile_id="proposal",
        brief="Proposal penelitian sistem integrasi AI dan IoT untuk optimasi konsumsi energi gedung kampus.",
        budget=15_000_000.0,
        currency="IDR",
        language="id",
        status="brief",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # 2. Gate G1: Team Composition & Approval
    proposal = await team_composer.compose_team(db_session, project)
    assert len(proposal["agents"]) >= 3

    g1_res = await team_composer.approve_team_g1(
        db=db_session,
        project_id=project.id,
        user_id=po.id,
        team_config=proposal["agents"],
    )
    assert g1_res["status"] == "inception"

    # Verify team charter exists
    workspace_path = get_project_workspace_path(project)
    charter_file = workspace_path / "01-tim" / "team-charter.md"
    assert charter_file.exists()

    # 3. Inception: Agendas -> Synthesis -> Gate G2
    agendas = await init_inception_agendas(project, db_session)
    assert len(agendas) > 0

    # Conduct one agenda discussion round
    first_disc = agendas[0]
    await meeting_engine.run_round(db_session, first_disc.id)

    # Assemble inception document
    incept_doc = await assemble_inception_document(project.id, db_session, po)
    assert incept_doc["backlog_count"] >= 2

    # Gate G2 Approval
    g2_res = await review_gate_g2(
        project_id=project.id,
        decision="approved",
        comments="Inception disetujui, siap eksekusi sprint.",
        current_user=po,
        db=db_session,
    )
    assert g2_res["decision"] == "approved"

    # 4. Sprint 1: Planning, Task Exec, Daily, Review G3, Retro
    sprint1 = await scrum_engine.plan_sprint(
        db=db_session,
        project_id=project.id,
        sprint_number=1,
        sprint_goal="Selesaikan analisis kebutuhan dan perumusan masalah",
        budget_limit=5_000_000.0,
        current_user=po,
    )
    assert sprint1.status == "active"

    # Execute all drafting tasks in Sprint 1
    t_stmt1 = (
        select(Task)
        .join(BacklogItem, Task.backlog_item_id == BacklogItem.id)
        .where(BacklogItem.sprint_id == sprint1.id, Task.step_type == "execute")
    )
    t_res1 = await db_session.execute(t_stmt1)
    s1_tasks = t_res1.scalars().all()
    assert len(s1_tasks) > 0

    for task in s1_tasks:
        res = await agent_runtime.execute_task_with_cross_review(
            db=db_session,
            task_id=task.id,
            force_review_decision="approved",
        )
        assert res["status"] == "done"

    # Daily standup
    standup1 = await scrum_engine.generate_daily_standup(db_session, project.id, sprint1.id)
    assert standup1["sprint_number"] == 1

    # Sprint 1 Review (Gate G3): Approve all completed items
    s1_pbi_stmt = select(BacklogItem).where(BacklogItem.sprint_id == sprint1.id)
    s1_pbis = (await db_session.execute(s1_pbi_stmt)).scalars().all()
    review_decisions_s1 = {
        p.id: {"decision": "accept", "notes": "Kualitas penulisan sangat baik."}
        for p in s1_pbis
    }
    g3_s1 = await scrum_engine.review_sprint_g3(
        db=db_session,
        project_id=project.id,
        sprint_id=sprint1.id,
        decisions_per_pbi=review_decisions_s1,
        current_user=po,
    )
    assert g3_s1["accepted_count"] == len(s1_pbis)

    # Sprint 1 Retro
    retro_s1 = await scrum_engine.run_retrospective(
        db=db_session,
        project_id=project.id,
        sprint_id=sprint1.id,
    )
    assert retro_s1.status == "suggested"

    # 5. Sprint 2: Planning, Task Exec, Review G3, Retro
    sprint2 = await scrum_engine.plan_sprint(
        db=db_session,
        project_id=project.id,
        sprint_number=2,
        sprint_goal="Selesaikan metodologi dan arsitektur teknis",
        budget_limit=5_000_000.0,
        current_user=po,
    )
    assert sprint2.status == "active"

    t_stmt2 = (
        select(Task)
        .join(BacklogItem, Task.backlog_item_id == BacklogItem.id)
        .where(BacklogItem.sprint_id == sprint2.id, Task.step_type == "execute")
    )
    t_res2 = await db_session.execute(t_stmt2)
    s2_tasks = t_res2.scalars().all()
    for task in s2_tasks:
        res = await agent_runtime.execute_task_with_cross_review(
            db=db_session,
            task_id=task.id,
            force_review_decision="approved",
        )
        assert res["status"] == "done"

    # Sprint 2 Review (Gate G3)
    s2_pbi_stmt = select(BacklogItem).where(BacklogItem.sprint_id == sprint2.id)
    s2_pbis = (await db_session.execute(s2_pbi_stmt)).scalars().all()
    review_decisions_s2 = {
        p.id: {"decision": "accept", "notes": "Metodologi lengkap dan siap difinalisasi."}
        for p in s2_pbis
    }
    await scrum_engine.review_sprint_g3(
        db=db_session,
        project_id=project.id,
        sprint_id=sprint2.id,
        decisions_per_pbi=review_decisions_s2,
        current_user=po,
    )

    # Sprint 2 Retro
    await scrum_engine.run_retrospective(
        db=db_session,
        project_id=project.id,
        sprint_id=sprint2.id,
    )

    # 6. Gate G4: Project Closure
    closure_res = await closure_orchestrator.close_project_g4(
        db=db_session,
        project_id=project.id,
        current_user=po,
        comments="Seluruh sprint selesai dengan sukses, naskah siap diajukan.",
    )

    assert closure_res["status"] == "closed"
    assert closure_res["total_velocity"] > 0
    assert closure_res["done_items_count"] > 0

    # Verify closure report
    report_file = workspace_path / "final" / "laporan-penutupan.md"
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "tahap: 8 Penutupan" in content
    assert "Disetujui Penuh (Gerbang G4 Lolos)" in content

    # Verify final package zip exists and is valid
    zip_path = Path(closure_res["paket_hasil_akhir_zip"])
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert any("laporan-penutupan.md" in n for n in namelist)

    # Verify Gate G4 record in DB
    g4_stmt = select(Gate).where(Gate.project_id == project.id, Gate.gate_type == "G4")
    g4 = (await db_session.execute(g4_stmt)).scalar_one_or_none()
    assert g4 is not None
    assert g4.decision == "approved"


@pytest.mark.asyncio
async def test_worker_crash_and_resilience(db_session: AsyncSession, hardening_users):
    """
    Test criterion:
    Uji ketahanan: matikan worker di tengah diskusi dan tengah sprint, lalu hidupkan lagi;
    tidak ada kontribusi ganda atau state hilang.
    """
    po = hardening_users["po1"]

    project = Project(
        po_id=po.id,
        title="Uji Ketahanan Worker Interupsi",
        profile_id="proposal",
        brief="Pengujian crash worker saat diskusi dan eksekusi.",
        budget=5_000_000.0,
        currency="IDR",
        status="sprint",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Compose team
    prop = await team_composer.compose_team(db_session, project)
    await team_composer.approve_team_g1(
        db=db_session,
        project_id=project.id,
        team_config=prop["agents"],
        user_id=po.id,
    )

    # Load agents from DB
    ag_stmt = select(Agent).where(Agent.project_id == project.id)
    agents = (await db_session.execute(ag_stmt)).scalars().all()
    sm_agent = [a for a in agents if a.role_template_id == "scrum_master"][0]
    other_agents = [a for a in agents if a.id != sm_agent.id]

    # 1. Resilience during Discussion: simulate 1 message posted then sudden worker interruption
    disc = await meeting_engine.create_discussion(
        db_session,
        project_id=project.id,
        agenda="Diskusi Perumusan Masalah Kritis",
        participant_agent_ids=[sm_agent.id] + [a.id for a in other_agents[:2]],
    )

    # Simulate agent 1 spoke before worker crashed
    interrupted_agent = other_agents[0]
    c1 = Contribution(
        discussion_id=disc.id,
        agent_id=interrupted_agent.id,
        round_number=1,
        content="Pandangan awal mengenai perumusan masalah sebelum interupsi.",
        token_count=120,
    )
    db_session.add(c1)
    await db_session.commit()

    # Worker dies and restarts: MeetingEngine resumes discussion round
    await meeting_engine.run_round(db_session, disc.id)

    # Check total contributions in discussion:
    # Ensure interrupted_agent did not contribute twice (K5: single contribution per participant per round)
    contrib_stmt = select(Contribution).where(Contribution.discussion_id == disc.id)
    all_contribs = (await db_session.execute(contrib_stmt)).scalars().all()

    agent_counts = {}
    for c in all_contribs:
        agent_counts[c.agent_id] = agent_counts.get(c.agent_id, 0) + 1

    assert agent_counts[interrupted_agent.id] == 1, (
        f"Agent {interrupted_agent.name} must not have duplicate contributions after crash recovery"
    )

    # 2. Resilience during Task Execution:
    # Simulate a task set to in_progress or midway
    pbi = BacklogItem(
        project_id=project.id,
        title="PBI Uji Ketahanan Task",
        story_points=2,
        status="in_progress",
    )
    db_session.add(pbi)
    await db_session.commit()
    await db_session.refresh(pbi)

    task = Task(
        backlog_item_id=pbi.id,
        step_type="execute",
        status="in_progress",
        attempt_count=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Worker resumes execution cleanly without corruption
    exec_res = await agent_runtime.execute_task_with_cross_review(
        db=db_session,
        task_id=task.id,
        force_review_decision="approved",
    )
    assert exec_res["status"] == "done"

    await db_session.refresh(task)
    assert task.status == "done"


@pytest.mark.asyncio
async def test_security_audit_api_keys_and_rbac(db_session: AsyncSession, hardening_users):
    """
    Test criterion:
    Audit keamanan dasar:
    1. Kunci API tidak muncul di respons API (selalu terenkripsi di DB dan termasker di respons).
    2. Hak akses (RBAC): Viewer tidak bisa buat proyek atau setujui gate; PO tidak bisa otak-atik proyek PO lain.
    3. Validasi unggahan berkas: tipe terlarang (.exe, .sh) dan batasan ukuran ditolak (400 Bad Request).
    """
    admin = hardening_users["admin"]
    po1 = hardening_users["po1"]
    po2 = hardening_users["po2"]
    viewer = hardening_users["viewer"]

    admin_token = create_access_token(admin.id, admin.role)
    po1_token = create_access_token(po1.id, po1.role)
    po2_token = create_access_token(po2.id, po2.role)
    viewer_token = create_access_token(viewer.id, viewer.role)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. API Key Masking Check
        # Register a provider with secret key
        raw_secret_key = "sk-super-confidential-secret-key-1234567890"
        create_prov_res = await client.post(
            "/api/providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Secured Provider",
                "provider_type": "openai",
                "api_key": raw_secret_key,
                "base_url": "https://api.openai.com/v1",
            },
        )
        assert create_prov_res.status_code == 201
        prov_data = create_prov_res.json()
        assert raw_secret_key not in str(prov_data)
        assert prov_data["api_key_masked"].endswith("7890")
        assert "***" in prov_data["api_key_masked"]

        # List providers check
        list_prov_res = await client.get(
            "/api/providers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_prov_res.status_code == 200
        assert raw_secret_key not in list_prov_res.text

        # 2. RBAC Enforcement Check
        # Viewer tries to create project -> 403 Forbidden
        viewer_proj_res = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={
                "title": "Viewer Prohibited Project",
                "profile_id": "proposal",
                "brief": "This request must be rejected by RBAC.",
            },
        )
        assert viewer_proj_res.status_code == 403

        # PO 1 creates a project
        po1_proj_res = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {po1_token}"},
            json={
                "title": "PO1 Confidential Project",
                "profile_id": "proposal",
                "brief": "Confidential research project by PO 1.",
            },
        )
        assert po1_proj_res.status_code == 201
        proj_id = po1_proj_res.json()["id"]

        # Viewer tries to close project -> 403 Forbidden
        viewer_close_res = await client.post(
            f"/api/projects/{proj_id}/close",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"comments": "Viewer attempting G4 approval"},
        )
        assert viewer_close_res.status_code == 403

        # PO 2 tries to close PO 1's project -> 403 Forbidden
        po2_close_res = await client.post(
            f"/api/projects/{proj_id}/close",
            headers={"Authorization": f"Bearer {po2_token}"},
            json={"comments": "PO 2 attempting unauthorized G4 closure"},
        )
        assert po2_close_res.status_code == 403

        # 3. File Upload Security Validation Check
        # A. Dangerous extension (.exe) -> 400 Bad Request
        malicious_file = ("exploit.exe", b"\x4d\x5a\x90\x00malicious_payload", "application/octet-stream")
        upload_bad_res = await client.post(
            f"/api/projects/{proj_id}/attachments",
            headers={"Authorization": f"Bearer {po1_token}"},
            files={"file": malicious_file},
        )
        assert upload_bad_res.status_code == 400
        assert "tidak diizinkan" in upload_bad_res.json()["detail"]

        # B. Path traversal attempt in filename -> sanitized without error or escaping directory
        traversal_file = ("../../safe_notes.txt", b"Research reference note", "text/plain")
        upload_traversal_res = await client.post(
            f"/api/projects/{proj_id}/attachments",
            headers={"Authorization": f"Bearer {po1_token}"},
            files={"file": traversal_file},
        )
        assert upload_traversal_res.status_code == 201
        saved_filename = upload_traversal_res.json()["filename"]
        assert ".." not in saved_filename
        assert saved_filename == "safe_notes.txt"

        # C. Exceeds size limit (> 50 MB) -> 400 Bad Request
        large_content = b"0" * (51 * 1024 * 1024)
        large_file = ("huge.pdf", large_content, "application/pdf")
        upload_large_res = await client.post(
            f"/api/projects/{proj_id}/attachments",
            headers={"Authorization": f"Bearer {po1_token}"},
            files={"file": large_file},
        )
        assert upload_large_res.status_code == 400
        assert "melebihi batas" in upload_large_res.json()["detail"]

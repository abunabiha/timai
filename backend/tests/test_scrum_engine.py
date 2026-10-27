"""Comprehensive tests for Prompt 7: Scrum Engine, Sprints, Daily Standup, Review G3, Retro, Burndown and Velocity."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models import BacklogItem, Gate, Lesson, Model, Project, Provider, User
from app.main import app


@pytest.fixture
async def scrum_users(db_session: AsyncSession):
    prov = Provider(name="Fake Provider", provider_type="fake", is_active=True)
    db_session.add(prov)
    await db_session.flush()

    for tier, name, ident in [
        ("low", "Fake Low", "fake-low"),
        ("medium", "Fake Med", "fake-med"),
        ("high", "Fake High", "fake-high"),
        ("xhigh", "Fake XHigh", "fake-xhigh"),
    ]:
        m = Model(
            provider_id=prov.id,
            name=name,
            model_identifier=ident,
            tier=tier,
            input_price=0.001,
            output_price=0.002,
            competency_score=4.5,
            is_active=True,
        )
        db_session.add(m)

    po = User(
        email="po_scrum@example.com",
        name="Product Owner Scrum",
        password_hash=hash_password("password123"),
        role="po",
        is_active=True,
    )
    viewer = User(
        email="viewer_scrum@example.com",
        name="Viewer Scrum",
        password_hash=hash_password("password123"),
        role="viewer",
        is_active=True,
    )
    db_session.add_all([po, viewer])
    await db_session.commit()
    await db_session.refresh(po)
    await db_session.refresh(viewer)
    return {"po": po, "viewer": viewer}


@pytest.mark.asyncio
async def test_full_sprint_simulation_g3_rejection_and_burndown(db_session: AsyncSession, scrum_users):
    """
    Test criterion:
    1. Simulasi satu sprint penuh: Planning -> Eksekusi (palsu) -> Review -> Retro, dengan G3 menolak satu PBI dan PBI itu kembali ke backlog.
    2. Burndown dan velocity terhitung benar pada data simulasi.
    """
    po = scrum_users["po"]
    po_token = create_access_token(po.id, po.role)
    headers = {"Authorization": f"Bearer {po_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Proposal project, approve G1, and assemble Inception to get Product Backlog
        create_res = await client.post(
            "/api/projects",
            headers=headers,
            json={
                "title": "Proposal Riset Scrum AI",
                "profile_id": "proposal",
                "brief": "Menguji siklus penuh Scrum Engine dari planning hingga review.",
                "budget": 20000000.0,
                "currency": "IDR",
                "language": "id",
            },
        )
        assert create_res.status_code == 201
        project_id = create_res.json()["id"]

        compose_res = await client.post(f"/api/projects/{project_id}/compose-team?package=balanced", headers=headers)
        assert compose_res.status_code == 200
        team_data = compose_res.json()

        await client.post(
            f"/api/projects/{project_id}/approve-team",
            headers=headers,
            json={"agents": team_data["agents"], "clarification_notes": "Brief diverifikasi."},
        )

        await client.post(
            f"/api/inceptions/projects/{project_id}/assemble",
            headers=headers,
        )

        # 2. Get Backlog items
        backlog_res = await client.get(f"/api/inceptions/projects/{project_id}/backlog", headers=headers)
        assert backlog_res.status_code == 200
        epics = backlog_res.json()
        all_pbis = [it for ep in epics for it in ep["items"]]
        assert len(all_pbis) >= 2
        pbi_1 = all_pbis[0]
        pbi_2 = all_pbis[1]

        # 3. Sprint Planning (Sprint 1)
        plan_res = await client.post(
            f"/api/projects/{project_id}/sprints/plan",
            headers=headers,
            json={
                "sprint_number": 1,
                "sprint_goal": "Menyelesaikan kajian literatur awal dan kerangka metodologi.",
                "target_pbi_ids": [pbi_1["id"], pbi_2["id"]],
                "budget_limit": 5000000.0,
            },
        )
        assert plan_res.status_code == 200
        sprint_data = plan_res.json()
        sprint_id = sprint_data["id"]
        assert sprint_data["sprint_number"] == 1
        assert sprint_data["status"] == "active"

        # Verify sprint-plan.md in workspace
        p_res = await db_session.execute(select(Project).where(Project.id == project_id))
        project = p_res.scalar_one()
        sprint_dir = Path(project.workspace_path) / "sprints" / "sprint-01"
        assert (sprint_dir / "sprint-plan.md").exists()
        plan_md = (sprint_dir / "sprint-plan.md").read_text(encoding="utf-8")
        assert "dokumen: Sprint Plan" in plan_md
        assert "tahap: 4 Sprint Planning" in plan_md

        # 4. Daily Standup report
        daily_res = await client.post(f"/api/sprints/{sprint_id}/daily", headers=headers)
        assert daily_res.status_code == 200
        daily_data = daily_res.json()
        assert daily_data["sprint_number"] == 1
        assert (sprint_dir / "daily" / f"{daily_data['date']}.md").exists()

        # 5. Simulate task execution (FakeProvider)
        sim_res = await client.post(f"/api/sprints/{sprint_id}/simulate", headers=headers)
        assert sim_res.status_code == 200
        assert sim_res.json()["status"] == "review"

        # 6. Sprint Review (Gate G3): PO accepts PBI 1, but REJECTS PBI 2!
        review_payload = {
            "decisions": {
                pbi_1["id"]: {"decision": "accept", "notes": "Memenuhi seluruh kriteria DoD."},
                pbi_2["id"]: {"decision": "reject", "notes": "Rujukan kurang dari 15, metodologi belum replikatif."},
            }
        }
        review_res = await client.post(
            f"/api/sprints/{sprint_id}/review",
            headers=headers,
            json=review_payload,
        )
        assert review_res.status_code == 200
        review_data = review_res.json()
        assert review_data["accepted_count"] == 1
        assert review_data["rejected_count"] == 1
        # Velocity achieved must equal story points of accepted PBI 1
        assert review_data["velocity_achieved"] == pbi_1["story_points"]

        # Verify DB states:
        # PBI 1 must be 'done'
        pbi1_db = (await db_session.execute(select(BacklogItem).where(BacklogItem.id == pbi_1["id"]))).scalar_one()
        assert pbi1_db.status == "done"

        # PBI 2 must be returned to 'product_backlog'! (Kriteria Selesai)
        pbi2_db = (await db_session.execute(select(BacklogItem).where(BacklogItem.id == pbi_2["id"]))).scalar_one()
        assert pbi2_db.status == "product_backlog"
        assert pbi2_db.sprint_id is None

        # Verify Gate G3 recorded
        gate_db = (await db_session.execute(select(Gate).where(Gate.target_id == sprint_id, Gate.gate_type == "G3"))).scalar_one()
        assert gate_db.gate_type == "G3"

        # Verify review files in workspace
        assert (sprint_dir / "review.md").exists()
        assert (sprint_dir / "laporan-sprint.md").exists()

        # 7. Sprint Retrospective
        retro_res = await client.post(
            f"/api/sprints/{sprint_id}/retro",
            headers=headers,
            json={"action_item": "Libatkan Fact Checker lebih awal untuk memverifikasi rujukan sebelum draf selesai."},
        )
        assert retro_res.status_code == 200
        retro_data = retro_res.json()
        assert retro_data["status"] == "suggested"
        assert (sprint_dir / "retro.md").exists()

        # Verify Lesson recorded in DB
        lesson_db = (await db_session.execute(select(Lesson).where(Lesson.id == retro_data["lesson_id"]))).scalar_one()
        assert lesson_db.status == "suggested"
        assert lesson_db.layer == "retro"

        # 8. Burndown and Velocity Calculation check
        burndown_res = await client.get(f"/api/sprints/{sprint_id}/burndown", headers=headers)
        assert burndown_res.status_code == 200
        bd_data = burndown_res.json()
        assert bd_data["velocity_achieved"] == pbi_1["story_points"]
        assert bd_data["completed_points"] == pbi_1["story_points"]
        assert len(bd_data["burndown"]) == 8

        # 9. Kanban Board Verification
        kanban_res = await client.get(f"/api/projects/{project_id}/kanban", headers=headers)
        assert kanban_res.status_code == 200
        cols = kanban_res.json()["columns"]
        # PBI 1 must appear in 'done' column
        assert any(item["id"] == pbi_1["id"] for item in cols["done"])
        # PBI 2 must appear in 'product_backlog' column
        assert any(item["id"] == pbi_2["id"] for item in cols["product_backlog"])

"""Comprehensive tests for Prompt 6: Inception stage, Document Assembly, Backlog, and G2 Gate."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models import Gate, Model, Project, Provider, User
from app.main import app


@pytest.fixture
async def inception_users(db_session: AsyncSession):
    # Setup Provider & Models for TeamComposer & MeetingEngine
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

    # PO user
    po = User(
        email="po_inception@example.com",
        name="Product Owner Inception",
        password_hash=hash_password("password123"),
        role="po",
        is_active=True,
    )
    # Viewer user
    viewer = User(
        email="viewer_inception@example.com",
        name="Viewer Inception",
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
async def test_inception_flow_to_g2_and_workspace_outputs(db_session: AsyncSession, inception_users):
    """Test full Inception flow from project creation to G2 with FakeProvider and check all output files and PRD 5.2d metadata."""
    po = inception_users["po"]
    po_token = create_access_token(po.id, po.role)
    headers = {"Authorization": f"Bearer {po_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create a proposal project
        create_res = await client.post(
            "/api/projects",
            headers=headers,
            json={
                "title": "Proposal Riset IoT Pertanian",
                "profile_id": "proposal",
                "brief": "Mengajukan proposal hibah riset sensor tanah pintar berbasis IoT dan AI dengan kepatuhan panduan hibah Bima Kemdikbudristek.",
                "budget": 15000000.0,
                "currency": "IDR",
                "language": "id",
            },
        )
        assert create_res.status_code == 201
        project_id = create_res.json()["id"]

        # 2. Team Composer and G1 approval
        compose_res = await client.post(f"/api/projects/{project_id}/compose-team?package=balanced", headers=headers)
        assert compose_res.status_code == 200
        team_data = compose_res.json()
        agents = team_data["agents"]

        approve_res = await client.post(
            f"/api/projects/{project_id}/approve-team",
            json={"agents": agents, "clarification_notes": "Panduan resmi hibah Bima 2026 terverifikasi."},
            headers=headers,
        )
        assert approve_res.status_code == 200

        # 3. Initialize Inception agendas for proposal profile
        init_res = await client.post(
            f"/api/inceptions/projects/{project_id}/init",
            headers=headers,
        )
        assert init_res.status_code == 200
        # Proposal has 5 agendas
        assert init_res.json()["count"] == 5

        # Check status endpoint
        status_res = await client.get(
            f"/api/inceptions/projects/{project_id}/status",
            headers=headers,
        )
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert len(status_data["agendas"]) == 5
        assert status_data["profile_id"] == "proposal"

        # 4. Simulate running discussion on each agenda using FakeProvider
        for agenda_info in status_data["agendas"]:
            disc_id = agenda_info["discussion_id"]
            assert disc_id is not None

            # Execute discussion round via API
            start_res = await client.post(f"/api/discussions/{disc_id}/start", headers=headers)
            assert start_res.status_code == 200
            disc_data = start_res.json()
            assert disc_data["status"] == "waiting_po"
            assert len(disc_data["confirmations"]) >= 1

            # Record PO decision (selecting Option A)
            conf_id = disc_data["confirmations"][0]["id"]
            decide_res = await client.post(
                f"/api/confirmations/{conf_id}/decide",
                headers=headers,
                json={"action": "choose_option", "selected_option": "A", "po_notes": "Disetujui opsi A"},
            )
            assert decide_res.status_code == 200

        # Verify all agendas are now completed
        status_res2 = await client.get(
            f"/api/inceptions/projects/{project_id}/status",
            headers=headers,
        )
        assert status_res2.status_code == 200
        assert status_res2.json()["is_ready_for_assembly"] is True

        # 5. Assemble Inception Document
        assemble_res = await client.post(
            f"/api/inceptions/projects/{project_id}/assemble",
            headers=headers,
        )
        assert assemble_res.status_code == 200
        assemble_data = assemble_res.json()
        assert assemble_data["version"] >= 1
        assert assemble_data["backlog_count"] > 0
        assert len(assemble_data["files_generated"]) == 5

        # 6. Verify all files exist in workspace and contain PRD 5.2d metadata
        stmt = select(Project).where(Project.id == project_id)
        p_res = await db_session.execute(stmt)
        project = p_res.scalar_one()

        workspace_dir = Path(project.workspace_path) / "02-inception"
        assert workspace_dir.exists()

        expected_files = [
            "dokumen-inception.md",
            "product-backlog.json",
            "dod.md",
            "rencana-rilis.md",
            "risiko.md",
        ]
        for fname in expected_files:
            target_path = workspace_dir / fname
            assert target_path.exists(), f"File {fname} harus ada di {workspace_dir}"

            if fname.endswith(".md"):
                content = target_path.read_text(encoding="utf-8")
                # Check PRD 5.2d YAML frontmatter keys
                assert "proyek: Proposal Riset IoT Pertanian" in content
                assert "tahap: 3 Inception" in content
                assert "dokumen:" in content
                assert "versi:" in content
                assert "dibuat_oleh:" in content
                assert "status:" in content

        # 7. Decide Gate G2: PO Approves
        g2_res = await client.post(
            f"/api/inceptions/projects/{project_id}/g2",
            headers=headers,
            json={"decision": "approved", "comments": "Dokumen rencana dan backlog disetujui penuh."},
        )
        assert g2_res.status_code == 200
        g2_data = g2_res.json()
        assert g2_data["gate"] == "G2"
        assert g2_data["decision"] == "approved"

        # Verify gate in DB
        gate_stmt = select(Gate).where(Gate.project_id == project_id, Gate.gate_type == "G2")
        g_res = await db_session.execute(gate_stmt)
        gate_db = g_res.scalar_one()
        assert gate_db.decision == "approved"

        # Verify updated metadata in dokumen-inception.md
        doc_content = (workspace_dir / "dokumen-inception.md").read_text(encoding="utf-8")
        assert "status: disetujui" in doc_content
        assert f"disetujui_oleh: {po.name}" in doc_content

        # 8. Export DOCX and PDF
        docx_res = await client.get(
            f"/api/inceptions/projects/{project_id}/export/docx",
            headers=headers,
        )
        assert docx_res.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in docx_res.headers["content-type"]
        assert len(docx_res.content) > 1000

        pdf_res = await client.get(
            f"/api/inceptions/projects/{project_id}/export/pdf",
            headers=headers,
        )
        assert pdf_res.status_code == 200
        assert "application/pdf" in pdf_res.headers["content-type"]
        assert len(pdf_res.content) > 1000


@pytest.mark.asyncio
async def test_reordering_backlog_restricted_to_po(db_session: AsyncSession, inception_users):
    """Test criterion: Mengubah urutan Product Backlog HANYA bisa dilakukan PO."""
    po = inception_users["po"]
    viewer = inception_users["viewer"]

    po_token = create_access_token(po.id, po.role)
    viewer_token = create_access_token(viewer.id, viewer.role)

    po_headers = {"Authorization": f"Bearer {po_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create project and assemble inception to get backlog
        create_res = await client.post(
            "/api/projects",
            headers=po_headers,
            json={
                "title": "Proyek Uji Urutan Backlog",
                "profile_id": "software",
                "brief": "Mengembangkan aplikasi manajemen inventaris berbasis web dan REST API.",
                "budget": 10000000.0,
                "currency": "IDR",
                "language": "id",
            },
        )
        assert create_res.status_code == 201
        project_id = create_res.json()["id"]

        compose_res = await client.post(f"/api/projects/{project_id}/compose-team?package=balanced", headers=po_headers)
        assert compose_res.status_code == 200
        team_data = compose_res.json()

        await client.post(
            f"/api/projects/{project_id}/approve-team",
            headers=po_headers,
            json={"agents": team_data["agents"], "clarification_notes": "Brief jelas."},
        )

        await client.post(
            f"/api/inceptions/projects/{project_id}/assemble",
            headers=po_headers,
        )

        # Get backlog items
        backlog_res = await client.get(
            f"/api/inceptions/projects/{project_id}/backlog",
            headers=po_headers,
        )
        assert backlog_res.status_code == 200
        epics = backlog_res.json()
        assert len(epics) > 0
        all_item_ids = [it["id"] for ep in epics for it in ep["items"]]
        assert len(all_item_ids) >= 2

        # Reverse order
        reversed_order = list(reversed(all_item_ids))

        # Attempt 1: Viewer tries to reorder backlog -> MUST RETURN 403 Forbidden!
        viewer_reorder_res = await client.post(
            f"/api/inceptions/projects/{project_id}/backlog/reorder",
            headers=viewer_headers,
            json={"ordered_item_ids": reversed_order},
        )
        assert viewer_reorder_res.status_code == 403
        assert "Hanya Product Owner (PO)" in viewer_reorder_res.json()["detail"]

        # Attempt 2: PO reorders backlog -> MUST SUCCEED (200 OK)
        po_reorder_res = await client.post(
            f"/api/inceptions/projects/{project_id}/backlog/reorder",
            headers=po_headers,
            json={"ordered_item_ids": reversed_order},
        )
        assert po_reorder_res.status_code == 200
        updated_items = po_reorder_res.json()
        assert updated_items[0]["id"] == reversed_order[0]
        assert updated_items[0]["po_sort_order"] == 0

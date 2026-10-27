import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Agent, Contribution, Model, Project, Provider
from app.gateway.fake import FakeProviderAdapter
from app.gateway.gateway import model_gateway
from app.main import app
from app.orchestrator.meeting import meeting_engine


@pytest.fixture
def fake_gateway_adapter():
    adapter = FakeProviderAdapter()
    adapter.register_response("Agenda Diskusi", "Kontribusi agen: Saya sepakat dengan arah awal namun menyarankan verifikasi empiris.")
    model_gateway.register_adapter("fake", adapter)
    return adapter


@pytest.mark.asyncio
async def test_single_round_and_no_duplicate_contributions(db_session: AsyncSession, fake_gateway_adapter):
    """
    Test:
    1. One single round: each participant speaks exactly once.
    2. Synthesis is generated and discussion enters waiting_po.
    3. Resuming/restarting mid-discussion does not duplicate contributions.
    """
    # Create project and 3 agents
    provider = Provider(name="Fake Provider", provider_type="fake", is_active=True)
    db_session.add(provider)
    await db_session.flush()

    model = Model(provider_id=provider.id, name="Fake Model", model_identifier="fake-1", tier="medium", is_active=True)
    db_session.add(model)
    await db_session.flush()

    project = Project(
        po_id="test-po",
        title="Uji Meeting Satu Putaran",
        profile_id="proposal",
        brief="Pengembangan sistem deteksi.",
        status="inception",
    )
    db_session.add(project)
    await db_session.flush()

    sm = Agent(project_id=project.id, role_template_id="scrum_master", name="Scrum Master", model_id=model.id)
    lead = Agent(project_id=project.id, role_template_id="research_lead", name="Research Lead", model_id=model.id)
    rev = Agent(project_id=project.id, role_template_id="reviewer_metodologi", name="Reviewer Metodologi", model_id=model.id)
    db_session.add_all([sm, lead, rev])
    await db_session.commit()

    # Create discussion
    disc = await meeting_engine.create_discussion(
        db_session,
        project_id=project.id,
        agenda="Perumusan Gap Penelitian dan Novelty",
        participant_agent_ids=[sm.id, lead.id, rev.id],
    )
    assert disc.status == "draft"
    assert disc.round_number == 1

    # Execute round
    disc = await meeting_engine.run_round(db_session, disc.id)
    assert disc.status == "waiting_po"
    assert disc.synthesis is not None
    assert "proposed_decision" in disc.synthesis

    # Verify contributions: speakers were lead and rev (SM synthesizes)
    contrib_res = await db_session.execute(
        select(Contribution).where(Contribution.discussion_id == disc.id)
    )
    contribs = contrib_res.scalars().all()
    assert len(contribs) == len(disc.speaker_order)
    # Exactly one contribution per participant in this round
    agent_counts = {}
    for c in contribs:
        agent_counts[c.agent_id] = agent_counts.get(c.agent_id, 0) + 1
    for count in agent_counts.values():
        assert count == 1

    # Simulate restart worker: calling run_round again on waiting_po does not run or duplicate
    disc_after = await meeting_engine.run_round(db_session, disc.id)
    assert disc_after.status == "waiting_po"
    contrib_res2 = await db_session.execute(
        select(Contribution).where(Contribution.discussion_id == disc.id)
    )
    assert len(contrib_res2.scalars().all()) == len(contribs)


@pytest.mark.asyncio
async def test_token_ceiling_halts_round(db_session: AsyncSession, fake_gateway_adapter):
    """Test that round token ceiling stops further contributions cleanly."""
    provider = Provider(name="Fake Prov Ceiling", provider_type="fake", is_active=True)
    db_session.add(provider)
    await db_session.flush()

    model = Model(provider_id=provider.id, name="Fake Model", model_identifier="fake-1", tier="medium", is_active=True)
    db_session.add(model)
    await db_session.flush()

    project = Project(po_id="test-po", title="Uji Plafon Token", profile_id="proposal", brief="B", status="inception")
    db_session.add(project)
    await db_session.flush()

    ag1 = Agent(project_id=project.id, role_template_id="a1", name="Agent 1", model_id=model.id)
    ag2 = Agent(project_id=project.id, role_template_id="a2", name="Agent 2", model_id=model.id)
    ag3 = Agent(project_id=project.id, role_template_id="a3", name="Agent 3", model_id=model.id)
    db_session.add_all([ag1, ag2, ag3])
    await db_session.commit()

    disc = await meeting_engine.create_discussion(
        db_session,
        project_id=project.id,
        agenda="Plafon Token Test",
        participant_agent_ids=[ag1.id, ag2.id, ag3.id],
    )

    # Set very small ceiling: stops after first speaker
    disc = await meeting_engine.run_round(db_session, disc.id, token_ceiling=15)
    contrib_res = await db_session.execute(
        select(Contribution).where(Contribution.discussion_id == disc.id)
    )
    contribs = contrib_res.scalars().all()
    # At least 1 spoke, but ceiling prevented all from speaking
    assert len(contribs) < len(disc.speaker_order)
    assert disc.status == "waiting_po"


@pytest.mark.asyncio
async def test_demo_meeting_flow_po_selects_option_b(db_session: AsyncSession, fake_gateway_adapter, tmp_path):
    """
    Demo requirement:
    Discussion with 3 fake agents -> synthesis -> PO selects Option B -> decision enters Decision Log & notulen written.
    """
    workspace_dir = str(tmp_path / "workspace_demo")
    os.makedirs(os.path.join(workspace_dir, "02-inception", "notulen"), exist_ok=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Setup admin
        admin_res = await client.post(
            "/api/auth/setup-admin",
            json={"name": "PO Demo", "email": "podemo@example.com", "password": "Password123!"},
        )
        assert admin_res.status_code == 200
        token = admin_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create project in DB
        project = Project(
            po_id=admin_res.json()["user"]["id"],
            title="Proyek Manuskrip ESP32",
            profile_id="jurnal",
            brief="Deteksi bau TPS berbasis ESP32 dan K-Means.",
            status="inception",
            workspace_path=workspace_dir,
        )
        db_session.add(project)
        await db_session.flush()

        prov = Provider(name="Fake", provider_type="fake", is_active=True)
        db_session.add(prov)
        await db_session.flush()
        mod = Model(provider_id=prov.id, name="Fake Mod", model_identifier="fake-1", tier="medium", is_active=True)
        db_session.add(mod)
        await db_session.flush()

        # 3 Agents: Scrum Master, Research Lead, Journal-Fit Reviewer
        sm = Agent(project_id=project.id, role_template_id="scrum_master", name="Scrum Master", model_id=mod.id)
        lead = Agent(project_id=project.id, role_template_id="research_lead", name="Research Lead", model_id=mod.id)
        rev = Agent(project_id=project.id, role_template_id="journal_reviewer", name="Journal-Fit Reviewer", model_id=mod.id)
        db_session.add_all([sm, lead, rev])
        await db_session.commit()

        # 1. Create Discussion via API
        create_disc = await client.post(
            "/api/discussions",
            json={
                "project_id": project.id,
                "agenda": "Kontribusi dan Target Jurnal",
                "discussion_type": "inception",
                "participants": [sm.id, lead.id, rev.id],
            },
            headers=headers,
        )
        assert create_disc.status_code == 201
        disc_id = create_disc.json()["id"]

        # 2. Run one round via API
        start_res = await client.post(f"/api/discussions/{disc_id}/start", headers=headers)
        assert start_res.status_code == 200
        disc_data = start_res.json()
        assert disc_data["status"] == "waiting_po"
        assert len(disc_data["confirmations"]) == 1
        conf_id = disc_data["confirmations"][0]["id"]
        assert len(disc_data["confirmations"][0]["options"]) >= 2

        # 3. Check Kotak Konfirmasi (Pending confirmations endpoint)
        conf_box = await client.get("/api/confirmations", headers=headers)
        assert conf_box.status_code == 200
        assert any(c["id"] == conf_id for c in conf_box.json())

        # 4. PO selects Option B
        decide_res = await client.post(
            f"/api/confirmations/{conf_id}/decide",
            json={
                "action": "choose_option",
                "selected_option": "B",
                "po_notes": "Fokus pada jurnal sensor dan instrumentasi untuk menjamin rigor validasi.",
            },
            headers=headers,
        )
        assert decide_res.status_code == 200
        assert decide_res.json()["status"] == "finished"

        # 5. Verify Decision Log in DB
        dec_res = await client.get(f"/api/confirmations/projects/{project.id}/decisions", headers=headers)
        assert dec_res.status_code == 200
        decisions = dec_res.json()
        assert len(decisions) >= 1
        assert "sensor" in decisions[0]["rationale"].lower() or "b" in decisions[0]["summary"].lower()

        # 6. Verify decision-log.md and notulen file written to workspace
        dec_log_file = os.path.join(workspace_dir, "02-inception", "decision-log.md")
        assert os.path.exists(dec_log_file)
        with open(dec_log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
        assert "Kontribusi dan Target Jurnal" in log_content
        assert "Konfirmasi B" in log_content

        # Verify notulen
        notulen_dir = os.path.join(workspace_dir, "02-inception", "notulen")
        files = os.listdir(notulen_dir)
        assert len(files) >= 1
        notulen_file = os.path.join(notulen_dir, files[0])
        with open(notulen_file, "r", encoding="utf-8") as f:
            notulen_content = f.read()
        assert "dokumen: Notulen Diskusi" in notulen_content
        assert "status: disetujui" in notulen_content

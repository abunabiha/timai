import io
import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Agent, Gate
from app.main import app
from app.orchestrator.extractor import extract_text_from_file


def test_file_extractor():
    # Test CSV extraction
    csv_bytes = b"title,author,year\nDeep Learning,Goodfellow,2016\nAttention,Vaswani,2017"
    text, summary = extract_text_from_file("papers.csv", csv_bytes)
    assert "Headers: title, author, year" in text
    assert "papers.csv" in summary

    # Test BibTeX extraction
    bib_bytes = b"@article{vaswani2017attention, title={Attention is all you need}, author={Vaswani, Ashish}, year={2017}}"
    text, summary = extract_text_from_file("ref.bib", bib_bytes)
    assert "vaswani2017attention" in text
    assert "ref.bib" in summary


@pytest.mark.asyncio
async def test_team_composer_flow_proposal_to_g1(db_session: AsyncSession):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup admin and PO
        admin_res = await client.post(
            "/api/auth/setup-admin",
            json={"name": "Admin TimAI", "email": "admin@example.com", "password": "AdminPassword123!"},
        )
        assert admin_res.status_code == 200
        admin_token = admin_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Admin adds fake provider & active models for each tier
        prov_res = await client.post(
            "/api/providers",
            json={"name": "Fake Provider", "provider_type": "fake", "api_key": "fake-key"},
            headers=admin_headers,
        )
        prov_id = prov_res.json()["id"]

        for tier, name, ident in [
            ("low", "Fake Low", "fake-low"),
            ("medium", "Fake Med", "fake-med"),
            ("high", "Fake High", "fake-high"),
            ("xhigh", "Fake XHigh", "fake-xhigh"),
        ]:
            await client.post(
                "/api/models",
                json={
                    "provider_id": prov_id,
                    "name": name,
                    "model_identifier": ident,
                    "tier": tier,
                    "input_price": 0.001,
                    "output_price": 0.002,
                    "competency_score": 4.5,
                },
                headers=admin_headers,
            )

        # 3. PO creates a Proposal project
        create_proj_res = await client.post(
            "/api/projects",
            json={
                "title": "Proposal Hibah AI untuk Deteksi Hama",
                "profile_id": "proposal",
                "brief": "Mengembangkan sistem computer vision deteksi hama berbasis deep learning dengan pengujian akurasi statistik dan kepatuhan panduan hibah Bima Kemdikbudristek.",
                "budget": 50_000_000.0,
                "currency": "IDR",
                "profile_fields": {"scheme": "Fundamental", "tkt_target": 4},
            },
            headers=admin_headers,
        )
        assert create_proj_res.status_code == 201
        proj_data = create_proj_res.json()
        proj_id = proj_data["id"]

        # 4. Upload Attachment
        csv_content = b"col1,col2\nval1,val2"
        files = {"file": ("dataset_preview.csv", io.BytesIO(csv_content), "text/csv")}
        att_res = await client.post(f"/api/projects/{proj_id}/attachments", files=files, headers=admin_headers)
        assert att_res.status_code == 201
        assert "dataset_preview.csv" in att_res.json()["filename"]

        # 5. Clarification Interview
        clarify_res = await client.post(f"/api/projects/{proj_id}/clarify", headers=admin_headers)
        assert clarify_res.status_code == 200
        questions = clarify_res.json()
        assert 1 <= len(questions) <= 7

        # PO submits answers
        ans_payload = {
            "answers": [
                {"id": questions[0]["id"], "question": questions[0]["question"], "answer": "Skema Penelitian Fundamental Reguler, durasi 1 tahun."},
            ]
        }
        ans_res = await client.post(f"/api/projects/{proj_id}/clarify/answers", json=ans_payload, headers=admin_headers)
        assert ans_res.status_code == 200

        # 6. Team Composer: Generate proposal
        compose_res = await client.post(f"/api/projects/{proj_id}/compose-team?package=balanced", headers=admin_headers)
        assert compose_res.status_code == 200
        team_data = compose_res.json()

        agents = team_data["agents"]
        assert len(agents) >= 5
        # Must have a reviewer in Proposal (Reviewer Metodologi or Fact Checker)
        assert team_data["has_reviewer"] is True
        assert any(a["is_reviewer"] is True for a in agents)
        # Cost range must be present
        cost_range = team_data["cost_range"]
        assert cost_range["min_idr"] > 0
        assert cost_range["max_idr"] >= cost_range["min_idr"]

        # 7. Dynamic Recalculation: change tier of first agent to xhigh
        agents_modified = list(agents)
        agents_modified[0]["tier"] = "xhigh"
        recalc_res = await client.post(
            f"/api/projects/{proj_id}/recalculate-estimate",
            json={"agents": agents_modified, "size": team_data["brief_analysis"]["size"]},
            headers=admin_headers,
        )
        assert recalc_res.status_code == 200
        new_cost = recalc_res.json()["cost_range"]
        # Upgrading tier increases maximum cost
        assert new_cost["max_usd"] > cost_range["min_usd"]

        # 8. Approve Team (G1)
        approve_res = await client.post(
            f"/api/projects/{proj_id}/approve-team",
            json={"agents": agents, "clarification_notes": "Panduan resmi Bima 2026 terverifikasi."},
            headers=admin_headers,
        )
        assert approve_res.status_code == 200
        appr_data = approve_res.json()
        assert appr_data["status"] == "inception"
        assert appr_data["agent_count"] == len(agents)

        # 9. Verify DB records created
        # Check Gate
        gate_res = await db_session.execute(select(Gate).where(Gate.project_id == proj_id, Gate.gate_type == "G1"))
        gate = gate_res.scalar_one_or_none()
        assert gate is not None
        assert gate.decision == "approved"

        # Check Agents in DB
        db_agents_res = await db_session.execute(select(Agent).where(Agent.project_id == proj_id))
        db_agents = db_agents_res.scalars().all()
        assert len(db_agents) == len(agents)

        # 10. Verify workspace directory and team-charter.md on disk
        charter_file = appr_data["team_charter_file"]
        assert os.path.exists(charter_file)
        with open(charter_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify PRD 5.2d metadata
        assert "tahap: 2 Usulan Tim" in content
        assert "dokumen: Team Charter" in content
        assert "status: disetujui" in content
        assert "Scrum Master" in content

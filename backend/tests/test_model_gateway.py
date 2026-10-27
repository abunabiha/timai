import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_secret, encrypt_secret, mask_secret
from app.db.models import Model, Provider, UsageRecord
from app.gateway.fake import FakeProviderAdapter
from app.gateway.gateway import ModelGateway
from app.main import app


@pytest.mark.asyncio
async def test_crypto_encryption_and_masking():
    secret = "sk-proj-supersecretkey1234567890abcdef"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert len(encrypted) > 20

    decrypted = decrypt_secret(encrypted)
    assert decrypted == secret

    masked = mask_secret(secret)
    assert masked.startswith("sk-")
    assert masked.endswith("cdef")
    assert "supersecretkey" not in masked


@pytest.mark.asyncio
async def test_model_gateway_complete_records_usage(db_session: AsyncSession):
    fake_adapter = FakeProviderAdapter()
    fake_adapter.register_response("ping", "pong fake reply", prompt_tokens=15, completion_tokens=8)

    gateway = ModelGateway()
    gateway.register_adapter("fake", fake_adapter)

    # Create Provider and Model in DB
    provider = Provider(
        name="Fake Provider",
        provider_type="fake",
        api_key_encrypted=encrypt_secret("test-key"),
        is_active=True,
    )
    db_session.add(provider)
    await db_session.flush()

    model = Model(
        provider_id=provider.id,
        name="Fake Fast 1.0",
        model_identifier="fake-fast-1",
        tier="low",
        input_price=0.001,
        output_price=0.002,
        competency_score=3.5,
        is_active=True,
    )
    db_session.add(model)
    await db_session.commit()

    resp = await gateway.complete(
        agent_context="Research Agent - Test",
        messages=[{"role": "user", "content": "ping"}],
        model=model,
        db=db_session,
    )
    assert resp.content == "pong fake reply"
    assert resp.requested_model == "fake-fast-1"
    assert resp.actual_model == "fake-fast-1"
    assert resp.input_tokens == 15
    assert resp.output_tokens == 8
    assert resp.cost > 0

    # Verify UsageRecord created in DB
    result = await db_session.execute(
        select(UsageRecord).where(UsageRecord.requested_model == "fake-fast-1")
    )
    records = result.scalars().all()
    assert len(records) == 1
    rec = records[0]
    assert rec.requested_model == "fake-fast-1"
    assert rec.actual_model == "fake-fast-1"
    assert rec.input_tokens == 15
    assert rec.output_tokens == 8
    assert rec.cost == resp.cost


@pytest.mark.asyncio
async def test_model_gateway_model_mismatch_warning(db_session: AsyncSession):
    fake_adapter = FakeProviderAdapter()
    fake_adapter.set_actual_model_override("fake-fast-actual-v2")
    fake_adapter.register_response("hello", "world")

    gateway = ModelGateway()
    gateway.register_adapter("fake", fake_adapter)

    provider = Provider(
        name="Fake Provider Mismatch",
        provider_type="fake",
        api_key_encrypted=encrypt_secret("test-key"),
        is_active=True,
    )
    db_session.add(provider)
    await db_session.flush()

    model = Model(
        provider_id=provider.id,
        name="Fake Mismatch Model",
        model_identifier="fake-requested-v1",
        tier="medium",
        is_active=True,
    )
    db_session.add(model)
    await db_session.commit()

    resp = await gateway.complete(
        agent_context="Mismatch Test",
        messages=[{"role": "user", "content": "hello"}],
        model=model,
        db=db_session,
    )
    assert resp.content == "world"
    assert resp.requested_model == "fake-requested-v1"
    assert resp.actual_model == "fake-fast-actual-v2"
    assert resp.warning is not None
    assert "mismatch" in resp.warning.lower()


@pytest.mark.asyncio
async def test_model_gateway_fallback_to_higher_or_equal_tier(db_session: AsyncSession):
    fake_adapter = FakeProviderAdapter()
    fake_adapter.set_should_fail(True, "Primary model is down")

    working_adapter = FakeProviderAdapter()
    working_adapter.register_response("compute", "fallback computed successfully")

    gateway = ModelGateway()
    gateway.register_adapter("fake_down", fake_adapter)
    gateway.register_adapter("fake_working", working_adapter)

    prov1 = Provider(name="Down Provider", provider_type="fake_down", is_active=True)
    prov2 = Provider(name="Working Provider", provider_type="fake_working", is_active=True)
    db_session.add_all([prov1, prov2])
    await db_session.flush()

    # Primary model (medium tier)
    primary = Model(
        provider_id=prov1.id,
        name="Primary Medium",
        model_identifier="primary-medium",
        tier="medium",
        is_active=True,
    )
    # Lower tier model (low) -> should NOT be used as fallback
    lower = Model(
        provider_id=prov2.id,
        name="Lower Tier",
        model_identifier="lower-tier",
        tier="low",
        is_active=True,
    )
    # Higher tier model (high) -> valid fallback
    higher = Model(
        provider_id=prov2.id,
        name="Higher Tier",
        model_identifier="higher-tier",
        tier="high",
        is_active=True,
    )
    db_session.add_all([primary, lower, higher])
    await db_session.commit()

    resp = await gateway.complete(
        agent_context="Fallback Test",
        messages=[{"role": "user", "content": "compute"}],
        model=primary,
        fallback_model=higher,
        db=db_session,
    )
    assert resp.content == "fallback computed successfully"
    assert resp.requested_model == "primary-medium"
    assert resp.actual_model == "higher-tier"
    assert resp.is_fallback is True
    assert resp.warning is not None
    assert "fallback" in resp.warning.lower()

    # Verify usage record in DB recorded fallback
    result = await db_session.execute(
        select(UsageRecord).where(UsageRecord.requested_model == "primary-medium")
    )
    records = result.scalars().all()
    assert len(records) == 1
    assert records[0].actual_model == "higher-tier"


@pytest.mark.asyncio
async def test_provider_and_model_api_crud_and_rbac(db_session: AsyncSession):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Setup admin
        admin_res = await client.post(
            "/api/auth/setup-admin",
            json={
                "name": "Super Admin",
                "email": "superadmin@example.com",
                "password": "AdminPassword123!",
            },
        )
        assert admin_res.status_code == 200
        admin_token = admin_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. Admin creates provider with secret API key
        prov_payload = {
            "name": "OpenAI Production",
            "provider_type": "openai",
            "api_key": "sk-proj-1234567890abcdefabcdef1234567890",
            "base_url": "https://api.openai.com/v1",
        }
        create_prov = await client.post("/api/providers", json=prov_payload, headers=admin_headers)
        assert create_prov.status_code == 201
        prov_data = create_prov.json()
        prov_id = prov_data["id"]
        # Assert key is masked and not exposed in full
        assert "sk-proj-1234567890abcdefabcdef1234567890" not in str(prov_data)
        assert prov_data["has_api_key"] is True
        assert prov_data["api_key_masked"].endswith("7890")

        # 2. Admin lists providers
        list_prov = await client.get("/api/providers", headers=admin_headers)
        assert list_prov.status_code == 200
        assert any(p["id"] == prov_id for p in list_prov.json())

        # 3. Create a fake provider for connection test
        fake_prov_res = await client.post(
            "/api/providers",
            json={"name": "Test Fake Provider", "provider_type": "fake", "api_key": "fake-secret"},
            headers=admin_headers,
        )
        fake_prov_id = fake_prov_res.json()["id"]

        test_conn = await client.post(f"/api/providers/{fake_prov_id}/test", headers=admin_headers)
        assert test_conn.status_code == 200
        assert test_conn.json()["success"] is True

        # 4. Admin creates a Model
        model_payload = {
            "provider_id": fake_prov_id,
            "name": "Fake Fast GPT",
            "model_identifier": "fake-gpt-fast",
            "context_window": 128000,
            "input_price": 0.0015,
            "output_price": 0.003,
            "supports_tools": True,
            "supports_vision": False,
            "competency_score": 4.2,
            "tier": "medium",
        }
        create_model = await client.post("/api/models", json=model_payload, headers=admin_headers)
        assert create_model.status_code == 201
        model_id = create_model.json()["id"]

        # 5. List models
        models_list = await client.get("/api/models", headers=admin_headers)
        assert models_list.status_code == 200
        assert any(m["id"] == model_id for m in models_list.json())

        # 6. Update model
        update_res = await client.put(
            f"/api/models/{model_id}",
            json={"tier": "high", "competency_score": 4.8},
            headers=admin_headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["tier"] == "high"
        assert update_res.json()["competency_score"] == 4.8

        # 7. Model health check
        hc_res = await client.post(f"/api/models/{model_id}/health-check", headers=admin_headers)
        assert hc_res.status_code == 200
        assert hc_res.json()["is_healthy"] is True

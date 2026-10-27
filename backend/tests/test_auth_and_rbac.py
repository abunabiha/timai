from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.db.models import Base, ProjectProfile, User
from app.db.session import get_db
from app.main import app

# Test database setup with SQLite in-memory
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test and seed initial profiles."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed the 5 profiles
    async with TestSessionLocal() as session:
        now = datetime.now(timezone.utc)
        profiles = [
            ProjectProfile(id="software", name="Software", description="Software dev", created_at=now, updated_at=now),
            ProjectProfile(id="iot", name="IoT", description="IoT systems", created_at=now, updated_at=now),
            ProjectProfile(id="proposal", name="Proposal Penelitian", description="Research proposal", created_at=now, updated_at=now),
            ProjectProfile(id="jurnal", name="Artikel Jurnal", description="Journal article", created_at=now, updated_at=now),
            ProjectProfile(id="buku", name="Buku", description="Book chapter", created_at=now, updated_at=now),
        ]
        session.add_all(profiles)
        await session.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_wizard_and_login() -> None:
    """Test initial admin wizard and subsequent login."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup status should be false initially
        res = await client.get("/api/auth/setup-status")
        assert res.status_code == 200
        assert res.json()["is_setup"] is False

        # 2. Setup initial admin
        admin_payload = {
            "name": "Super Admin",
            "email": "admin@example.com",
            "password": "Password123!",
        }
        res = await client.post("/api/auth/setup-admin", json=admin_payload)
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"

        # 3. Subsequent setup-admin attempt must be rejected
        res2 = await client.post("/api/auth/setup-admin", json=admin_payload)
        assert res2.status_code == 400

        # 4. Login with correct password
        login_res = await client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": "Password123!",
        })
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()

        # 5. Login with invalid password
        bad_login = await client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": "wrongpassword",
        })
        assert bad_login.status_code == 401


@pytest.mark.asyncio
async def test_rbac_and_project_isolation() -> None:
    """
    Test Role-Based Access Control:
    - Viewer cannot create projects (403)
    - PO only sees their own projects
    - PO cannot access another PO's project
    - Admin can view all projects
    """
    async with TestSessionLocal() as session:
        # Create users: Admin, PO1, PO2, Viewer
        admin = User(name="Admin", email="admin@test.com", password_hash=hash_password("pw"), role="admin")
        po1 = User(name="PO One", email="po1@test.com", password_hash=hash_password("pw"), role="po")
        po2 = User(name="PO Two", email="po2@test.com", password_hash=hash_password("pw"), role="po")
        viewer = User(name="Viewer", email="viewer@test.com", password_hash=hash_password("pw"), role="viewer")
        session.add_all([admin, po1, po2, viewer])
        await session.commit()
        await session.refresh(admin)
        await session.refresh(po1)
        await session.refresh(po2)
        await session.refresh(viewer)

        admin_id, po1_id, po2_id, viewer_id = admin.id, po1.id, po2.id, viewer.id

    token_admin = create_access_token(admin_id, "admin")
    token_po1 = create_access_token(po1_id, "po")
    token_po2 = create_access_token(po2_id, "po")
    token_viewer = create_access_token(viewer_id, "viewer")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # A. Viewer tries to create project -> 403 Forbidden
        viewer_headers = {"Authorization": f"Bearer {token_viewer}"}
        res = await client.post("/api/projects", json={
            "title": "Viewer Project",
            "profile_id": "proposal",
            "brief": "Brief content for testing viewer",
        }, headers=viewer_headers)
        assert res.status_code == 403

        # B. PO1 creates Project 1 -> 201 Created
        po1_headers = {"Authorization": f"Bearer {token_po1}"}
        res_p1 = await client.post("/api/projects", json={
            "title": "PO1 Research Project",
            "profile_id": "proposal",
            "brief": "Brief content for research proposal",
        }, headers=po1_headers)
        assert res_p1.status_code == 201
        p1_id = res_p1.json()["id"]

        # C. PO2 creates Project 2 -> 201 Created
        po2_headers = {"Authorization": f"Bearer {token_po2}"}
        res_p2 = await client.post("/api/projects", json={
            "title": "PO2 Journal Project",
            "profile_id": "jurnal",
            "brief": "Brief content for journal manuscript",
        }, headers=po2_headers)
        assert res_p2.status_code == 201
        p2_id = res_p2.json()["id"]

        # D. PO1 list projects -> only sees Project 1
        res_po1_list = await client.get("/api/projects", headers=po1_headers)
        assert res_po1_list.status_code == 200
        items_po1 = res_po1_list.json()
        assert len(items_po1) == 1
        assert items_po1[0]["id"] == p1_id

        # E. PO2 list projects -> only sees Project 2
        res_po2_list = await client.get("/api/projects", headers=po2_headers)
        assert res_po2_list.status_code == 200
        items_po2 = res_po2_list.json()
        assert len(items_po2) == 1
        assert items_po2[0]["id"] == p2_id

        # F. PO1 tries to get Project 2 -> 403 Forbidden
        res_cross = await client.get(f"/api/projects/{p2_id}", headers=po1_headers)
        assert res_cross.status_code == 403

        # G. Admin list projects -> sees both Project 1 and Project 2
        admin_headers = {"Authorization": f"Bearer {token_admin}"}
        res_admin_list = await client.get("/api/projects", headers=admin_headers)
        assert res_admin_list.status_code == 200
        admin_items = res_admin_list.json()
        assert len(admin_items) == 2
        ids = [item["id"] for item in admin_items]
        assert p1_id in ids
        assert p2_id in ids

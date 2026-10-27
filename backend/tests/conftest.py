from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, ProjectProfile
from app.db.session import get_db
from app.main import app

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


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an independent session for test setup or assertion."""
    async with TestSessionLocal() as session:
        yield session

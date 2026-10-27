import os

import pytest
from alembic.config import Config

from alembic import command


def test_alembic_migrations_up_and_down(tmp_path: pytest.TempPathFactory) -> None:
    """Verify that Alembic migrations run cleanly up to head and down to base."""
    # Create a temporary SQLite database for migration validation
    db_file = tmp_path / "migration_test.db"
    db_url = f"sqlite:///{db_file}"

    alembic_cfg = Config("backend/alembic.ini" if os.path.exists("backend/alembic.ini") else "alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    alembic_cfg.set_main_option("script_location", "backend/alembic" if os.path.exists("backend/alembic") else "alembic")

    # 1. Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # 2. Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # 3. Upgrade to head again to verify idempotency
    command.upgrade(alembic_cfg, "head")

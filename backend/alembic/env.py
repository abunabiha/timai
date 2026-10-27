import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

# Allow overriding database URL from environment variable
database_url = os.getenv("SYNC_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/timai")
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import create_engine
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

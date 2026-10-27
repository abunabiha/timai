import logging
import os
import signal
import time
from typing import Any

import redis
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [Worker] %(message)s",
)
logger = logging.getLogger("worker")

DATABASE_URL = os.getenv("SYNC_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/timai")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

_running = True


def _handle_exit(signum: int, frame: Any) -> None:
    global _running
    logger.info("Received termination signal %s, shutting down...", signum)
    _running = False


signal.signal(signal.SIGINT, _handle_exit)
signal.signal(signal.SIGTERM, _handle_exit)


def check_postgres() -> bool:
    """Verify PostgreSQL connectivity."""
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1")).scalar()
            return res == 1
    except Exception as exc:
        logger.warning("Postgres connection check failed: %s", exc)
        return False


def check_redis() -> bool:
    """Verify Redis connectivity."""
    try:
        r = redis.from_url(REDIS_URL)
        return bool(r.ping())
    except Exception as exc:
        logger.warning("Redis connection check failed: %s", exc)
        return False


def worker_tick() -> dict[str, bool]:
    """Execute a single heartbeat and connection check."""
    logger.info("worker alive")
    pg_ok = check_postgres()
    rd_ok = check_redis()
    logger.info("Connection status: Postgres=%s, Redis=%s", pg_ok, rd_ok)
    return {"postgres": pg_ok, "redis": rd_ok}


def run_worker_loop(single_run: bool = False, sleep_interval: float = 10.0) -> None:
    """Main worker loop."""
    logger.info("Worker starting up. Connecting to Postgres and Redis...")
    while _running:
        worker_tick()
        if single_run:
            break
        for _ in range(int(sleep_interval * 10)):
            if not _running:
                break
            time.sleep(0.1)


if __name__ == "__main__":
    run_worker_loop()

from unittest.mock import patch

from main import worker_tick


def test_worker_tick_success() -> None:
    """Test worker_tick returns status for both connections."""
    with (
        patch("main.check_postgres", return_value=True),
        patch("main.check_redis", return_value=True),
    ):
        status = worker_tick()
        assert status["postgres"] is True
        assert status["redis"] is True


def test_worker_tick_failure() -> None:
    """Test worker_tick handles connection failures."""
    with (
        patch("main.check_postgres", return_value=False),
        patch("main.check_redis", return_value=False),
    ):
        status = worker_tick()
        assert status["postgres"] is False
        assert status["redis"] is False

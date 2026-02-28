import logging

from shared.config import get_settings


def configure_logging() -> None:
    """Configure root logging from settings."""
    level = get_settings().log_level.upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

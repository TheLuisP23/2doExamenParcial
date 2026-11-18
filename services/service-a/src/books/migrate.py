"""Aplica migraciones Alembic (REQ-A-012). Uso: python -m books.migrate"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

MIGRATIONS = Path(__file__).parent / "repository" / "migrations"


def upgrade(url: str) -> None:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(cfg, "head")


def main() -> None:  # pragma: no cover
    from .config import Settings

    upgrade(Settings().database_url)


if __name__ == "__main__":  # pragma: no cover
    main()

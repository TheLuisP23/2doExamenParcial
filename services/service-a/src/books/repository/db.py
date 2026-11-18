from __future__ import annotations

from sqlalchemy import Engine, create_engine


def make_engine(url: str, pool_size: int = 5, connect_timeout: int = 2) -> Engine:
    return create_engine(
        url, pool_size=pool_size, pool_pre_ping=True, connect_args={"connect_timeout": connect_timeout}
    )

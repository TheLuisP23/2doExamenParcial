from __future__ import annotations

from sqlalchemy import Column, DateTime, MetaData, SmallInteger, String, Table, Uuid, func

metadata = MetaData()

books = Table(
    "books",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=func.gen_random_uuid()),
    Column("isbn", String(13), nullable=False, unique=True),
    Column("title", String(255), nullable=False),
    Column("author", String(255), nullable=False),
    Column("publisher", String(255)),
    Column("published_year", SmallInteger),
    Column("genre", String(64)),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

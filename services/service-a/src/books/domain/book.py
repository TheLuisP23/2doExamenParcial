from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BookData:
    isbn: str
    title: str
    author: str
    publisher: str | None
    published_year: int | None
    genre: str | None


@dataclass(frozen=True)
class Book(BookData):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

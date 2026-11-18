from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from .book import Book, BookData

SORTS = ("title", "-title", "author", "-author", "created_at", "-created_at")


@dataclass(frozen=True)
class ListQuery:
    limit: int = 20
    offset: int = 0
    q: str | None = None
    genre: str | None = None
    sort: str = "-created_at"


class BookRepository(Protocol):
    def add(self, data: BookData) -> Book: ...
    def get(self, book_id: uuid.UUID) -> Book: ...
    def replace(self, book_id: uuid.UUID, data: BookData) -> Book: ...
    def delete(self, book_id: uuid.UUID) -> None: ...
    def list(self, query: ListQuery) -> tuple[list[Book], int]: ...
    def ping(self) -> bool: ...

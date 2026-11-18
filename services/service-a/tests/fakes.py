from __future__ import annotations

import unicodedata
import uuid
from datetime import UTC, datetime

from books.domain.book import Book, BookData
from books.domain.errors import BookNotFound, DuplicateIsbn
from books.domain.ports import ListQuery


def _fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


class InMemoryBookRepository:
    def __init__(self) -> None:
        self.books: dict[uuid.UUID, Book] = {}
        self.healthy = True
        self._tick = 0

    def _now(self) -> datetime:
        self._tick += 1
        return datetime(2026, 1, 1, tzinfo=UTC).replace(microsecond=self._tick)

    def _check_isbn(self, isbn: str, exclude: uuid.UUID | None = None) -> None:
        if any(b.isbn == isbn and b.id != exclude for b in self.books.values()):
            raise DuplicateIsbn(isbn)

    def add(self, data: BookData) -> Book:
        self._check_isbn(data.isbn)
        now = self._now()
        book = Book(id=uuid.uuid4(), created_at=now, updated_at=now, **data.__dict__)
        self.books[book.id] = book
        return book

    def get(self, book_id: uuid.UUID) -> Book:
        if book_id not in self.books:
            raise BookNotFound(book_id)
        return self.books[book_id]

    def replace(self, book_id: uuid.UUID, data: BookData) -> Book:
        old = self.get(book_id)
        self._check_isbn(data.isbn, exclude=book_id)
        book = Book(id=book_id, created_at=old.created_at, updated_at=self._now(), **data.__dict__)
        self.books[book_id] = book
        return book

    def delete(self, book_id: uuid.UUID) -> None:
        self.get(book_id)
        del self.books[book_id]

    def list(self, query: ListQuery) -> tuple[list[Book], int]:
        items = list(self.books.values())
        if query.q:
            q = _fold(query.q)
            items = [b for b in items if q in _fold(b.title) or q in _fold(b.author)]
        if query.genre:
            items = [b for b in items if (b.genre or "").lower() == query.genre.lower()]
        field = query.sort.lstrip("-")
        items.sort(key=lambda b: (getattr(b, field), str(b.id)), reverse=query.sort.startswith("-"))
        return items[query.offset : query.offset + query.limit], len(items)

    def ping(self) -> bool:
        return self.healthy

from __future__ import annotations

import uuid


class DomainError(Exception):
    pass


class BookNotFound(DomainError):
    def __init__(self, book_id: uuid.UUID) -> None:
        super().__init__(f"Book {book_id} not found")


class DuplicateIsbn(DomainError):
    def __init__(self, isbn: str) -> None:
        super().__init__(f"A book with ISBN {isbn} already exists")

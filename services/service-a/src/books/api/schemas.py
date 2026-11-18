from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from ..domain.book import Book, BookData
from ..domain.isbn import is_valid_isbn13, normalize_isbn

Text255 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class BookInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    isbn: str
    title: Text255
    author: Text255
    publisher: Annotated[str, StringConstraints(max_length=255)] | None = None
    published_year: Annotated[int, Field(ge=1450)] | None = None
    genre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)] | None = None

    @field_validator("isbn")
    @classmethod
    def _isbn(cls, v: str) -> str:
        n = normalize_isbn(v)
        if not is_valid_isbn13(n):
            raise ValueError("invalid ISBN-13 (prefix 978/979 and check digit)")
        return n

    @field_validator("published_year")
    @classmethod
    def _year(cls, v: int | None) -> int | None:
        if v is not None and v > datetime.now(UTC).year:
            raise ValueError("published_year cannot be in the future")
        return v

    def to_domain(self) -> BookData:
        return BookData(**self.model_dump())


class BookOut(BaseModel):
    id: uuid.UUID
    isbn: str
    title: str
    author: str
    publisher: str | None
    published_year: int | None
    genre: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, b: Book) -> BookOut:
        return cls(**b.__dict__)


class BookPage(BaseModel):
    items: list[BookOut]
    total: int
    limit: int
    offset: int

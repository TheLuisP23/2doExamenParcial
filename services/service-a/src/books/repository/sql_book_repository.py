from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Engine, delete, func, insert, literal, or_, select, text, update
from sqlalchemy.exc import IntegrityError

from ..domain.book import Book, BookData
from ..domain.errors import BookNotFound, DuplicateIsbn
from ..domain.ports import ListQuery
from .models import books


def _row(r: Any) -> Book:
    return Book(**r._mapping)


def _fold(expr: Any) -> Any:
    return func.immutable_unaccent(func.lower(expr))


class SqlBookRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def add(self, data: BookData) -> Book:
        try:
            with self.engine.begin() as c:
                return _row(c.execute(insert(books).values(**data.__dict__).returning(books)).one())
        except IntegrityError as exc:
            raise DuplicateIsbn(data.isbn) from exc

    def get(self, book_id: uuid.UUID) -> Book:
        with self.engine.connect() as c:
            r = c.execute(select(books).where(books.c.id == book_id)).first()
        if r is None:
            raise BookNotFound(book_id)
        return _row(r)

    def replace(self, book_id: uuid.UUID, data: BookData) -> Book:
        try:
            with self.engine.begin() as c:
                r = c.execute(
                    update(books)
                    .where(books.c.id == book_id)
                    .values(**data.__dict__, updated_at=func.clock_timestamp())
                    .returning(books)
                ).first()
        except IntegrityError as exc:
            raise DuplicateIsbn(data.isbn) from exc
        if r is None:
            raise BookNotFound(book_id)
        return _row(r)

    def delete(self, book_id: uuid.UUID) -> None:
        with self.engine.begin() as c:
            if c.execute(delete(books).where(books.c.id == book_id)).rowcount == 0:
                raise BookNotFound(book_id)

    def list(self, query: ListQuery) -> tuple[list[Book], int]:
        conds = []
        if query.q:
            pattern = func.concat("%", _fold(literal(query.q, books.c.title.type)), "%")
            conds.append(or_(_fold(books.c.title).like(pattern), _fold(books.c.author).like(pattern)))
        if query.genre:
            conds.append(func.lower(books.c.genre) == query.genre.lower())
        col = books.c[query.sort.lstrip("-")]
        order = [col.desc() if query.sort.startswith("-") else col.asc(), books.c.id]
        with self.engine.connect() as c:
            total = c.execute(select(func.count()).select_from(books).where(*conds)).scalar_one()
            rows = c.execute(
                select(books).where(*conds).order_by(*order).limit(query.limit).offset(query.offset)
            )
            return [_row(r) for r in rows], int(total)

    def ping(self) -> bool:
        try:
            with self.engine.connect() as c:
                c.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

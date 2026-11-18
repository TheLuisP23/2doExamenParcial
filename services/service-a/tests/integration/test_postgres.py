"""Integración real con PostgreSQL 16 (Testcontainers)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from testcontainers.postgres import PostgresContainer

from books.config import Settings
from books.domain.book import BookData
from books.domain.errors import BookNotFound, DuplicateIsbn
from books.domain.ports import ListQuery
from books.main import create_app
from books.migrate import upgrade
from books.repository.db import make_engine
from books.repository.sql_book_repository import SqlBookRepository


@pytest.fixture(scope="module")
def db_url() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as pg:
        url = pg.get_connection_url()
        upgrade(url)
        yield url


@pytest.fixture
def repo(db_url: str) -> Iterator[SqlBookRepository]:
    engine = make_engine(db_url)
    with engine.begin() as c:
        c.exec_driver_sql("TRUNCATE books")
    yield SqlBookRepository(engine)
    engine.dispose()


def data(isbn: str = "9780306406157", **kw: object) -> BookData:
    base = {
        "isbn": isbn,
        "title": "Ficciones",
        "author": "Borges",
        "publisher": None,
        "published_year": 1944,
        "genre": None,
    }
    return BookData(**{**base, **kw})  # type: ignore[arg-type]


@pytest.mark.req("REQ-A-012")
def test_migrations_idempotent(db_url: str) -> None:
    upgrade(db_url)  # segunda vez no falla
    insp = inspect(make_engine(db_url))
    assert "books" in insp.get_table_names()


@pytest.mark.req("REQ-A-001", "REQ-A-002", "REQ-A-004", "REQ-A-005")
def test_crud_roundtrip(repo: SqlBookRepository) -> None:
    b = repo.add(data())
    assert repo.get(b.id).title == "Ficciones"
    b2 = repo.replace(b.id, data(title="Otro"))
    assert b2.title == "Otro" and b2.updated_at >= b.updated_at
    repo.delete(b.id)
    with pytest.raises(BookNotFound):
        repo.get(b.id)


@pytest.mark.req("REQ-A-006")
def test_unique_isbn(repo: SqlBookRepository) -> None:
    repo.add(data())
    with pytest.raises(DuplicateIsbn):
        repo.add(data())


@pytest.mark.req("REQ-A-003", "REQ-A-010", "REQ-A-011")
def test_search_sort_paginate(repo: SqlBookRepository) -> None:
    repo.add(
        data("9780307474728", title="Cien años de soledad", author="Gabriel García Márquez", genre="Novela")
    )
    repo.add(data())
    items, total = repo.list(ListQuery(q="garcia"))
    assert total == 1 and items[0].author == "Gabriel García Márquez"
    assert repo.list(ListQuery(genre="novela"))[1] == 1
    items, total = repo.list(ListQuery(sort="title", limit=1, offset=1))
    assert total == 2 and items[0].title == "Ficciones"


@pytest.mark.req("REQ-A-009")
def test_ready_against_real_db(db_url: str) -> None:
    client = TestClient(create_app(Settings(database_url=db_url)))
    assert client.get("/health/ready").status_code == 200
    down = TestClient(create_app(Settings(database_url="postgresql+psycopg://u:p@127.0.0.1:1/x")))
    assert down.get("/health/ready").status_code == 503

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from books.config import Settings
from books.main import create_app

from .fakes import InMemoryBookRepository

os.environ.setdefault("SERVICE_A_DATABASE_URL", "postgresql+psycopg://u:p@localhost:1/x")


@pytest.fixture
def repo() -> InMemoryBookRepository:
    return InMemoryBookRepository()


@pytest.fixture
def client(repo: InMemoryBookRepository) -> TestClient:
    settings = Settings(database_url="postgresql+psycopg://u:p@localhost:1/x")
    return TestClient(create_app(settings, repository=repo))


VALID = {
    "isbn": "978-0-306-40615-7",
    "title": "Ficciones",
    "author": "Jorge Luis Borges",
    "published_year": 1944,
}

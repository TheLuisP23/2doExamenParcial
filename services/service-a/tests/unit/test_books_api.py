from __future__ import annotations

import uuid

import pytest

from ..conftest import VALID

PROBLEM = "application/problem+json"


def create(client, **over):
    return client.post("/books", json={**VALID, **over})


@pytest.mark.req("REQ-A-001")
def test_create_returns_201_location_and_normalized_isbn(client):
    r = create(client)
    assert r.status_code == 201
    body = r.json()
    assert body["isbn"] == "9780306406157"
    assert r.headers["location"] == f"/books/{body['id']}"
    assert set(body) == {
        "id",
        "isbn",
        "title",
        "author",
        "publisher",
        "published_year",
        "genre",
        "created_at",
        "updated_at",
    }


@pytest.mark.req("REQ-A-002")
def test_get_existing_and_missing(client):
    book = create(client).json()
    assert client.get(f"/books/{book['id']}").json()["title"] == "Ficciones"
    r = client.get(f"/books/{uuid.uuid4()}")
    assert r.status_code == 404 and r.headers["content-type"].startswith(PROBLEM)


@pytest.mark.req("REQ-A-002", "REQ-A-007")
def test_get_invalid_uuid_is_422(client):
    assert client.get("/books/not-a-uuid").status_code == 422


@pytest.mark.req("REQ-A-003")
def test_list_pagination(client):
    for i in range(25):
        isbn = f"978000000{i:03d}"
        create(client, isbn=isbn + str(_check(isbn)), title=f"T{i}")
    page = client.get("/books?limit=10&offset=20").json()
    assert page["total"] == 25 and len(page["items"]) == 5 and page["limit"] == 10 and page["offset"] == 20
    assert client.get("/books?limit=101").status_code == 422
    assert client.get("/books?offset=-1").status_code == 422


@pytest.mark.req("REQ-A-004")
def test_replace(client):
    book = create(client).json()
    r = client.put(f"/books/{book['id']}", json={**VALID, "title": "Ficciones (ed. 2)"})
    assert r.status_code == 200 and r.json()["title"] == "Ficciones (ed. 2)"
    assert r.json()["updated_at"] > book["updated_at"]
    assert client.put(f"/books/{uuid.uuid4()}", json=VALID).status_code == 404


@pytest.mark.req("REQ-A-005")
def test_delete(client):
    book = create(client).json()
    assert client.delete(f"/books/{book['id']}").status_code == 204
    assert client.get(f"/books/{book['id']}").status_code == 404
    assert client.delete(f"/books/{book['id']}").status_code == 404


@pytest.mark.req("REQ-A-006")
def test_duplicate_isbn_409(client):
    create(client)
    r = create(client, isbn="9780306406157", title="Otro")
    assert r.status_code == 409 and r.json()["type"] == "/problems/duplicate-isbn"
    other = create(client, isbn="9780307474728", title="Cien años").json()
    assert client.put(f"/books/{other['id']}", json=VALID).status_code == 409


@pytest.mark.req("REQ-A-007", "REQ-SYS-006")
@pytest.mark.parametrize(
    "over,field",
    [
        ({"isbn": "9780306406158"}, "body.isbn"),
        ({"published_year": 3000}, "body.published_year"),
        ({"title": "   "}, "body.title"),
        ({"foo": 1}, "body.foo"),
    ],
)
def test_validation_problem(client, over, field):
    r = create(client, **over)
    assert r.status_code == 422
    assert r.headers["content-type"].startswith(PROBLEM)
    body = r.json()
    assert body["status"] == 422 and body["type"] == "/problems/validation-error"
    assert any(e["field"] == field for e in body["errors"])


@pytest.mark.req("REQ-A-010")
def test_search_accent_insensitive_and_genre(client):
    create(
        client,
        isbn="9780307474728",
        title="Cien años de soledad",
        author="Gabriel García Márquez",
        genre="Novela",
    )
    create(client)
    page = client.get("/books?q=garcia").json()
    assert [b["author"] for b in page["items"]] == ["Gabriel García Márquez"]
    assert client.get("/books?genre=novela").json()["total"] == 1


@pytest.mark.req("REQ-A-011")
def test_sort(client):
    create(client, isbn="9780307474728", title="Zeta")
    create(client, title="Alfa")
    titles = [b["title"] for b in client.get("/books?sort=title").json()["items"]]
    assert titles == ["Alfa", "Zeta"]
    assert client.get("/books?sort=precio").status_code == 422


def _check(twelve: str) -> int:
    s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(twelve))
    return (10 - s % 10) % 10

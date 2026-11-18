from __future__ import annotations

import json
import logging

import pytest
from pydantic import ValidationError

from books.config import Settings
from books.domain.isbn import is_valid_isbn13, normalize_isbn
from books.logging import JsonFormatter, request_id_var


@pytest.mark.req("REQ-A-008")
def test_liveness_ignores_db(client, repo):
    repo.healthy = False
    r = client.get("/health/live")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


@pytest.mark.req("REQ-A-009")
def test_readiness(client, repo):
    assert client.get("/health/ready").json() == {"status": "ok", "checks": {"database": "ok"}}
    repo.healthy = False
    r = client.get("/health/ready")
    assert r.status_code == 503 and r.json() == {"status": "unavailable", "checks": {"database": "error"}}


@pytest.mark.req("REQ-SYS-005")
def test_settings_require_database_url(monkeypatch):
    monkeypatch.delenv("SERVICE_A_DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]
    monkeypatch.setenv("SERVICE_A_DATABASE_URL", "postgresql+psycopg://a:b@h/d")
    assert Settings().port == 8000


@pytest.mark.req("REQ-SYS-004")
def test_request_id_header_and_json_log(client):
    r = client.get("/health/live", headers={"X-Request-ID": "abc-123"})
    assert r.headers["x-request-id"] == "abc-123"
    assert client.get("/health/live").headers["x-request-id"]
    token = request_id_var.set("rid-1")
    try:
        rec = logging.LogRecord("books", logging.INFO, __file__, 1, "hola", None, None)
        line = json.loads(JsonFormatter().format(rec))
    finally:
        request_id_var.reset(token)
    assert line["message"] == "hola" and line["request_id"] == "rid-1" and line["service"] == "service-a"
    assert {"timestamp", "level"} <= set(line)


@pytest.mark.req("REQ-A-007")
def test_isbn_rules():
    assert normalize_isbn(" 978-0-306 40615-7 ") == "9780306406157"
    assert is_valid_isbn13("9780306406157")
    assert not is_valid_isbn13("9780306406158")
    assert not is_valid_isbn13("1234567890123")
    assert not is_valid_isbn13("978030640615")


@pytest.mark.req("REQ-SYS-006")
def test_unknown_route_problem(client):
    r = client.get("/nope")
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/problem+json")

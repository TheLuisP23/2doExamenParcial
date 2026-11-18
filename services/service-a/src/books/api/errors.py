"""Errores en application/problem+json (REQ-SYS-006)."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from ..domain.errors import BookNotFound, DuplicateIsbn

TITLES = {404: "Not Found", 409: "Conflict", 422: "Unprocessable Content", 500: "Internal Server Error"}


def problem(status: int, type_: str, detail: str, **extra: object) -> JSONResponse:
    body = {"type": type_, "title": TITLES.get(status, "Error"), "status": status, "detail": detail, **extra}
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


def install(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return problem(422, "/problems/validation-error", "Request validation failed", errors=errors)

    @app.exception_handler(BookNotFound)
    async def _not_found(_: Request, exc: BookNotFound) -> JSONResponse:
        return problem(404, "/problems/not-found", str(exc))

    @app.exception_handler(DuplicateIsbn)
    async def _dup(_: Request, exc: DuplicateIsbn) -> JSONResponse:
        return problem(409, "/problems/duplicate-isbn", str(exc))

    @app.exception_handler(HTTPException)
    async def _http(_: Request, exc: HTTPException) -> JSONResponse:
        return problem(exc.status_code, "about:blank", str(exc.detail))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:  # pragma: no cover
        logging.getLogger("books").exception("unhandled error")
        return problem(500, "about:blank", "Unexpected error")

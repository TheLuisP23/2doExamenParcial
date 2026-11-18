from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse

from ..domain.ports import BookRepository, ListQuery
from .schemas import BookInput, BookOut, BookPage

router = APIRouter()
Sort = Literal["title", "-title", "author", "-author", "created_at", "-created_at"]


def repo(request: Request) -> BookRepository:
    r: BookRepository = request.app.state.repository
    return r


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(request: Request) -> JSONResponse:
    if repo(request).ping():
        return JSONResponse({"status": "ok", "checks": {"database": "ok"}})
    return JSONResponse({"status": "unavailable", "checks": {"database": "error"}}, status_code=503)


@router.get("/books")
def list_books(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    genre: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
    sort: Sort = "-created_at",
) -> BookPage:
    items, total = repo(request).list(ListQuery(limit=limit, offset=offset, q=q, genre=genre, sort=sort))
    return BookPage(items=[BookOut.of(b) for b in items], total=total, limit=limit, offset=offset)


@router.post("/books", status_code=201)
def create_book(request: Request, body: BookInput, response: Response) -> BookOut:
    book = repo(request).add(body.to_domain())
    response.headers["Location"] = f"/books/{book.id}"
    return BookOut.of(book)


@router.get("/books/{book_id}")
def get_book(request: Request, book_id: uuid.UUID) -> BookOut:
    return BookOut.of(repo(request).get(book_id))


@router.put("/books/{book_id}")
def replace_book(request: Request, book_id: uuid.UUID, body: BookInput) -> BookOut:
    return BookOut.of(repo(request).replace(book_id, body.to_domain()))


@router.delete("/books/{book_id}", status_code=204)
def delete_book(request: Request, book_id: uuid.UUID) -> Response:
    repo(request).delete(book_id)
    return Response(status_code=204)

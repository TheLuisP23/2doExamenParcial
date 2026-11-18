"""App factory. Arranque: `python -m books.migrate && uvicorn books.main:create_app --factory`."""

from __future__ import annotations

from fastapi import FastAPI

from .api import errors
from .api.routes import router
from .config import Settings
from .domain.ports import BookRepository
from .logging import configure_logging, request_id_middleware


def create_app(settings: Settings | None = None, repository: BookRepository | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)
    if repository is None:
        from .repository.db import make_engine
        from .repository.sql_book_repository import SqlBookRepository

        engine = make_engine(settings.database_url, settings.db_pool_size, settings.ready_timeout_s)
        repository = SqlBookRepository(engine)
    app = FastAPI(title="Servicio A — Catálogo de libros", version="0.1.0")
    app.state.repository = repository
    app.middleware("http")(request_id_middleware)
    errors.install(app)
    app.include_router(router)
    return app

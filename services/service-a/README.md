# Servicio A — Catálogo de libros

Python 3.12 · FastAPI · PostgreSQL 16 · puerto `8000`.

> **Estado: solo esqueleto.** El código se crea a partir de `TASK-A-01`
> ([specs/001-servicio-a/tasks.md](../../specs/001-servicio-a/tasks.md)).

- Spec: [specs/001-servicio-a/spec.md](../../specs/001-servicio-a/spec.md)
- Contrato: [specs/001-servicio-a/contracts/openapi.yaml](../../specs/001-servicio-a/contracts/openapi.yaml)
- Modelo de datos: [data-model.md](../../specs/001-servicio-a/data-model.md) · Plan: [plan.md](../../specs/001-servicio-a/plan.md)

Estructura prevista: `src/books/{api,domain,repository}`, `tests/{unit,integration,contract}`.
Comandos (tras TASK-A-01): `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.
Este servicio **no** conoce al servicio B ni a MongoDB.

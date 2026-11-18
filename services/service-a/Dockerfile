# REQ-P-001 — multi-stage, base fijada, no-root
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=build /app /app
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 SERVICE_A_PORT=8000
USER 10001
EXPOSE 8000
CMD ["sh", "-c", "python -m books.migrate && exec uvicorn books.main:create_app --factory --host 0.0.0.0 --port ${SERVICE_A_PORT} --no-access-log"]

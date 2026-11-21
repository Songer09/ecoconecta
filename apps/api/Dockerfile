FROM ghcr.io/astral-sh/uv:0.11.23 AS uv
FROM python:3.12-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app/apps/api
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY apps/api/ecoconecta ./ecoconecta
COPY apps/api/alembic.ini ./
COPY db/schema.sql /app/db/schema.sql
COPY db/migrations /app/db/migrations
RUN uv sync --locked --no-dev

EXPOSE 8000
CMD ["/app/apps/api/.venv/bin/uvicorn", "ecoconecta.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]

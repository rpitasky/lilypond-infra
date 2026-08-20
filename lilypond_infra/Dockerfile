FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# lockfile is shared across all services at the repo root
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app/lilypond_infra

CMD ["uv", "run", "gunicorn", "lilypond_infra.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

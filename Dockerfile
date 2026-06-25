# ─── Sports Intelligence Platform — Dockerfile ───────────────────────────────
# Multi-stage build: base → development → production

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock* ./
COPY requirements.txt ./

# ─── development ─────────────────────────────────────────────────────────────
FROM base AS development

RUN uv sync --all-groups 2>/dev/null || uv pip install --system -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--log-level", "info"]

# ─── production ──────────────────────────────────────────────────────────────
FROM base AS production

RUN uv sync --no-dev 2>/dev/null || uv pip install --system \
    fastapi uvicorn[standard] pydantic pydantic-settings \
    sqlalchemy asyncpg alembic \
    python-jose[cryptography] passlib[bcrypt] \
    httpx tenacity apscheduler slowapi orjson \
    sentry-sdk[fastapi] jinja2 python-multipart

COPY . .

ENV PORT=8000

CMD ["sh", "-c", \
     "alembic upgrade head && \
      uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT} \
        --workers 2 \
        --log-level warning"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health/ready')" || exit 1

# ─── Sports Intelligence Platform — Dockerfile ───────────────────────────────
# Multi-stage build: base → development → production

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required by asyncpg and passlib[bcrypt]
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml ./
# If uv.lock exists it will be used; otherwise uv resolves from pyproject.toml
COPY uv.lock* ./

# ─── development ─────────────────────────────────────────────────────────────
FROM base AS development

# Install all dependencies including dev group
RUN uv sync --all-groups 2>/dev/null || uv pip install --system -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--log-level", "info"]

# ─── production ──────────────────────────────────────────────────────────────
FROM base AS production

# Install only production dependencies
RUN uv sync --no-dev 2>/dev/null || uv pip install --system \
    fastapi uvicorn[standard] pydantic pydantic-settings \
    sqlalchemy asyncpg alembic \
    python-jose[cryptography] passlib[bcrypt] \
    httpx apscheduler slowapi orjson \
    sentry-sdk[fastapi] jinja2 python-multipart

COPY . .

# Run migrations then start the server
CMD ["sh", "-c", \
     "alembic upgrade head && \
      uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 2 \
        --log-level warning"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

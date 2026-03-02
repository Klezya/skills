# Multi-stage Dockerfile for Python FastAPI application with uv.
#
# Features:
#   - Multi-stage build (smaller final image)
#   - Dependency caching (pyproject.toml/uv.lock layer)
#   - Non-root user for security
#   - Health check built in
#   - Single process (scale with container replicas)
#
# Build:  docker build -t my-api:latest .
# Run:    docker run -d -p 8000:8000 --env-file .env my-api:latest

# ── Build Stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first (cached if pyproject.toml/uv.lock unchanged)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

# ── Runtime Stage ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root user for security (OWASP best practice)
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy installed packages and application from builder
COPY --from=builder /app /app

# Switch to non-root user
USER appuser

# Health check — Docker uses this for container health status
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Single process per container — scale horizontally with replicas
CMD ["uv", "run", "fastapi", "run", "src/main.py"]

---
name: production-deployment
description: "Production deployment patterns for Python web APIs: nginx reverse proxy, TLS/SSL, Docker multi-stage builds, docker-compose stacks, health checks, environment strategy, and monitoring. Trigger: When deploying, containerizing, or configuring infrastructure for a Python web API."
---

## When to Use

- Deploying a Python web API to production (any framework)
- Setting up nginx as a reverse proxy
- Containerizing with Docker or Docker Compose
- Configuring TLS/SSL certificates
- Adding health check endpoints
- Setting up monitoring or log aggregation
- Planning environment strategy (dev/staging/prod)

> **For FastAPI-specific application code**: see `fastapi-best-practices` skill.
> **For security hardening**: see `web-security` skill.
> This skill covers **infrastructure and deployment** patterns.

---

## Architecture Overview

```
Internet
  │
  ▼
┌─────────────────────┐
│  Nginx              │  ← TLS termination, rate limiting, static files
│  (reverse proxy)    │
└────────┬────────────┘
         │ HTTP (internal)
         ▼
┌─────────────────────┐
│  Uvicorn / Gunicorn │  ← Python ASGI server (1 process per container)
│  + FastAPI app      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  PostgreSQL / Redis │  ← Databases, caches
└─────────────────────┘
```

**Key principle:** One process per container. Scale horizontally with replicas, not with `--workers N` inside Docker.

---

## Nginx Reverse Proxy

### Why Nginx in Front of Your API

| Concern | Nginx handles it | Without nginx |
|---------|-----------------|---------------|
| TLS termination | ✅ Offloads crypto from app | App handles TLS (slower, more complex) |
| Static files | ✅ Serves directly, no Python overhead | Every static request hits the ASGI server |
| Rate limiting | ✅ Coarse IP-based limits before app | All traffic reaches the app |
| Request buffering | ✅ Absorbs slow clients | Slow clients tie up workers |
| Load balancing | ✅ Distribute across app replicas | Need external LB or platform feature |
| Security headers | ✅ Centralized for all backends | Each app must add its own |

### Basic Configuration

```nginx
# /etc/nginx/conf.d/api.conf
upstream api_backend {
    server app:8000;        # Docker service name or IP:port
    # server app2:8000;     # add more for load balancing
}

server {
    listen 80;
    server_name api.example.com;

    # Redirect HTTP → HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # ── TLS ──────────────────────────────────────────────────────────────
    ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ── Security Headers ─────────────────────────────────────────────────
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # ── Rate Limiting ────────────────────────────────────────────────────
    # Define zone in http {} block: limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    limit_req_status 429;

    # ── Request Limits ───────────────────────────────────────────────────
    client_max_body_size 10m;           # max upload size
    client_body_timeout 30s;
    client_header_timeout 30s;

    # ── Hide Server Version ──────────────────────────────────────────────
    server_tokens off;

    # ── Proxy to App ─────────────────────────────────────────────────────
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering — absorb slow clients
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
    }

    # ── Health Check (optional, for load balancers) ──────────────────────
    location /health {
        proxy_pass http://api_backend/health;
        access_log off;     # don't flood logs with health checks
    }
}
```

### Nginx Rate Limiting (http block)

Add to the `http {}` block in `/etc/nginx/nginx.conf`:

```nginx
# Rate limit zones — define before server blocks
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=2r/s;
```

```nginx
# In server block — stricter limit for auth endpoints
location /auth/ {
    limit_req zone=auth burst=5 nodelay;
    proxy_pass http://api_backend;
    # ... same proxy headers ...
}
```

> **Use both** nginx rate limiting (coarse, IP-based) and app-level rate limiting (fine-grained, user-aware). See `web-security` skill.

---

## TLS/SSL with Let's Encrypt

### Initial Setup (certbot)

```bash
# Install certbot
apt install certbot python3-certbot-nginx

# Obtain certificate (nginx plugin auto-configures)
certbot --nginx -d api.example.com

# Verify auto-renewal
certbot renew --dry-run
```

### Auto-Renewal (cron or systemd timer)

```bash
# Cron (runs twice daily — certbot only renews if needed)
echo "0 0,12 * * * root certbot renew --quiet --post-hook 'nginx -s reload'" >> /etc/crontab
```

### Docker + Certbot

For Docker deployments, use a certbot sidecar or mount certificates as volumes:

```yaml
# In docker-compose.yml
volumes:
  - /etc/letsencrypt:/etc/letsencrypt:ro    # mount host certificates
  - /var/www/certbot:/var/www/certbot:ro    # ACME challenge files
```

---

## Docker

### Multi-Stage Dockerfile (Python + uv)

```dockerfile
# ── Build Stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies (cached if pyproject.toml/uv.lock unchanged)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

# ── Runtime Stage ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Copy installed packages and app from builder
COPY --from=builder /app /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Single process — scale with container replicas
CMD ["uv", "run", "fastapi", "run", "src/main.py"]
```

### .dockerignore

```
.git
.env
.venv
__pycache__
*.pyc
.mypy_cache
.pytest_cache
.ruff_cache
node_modules
tests/
docs/
*.md
```

### Build & Run

```bash
# Build
docker build -t my-api:latest .

# Run (single container)
docker run -d \
    --name my-api \
    -p 8000:8000 \
    --env-file .env \
    my-api:latest
```

---

## Docker Compose — Full Stack

```yaml
# docker-compose.yml
services:
  # ── Application ────────────────────────────────────────────────────────
  app:
    build: .
    restart: unless-stopped
    env_file: .env
    expose:
      - "8000"                          # internal only — nginx handles external
    depends_on:
      db:
        condition: service_healthy
    networks:
      - internal

  # ── Database ───────────────────────────────────────────────────────────
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-myapi}
      POSTGRES_USER: ${POSTGRES_USER:-myapi}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-myapi}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - internal

  # ── Reverse Proxy ──────────────────────────────────────────────────────
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - app
    networks:
      - internal
      - external

networks:
  internal:
    driver: bridge
  external:
    driver: bridge

volumes:
  postgres_data:
```

### Key Patterns

| Pattern | Why |
|---------|-----|
| `expose` not `ports` for app | Only nginx is publicly accessible |
| `depends_on` + `service_healthy` | App waits until DB is ready |
| Named volume for postgres | Data persists across container restarts |
| Separate networks | Internal services not exposed to host |
| `restart: unless-stopped` | Auto-restart on crash, not on manual stop |

---

## Health Checks

Two endpoints: **liveness** (is the process alive?) and **readiness** (can it serve traffic?).

```python
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, text

app = FastAPI()

@app.get("/health", status_code=200)
def health():
    """Liveness probe — is the process alive?

    Always returns 200 if the server is responding.
    Used by: Docker HEALTHCHECK, Kubernetes livenessProbe.
    """
    return {"status": "ok"}


@app.get("/ready", status_code=200)
def readiness(session: SessionDep):
    """Readiness probe — can the app serve traffic?

    Checks database connectivity. Returns 503 if dependencies are down.
    Used by: Kubernetes readinessProbe, load balancer health checks.
    """
    try:
        session.exec(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "database": "disconnected"},
        )
```

### Kubernetes Probes

```yaml
# In deployment.yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## Environment Strategy

| Environment | Purpose | Config source | Debug | Docs |
|------------|---------|--------------|-------|------|
| **Local** | Development | `.env` file | ✅ | ✅ |
| **CI** | Testing | GitHub Actions secrets / env vars | ❌ | ❌ |
| **Staging** | Pre-production validation | Secrets manager or platform env vars | ❌ | ✅ (optional) |
| **Production** | Live traffic | Secrets manager (Vault, AWS SM, GCP SM) | ❌ | ❌ |

**Rules:**
- Each environment has its own secrets — never share between environments
- `.env` files are for local development only — never deploy them
- Use `ENVIRONMENT=production` env var to control behavior
- Staging should mirror production as closely as possible

---

## Logging in Production

### Structured JSON Logs

Production logs should be machine-parseable JSON, not human-formatted text:

```python
import logging
import json
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        return json.dumps(log_entry)

# Setup
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### Log Aggregation

| Tool | Use case |
|------|----------|
| **ELK Stack** (Elasticsearch + Logstash + Kibana) | Full-featured, self-hosted |
| **Loki + Grafana** | Lightweight, integrates with Prometheus |
| **CloudWatch / Cloud Logging** | AWS / GCP managed |
| **Datadog / New Relic** | SaaS, managed, APM included |

**Rule:** Always log to **stdout** in containers. Let the platform (Docker, Kubernetes) handle log collection and routing.

---

## Monitoring

### Prometheus Metrics Endpoint

```python
# uv add prometheus-fastapi-instrumentator
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
# Metrics available at GET /metrics
```

### Key Metrics to Track

| Metric | Why |
|--------|-----|
| Request latency (p50, p95, p99) | Detect performance degradation |
| Request rate (RPS) | Capacity planning, anomaly detection |
| Error rate (4xx, 5xx) | Application health |
| Database connection pool usage | Prevent pool exhaustion |
| Memory / CPU usage | Resource planning |

### Alerting Rules (examples)

| Condition | Severity | Action |
|-----------|----------|--------|
| Error rate > 5% for 5 minutes | Warning | Investigate |
| Error rate > 20% for 2 minutes | Critical | Page on-call |
| p99 latency > 2s for 10 minutes | Warning | Investigate |
| DB pool > 80% utilized | Warning | Scale or optimize queries |
| Health check failing | Critical | Auto-restart + page on-call |

---

## Quick Reference — Deployment Checklist

Before going to production:

- [ ] Nginx reverse proxy configured with TLS
- [ ] HTTP → HTTPS redirect enabled
- [ ] TLS certificates auto-renewing (certbot cron)
- [ ] `server_tokens off` in nginx (hide version)
- [ ] `client_max_body_size` set in nginx
- [ ] Docker image uses multi-stage build
- [ ] Docker container runs as non-root user
- [ ] HEALTHCHECK defined in Dockerfile
- [ ] `/health` and `/ready` endpoints implemented
- [ ] Single process per container (no `--workers N` in Docker)
- [ ] `depends_on` with `service_healthy` in docker-compose
- [ ] App only exposed internally (nginx handles external traffic)
- [ ] Environment-specific secrets (no shared secrets across envs)
- [ ] `.env` file NOT deployed to production
- [ ] Structured JSON logging to stdout
- [ ] Monitoring/metrics endpoint available
- [ ] Rate limiting at nginx level (coarse) + app level (fine)

---

## Resources

- **Nginx reverse proxy docs**: https://nginx.org/en/docs/http/ngx_http_proxy_module.html
- **Let's Encrypt / Certbot**: https://certbot.eff.org/
- **Docker multi-stage builds**: https://docs.docker.com/build/building/multi-stage/
- **FastAPI Docker deployment**: https://fastapi.tiangolo.com/deployment/docker/
- **Prometheus FastAPI Instrumentator**: https://github.com/trallnag/prometheus-fastapi-instrumentator
- **For application code patterns**: see `fastapi-best-practices` skill
- **For security hardening**: see `web-security` skill

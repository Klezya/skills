"""
Health Check Endpoints — Liveness and Readiness probes.

Provides two standard health check endpoints:
    - GET /health  → Liveness probe (is the process alive?)
    - GET /ready   → Readiness probe (can it serve traffic?)

Used by:
    - Docker HEALTHCHECK
    - Kubernetes livenessProbe / readinessProbe
    - Load balancer health checks
    - Monitoring systems

Usage:
    from src.shared.health import health_router
    app.include_router(health_router)
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, text

health_router = APIRouter(tags=["health"])


# ── Liveness ─────────────────────────────────────────────────────────────────

@health_router.get("/health", status_code=200)
def health():
    """Liveness probe — is the process alive?

    Always returns 200 if the server is responding.
    No dependency checks — this should never fail unless the process is dead.
    """
    return {"status": "ok"}


# ── Readiness ────────────────────────────────────────────────────────────────

@health_router.get("/ready", status_code=200)
def readiness(session: Session = Depends()):  # replace with your SessionDep
    """Readiness probe — can the app serve traffic?

    Checks database connectivity. Returns 503 if dependencies are down.
    Load balancers should route traffic only to ready instances.
    """
    checks = {"database": "connected"}
    all_ready = True

    # Database check
    try:
        session.exec(text("SELECT 1"))
    except Exception:
        checks["database"] = "disconnected"
        all_ready = False

    if all_ready:
        return {"status": "ready", "checks": checks}

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "not ready", "checks": checks},
    )


# ── Example: Add More Checks ────────────────────────────────────────────────

# def check_redis(redis_client) -> bool:
#     try:
#         return redis_client.ping()
#     except Exception:
#         return False
#
# def check_external_api(url: str) -> bool:
#     try:
#         resp = httpx.get(url, timeout=5)
#         return resp.status_code == 200
#     except Exception:
#         return False

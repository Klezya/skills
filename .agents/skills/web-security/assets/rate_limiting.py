"""
Rate Limiting — slowapi setup for FastAPI.

Protects against brute-force, abuse, and resource exhaustion with
per-endpoint, per-user, and per-IP rate limits.

Dependencies:
    uv add slowapi

Usage:
    Import and apply to your FastAPI app (see bottom of file).
"""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ── Key Functions ────────────────────────────────────────────────────────────

def get_ip(request: Request) -> str:
    """Rate limit by client IP (default for unauthenticated endpoints)."""
    return get_remote_address(request)


def get_user_or_ip(request: Request) -> str:
    """Rate limit by user ID if authenticated, otherwise by IP.

    Requires that auth middleware sets request.state.user_id.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address(request)


# ── Limiter Instance ────────────────────────────────────────────────────────

limiter = Limiter(
    key_func=get_ip,
    default_limits=["60/minute"],       # default for all endpoints
    storage_uri="memory://",            # use "redis://localhost:6379" for distributed
)


# ── Exception Handler ───────────────────────────────────────────────────────

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Return 429 with Retry-After header."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
        headers={"Retry-After": str(exc.retry_after)},
    )


# ── Setup Function ──────────────────────────────────────────────────────────

def setup_rate_limiting(app: FastAPI) -> None:
    """Attach rate limiter to a FastAPI app."""
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# ── Endpoint Examples ───────────────────────────────────────────────────────

if __name__ == "__main__":
    from fastapi import FastAPI

    app = FastAPI()
    setup_rate_limiting(app)

    # Strict: auth endpoints (brute-force protection)
    @app.post("/auth/login")
    @limiter.limit("5/minute")
    def login(request: Request):
        return {"token": "..."}

    @app.post("/auth/register")
    @limiter.limit("3/minute")
    def register(request: Request):
        return {"message": "registered"}

    # Moderate: authenticated API endpoints
    @app.get("/items")
    @limiter.limit("60/minute", key_func=get_user_or_ip)
    def list_items(request: Request):
        return []

    # Strict: file uploads
    @app.post("/upload")
    @limiter.limit("5/minute", key_func=get_user_or_ip)
    def upload_file(request: Request):
        return {"message": "uploaded"}

    # No explicit limit — uses the default (60/minute by IP)
    @app.get("/health")
    def health():
        return {"status": "ok"}

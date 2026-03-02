"""
Security Headers Middleware — OWASP-aligned response headers.

Adds security headers to every HTTP response. Use as middleware in
FastAPI/Starlette applications.

Usage:
    from src.shared.middleware import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware)

Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 0 (disabled — use CSP instead)
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: camera=(), microphone=(), geolocation=()
    - Content-Security-Policy: default-src 'self'; frame-ancestors 'none'

HSTS is commented out by default — only enable at the TLS termination point.
If nginx handles TLS and proxies to this app over HTTP, set HSTS in nginx instead.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers to all responses."""

    def __init__(self, app, *, enable_hsts: bool = False, hsts_max_age: int = 63072000):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking — DENY blocks all framing; use SAMEORIGIN if you need iframes
        response.headers["X-Frame-Options"] = "DENY"

        # Disabled: modern browsers use CSP instead. Value "0" prevents legacy XSS filter issues
        response.headers["X-XSS-Protection"] = "0"

        # Control referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disable browser features not needed by APIs
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Content Security Policy — adjust per project needs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'"
        )

        # HSTS — only enable at the TLS termination point
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains; preload"
            )

        return response


# ── Usage Examples ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    from fastapi import FastAPI

    app = FastAPI()

    # Basic: no HSTS (app is behind nginx that handles TLS)
    app.add_middleware(SecurityHeadersMiddleware)

    # With HSTS: only if this app terminates TLS directly
    # app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True)

    @app.get("/health")
    def health():
        return {"status": "ok"}

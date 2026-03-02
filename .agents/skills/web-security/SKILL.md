---
name: web-security
description: "Enforces OWASP-aligned security practices for Python web APIs: security headers, rate limiting, input sanitization, JWT hardening, password hashing, secrets management, and dependency auditing. Trigger: When hardening a web API, reviewing security, discussing OWASP compliance, or adding authentication/authorization logic."
---

## When to Use

- Hardening a Python web API for production
- Reviewing or auditing security of an existing API
- Adding authentication, authorization, or access control
- Configuring security headers or rate limiting
- Discussing OWASP compliance or threat modeling
- Managing secrets, passwords, or cryptographic operations

> **For FastAPI-specific implementation** (Depends, HTTPBearer, CORS middleware code): see `fastapi-best-practices` skill.
> This skill covers the *policy and reasoning* behind security decisions.

---

## OWASP Top 10 (2021) — Quick Reference

### A01: Broken Access Control

**Risk:** Users act outside their intended permissions.

| Mitigation | Implementation |
|-----------|----------------|
| Deny by default | Every endpoint requires explicit auth unless marked public |
| Resource ownership checks | Verify `resource.owner_id == current_user.id` in a dependency, not the endpoint |
| Role-based access control (RBAC) | Parameterized role checker dependency (see `fastapi-best-practices` JWT section) |
| No direct object references | Validate that the user can access the requested resource ID |
| Rate limit admin endpoints | Stricter rate limits on sensitive operations |

```python
# ❌ BAD: no ownership check — any authenticated user can access any item
@router.get("/items/{item_id}")
def get_item(item_id: int, session: SessionDep):
    return session.get(Item, item_id)

# ✅ GOOD: ownership validated in dependency
def verify_item_owner(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: SessionDep,
) -> Item:
    item = session.get(Item, item_id)
    if not item or item.owner_id != current_user.id:
        raise HTTPException(404, "Item not found")
    return item

@router.get("/items/{item_id}")
def get_item(item: Item = Depends(verify_item_owner)):
    return item
```

### A02: Cryptographic Failures

**Risk:** Sensitive data exposed due to weak or missing encryption.

| Mitigation | Implementation |
|-----------|----------------|
| TLS everywhere | Terminate TLS at reverse proxy (nginx); never serve HTTP in production |
| Strong password hashing | argon2id (preferred) or bcrypt — never MD5/SHA1/plain SHA256 |
| No secrets in logs | Structured logging with explicit field selection; never log tokens, passwords, or keys |
| No secrets in code | `.env` + `pydantic-settings` for dev; vault/secrets manager for prod |
| Encrypt at rest | Database-level encryption for PII; application-level for highly sensitive fields |

### A03: Injection

**Risk:** Untrusted data sent to an interpreter as part of a command or query.

| Mitigation | Implementation |
|-----------|----------------|
| Parameterized queries | SQLModel/SQLAlchemy use parameterized queries by default — **never** use f-strings in SQL |
| Input validation | Pydantic schemas with `Field()` constraints on every endpoint |
| ORM by default | Raw SQL only with explicit user approval and parameterized binds |

```python
# ❌ CRITICAL: SQL injection via f-string
stmt = text(f"SELECT * FROM users WHERE email = '{email}'")

# ✅ GOOD: parameterized query
stmt = text("SELECT * FROM users WHERE email = :email").bindparams(email=email)

# ✅ BEST: use SQLModel/SQLAlchemy ORM (parameterized by default)
stmt = select(User).where(User.email == email)
```

### A04: Insecure Design

**Risk:** Missing or ineffective security controls at the design level.

**Checklist before building any feature:**
- Who should access this? (roles, ownership, public/private)
- What's the worst case if input is malicious? (file uploads, URLs, IDs)
- What data is sensitive? (PII, tokens, financial data)
- What happens at scale? (rate limiting, pagination, resource exhaustion)

### A05: Security Misconfiguration

**Risk:** Default configs, unnecessary features, or verbose errors exposed.

| Mitigation | Implementation |
|-----------|----------------|
| Disable debug in production | `docs_url=None`, `redoc_url=None`, `openapi_url=None` |
| Remove default credentials | No default admin passwords in code or config |
| Minimize attack surface | Only install needed dependencies; remove unused endpoints |
| Custom error responses | Global exception handler returns generic messages (see below) |
| Security headers | Add via middleware (see Security Headers section) |

### A06: Vulnerable and Outdated Components

**Risk:** Known vulnerabilities in dependencies.

```bash
# Audit dependencies for known vulnerabilities
uv audit                          # if using uv (preferred)
pip-audit                         # alternative

# Automate with CI
# GitHub: enable Dependabot alerts + security updates
# GitLab: use dependency scanning CI template
```

**Rules:**
- Pin dependencies in `pyproject.toml` (minimum versions with `>=`)
- Run `uv audit` in CI on every PR
- Review and update dependencies monthly
- Subscribe to security advisories for critical deps (FastAPI, SQLAlchemy, PyJWT)

### A07: Identification and Authentication Failures

**Risk:** Weak authentication allows attackers to compromise accounts.

| Mitigation | Implementation |
|-----------|----------------|
| Short-lived access tokens | 15–30 minutes max for access tokens |
| Refresh token rotation | Issue new refresh token on each use; invalidate the old one |
| Audience and issuer validation | Always verify `aud` and `iss` claims in JWT |
| Account lockout | Lock after N failed attempts (5–10); unlock via email or time-based |
| No credentials in URLs | Tokens in `Authorization` header, never in query params |

> **JWT implementation details** (HTTPBearer, verify_token, RoleChecker): see `fastapi-best-practices` skill.

### A08: Software and Data Integrity Failures

**Risk:** Code or data modified without verification.

| Mitigation | Implementation |
|-----------|----------------|
| Signed JWTs | Always verify signature; use asymmetric keys (RS256) for distributed systems |
| CI/CD integrity | Pin GitHub Actions versions by SHA, not tag |
| Dependency verification | Use lockfiles (`uv.lock`); verify checksums |

### A09: Security Logging and Monitoring Failures

**Risk:** Breaches go undetected due to insufficient logging.

**What to log (always):**
- Authentication events (login success/failure, token refresh, logout)
- Authorization failures (403 responses)
- Input validation failures (400 responses with suspicious patterns)
- Server errors (500 responses — full traceback server-side only)

**What to NEVER log:**
- Passwords, tokens, API keys, secrets
- Full credit card numbers, SSNs, or PII beyond what's needed
- Request/response bodies containing sensitive data

```python
# ✅ GOOD: log auth events with context, no secrets
logger.info("Login successful", extra={"user_id": user.id, "ip": request.client.host})
logger.warning("Login failed", extra={"email": email, "ip": request.client.host, "reason": "invalid_password"})

# ❌ BAD: logging the actual password
logger.info("Login attempt", extra={"email": email, "password": password})
```

### A10: Server-Side Request Forgery (SSRF)

**Risk:** Attacker tricks the server into making requests to internal resources.

| Mitigation | Implementation |
|-----------|----------------|
| URL allowlisting | Validate external URLs against an allowlist before fetching |
| Block internal networks | Reject `127.0.0.1`, `10.x`, `172.16-31.x`, `192.168.x`, `169.254.x` |
| No raw URL forwarding | Never pass user-supplied URLs directly to `httpx.get()` or `requests.get()` |

```python
import ipaddress
from urllib.parse import urlparse

ALLOWED_HOSTS = {"api.example.com", "cdn.example.com"}

def validate_external_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Host not allowed: {parsed.hostname}")
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError("Internal network access forbidden")
    except ValueError:
        pass  # hostname, not IP — resolved by DNS, allowlist handles it
    return url
```

---

## Security Headers

Add security headers to every response. Use middleware for consistency:

```python
# ✅ Security headers middleware (framework-agnostic pattern, FastAPI/Starlette example)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"  # modern browsers: use CSP instead
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Content-Security-Policy — adjust per project needs
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        # HSTS — only if TLS is terminated at this layer (skip if behind a reverse proxy that handles it)
        # response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response

# Usage:
# app.add_middleware(SecurityHeadersMiddleware)
```

| Header | Purpose | Value |
|--------|---------|-------|
| `X-Content-Type-Options` | Prevent MIME-type sniffing | `nosniff` |
| `X-Frame-Options` | Prevent clickjacking | `DENY` or `SAMEORIGIN` |
| `X-XSS-Protection` | Disabled — CSP is the modern replacement | `0` |
| `Referrer-Policy` | Control referrer information leakage | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | Prevent XSS, data injection | `default-src 'self'` (adjust per project) |
| `Permissions-Policy` | Disable browser features you don't need | `camera=(), microphone=(), geolocation=()` |
| `Strict-Transport-Security` | Force HTTPS | `max-age=63072000; includeSubDomains` (only at TLS termination point) |

> **HSTS caveat:** Only set `Strict-Transport-Security` at the layer that terminates TLS. If nginx handles TLS and proxies to your app over HTTP, set HSTS in nginx, not in the app.

---

## Rate Limiting

Protect against brute-force, abuse, and resource exhaustion.

### Strategy

| Endpoint type | Rate limit | Key |
|--------------|-----------|-----|
| Public (health, docs) | High or exempt | IP |
| Authentication (login, register) | Strict: 5–10/min | IP + email |
| Authenticated API | Moderate: 60–100/min | User ID |
| Admin operations | Moderate with audit logging | User ID |
| File uploads | Strict: 5–10/min | User ID |

### Implementation with slowapi

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
        headers={"Retry-After": str(exc.retry_after)},
    )

# Per-endpoint rate limits
@app.post("/auth/login")
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest):
    ...

@app.get("/items")
@limiter.limit("60/minute")
def list_items(request: Request):
    ...
```

> **Reverse proxy rate limiting** is complementary, not a replacement. Use both: nginx for coarse IP-based limits, app-level for user-aware limits. See `production-deployment` skill.

---

## Password Hashing

### Recommended: argon2id

```python
# pip install argon2-cffi  /  uv add argon2-cffi
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hash: str) -> bool:
    try:
        return ph.verify(hash, password)
    except VerifyMismatchError:
        return False
```

### Alternative: bcrypt

```python
# pip install bcrypt  /  uv add bcrypt
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())
```

### Decision Guide

| Algorithm | When to use |
|-----------|------------|
| **argon2id** (preferred) | New projects — winner of the Password Hashing Competition, memory-hard, resistant to GPU attacks |
| **bcrypt** | Existing projects already using it — battle-tested, widely supported, still secure |
| ❌ MD5, SHA1, SHA256 | **Never** — not designed for passwords, trivially crackable |
| ❌ `hashlib.pbkdf2_hmac` | Avoid — technically usable but argon2id/bcrypt are better choices with simpler APIs |

**Password policy rules:**
- Minimum 8 characters (NIST SP 800-63B recommends allowing up to 64)
- Check against breached password lists (HaveIBeenPwned API or local top-10k list)
- Do NOT enforce complexity rules (uppercase + symbol + number) — NIST discourages this
- Rate limit login attempts (see Rate Limiting section)

---

## JWT Security Best Practices

> **Implementation code** (HTTPBearer, verify_token, RoleChecker): see `fastapi-best-practices` skill.
> This section covers the **security policy** for JWT usage.

### Token Lifetime

| Token type | TTL | Storage |
|-----------|-----|---------|
| Access token | 15–30 minutes | Memory only (never localStorage for web apps) |
| Refresh token | 7–30 days | httpOnly cookie or secure server-side storage |
| Password reset | 15–60 minutes | One-time use, stored server-side |

### Must-Validate Claims

```python
payload = jwt.decode(
    token,
    key,
    algorithms=["RS256"],       # explicit algorithm — NEVER use "none" or allow header to dictate
    audience="my-api",          # reject tokens not intended for this service
    issuer="auth.myapp.com",    # reject tokens from unknown issuers
    options={
        "require": ["exp", "iat", "sub", "aud", "iss"],  # all required
    },
)
```

### Key Management

| Scenario | Algorithm | Notes |
|----------|-----------|-------|
| Single service (API signs + verifies) | HS256 | Symmetric; secret must never leave the server |
| Distributed (auth service signs, API verifies) | RS256/ES256 | Asymmetric; share only the public key |
| Key rotation | JWKS endpoint | Publish public keys at `/.well-known/jwks.json`; clients fetch dynamically |

### Refresh Token Rotation

```
Client → POST /auth/refresh { refresh_token: "abc123" }
Server:
  1. Validate refresh_token "abc123"
  2. Invalidate "abc123" (one-time use)
  3. Issue new access_token + new refresh_token "def456"
  4. If "abc123" was already used → COMPROMISE DETECTED → revoke all tokens for user
```

---

## Secrets Management

| Environment | Strategy |
|------------|----------|
| Local development | `.env` file + `pydantic-settings` (NEVER commit `.env`) |
| CI/CD | GitHub Actions secrets / GitLab CI variables (masked) |
| Staging/Production | Secrets manager: AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault, or Kubernetes secrets |

**Rules:**
- `.env` must be in `.gitignore` — verify before every commit
- Provide `.env.example` with dummy values and comments
- Rotate secrets on any suspected compromise
- Use separate secrets per environment (dev ≠ staging ≠ prod)
- Never pass secrets as CLI arguments (visible in `ps aux`)

---

## Input Validation Beyond Pydantic

Pydantic handles type validation and constraints. These additional checks cover edge cases:

### File Uploads

```python
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

from pathlib import Path
from fastapi import UploadFile, HTTPException

async def validate_upload(file: UploadFile) -> UploadFile:
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type not allowed: {ext}")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large (max 10 MB)")
    await file.seek(0)  # reset for downstream consumers
    return file
```

### Path Traversal Prevention

```python
from pathlib import Path

UPLOAD_DIR = Path("/app/uploads").resolve()

def safe_file_path(filename: str) -> Path:
    """Prevent path traversal attacks (../../etc/passwd)."""
    safe = UPLOAD_DIR / Path(filename).name  # .name strips directory components
    if not safe.resolve().is_relative_to(UPLOAD_DIR):
        raise ValueError("Path traversal detected")
    return safe
```

---

## Global Exception Handler — No Stack Traces to Clients

```python
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
```

> This is **OWASP A05 compliance**: never expose stack traces, SQL errors, or internal details to clients. Log everything server-side for debugging.

---

## Quick Reference — Security Checklist

Before deploying any API to production, verify:

- [ ] All endpoints require authentication unless explicitly public
- [ ] Resource ownership is validated (not just authentication)
- [ ] Security headers middleware is active
- [ ] Rate limiting is configured (app-level and/or reverse proxy)
- [ ] Passwords hashed with argon2id or bcrypt
- [ ] JWT access tokens expire in ≤ 30 minutes
- [ ] JWT `aud`, `iss`, `exp` claims are validated
- [ ] Algorithm is explicit in `jwt.decode()` — never trust the header
- [ ] No secrets in code, logs, or URLs
- [ ] `.env` is in `.gitignore`
- [ ] Dependency audit passes (`uv audit`)
- [ ] Global exception handler prevents stack trace leaks
- [ ] File uploads validated (type, size, path traversal)
- [ ] External URLs validated against allowlist (SSRF prevention)
- [ ] Structured logging for all auth events (no sensitive data)
- [ ] Debug mode / docs disabled in production
- [ ] TLS termination configured (reverse proxy or platform)

---

## Resources

- **OWASP Top 10 (2021)**: https://owasp.org/Top10/
- **NIST SP 800-63B (password guidelines)**: https://pages.nist.gov/800-63-4/sp800-63b.html
- **JWT Best Practices (RFC 8725)**: https://datatracker.ietf.org/doc/html/rfc8725
- **Security headers reference**: https://securityheaders.com/
- **slowapi (rate limiting)**: https://github.com/laurentS/slowapi
- **argon2-cffi**: https://argon2-cffi.readthedocs.io/
- **For FastAPI-specific implementation**: see `fastapi-best-practices` skill
- **For deployment/infrastructure security**: see `production-deployment` skill

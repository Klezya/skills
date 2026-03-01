---
name: fastapi-best-practices
description: "Enforces FastAPI best practices: async/sync correctness, domain-driven structure, Pydantic validation, dependency injection, production hardening, and structured logging. Trigger: When creating or modifying FastAPI endpoints, services, dependencies, routers, or any backend Python code that uses FastAPI."
---

## When to Use

- Creating new FastAPI projects, routers, endpoints, or services
- Reviewing or refactoring existing FastAPI code
- Adding dependencies, background tasks, or database connections
- Configuring FastAPI for production deployment
- Setting up project structure for a new API

---

## Stack & Versions

| Package | Version | Notes |
|---------|---------|-------|
| Python | 3.12+ | 3.8 dropped in FastAPI 0.125.0 |
| FastAPI | 0.133.1 | |
| Pydantic | 2.12.5 | v1 removed in FastAPI 0.128.0 |
| **SQLModel** | 0.0.37 | **Primary ORM** — unifies Pydantic + SQLAlchemy |
| SQLAlchemy | 2.0.47 | Fallback only — requires user consent (see below) |
| Uvicorn | 0.41.0 | |
| python-jose | 3.5.0 | |
| Package manager | **uv** | Always prefer `uv` over `pip` |
| Event loop | **uvloop** | Always install as project dependency |

---

## Critical Rules

### ALWAYS DO

| Rule | Reason |
|------|--------|
| Use **SQLModel** as the primary ORM | Unifies Pydantic schemas + SQLAlchemy models — no duplication |
| Fall back to raw SQLAlchemy **only with user consent** | Complex queries that SQLModel can't express cleanly; must be explicitly approved and commented |
| Use `async def` **only** for non-blocking I/O | Database async drivers, `httpx`, `aiofiles` |
| Use `def` for any blocking operation | `time.sleep`, `requests`, sync DB clients, file I/O with sync libs |
| Validate with `Pydantic Field()` | Constraints, defaults, descriptions — all in the schema |
| Use `Depends()` for DB, auth, validation | Dependency injection everywhere |
| Return proper HTTP status codes | `201` create, `204` delete, `404` not found, etc. |
| Use `lifespan` for app-level resources | Startup/shutdown logic |
| Use structured logging (`loguru`, `structlog`, `logging`) | Never `print()` |
| Use `.env` + `pydantic_settings` or `dynaconf` for config | Never hardcode secrets |
| Use connection pooling via DI | Never create DB connections per request |
| Use `uv` for package management | Faster, more reliable than pip |
| Install `uvloop` | Better async event loop performance |

### NEVER DO

| Rule | Reason |
|------|--------|
| Never use blocking calls in `async def` routes | No `time.sleep()`, `requests.get()`, sync DB drivers, or any blocking library inside `async def` |
| Never put business logic in routes | Use service layer |
| Never hardcode secrets | Use environment variables via config classes |
| Never skip validation | Always use Pydantic schemas |
| Never use `*` in CORS origins for production | Specify exact origins |
| Never validate `response_model` manually | FastAPI handles serialization — return raw data |
| Never do field validation in endpoints | All validation belongs in Pydantic models |
| Never use `@app.on_event("startup")` / `@app.on_event("shutdown")` | Use `lifespan` context manager |
| Never use Swagger/OpenAPI/ReDoc in production | Disable unless explicitly required (e.g., public APIs) |
| Never log sensitive data | No API keys, DB passwords, tokens, or secrets in logs |

---

## SQLModel vs SQLAlchemy — Strategy

**Default: use SQLModel for everything.**
SQLModel (by the same author as FastAPI) was designed to eliminate the duplication between Pydantic schemas and SQLAlchemy models. It is the first choice for all table definitions, relationships, and request/response schemas.

> **Official example**: See [assets/sqlmodel_official_example.py](assets/sqlmodel_official_example.py) for a complete CRUD API using SQLModel with session DI, `select()`, pagination, and HTTP error handling — sourced from the [FastAPI official docs](https://fastapi.tiangolo.com/tutorial/sql-databases/#create-models).

```
Does SQLModel handle this use case?
├── YES → Use SQLModel (default)
│
└── NO (complex raw SQL, advanced ORM feature, or SQLModel limitation)
    ├── Stop and inform the user:
    │   "This requires a raw SQLAlchemy feature that SQLModel doesn't expose cleanly.
    │    I need your approval to write pure SQLAlchemy code here."
    ├── Wait for explicit user confirmation
    └── Add a mandatory comment at the exact function/class:
        # SQLALCHEMY FALLBACK — approved by user on <date>
        # Reason: <why SQLModel was insufficient>
```

```python
# ✅ DEFAULT: SQLModel for all models and schemas
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=255)
    items: list["Item"] = Relationship(back_populates="owner")

class UserCreate(SQLModel):       # Request schema — no `table=True`
    name: str = Field(..., min_length=2, max_length=100)
    email: str

class UserOut(SQLModel):          # Response schema — no `table=True`
    id: int
    name: str
    email: str


# ⚠️ FALLBACK (user-approved only): pure SQLAlchemy
# SQLALCHEMY FALLBACK — approved by user on 2026-03-01
# Reason: complex window function not supported by SQLModel query API
from sqlalchemy import select, func, over
stmt = select(
    User,
    func.rank().over(order_by=User.created_at.desc()).label("rank"),
)
```

---

## async def vs def — Decision Tree

```
Is the operation blocking?
├── YES (time.sleep, requests, sync DB, subprocess, heavy file I/O)
│   └── Use `def` → FastAPI runs it in a threadpool automatically
│
└── NO
    ├── Is it async-native? (asyncpg, httpx, aiofiles, asyncio.sleep)
    │   └── Use `async def`
    │
    └── Is it pure computation with NO I/O?
        ├── Light computation → `def` or `async def` (both fine)
        └── Heavy CPU/GPU computation → ⚠️ DO NOT put in endpoint
            └── Ask user for confirmation if absolutely required
            └── Recommend: Celery, ARQ, or dedicated worker queue
```

**This rule applies equally to endpoints, dependencies, and background tasks.**

---

## Heavy Computation Policy

**Never** perform heavy CPU or GPU work inside FastAPI endpoints, dependencies, or background tasks.

If the user explicitly requests it or it is **completely unavoidable**:

1. **Stop and ask for confirmation** before implementing
2. Clearly explain the performance impact: "This will block the event loop / consume worker threads and degrade API responsiveness"
3. Recommend alternatives: task queues (Celery, ARQ, Dramatiq), dedicated worker processes
4. If confirmed, isolate in `def` (never `async def`) and add a warning comment

---

## BackgroundTasks — When to Use

| Use BackgroundTasks | Do NOT use BackgroundTasks |
|---------------------|---------------------------|
| Small, non-critical tasks | Guaranteed delivery required |
| Sending emails/notifications | Retry logic needed |
| Logging/analytics events | Long-running tasks (> few seconds) |
| Cache warming | Tasks that must survive app crashes |
| Non-essential cleanup | Heavy CPU/GPU operations |

For robust needs → **always recommend a queue + workers** (Celery, ARQ, Dramatiq, etc.)

```python
# ✅ Good: small, non-critical background task
from fastapi import BackgroundTasks

def send_welcome_email(email: str):
    """Blocking call — use def, not async def."""
    # ... send email via SMTP ...

@router.post("/users", status_code=201)
async def create_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    new_user = await user_service.create(db, user)
    background_tasks.add_task(send_welcome_email, new_user.email)
    return new_user
```

---

## response_model — Let FastAPI Handle It

```python
# ❌ BAD: manual serialization
@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_service.get(db, user_id)
    return UserOut(**user.__dict__)  # ← unnecessary

# ✅ GOOD: return raw data, FastAPI serializes via response_model
@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_service.get(db, user_id)
    return user  # ← FastAPI handles validation & serialization
```

---

## Validation — Always in Pydantic

```python
# ❌ BAD: validating in the endpoint
@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    if len(user.name) < 2:
        raise HTTPException(400, "Name too short")
    if not user.email.endswith("@company.com"):
        raise HTTPException(400, "Invalid email domain")
    ...

# ✅ GOOD: validation in Pydantic schema
from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        if not v.endswith("@company.com"):
            raise ValueError("Must be a company email")
        return v
```

---

## DB-Dependent Validation — Use Dependencies

If validation requires a database query (e.g., checking resource ownership), it belongs in a **dependency**, not in the endpoint or service.

```python
# ✅ GOOD: DB validation as a dependency
async def verify_item_owner(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Item:
    item = await item_service.get(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your item")
    return item

@router.put("/items/{item_id}")
async def update_item(
    payload: ItemUpdate,
    item: Item = Depends(verify_item_owner),
    db: AsyncSession = Depends(get_db),
):
    return await item_service.update(db, item, payload)
```

---

## Database Connections — Pool via DI

```python
# ❌ BAD: creating connection per request
@router.get("/users")
async def get_users():
    engine = create_async_engine("postgresql+asyncpg://...")
    async with AsyncSession(engine) as session:
        ...

# ✅ GOOD: connection pool + dependency injection
# src/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config import settings

engine = create_async_engine(settings.database_url, pool_size=20, max_overflow=10)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

---

## Lifespan — App-Level Resources

```python
# ❌ BAD: deprecated event handlers
@app.on_event("startup")
async def startup():
    ...

# ✅ GOOD: lifespan context manager
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Application started")
    yield
    # Shutdown
    await close_db()
    logger.info("Application shut down")

app = FastAPI(lifespan=lifespan)
```

---

## Configuration — Never Hardcode Secrets

```python
# ✅ GOOD: pydantic-settings
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "My API"
    debug: bool = False
    database_url: str
    secret_key: str
    allowed_origins: list[str] = ["https://myapp.com"]

settings = Settings()
```

---

## Disable Docs in Production

```python
from src.config import settings

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)
```

> Only enable Swagger/ReDoc/OpenAPI in production if **explicitly requested** (e.g., public-facing APIs).

---

## Structured Logging

```python
# ✅ GOOD: structured logging with loguru
from loguru import logger

logger.info("User created", extra={"user_id": user.id, "email": user.email})

# ❌ BAD: print statements
print(f"User created: {user.id}")

# ❌ BAD: logging sensitive data
logger.info("DB connected", extra={"password": settings.db_password})  # NEVER
```

---

## Running the Server

### Development — `fastapi dev` (official CLI, recommended)

```bash
# Auto-reload enabled, listens on 127.0.0.1 only
uv run fastapi dev src/main.py
```

- Hot-reload on code changes (resource-intensive, dev only)
- Binds to `127.0.0.1:8000` (localhost only — not publicly accessible)
- Swagger docs enabled by default

### Production — `fastapi run` (official CLI, recommended)

```bash
# Single process — use this inside containers (Docker, Kubernetes, etc.)
# Scale horizontally by running more container replicas instead
uv run fastapi run src/main.py

# Multiple workers — only for bare-metal / VM deployments (NOT for Docker/Kubernetes/containers)
# When using containers, keep 1 process per container and scale with replicas
# Formula: workers = (CPU cores × 2) + 1  (recommended, not mandatory)
uv run fastapi run src/main.py --workers 5
```

- Auto-reload disabled
- Binds to `0.0.0.0:8000` (publicly accessible)
- Manages workers automatically without Gunicorn
- Preferred for new projects

### Production — Legacy (Gunicorn + UvicornWorker)

> **Not recommended for Docker/Kubernetes/containers.** Use a single process per container and scale with replicas instead. Gunicorn multi-worker is only appropriate for bare-metal or VM deployments.

```bash
# Install gunicorn if not present
uv add gunicorn

# Run with uvicorn workers — bare-metal / VM only (NOT for Docker/Kubernetes/containers)
# Formula: workers = (CPU cores × 2) + 1  (recommended, not mandatory)
gunicorn src.main:app \
    --workers 5 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

- Valid and battle-tested alternative
- Preferred when Gunicorn's process management features are needed (graceful reload, advanced signals, etc.)
- Workers formula: `(CPU cores × 2) + 1` — same guideline applies

> **Choose `fastapi run --workers`** for new projects (bare-metal/VM only).
> Choose **Gunicorn** when you need its advanced process manager features or your infra already depends on it.
> **Using containers?** Keep `--workers 1` (or omit it) and scale horizontally with replicas.

- Always install `uvloop` as a project dependency for better event loop performance

---

## Project Structure — Domain-Driven

```
my-api/
├── pyproject.toml
├── .env                      # Secrets — NEVER commit
├── src/
│   ├── __init__.py
│   ├── main.py               # FastAPI app initialization + lifespan
│   ├── config.py             # Settings via pydantic_settings
│   ├── database.py           # Engine, session factory, get_db dependency
│   │
│   ├── auth/                 # Auth domain
│   │   ├── __init__.py
│   │   ├── router.py         # Auth endpoints
│   │   ├── schemas.py        # Pydantic models (request/response)
│   │   ├── models.py         # SQLAlchemy/SQLModel ORM models
│   │   ├── service.py        # Business logic
│   │   └── dependencies.py   # Auth dependencies (get_current_user, etc.)
│   │
│   ├── items/                # Items domain
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── service.py
│   │   └── dependencies.py
│   │
│   └── shared/               # Shared utilities
│       ├── __init__.py
│       └── exceptions.py     # Custom exception handlers
│
└── tests/
    ├── conftest.py
    ├── auth/
    │   └── test_router.py
    └── items/
        └── test_router.py
```

**Rules:**
- One domain = one folder with its own router, schemas, models, service, dependencies
- **SQLModel is the default** — `models.py` holds SQLModel classes (both table models and schemas)
  - `class User(SQLModel, table=True)` → DB table
  - `class UserCreate(SQLModel)` / `class UserOut(SQLModel)` → request/response schemas in the same file
- Only split into separate `schemas.py` + `models.py` if the domain grows complex enough to justify it
- If raw SQLAlchemy is needed anywhere, it requires user approval and a comment (see SQLModel vs SQLAlchemy section)
- Business logic lives in `service.py`, never in `router.py`
- Cross-domain shared code goes in `shared/`

---

## CORS — Production Safety

```python
from fastapi.middleware.cors import CORSMiddleware

# ❌ BAD: allow all origins in production
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# ✅ GOOD: explicit origins from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # ["https://myapp.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## Commands

```bash
# Create new project with uv
uv init my-api
cd my-api

# Add core dependencies
uv add "fastapi[standard]" uvloop uvloop pydantic-settings sqlmodel asyncpg

# Add dev dependencies
uv add --dev pytest pytest-asyncio httpx ruff

# ── Development ──────────────────────────────────────────────────────────────
# Official FastAPI CLI (recommended)
uv run fastapi dev src/main.py

# Legacy uvicorn (still valid)
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

# ── Production ───────────────────────────────────────────────────────────────
# Official FastAPI CLI — single process (containers: Docker, Kubernetes)
uv run fastapi run src/main.py

# Official FastAPI CLI — multiple workers (bare-metal / VMs)
# workers = (CPU cores × 2) + 1
uv run fastapi run src/main.py --workers 5

# Legacy Gunicorn + UvicornWorker (when advanced process management is needed)
uv run gunicorn src.main:app \
    --workers 5 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

---

## Quick Reference — Endpoint Checklist

Before writing any endpoint, verify:

- [ ] `async def` only for non-blocking I/O; `def` for blocking ops
- [ ] No heavy CPU/GPU work (redirect to queue if needed)
- [ ] `response_model` set, raw data returned (no manual serialization)
- [ ] All field validation in Pydantic schemas
- [ ] DB-dependent validation in dependencies, not endpoint body
- [ ] DB session from `Depends(get_db)`, not created inline
- [ ] Proper HTTP status code set (`status_code=` param)
- [ ] Business logic in service layer, not in router
- [ ] No hardcoded secrets or env vars
- [ ] Structured logging, no `print()`

---

## Resources

- **Official SQLModel CRUD example**: See [assets/sqlmodel_official_example.py](assets/sqlmodel_official_example.py) — complete CRUD with session DI, `select()`, pagination, and 404 handling
- **FastAPI SQL databases guide**: https://fastapi.tiangolo.com/tutorial/sql-databases/#create-models


"""
SQLModel Sync CRUD Pattern
Pattern: service layer + thin router + SessionDep + model_dump(exclude_unset=True)

Use this when your SQLModel session is SYNCHRONOUS (sync SQLAlchemy engine, not asyncpg).

⚠️  async/sync rule:
    - `def`       → CORRECT for sync SQLModel sessions (FastAPI runs in threadpool)
    - `async def` → DO NOT use with a sync session — it blocks the event loop
    If you need async DB, switch to asyncpg + SQLAlchemy async session instead.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Field, Session, SQLModel, create_engine, select

# ── Models (table model + request/response schemas in one file) ───────────────

class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: float = Field(..., gt=0)
    active: bool = Field(default=True)

class ItemCreate(SQLModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: float = Field(..., gt=0)

class ItemUpdate(SQLModel):
    # All fields optional — PATCH semantics: only update what the client sends
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    active: bool | None = None


# ── Database setup ─────────────────────────────────────────────────────────────
# engine and get_session live in a shared database.py module (not inline here)

engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_pre_ping=True,   # reconnect if the connection was dropped
    pool_size=5,
    max_overflow=10,
)

def get_session():
    with Session(engine) as session:
        yield session

# Annotated alias → cleaner type hints in every service and route function
SessionDep = Annotated[Session, Depends(get_session)]


# ── Service layer (all business logic lives here, NOT in the router) ──────────

def get_item(session: Session, item_id: int) -> Item:
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

def list_items(session: Session) -> list[Item]:
    return session.exec(select(Item)).all()

def create_item(session: Session, data: ItemCreate) -> Item:
    item = Item.model_validate(data)   # Pydantic v2: validates + converts schema → model
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def update_item(session: Session, item_id: int, data: ItemUpdate) -> Item:
    item = get_item(session, item_id)
    # exclude_unset=True → only apply fields the client explicitly sent (true PATCH)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def delete_item(session: Session, item_id: int) -> None:
    item = get_item(session, item_id)
    session.delete(item)
    session.commit()


# ── Router (thin — delegates everything to the service layer) ─────────────────

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/", response_model=list[Item])
def route_list_items(session: SessionDep):
    return list_items(session)

@router.get("/{item_id}", response_model=Item)
def route_get_item(item_id: int, session: SessionDep):
    return get_item(session, item_id)

# 201 Created for POST — FastAPI defaults to 200 if not set
@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
def route_create_item(data: ItemCreate, session: SessionDep):
    return create_item(session, data)

# PATCH (partial update) — uses ItemUpdate with all-optional fields
@router.patch("/{item_id}", response_model=Item)
def route_update_item(item_id: int, data: ItemUpdate, session: SessionDep):
    return update_item(session, item_id, data)

# 204 No Content for DELETE — return None (no body)
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def route_delete_item(item_id: int, session: SessionDep):
    delete_item(session, item_id)

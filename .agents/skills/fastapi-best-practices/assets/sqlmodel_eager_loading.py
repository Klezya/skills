"""
SQLModel — Eager Loading with selectinload + load_only

❓ WHY THIS IS A SQLALCHEMY FALLBACK:
SQLModel's Relationship() uses lazy loading by default.
For eager loading (to avoid N+1 queries), SQLModel does not expose
`options()`, `selectinload()`, or `load_only()` natively.
This requires dropping down to SQLAlchemy's query option API.

# SQLALCHEMY FALLBACK — approved pattern
# Reason: SQLModel does not expose selectinload/load_only in its query API.
#         Use this when eager-loading relationships to avoid N+1 queries,
#         or when you need to SELECT only specific columns from a related model.

✅ When to use this pattern:
  - You have a parent → children relationship and need the children in one query
  - You want to avoid loading all columns of the related model (load_only)
  - You need to prevent N+1 queries on list endpoints
"""

from sqlmodel import Field, Relationship, SQLModel, Session, select
from sqlalchemy.orm import selectinload, load_only
from fastapi import HTTPException, status


# ── Models ─────────────────────────────────────────────────────────────────────

class Course(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    items: list["Item"] = Relationship(back_populates="course")

class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    body: str
    active: bool = Field(default=True)
    course_id: int = Field(foreign_key="course.id")
    course: "Course" = Relationship(back_populates="items")


# ── ❌ Without eager loading (lazy — triggers N+1 if called in a loop) ─────────

def get_course_items_lazy(session: Session, course_id: int) -> list[Item]:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    # ⚠️ Accessing `course.items` triggers a second SELECT here (lazy load).
    # In a loop over multiple courses this becomes N+1 queries.
    return course.items


# ── SQLALCHEMY FALLBACK — approved pattern ─────────────────────────────────────
# Reason: SQLModel does not expose selectinload/load_only in its query API.

def get_course_items_eager(session: Session, course_id: int) -> list[Item]:
    """
    Loads course + items in exactly 2 SQL queries (no N+1):
      1. SELECT * FROM course WHERE id = ?
      2. SELECT id, title, active FROM item WHERE course_id IN (?)

    selectinload  → emits a single IN query for the relationship (efficient)
    load_only     → restricts the SELECT to the specified columns only
    """
    statement = (
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.items).options(
                load_only(Item.id, Item.title, Item.active)
            )
        )
    )
    course = session.exec(statement).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course.items


# ── When NOT to use this pattern ──────────────────────────────────────────────
#
# If you only need the parent (Course) without its children → plain select() is fine:
#   course = session.get(Course, course_id)
#
# If you need a flat JOIN query → use SQLAlchemy join() directly.
# If the relationship is many-to-many → consider joinedload instead of selectinload.

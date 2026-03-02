"""
JWT Authentication + Role-Based Access Control
Pattern: HTTPBearer → verify_token dependency → parameterized RoleChecker

This is a generic JWT auth pattern for FastAPI.
Adapt the algorithm, key loading, and role claim name to your use case.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

# ── Configuration (never hardcode — load from settings) ───────────────────────
# RS256 (asymmetric): load the public key from a .pem file or secrets manager
# HS256 (symmetric):  use a shared secret string

with open("keys/public_key.pem", "rb") as f:
    PUBLIC_KEY = f.read()

ALGORITHM = "RS256"   # or "HS256" for symmetric JWTs

# ── Token verification dependency ─────────────────────────────────────────────
security = HTTPBearer()

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validates the Bearer token and returns the decoded payload.
    Raises HTTP 401 on invalid or expired tokens.

    Chain this as a dependency to protect any endpoint:
        @router.get("/me")
        def get_me(payload: dict = Depends(verify_token)):
            user_id = payload["sub"]
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or signature",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Role-Based Access Control ─────────────────────────────────────────────────

class RoleChecker:
    """
    Parameterized dependency for role-based access control.
    Reads roles from the token payload's "roles" claim (list of strings).

    Customize `roles_claim` if your JWT uses a different key (e.g., "permissions").

    Usage:
        require_admin = RoleChecker(["admin"])

        @router.delete("/items/{id}", status_code=204)
        def delete_item(payload: dict = Depends(require_admin)):
            ...
    """

    def __init__(self, allowed_roles: list[str], roles_claim: str = "roles") -> None:
        self.allowed_roles = set(allowed_roles)  # set for O(1) lookup
        self.roles_claim = roles_claim

    def __call__(self, payload: dict = Depends(verify_token)) -> dict:
        user_roles = set(payload.get(self.roles_claim, []))
        if not (user_roles & self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return payload  # return payload so endpoints can access user context


# ── Pre-configured role guards ────────────────────────────────────────────────
# Define one instance per role combination — reuse across routers.
# No need to instantiate RoleChecker inside each route.

require_admin  = RoleChecker(["admin"])
require_editor = RoleChecker(["admin", "editor"])
require_viewer = RoleChecker(["admin", "editor", "viewer"])


# ── Endpoint examples ─────────────────────────────────────────────────────────

router = APIRouter(prefix="/items", tags=["items"])

# Any authenticated user (viewer+)
@router.get("/")
def list_items(payload: dict = Depends(require_viewer)):
    user_id = payload.get("sub")
    return {"user": user_id, "items": []}

# Editors and admins only
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_item(payload: dict = Depends(require_editor)):
    return {"created": True}

# Admins only
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, payload: dict = Depends(require_admin)):
    return None

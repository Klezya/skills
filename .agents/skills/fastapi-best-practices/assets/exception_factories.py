"""
Exception Factories — Organized HTTP Error Responses

Group related HTTP exceptions into factory classes by domain.
Each static method returns a pre-configured HTTPException instance.

Benefits:
  - Centralized error messages (no scattered magic strings)
  - Consistent status codes and headers across the codebase
  - Easy to audit all possible error responses per domain
  - Reusable across services and routers

Usage:
    raise AuthExceptions.expired_token()
    raise UserExceptions.duplicate_email()
"""

from fastapi import HTTPException, status


# ── Auth domain exceptions ────────────────────────────────────────────────────

class AuthExceptions:
    """Exceptions related to authentication and authorization."""

    @staticmethod
    def expired_token():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def invalid_token():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or signature",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def invalid_issuer():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def insufficient_permissions():
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


# ── Login domain exceptions ──────────────────────────────────────────────────

class LoginExceptions:
    """Exceptions related to the login flow."""

    @staticmethod
    def invalid_credentials():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def user_not_found():
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    @staticmethod
    def access_denied():
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )


# ── Resource domain exceptions (generic, extend per domain) ──────────────────

class ResourceExceptions:
    """Generic CRUD exceptions — subclass or adapt per domain."""

    def __init__(self, resource_name: str):
        self.resource_name = resource_name

    def not_found(self, resource_id=None):
        detail = f"{self.resource_name} not found"
        if resource_id is not None:
            detail = f"{self.resource_name} with id {resource_id} not found"
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    def duplicate(self, field: str = "resource"):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{self.resource_name} with this {field} already exists",
        )


# Pre-configured instances for common domains
UserErrors = ResourceExceptions("User")
ProductErrors = ResourceExceptions("Product")

# Usage:
#   raise UserErrors.not_found(user_id)
#   raise UserErrors.duplicate("email")
#   raise ProductErrors.not_found()

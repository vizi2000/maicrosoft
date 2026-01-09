"""Role-based access control middleware."""

from functools import wraps
from fastapi import HTTPException, status


ROLE_HIERARCHY = {
    "admin": 4,
    "owner": 3,
    "editor": 2,
    "viewer": 1,
}


def require_role(allowed_roles: list[str]):
    """Decorator to require specific roles."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict = None, **kwargs):
            if not current_user:
                raise HTTPException(status_code=401, detail="Not authenticated")

            user_role = current_user.get("role", "viewer")
            if user_role not in allowed_roles and user_role != "admin":
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def can_access(user_role: str, required_roles: list[str]) -> bool:
    """Check if user role can access resource."""
    if user_role == "admin":
        return True
    return user_role in required_roles

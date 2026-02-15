"""Authentication: credential validation (extensible to token-based auth)."""
import base64
from typing import Optional
from fastapi import Request


# Simple in-memory user store for Basic Auth (replace with DB/tokens later)
VALID_USERS = {"admin": "admin123", "user": "password"}


def validate_credentials(request: Request) -> Optional[dict]:
    """
    Validate credentials from request. Returns user info if valid, None otherwise.
    Centralized so we can switch from Basic Auth to Bearer token in one place.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    # Support "Basic <base64>" or "Bearer <token>" for future use
    parts = auth_header.split(maxsplit=1)
    if len(parts) != 2:
        return None

    scheme, value = parts[0].strip(), parts[1].strip()
    if scheme.lower() == "basic":
        try:
            decoded = base64.b64decode(value).decode("utf-8")
            if ":" not in decoded:
                return None
            username, password = decoded.split(":", 1)
            if VALID_USERS.get(username) == password:
                return {"username": username, "id": username}
            return None
        except Exception:
            return None
    # Future: elif scheme.lower() == "bearer": validate JWT, return user
    return None

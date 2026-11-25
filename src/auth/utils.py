"""
Authentication Utilities

Provides password hashing, verification, and authentication helper functions.
Uses Argon2id (OWASP 2025 recommended) for password hashing.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models.user import User
from src.repositories.user_repository import UserRepository

# Initialize Argon2id hasher with OWASP recommended parameters
# https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
ph = PasswordHasher(
    time_cost=2,        # Number of iterations (OWASP minimum: 2)
    memory_cost=19456,  # Memory usage in KiB (OWASP minimum: 19 MiB = 19456 KiB)
    parallelism=1,      # Degree of parallelism
    hash_len=32,        # Hash length in bytes
    salt_len=16         # Salt length in bytes
)


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id.

    Args:
        password: Plain text password

    Returns:
        Argon2id hashed password string

    Note:
        Argon2 automatically includes:
        - Unique salt per password
        - Algorithm parameters in the hash string
        - No 72-byte limit (unlike bcrypt)
    """
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its Argon2id hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Argon2id hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except (VerifyMismatchError, InvalidHash):
        return False


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password

    Returns:
        User if authentication successful, None otherwise
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(username)

    if not user:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def generate_session_token() -> str:
    """
    Generate a secure random session token.

    Returns:
        URL-safe random token string (32 bytes)
    """
    return secrets.token_urlsafe(32)


def create_session_cookie(user_id: int, remember_me: bool = False) -> dict:
    """
    Create session cookie data.

    Args:
        user_id: ID of authenticated user
        remember_me: Whether to create persistent session (30 days) or session-only

    Returns:
        Dictionary with session data (user_id, expires_at as an ISO 8601 UTC
        timestamp with a +00:00 offset)
    """
    if remember_me:
        # Persistent session: 30 days
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    else:
        # Session-only: 24 hours
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    return {
        "user_id": user_id,
        "expires_at": expires_at.isoformat()
    }


def get_current_user(db: Session, user_id: int) -> User:
    """
    Get current authenticated user by ID.

    Args:
        db: Database session
        user_id: User ID from session

    Returns:
        User object

    Raises:
        HTTPException: If user not found or inactive
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )

    return user

"""
Authentication API Schemas

Pydantic models for authentication request/response validation.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=1, max_length=50, description="Username")
    password: str = Field(..., min_length=1, description="Password")
    remember_me: bool = Field(default=False, description="Remember session for 30 days")


class LoginResponse(BaseModel):
    """Login response schema."""
    username: str
    role: str
    message: str = "Login successful"

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User information response schema."""
    id: int
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=72,  # bcrypt max
        description="New password (8-72 characters)"
    )


class ChangePasswordResponse(BaseModel):
    """Change password response schema."""
    message: str = "Password changed."


class ResetViewerPasswordRequest(BaseModel):
    """Reset viewer password request schema (admin only)."""
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=72,  # bcrypt max
        description="New password for viewer account (8-72 characters)"
    )


class ResetViewerPasswordResponse(BaseModel):
    """Reset viewer password response schema."""
    message: str = "Viewer password reset."

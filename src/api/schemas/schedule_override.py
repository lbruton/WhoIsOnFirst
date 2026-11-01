"""
Schedule Override Pydantic Schemas

Request and response models for schedule override API endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ScheduleOverrideRequest(BaseModel):
    """
    Request body for creating a schedule override.

    Used when admin creates a manual override for vacation, sick days, or swaps.
    """
    schedule_id: int = Field(
        ...,
        description="Schedule ID to override",
        examples=[123]
    )
    override_member_id: int = Field(
        ...,
        description="Team member ID covering the shift",
        examples=[5]
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for override (vacation, sick day, swap, etc.)",
        examples=["Vacation", "Sick day", "Swap with Dave"]
    )

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: Optional[str]) -> Optional[str]:
        """
        Trim whitespace from reason.

        Args:
            v: Reason string

        Returns:
            Trimmed reason or None
        """
        return v.strip() if v else None

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "schedule_id": 123,
                "override_member_id": 5,
                "reason": "Vacation - covering for Eve"
            }
        }


class ScheduleOverrideResponse(BaseModel):
    """
    Response schema for schedule override.

    Includes full override details with snapshot data for historical accuracy.
    """
    id: int = Field(
        ...,
        description="Override ID",
        examples=[1]
    )
    schedule_id: int = Field(
        ...,
        description="Original schedule ID",
        examples=[123]
    )
    override_member_id: int = Field(
        ...,
        description="Covering member ID",
        examples=[5]
    )
    original_member_name: str = Field(
        ...,
        description="Original assignee name (snapshot at override time)",
        examples=["Eve Echo"]
    )
    override_member_name: str = Field(
        ...,
        description="Covering member name (snapshot at override time)",
        examples=["Alice Alpha"]
    )
    override_date: datetime = Field(
        ...,
        description="Date/time of the shift being overridden",
        examples=["2025-11-27T08:00:00"]
    )
    reason: Optional[str] = Field(
        None,
        description="Override reason",
        examples=["Vacation"]
    )
    status: str = Field(
        ...,
        description="Override status: active, cancelled, completed",
        examples=["active"]
    )
    created_by: str = Field(
        ...,
        description="Admin username who created the override",
        examples=["admin"]
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp",
        examples=["2025-11-25T13:00:00"]
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp",
        examples=["2025-11-25T13:00:00"]
    )
    cancelled_at: Optional[datetime] = Field(
        None,
        description="Cancellation timestamp (if cancelled)",
        examples=[None]
    )

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "schedule_id": 123,
                "override_member_id": 5,
                "original_member_name": "Eve Echo",
                "override_member_name": "Alice Alpha",
                "override_date": "2025-11-27T08:00:00",
                "reason": "Vacation - Eve out until Friday",
                "status": "active",
                "created_by": "admin",
                "created_at": "2025-11-25T13:00:00",
                "updated_at": "2025-11-25T13:00:00",
                "cancelled_at": None
            }
        }


class ScheduleOverrideListResponse(BaseModel):
    """
    Response schema for paginated list of overrides.

    Used in audit trail table display with pagination controls.
    """
    overrides: list[ScheduleOverrideResponse] = Field(
        ...,
        description="List of override records"
    )
    pagination: dict = Field(
        ...,
        description="Pagination metadata"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "overrides": [
                    {
                        "id": 1,
                        "schedule_id": 123,
                        "override_member_id": 5,
                        "original_member_name": "Eve Echo",
                        "override_member_name": "Alice Alpha",
                        "override_date": "2025-11-27T08:00:00",
                        "reason": "Vacation",
                        "status": "active",
                        "created_by": "admin",
                        "created_at": "2025-11-25T13:00:00",
                        "updated_at": "2025-11-25T13:00:00",
                        "cancelled_at": None
                    }
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 25,
                    "total": 1,
                    "pages": 1,
                    "has_prev": False,
                    "has_next": False
                }
            }
        }


class ScheduleOverrideCancelRequest(BaseModel):
    """
    Request body for canceling an override.

    Currently no additional fields needed beyond override_id in URL path,
    but included for future extensibility (e.g., cancellation reason).
    """
    pass

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {}
        }

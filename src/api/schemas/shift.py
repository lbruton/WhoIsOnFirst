"""
Shift Pydantic Schemas

Request and response models for shift configuration API endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class ShiftBase(BaseModel):
    """
    Base schema for shift configuration with common fields.
    """
    shift_number: int = Field(
        ...,
        ge=1,
        le=7,
        description="Sequential shift number (1-7 for weekly rotation)",
        examples=[1]
    )
    day_of_week: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Day(s) of week for this shift (e.g., 'Monday' or 'Tuesday-Wednesday')",
        examples=["Monday", "Tuesday-Wednesday"]
    )
    duration_hours: int = Field(
        ...,
        description="Duration of shift in hours (24 or 48)",
        examples=[24, 48]
    )
    start_time: str = Field(
        ...,
        description="Time when shift starts in HH:MM or HH:MM:SS format (24-hour)",
        examples=["08:00", "08:00:00", "20:00"]
    )

    @field_validator('duration_hours')
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """
        Validate shift duration is 24 or 48 hours.

        Args:
            v: Duration in hours

        Returns:
            int: Validated duration

        Raises:
            ValueError: If duration is not 24 or 48
        """
        if v not in [24, 48]:
            raise ValueError('Duration must be either 24 or 48 hours')
        return v

    @field_validator('start_time')
    @classmethod
    def validate_start_time_format(cls, v: str) -> str:
        """
        Validate and normalize start time to HH:MM:SS format.

        Accepts both HH:MM and HH:MM:SS formats.

        Args:
            v: Time string

        Returns:
            str: Normalized time string in HH:MM:SS format

        Raises:
            ValueError: If time format is invalid
        """
        # Match HH:MM or HH:MM:SS
        if re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$', v):
            # Already HH:MM:SS format
            return v
        elif re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', v):
            # HH:MM format - add :00 for seconds
            return f"{v}:00"
        else:
            raise ValueError(
                'Start time must be in HH:MM or HH:MM:SS format (24-hour). '
                'Examples: 08:00 or 08:00:00'
            )


    @field_validator('day_of_week')
    @classmethod
    def validate_day_of_week(cls, v: str) -> str:
        """
        Validate and clean day of week string.

        Args:
            v: Day of week string

        Returns:
            str: Cleaned day of week string

        Raises:
            ValueError: If day string is empty
        """
        v = v.strip()
        if not v:
            raise ValueError('Day of week cannot be empty or whitespace only')
        return v


class ShiftCreate(ShiftBase):
    """
    Schema for creating a new shift configuration.

    All fields from ShiftBase are required.
    """


class ShiftUpdate(BaseModel):
    """
    Schema for updating an existing shift configuration.

    All fields are optional to support partial updates.
    """
    shift_number: Optional[int] = Field(
        None,
        ge=1,
        le=7,
        description="Sequential shift number (1-7 for weekly rotation)",
        examples=[1]
    )
    day_of_week: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Day(s) of week for this shift",
        examples=["Monday"]
    )
    duration_hours: Optional[int] = Field(
        None,
        description="Duration of shift in hours (24 or 48)",
        examples=[24]
    )
    start_time: Optional[str] = Field(
        None,
        description="Time when shift starts in HH:MM or HH:MM:SS format",
        examples=["08:00", "08:00:00"]
    )

    @field_validator('start_time')
    @classmethod
    def validate_start_time_format(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and normalize start time to HH:MM:SS format if provided.

        Accepts both HH:MM and HH:MM:SS formats.

        Args:
            v: Time string or None

        Returns:
            Optional[str]: Normalized time string in HH:MM:SS format or None

        Raises:
            ValueError: If time format is invalid
        """
        if v is None:
            return v

        # Match HH:MM or HH:MM:SS
        if re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$', v):
            # Already HH:MM:SS format
            return v
        elif re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', v):
            # HH:MM format - add :00 for seconds
            return f"{v}:00"
        else:
            raise ValueError(
                'Start time must be in HH:MM or HH:MM:SS format (24-hour). '
                'Examples: 08:00 or 08:00:00'
            )

    @field_validator('duration_hours')
    @classmethod
    def validate_duration(cls, v: Optional[int]) -> Optional[int]:
        """
        Validate shift duration if provided.

        Args:
            v: Duration in hours or None

        Returns:
            Optional[int]: Validated duration or None

        Raises:
            ValueError: If duration is not 24 or 48
        """
        if v is not None and v not in [24, 48]:
            raise ValueError('Duration must be either 24 or 48 hours')
        return v

    @field_validator('day_of_week')
    @classmethod
    def validate_day_of_week(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and clean day of week string if provided.

        Args:
            v: Day of week string or None

        Returns:
            Optional[str]: Cleaned day of week string or None

        Raises:
            ValueError: If day string is empty
        """
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Day of week cannot be empty or whitespace only')
        return v


class ShiftResponse(ShiftBase):
    """
    Schema for shift configuration responses.

    Includes all fields from ShiftBase plus database fields.
    """
    id: int = Field(
        ...,
        description="Unique shift configuration ID",
        examples=[1]
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the shift was created",
        examples=["2025-01-01T00:00:00"]
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "shift_number": 1,
                "day_of_week": "Monday",
                "duration_hours": 24,
                "start_time": "08:00",
                "created_at": "2025-01-01T00:00:00"
            }
        },
    )

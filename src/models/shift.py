"""
Shift model for WhoIsOnFirst.

Represents a shift configuration (e.g., Monday 24h, Tuesday-Wednesday 48h).
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Shift(Base):
    """
    Shift configuration model.

    Defines the structure of on-call shifts (days, duration, start time).

    Attributes:
        id: Primary key
        shift_number: Sequential shift number (1-6 for Mon-Sun pattern)
        day_of_week: Day(s) of week for this shift
        duration_hours: Length of shift in hours (24 or 48)
        start_time: Time when shift starts (default 08:00)
        created_at: Timestamp when shift configuration was created

    Relationships:
        schedules: List of schedule assignments for this shift

    Example:
        Shift 1: Monday, 24 hours, starts 08:00
        Shift 2: Tuesday-Wednesday, 48 hours, starts 08:00
        Shift 5: Saturday, 24 hours, starts 08:00
    """

    __tablename__ = "shifts"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Shift configuration
    shift_number = Column(Integer, unique=True, nullable=False, index=True)
    day_of_week = Column(String, nullable=False)  # e.g., "Monday" or "Tuesday-Wednesday"
    duration_hours = Column(Integer, nullable=False)  # 24 or 48
    start_time = Column(String, nullable=False, default="08:00")  # HH:MM format

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    schedules = relationship(
        "Schedule",
        back_populates="shift",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        """String representation of Shift."""
        return (
            f"<Shift(id={self.id}, shift_number={self.shift_number}, "
            f"day='{self.day_of_week}', duration={self.duration_hours}h)>"
        )

    def __str__(self):
        """Human-readable string representation."""
        return (
            f"Shift {self.shift_number}: {self.day_of_week} "
            f"({self.duration_hours}h starting at {self.start_time})"
        )

    def to_dict(self):
        """
        Convert model to dictionary for API responses.

        Returns:
            Dictionary representation of the shift
        """
        return {
            "id": self.id,
            "shift_number": self.shift_number,
            "day_of_week": self.day_of_week,
            "duration_hours": self.duration_hours,
            "start_time": self.start_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def is_weekend(self) -> bool:
        """
        Check if this shift falls on a weekend day.

        Returns:
            True if Saturday or Sunday, False otherwise
        """
        weekend_keywords = ["saturday", "sunday"]
        return any(
            keyword in self.day_of_week.lower()
            for keyword in weekend_keywords
        )

    @staticmethod
    def validate_duration(duration_hours: int) -> bool:
        """
        Validate shift duration is acceptable.

        Args:
            duration_hours: Duration in hours to validate

        Returns:
            True if valid (24 or 48), False otherwise
        """
        return duration_hours in [24, 48]

    @staticmethod
    def validate_start_time(start_time: str) -> bool:
        """
        Validate start time format is HH:MM.

        Args:
            start_time: Time string to validate

        Returns:
            True if valid format, False otherwise
        """
        import re
        pattern = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
        return bool(re.match(pattern, start_time))

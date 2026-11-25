"""
Schedule model for WhoIsOnFirst.

Represents a specific assignment of a team member to a shift.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from .database import Base


class Schedule(Base):
    """
    Schedule assignment model.

    Links a team member to a specific shift for a specific time period.

    Attributes:
        id: Primary key
        team_member_id: Foreign key to team_members table
        shift_id: Foreign key to shifts table
        week_number: Week number since epoch for tracking rotation
        start_datetime: When this assignment starts (timezone-aware)
        end_datetime: When this assignment ends (timezone-aware)
        notified: Whether SMS notification has been sent
        created_at: Timestamp when assignment was created

    Relationships:
        team_member: The team member assigned to this shift
        shift: The shift configuration for this assignment
        notification_logs: List of notification attempts for this assignment
    """

    __tablename__ = "schedule"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign keys
    team_member_id = Column(
        Integer,
        ForeignKey("team_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    shift_id = Column(
        Integer,
        ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False
    )

    # Schedule tracking
    week_number = Column(Integer, nullable=False, index=True)  # ISO week number
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=False)

    # Notification tracking
    notified = Column(Boolean, default=False, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    team_member = relationship("TeamMember", back_populates="schedules")
    shift = relationship("Shift", back_populates="schedules")
    notification_logs = relationship(
        "NotificationLog",
        back_populates="schedule",
        cascade="all, delete-orphan"
    )
    overrides = relationship(
        "ScheduleOverride",
        back_populates="schedule",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        """String representation of Schedule."""
        return (
            f"<Schedule(id={self.id}, member_id={self.team_member_id}, "
            f"shift_id={self.shift_id}, week={self.week_number}, "
            f"notified={self.notified})>"
        )

    def __str__(self):
        """Human-readable string representation."""
        member_name = self.team_member.name if self.team_member else "Unknown"
        shift_info = f"Shift {self.shift.shift_number}" if self.shift else "Unknown shift"
        start = self.start_datetime.strftime("%Y-%m-%d %H:%M") if self.start_datetime else "Unknown"
        return f"{member_name} - {shift_info} starting {start}"

    def to_dict(self):
        """
        Convert model to dictionary for API responses.

        Returns:
            Dictionary representation of the schedule assignment
        """
        return {
            "id": self.id,
            "team_member_id": self.team_member_id,
            "team_member_name": self.team_member.name if self.team_member else None,
            "shift_id": self.shift_id,
            "shift_number": self.shift.shift_number if self.shift else None,
            "week_number": self.week_number,
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "notified": self.notified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def is_active(self) -> bool:
        """
        Check if this schedule assignment is currently active.

        Returns:
            True if current time is between start and end, False otherwise
        """
        now = datetime.now()
        return self.start_datetime <= now <= self.end_datetime

    @property
    def is_upcoming(self) -> bool:
        """
        Check if this schedule assignment is upcoming (not yet started).

        Returns:
            True if start time is in the future, False otherwise
        """
        now = datetime.now()
        return self.start_datetime > now

    @property
    def is_past(self) -> bool:
        """
        Check if this schedule assignment is in the past.

        Returns:
            True if end time has passed, False otherwise
        """
        now = datetime.now()
        return self.end_datetime < now

    @property
    def needs_notification(self) -> bool:
        """
        Check if this assignment needs notification sent.

        Returns:
            True if not yet notified and start time is close, False otherwise
        """
        if self.notified:
            return False

        now = datetime.now()
        # Check if start time is within notification window (e.g., same day)
        return self.start_datetime.date() == now.date()

    @property
    def team_member_name(self) -> Optional[str]:
        """
        Get the name of the assigned team member.

        Returns:
            Team member name if relationship is loaded, None otherwise
        """
        return self.team_member.name if self.team_member else None

    @property
    def shift_number(self) -> Optional[int]:
        """
        Get the shift number for display.

        Returns:
            Shift number if relationship is loaded, None otherwise
        """
        return self.shift.shift_number if self.shift else None

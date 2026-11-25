"""
Schedule Override model for WhoIsOnFirst.

Represents manual overrides to scheduled shifts for vacation, sick days, swaps.
Overrides layer on top of generated schedules without modifying rotation algorithm.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class ScheduleOverride(Base):
    """
    Manual schedule overrides for vacation, sick days, swaps.

    Overrides layer on top of generated schedules without modifying rotation algorithm.
    When override exists for a date+shift, notification goes to override member.

    Attributes:
        id: Primary key
        schedule_id: Foreign key to schedule table (original assignment)
        override_member_id: Foreign key to team_members (replacement person)
        original_member_name: Snapshot of original assignee name
        override_member_name: Snapshot of override assignee name
        reason: Reason for override (vacation, sick, swap, etc.)
        status: Override status (active, cancelled, completed)
        created_by: Admin username who created the override
        created_at: When override was created
        updated_at: When override was last modified
        cancelled_at: When override was cancelled (if applicable)

    Relationships:
        schedule: The original schedule entry being overridden
        override_member: The team member covering the shift
    """

    __tablename__ = "schedule_overrides"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    schedule_id = Column(
        Integer,
        ForeignKey("schedule.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Original schedule entry being overridden"
    )

    override_member_id = Column(
        Integer,
        ForeignKey("team_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Team member covering the shift"
    )

    # Snapshot Fields (preserve historical accuracy if members change)
    original_member_name = Column(
        String(100),
        nullable=False,
        comment="Original assignee at time of override"
    )
    override_member_name = Column(
        String(100),
        nullable=False,
        comment="Override assignee at time of override"
    )

    # Override Details
    reason = Column(
        Text,
        nullable=True,
        comment="Reason for override (vacation, sick, swap, etc.)"
    )
    status = Column(
        String(20),
        nullable=False,
        default="active",
        index=True,
        comment="active, cancelled, completed"
    )

    # Audit Fields (standard WhoIsOnFirst pattern)
    created_by = Column(
        String(100),
        nullable=False,
        comment="Admin username who created override"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        index=True
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now()
    )
    cancelled_at = Column(
        DateTime,
        nullable=True,
        comment="When override was cancelled (if applicable)"
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="When override was marked completed (schedule date passed)"
    )

    # Relationships
    schedule = relationship("Schedule", back_populates="overrides")
    override_member = relationship("TeamMember", foreign_keys=[override_member_id])

    # Indexes for common queries
    __table_args__ = (
        Index('idx_override_schedule_status', 'schedule_id', 'status'),
        Index('idx_override_date_range', 'created_at'),
    )

    def __repr__(self):
        """String representation of ScheduleOverride."""
        return (
            f"<ScheduleOverride(id={self.id}, schedule_id={self.schedule_id}, "
            f"override_member_id={self.override_member_id}, status='{self.status}')>"
        )

    def __str__(self):
        """Human-readable string representation."""
        return (
            f"{self.override_member_name} covering for {self.original_member_name} "
            f"(Schedule #{self.schedule_id}) - {self.status}"
        )

    def to_dict(self):
        """
        Convert model to dictionary for API responses.

        Returns:
            Dictionary representation of the schedule override
        """
        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "override_member_id": self.override_member_id,
            "original_member_name": self.original_member_name,
            "override_member_name": self.override_member_name,
            "reason": self.reason,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @property
    def is_active(self) -> bool:
        """
        Check if this override is currently active.

        Returns:
            True if status is 'active', False otherwise
        """
        return self.status == "active"

    @property
    def is_cancelled(self) -> bool:
        """
        Check if this override has been cancelled.

        Returns:
            True if status is 'cancelled', False otherwise
        """
        return self.status == "cancelled"

    @property
    def is_completed(self) -> bool:
        """
        Check if this override has been completed.

        Returns:
            True if status is 'completed', False otherwise
        """
        return self.status == "completed"

    @property
    def override_date(self):
        """
        Get the date of the shift being overridden.

        Returns:
            Datetime of the schedule start if relationship is loaded, None otherwise
        """
        return self.schedule.start_datetime if self.schedule else None

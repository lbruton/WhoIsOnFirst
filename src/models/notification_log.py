"""
NotificationLog model for WhoIsOnFirst.

Tracks all SMS notification attempts for audit trail and troubleshooting.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class NotificationLog(Base):
    """
    Notification log model.

    Records all SMS notification attempts with status and error details.
    Snapshots recipient information at send time to preserve historical accuracy.

    Attributes:
        id: Primary key
        schedule_id: Foreign key to schedule table
        sent_at: Timestamp when notification was attempted
        status: Status of notification (sent, failed, pending)
        twilio_sid: Twilio message SID for tracking
        error_message: Error details if notification failed
        recipient_name: Team member name at time of notification (snapshot)
        recipient_phone: Team member phone at time of notification (snapshot)

    Relationships:
        schedule: The schedule assignment this notification is for

    Status Values:
        - 'sent': Successfully sent via Twilio
        - 'failed': Failed to send (temporary or permanent)
        - 'pending': Queued but not yet sent
        - 'delivered': Confirmed delivered by Twilio
        - 'undelivered': Confirmed not delivered by Twilio
    """

    __tablename__ = "notification_log"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key (nullable to preserve audit trail when schedules deleted)
    schedule_id = Column(
        Integer,
        ForeignKey("schedule.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Notification tracking
    sent_at = Column(DateTime, nullable=False, index=True, default=func.now())
    status = Column(String, nullable=False, index=True)  # sent, failed, pending, delivered, undelivered
    twilio_sid = Column(String, nullable=True)  # Twilio message SID
    error_message = Column(Text, nullable=True)  # Error details if failed

    # Recipient snapshot (preserves historical accuracy)
    recipient_name = Column(String(100), nullable=True)  # Name at time of notification
    recipient_phone = Column(String(15), nullable=True)  # Phone at time of notification

    # Relationships
    schedule = relationship("Schedule", back_populates="notification_logs")

    def __repr__(self):
        """String representation of NotificationLog."""
        return (
            f"<NotificationLog(id={self.id}, schedule_id={self.schedule_id}, "
            f"status='{self.status}', sid='{self.twilio_sid}')>"
        )

    def __str__(self):
        """Human-readable string representation."""
        timestamp = self.sent_at.strftime("%Y-%m-%d %H:%M:%S") if self.sent_at else "Unknown"
        return f"Notification {self.id}: {self.status} at {timestamp}"

    def to_dict(self):
        """
        Convert model to dictionary for API responses.

        Returns:
            Dictionary representation of the notification log
        """
        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "twilio_sid": self.twilio_sid,
            "error_message": self.error_message,
            "recipient_name": self.recipient_name,
            "recipient_phone": self.recipient_phone,
        }

    @property
    def is_success(self) -> bool:
        """
        Check if notification was successfully sent.

        Returns:
            True if status is 'sent' or 'delivered', False otherwise
        """
        return self.status in ['sent', 'delivered']

    @property
    def is_failure(self) -> bool:
        """
        Check if notification failed.

        Returns:
            True if status is 'failed' or 'undelivered', False otherwise
        """
        return self.status in ['failed', 'undelivered']

    @property
    def is_pending(self) -> bool:
        """
        Check if notification is still pending.

        Returns:
            True if status is 'pending', False otherwise
        """
        return self.status == 'pending'

    @staticmethod
    def validate_status(status: str) -> bool:
        """
        Validate notification status value.

        Args:
            status: Status string to validate

        Returns:
            True if valid status, False otherwise
        """
        valid_statuses = ['sent', 'failed', 'pending', 'delivered', 'undelivered']
        return status in valid_statuses

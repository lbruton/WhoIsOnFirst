"""
Notification API Schemas

Pydantic models for notification log requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class ManualNotificationRequest(BaseModel):
    """Request schema for sending manual notifications."""

    team_member_id: int = Field(..., description="Team member ID to send notification to", gt=0)
    message: str = Field(
        ...,
        description="SMS message text",
        min_length=1,
        max_length=1600,
        examples=["WhoIsOnFirst Alert\n\nHi {name}, manual test notification."]
    )

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()


class ManualNotificationResponse(BaseModel):
    """Response schema for manual notification send."""

    success: bool = Field(..., description="Whether SMS was sent successfully")
    notification_id: Optional[int] = Field(None, description="Notification log ID")
    twilio_sid: Optional[str] = Field(None, description="Twilio message SID")
    status: str = Field(..., description="Send status (sent, failed)")
    message: str = Field(..., description="Human-readable result message")
    recipient_name: str = Field(..., description="Recipient name")
    recipient_phone: str = Field(..., description="Recipient phone (masked)")
    sent_at: Optional[datetime] = Field(None, description="Timestamp when sent")
    error: Optional[str] = Field(None, description="Error details if failed")


class NotificationLogResponse(BaseModel):
    """Response schema for notification log entries."""

    id: int = Field(..., description="Notification log ID")
    schedule_id: Optional[int] = Field(None, description="Associated schedule ID (may be null if schedule deleted)")
    sent_at: datetime = Field(..., description="Timestamp when notification was sent")
    status: str = Field(..., description="Notification status (sent, failed, delivered, etc.)")
    twilio_sid: Optional[str] = Field(None, description="Twilio message SID")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    recipient_name: Optional[str] = Field(None, description="Recipient name at time of notification (snapshot)")
    recipient_phone: Optional[str] = Field(None, description="Recipient phone at time of notification (snapshot)")

    class Config:
        from_attributes = True


class NotificationStatsResponse(BaseModel):
    """Response schema for notification statistics."""

    total_sent: int = Field(..., description="Total notifications sent in period")
    this_month: int = Field(..., description="Notifications sent this month")
    delivery_rate: float = Field(..., description="Success rate percentage (0-100)")
    failed_count: int = Field(..., description="Number of failed notifications")
    sent_count: int = Field(..., description="Number of sent (not yet delivered)")
    delivered_count: int = Field(..., description="Number of confirmed delivered")
    pending_count: int = Field(..., description="Number still pending")
    period_days: int = Field(..., description="Number of days in the stats period")

    class Config:
        from_attributes = True

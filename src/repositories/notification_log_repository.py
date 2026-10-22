"""
Notification log repository for database operations.

Handles all database operations related to SMS notification tracking,
including logging attempts, tracking failures, and audit queries.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from .base_repository import BaseRepository
from ..models.notification_log import NotificationLog


class NotificationLogRepository(BaseRepository[NotificationLog]):
    """
    Repository for notification log database operations.

    Extends BaseRepository with notification-specific queries:
    - Get by schedule
    - Get by status
    - Get by date range
    - Get failed notifications
    - Track retry attempts

    Attributes:
        db: SQLAlchemy database session
    """

    def __init__(self, db: Session):
        """Initialize NotificationLogRepository."""
        super().__init__(db, NotificationLog)

    def get_by_schedule(self, schedule_id: int) -> List[NotificationLog]:
        """Get all notification logs for a specific schedule assignment."""
        try:
            return (
                self.db.query(self.model)
                .filter(self.model.schedule_id == schedule_id)
                .order_by(self.model.sent_at.desc())
                .all()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting notification logs by schedule: {str(e)}")

    def get_by_status(
        self,
        status: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[NotificationLog]:
        """Get notification logs by status."""
        try:
            query = self.db.query(self.model).filter(self.model.status == status)

            if start_date:
                query = query.filter(self.model.sent_at >= start_date)

            if end_date:
                query = query.filter(self.model.sent_at <= end_date)

            return query.order_by(self.model.sent_at.desc()).all()

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting notification logs by status: {str(e)}")

    def get_failed_notifications(
        self,
        hours_ago: Optional[int] = 24
    ) -> List[NotificationLog]:
        """Get failed notifications within a time window."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_ago)

            return (
                self.db.query(self.model)
                .filter(
                    and_(
                        self.model.status.in_(['failed', 'undelivered']),
                        self.model.sent_at >= cutoff_time
                    )
                )
                .options(joinedload(self.model.schedule))
                .order_by(self.model.sent_at.desc())
                .all()
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting failed notifications: {str(e)}")

    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        include_schedule: bool = True
    ) -> List[NotificationLog]:
        """Get notification logs within a date range."""
        try:
            query = self.db.query(self.model).filter(
                and_(
                    self.model.sent_at >= start_date,
                    self.model.sent_at <= end_date
                )
            )

            if include_schedule:
                query = query.options(joinedload(self.model.schedule))

            return query.order_by(self.model.sent_at.desc()).all()

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting notification logs by date range: {str(e)}")

    def get_by_twilio_sid(self, twilio_sid: str) -> Optional[NotificationLog]:
        """Get notification log by Twilio message SID."""
        try:
            return (
                self.db.query(self.model)
                .filter(self.model.twilio_sid == twilio_sid)
                .first()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting notification log by Twilio SID: {str(e)}")

    def update_status(
        self,
        notification_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[NotificationLog]:
        """Update the status of a notification log."""
        try:
            log = self.get_by_id(notification_id)
            if log:
                log.status = status
                if error_message:
                    log.error_message = error_message
                self.db.commit()
                self.db.refresh(log)
            return log

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error updating notification status: {str(e)}")

    def get_retry_count_for_schedule(self, schedule_id: int) -> int:
        """Get the number of retry attempts for a schedule."""
        try:
            return (
                self.db.query(self.model)
                .filter(self.model.schedule_id == schedule_id)
                .count()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error counting retries: {str(e)}")

    def get_success_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Calculate notification success rate."""
        try:
            query = self.db.query(self.model)

            if start_date:
                query = query.filter(self.model.sent_at >= start_date)

            if end_date:
                query = query.filter(self.model.sent_at <= end_date)

            total = query.count()

            if total == 0:
                return {
                    "total": 0,
                    "sent": 0,
                    "delivered": 0,
                    "failed": 0,
                    "undelivered": 0,
                    "pending": 0,
                    "success_rate": 0.0
                }

            sent_count = query.filter(self.model.status == 'sent').count()
            delivered_count = query.filter(self.model.status == 'delivered').count()
            failed_count = query.filter(self.model.status == 'failed').count()
            undelivered_count = query.filter(self.model.status == 'undelivered').count()
            pending_count = query.filter(self.model.status == 'pending').count()

            success_count = sent_count + delivered_count
            success_rate = (success_count / total) * 100 if total > 0 else 0.0

            return {
                "total": total,
                "sent": sent_count,
                "delivered": delivered_count,
                "failed": failed_count,
                "undelivered": undelivered_count,
                "pending": pending_count,
                "success_rate": round(success_rate, 2)
            }

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error calculating success rate: {str(e)}")

    def get_recent_logs(
        self,
        limit: int = 25,
        offset: int = 0,
        include_schedule: bool = True
    ) -> List[NotificationLog]:
        """Get most recent notification logs with pagination support."""
        try:
            query = self.db.query(self.model)

            if include_schedule:
                query = query.options(joinedload(self.model.schedule))

            return (
                query
                .order_by(self.model.sent_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting recent logs: {str(e)}")

    def count_all(self) -> int:
        """Get total count of all notification logs for pagination."""
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error counting notification logs: {str(e)}")

    def log_notification_attempt(
        self,
        schedule_id: int,
        status: str,
        twilio_sid: Optional[str] = None,
        error_message: Optional[str] = None,
        recipient_name: Optional[str] = None,
        recipient_phone: Optional[str] = None
    ) -> NotificationLog:
        """Log a send attempt; recipient name and phone are copied at send time for history."""
        try:
            log_data = {
                "schedule_id": schedule_id,
                "status": status,
                "sent_at": datetime.now(),
                "twilio_sid": twilio_sid,
                "error_message": error_message,
                "recipient_name": recipient_name,
                "recipient_phone": recipient_phone
            }

            return self.create(log_data)

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error logging notification attempt: {str(e)}")

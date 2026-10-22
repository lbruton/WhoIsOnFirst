"""
Schedule repository for database operations.

Handles all database operations related to schedule assignments,
including date range queries, notification tracking, and week-based lookups.
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from .base_repository import BaseRepository
from ..models.schedule import Schedule


class ScheduleRepository(BaseRepository[Schedule]):
    """
    Repository for schedule assignment database operations.

    Extends BaseRepository with schedule-specific queries:
    - Get by date ranges
    - Get by team member
    - Get by week number
    - Get pending notifications
    - Get current and upcoming assignments

    Attributes:
        db: SQLAlchemy database session
    """

    def __init__(self, db: Session):
        """Initialize ScheduleRepository."""
        super().__init__(db, Schedule)

    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        include_relationships: bool = True
    ) -> List[Schedule]:
        """Get all schedule assignments within a date range."""
        try:
            # Convert timezone-aware datetimes to naive for SQLite comparison
            start_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
            end_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date

            query = self.db.query(self.model).filter(
                and_(
                    self.model.start_datetime >= start_naive,
                    self.model.start_datetime <= end_naive
                )
            )

            if include_relationships:
                query = query.options(
                    joinedload(self.model.team_member),
                    joinedload(self.model.shift)
                )

            return query.order_by(self.model.start_datetime).all()

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting schedules by date range: {str(e)}")

    def get_by_team_member(
        self,
        team_member_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Schedule]:
        """Get all schedule assignments for a specific team member."""
        try:
            query = self.db.query(self.model).filter(
                self.model.team_member_id == team_member_id
            )

            if start_date:
                # Convert timezone-aware datetime to naive for SQLite comparison
                start_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
                query = query.filter(self.model.start_datetime >= start_naive)

            if end_date:
                # Convert timezone-aware datetime to naive for SQLite comparison
                end_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
                query = query.filter(self.model.start_datetime <= end_naive)

            return query.options(
                joinedload(self.model.shift)
            ).order_by(self.model.start_datetime).all()

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting schedules by team member: {str(e)}")

    def get_by_week_number(self, week_number: int) -> List[Schedule]:
        """Get all schedule assignments for a specific week."""
        try:
            return (
                self.db.query(self.model)
                .filter(self.model.week_number == week_number)
                .options(
                    joinedload(self.model.team_member),
                    joinedload(self.model.shift)
                )
                .order_by(self.model.start_datetime)
                .all()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting schedules by week number: {str(e)}")

    def get_current_week(self) -> List[Schedule]:
        """Get schedule assignments for the current week."""
        now = datetime.now()
        current_week = now.isocalendar()[1]
        return self.get_by_week_number(current_week)

    def get_upcoming_weeks(self, num_weeks: int = 4) -> List[Schedule]:
        """Get schedule assignments for upcoming weeks."""
        try:
            # Normalize to start of day to include all schedules starting today
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(weeks=num_weeks)

            return self.get_by_date_range(start_date, end_date)

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting upcoming weeks: {str(e)}")

    def get_pending_notifications(self, target_date: Optional[date] = None, force: bool = False) -> List[Schedule]:
        """Get schedule assignments that need notifications sent."""
        try:
            if target_date is None:
                target_date = datetime.now().date()

            # Get schedules starting on target_date
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())

            # Build filter conditions
            conditions = [
                self.model.start_datetime >= start_datetime,
                self.model.start_datetime <= end_datetime
            ]

            # Only filter by notified=False if force is False
            if not force:
                conditions.append(self.model.notified.is_(False))

            return (
                self.db.query(self.model)
                .filter(and_(*conditions))
                .options(
                    joinedload(self.model.team_member),
                    joinedload(self.model.shift)
                )
                .order_by(self.model.start_datetime)
                .all()
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting pending notifications: {str(e)}")

    def mark_as_notified(self, schedule_id: int) -> Optional[Schedule]:
        """Mark a schedule assignment as notified."""
        try:
            schedule = self.get_by_id(schedule_id)
            if schedule:
                schedule.notified = True
                self.db.commit()
                self.db.refresh(schedule)
            return schedule

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error marking schedule as notified: {str(e)}")

    def get_active_assignments(self) -> List[Schedule]:
        """Get currently active schedule assignments."""
        try:
            now = datetime.now()

            return (
                self.db.query(self.model)
                .filter(
                    and_(
                        self.model.start_datetime <= now,
                        self.model.end_datetime >= now
                    )
                )
                .options(
                    joinedload(self.model.team_member),
                    joinedload(self.model.shift)
                )
                .order_by(self.model.start_datetime)
                .all()
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting active assignments: {str(e)}")

    def get_by_shift(
        self,
        shift_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Schedule]:
        """Get all schedule assignments for a specific shift."""
        try:
            query = self.db.query(self.model).filter(
                self.model.shift_id == shift_id
            )

            if start_date:
                query = query.filter(self.model.start_datetime >= start_date)

            if end_date:
                query = query.filter(self.model.start_datetime <= end_date)

            return query.options(
                joinedload(self.model.team_member)
            ).order_by(self.model.start_datetime).all()

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting schedules by shift: {str(e)}")

    def delete_future_schedules(self, from_date: datetime) -> int:
        """Delete schedule assignments from a date forward and return the count deleted."""
        try:
            # Convert timezone-aware datetime to naive for SQLite comparison
            from_date_naive = from_date.replace(tzinfo=None) if from_date.tzinfo else from_date

            deleted_count = (
                self.db.query(self.model)
                .filter(self.model.start_datetime >= from_date_naive)
                .delete()
            )
            self.db.commit()
            return deleted_count

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error deleting future schedules: {str(e)}")

    def get_next_assignment_for_member(self, team_member_id: int) -> Optional[Schedule]:
        """Get the next upcoming assignment for a team member."""
        try:
            now = datetime.now()

            return (
                self.db.query(self.model)
                .filter(
                    and_(
                        self.model.team_member_id == team_member_id,
                        self.model.start_datetime > now
                    )
                )
                .options(joinedload(self.model.shift))
                .order_by(self.model.start_datetime)
                .first()
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting next assignment: {str(e)}")

    def bulk_create(self, schedules_data: List[dict]) -> List[Schedule]:
        """Create multiple schedule assignments in a single transaction."""
        try:
            schedules = [self.model(**data) for data in schedules_data]

            # Use add_all instead of bulk_save_objects to keep objects in session
            self.db.add_all(schedules)
            self.db.commit()

            # Refresh to get IDs and load relationships
            for schedule in schedules:
                self.db.refresh(schedule)

            return schedules

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error bulk creating schedules: {str(e)}")

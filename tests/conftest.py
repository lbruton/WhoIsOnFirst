"""
Pytest configuration and shared fixtures for WhoIsOnFirst tests.

This module provides reusable fixtures for database setup, test data,
and repository instances.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pytz

from src.models.database import Base
from src.models import TeamMember, Shift, Schedule, NotificationLog
from src.repositories import (
    TeamMemberRepository,
    ShiftRepository,
    ScheduleRepository,
    NotificationLogRepository
)


# Database Configuration
# ----------------------

@pytest.fixture(scope="function")
def test_db_engine():
    """
    Create an in-memory SQLite database engine for testing.

    Scope: function - New database for each test
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """
    Create a database session for testing.

    Uses a nested transaction (savepoint) to automatically roll back
    after each test, even if the code under test calls commit().

    Scope: function - New session for each test
    """
    from sqlalchemy import event

    connection = test_db_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection
    )

    session = SessionLocal()

    # Begin a nested transaction (savepoint)
    nested = connection.begin_nested()

    # Each time the session is committed, restart the savepoint
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        """Restart the savepoint after each commit."""
        if transaction.nested and not transaction._parent.nested:
            # Reopen the savepoint
            session.begin_nested()

    yield session

    # Rollback the outer transaction to undo all changes
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def db_session(test_db_session):
    """
    Alias for test_db_session for service layer tests.

    Provides consistent naming across repository and service tests.
    """
    return test_db_session


# Repository Fixtures
# ------------------

@pytest.fixture
def team_member_repo(test_db_session):
    """TeamMemberRepository instance with test database."""
    return TeamMemberRepository(test_db_session)


@pytest.fixture
def shift_repo(test_db_session):
    """ShiftRepository instance with test database."""
    return ShiftRepository(test_db_session)


@pytest.fixture
def schedule_repo(test_db_session):
    """ScheduleRepository instance with test database."""
    return ScheduleRepository(test_db_session)


@pytest.fixture
def notification_log_repo(test_db_session):
    """NotificationLogRepository instance with test database."""
    return NotificationLogRepository(test_db_session)


# Test Data Factories
# -------------------

@pytest.fixture
def sample_team_member_data():
    """Sample team member data for testing."""
    return {
        "name": "John Doe",
        "phone": "+15551234567",
        "is_active": True
    }


@pytest.fixture
def sample_shift_data():
    """Sample shift data for testing."""
    return {
        "shift_number": 1,
        "day_of_week": "Monday",
        "duration_hours": 24,
        "start_time": "08:00:00"
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data factory (requires IDs to be filled in)."""
    def _make_schedule_data(team_member_id: int, shift_id: int, week_number: int = 1):
        chicago_tz = pytz.timezone('America/Chicago')
        start = datetime.now(chicago_tz)
        return {
            "team_member_id": team_member_id,
            "shift_id": shift_id,
            "week_number": week_number,
            "start_datetime": start,
            "end_datetime": start + timedelta(hours=24),
            "notified": False
        }
    return _make_schedule_data


@pytest.fixture
def sample_notification_log_data():
    """Sample notification log data factory (requires schedule_id to be filled in)."""
    def _make_notification_data(schedule_id: int, status: str = "sent"):
        return {
            "schedule_id": schedule_id,
            "sent_at": datetime.now(),
            "status": status,
            "twilio_sid": "SM1234567890abcdef1234567890abcdef",
            "error_message": None if status == "sent" else "Test error"
        }
    return _make_notification_data


# Pre-populated Test Data
# -----------------------

@pytest.fixture
def populated_team_members(team_member_repo):
    """Create and return multiple team members in database."""
    members_data = [
        {"name": "Alice Smith", "phone": "+15551111111", "is_active": True},
        {"name": "Bob Johnson", "phone": "+15552222222", "is_active": True},
        {"name": "Charlie Brown", "phone": "+15553333333", "is_active": True},
        {"name": "Diana Prince", "phone": "+15554444444", "is_active": False},
        {"name": "Eve Adams", "phone": "+15555555555", "is_active": True},
    ]

    members = [team_member_repo.create(data) for data in members_data]
    return members


@pytest.fixture
def populated_shifts(shift_repo):
    """Create and return standard 6-day shift pattern."""
    shifts_data = [
        {"shift_number": 1, "day_of_week": "Monday", "duration_hours": 24, "start_time": "08:00:00"},
        {"shift_number": 2, "day_of_week": "Tuesday-Wednesday", "duration_hours": 48, "start_time": "08:00:00"},
        {"shift_number": 3, "day_of_week": "Thursday", "duration_hours": 24, "start_time": "08:00:00"},
        {"shift_number": 4, "day_of_week": "Friday", "duration_hours": 24, "start_time": "08:00:00"},
        {"shift_number": 5, "day_of_week": "Saturday", "duration_hours": 24, "start_time": "08:00:00"},
        {"shift_number": 6, "day_of_week": "Sunday", "duration_hours": 24, "start_time": "08:00:00"},
    ]

    shifts = [shift_repo.create(data) for data in shifts_data]
    return shifts


@pytest.fixture
def populated_schedules(schedule_repo, populated_team_members, populated_shifts):
    """Create and return sample schedules for current week."""
    chicago_tz = pytz.timezone('America/Chicago')
    base_date = datetime.now(chicago_tz)
    current_week = base_date.isocalendar()[1]

    schedules_data = []
    for i, (member, shift) in enumerate(zip(populated_team_members[:5], populated_shifts[:5])):
        start = base_date + timedelta(days=i)
        schedules_data.append({
            "team_member_id": member.id,
            "shift_id": shift.id,
            "week_number": current_week,
            "start_datetime": start,
            "end_datetime": start + timedelta(hours=shift.duration_hours),
            "notified": i % 2 == 0  # Alternate notified status
        })

    schedules = [schedule_repo.create(data) for data in schedules_data]
    return schedules


# Utility Fixtures
# ---------------

@pytest.fixture
def chicago_tz():
    """Return Chicago timezone for datetime operations."""
    return pytz.timezone('America/Chicago')


@pytest.fixture
def current_week_number():
    """Return current ISO week number."""
    return datetime.now().isocalendar()[1]

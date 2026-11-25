"""
SQLAlchemy models for WhoIsOnFirst.

This module exports all database models and configuration.
"""

from .database import Base, engine, SessionLocal, get_db, init_db, drop_db
from .team_member import TeamMember
from .shift import Shift
from .schedule import Schedule
from .schedule_override import ScheduleOverride
from .notification_log import NotificationLog
from .user import User, UserRole
from .settings import Settings

# Export all models and database utilities
__all__ = [
    # Database configuration
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "drop_db",
    # Models
    "TeamMember",
    "Shift",
    "Schedule",
    "ScheduleOverride",
    "NotificationLog",
    "User",
    "UserRole",
    "Settings",
]

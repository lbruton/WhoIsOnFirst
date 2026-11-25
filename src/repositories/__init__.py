"""
Repository layer for WhoIsOnFirst.

This module exports all repository classes for data access operations.
Repositories implement the Repository Pattern to abstract database operations.

Usage:
    from src.repositories import TeamMemberRepository, ScheduleRepository
    from src.models import get_db

    db = next(get_db())
    team_repo = TeamMemberRepository(db)
    active_members = team_repo.get_active()
"""

from .base_repository import BaseRepository
from .team_member_repository import TeamMemberRepository
from .shift_repository import ShiftRepository
from .schedule_repository import ScheduleRepository
from .notification_log_repository import NotificationLogRepository
from .user_repository import UserRepository
from .schedule_override_repository import ScheduleOverrideRepository

# Export all repositories
__all__ = [
    "BaseRepository",
    "TeamMemberRepository",
    "ShiftRepository",
    "ScheduleRepository",
    "NotificationLogRepository",
    "UserRepository",
    "ScheduleOverrideRepository",
]

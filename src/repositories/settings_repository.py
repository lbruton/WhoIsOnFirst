"""
Settings repository for database operations.

Handles all database operations related to application settings.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .base_repository import BaseRepository
from ..models.settings import Settings


class SettingsRepository(BaseRepository[Settings]):
    """
    Repository for settings database operations.

    Extends BaseRepository with settings-specific queries.

    Attributes:
        db: SQLAlchemy database session
    """

    def __init__(self, db: Session):
        """Initialize SettingsRepository."""
        super().__init__(db, Settings)

    def get_by_key(self, key: str) -> Optional[Settings]:
        """Get a setting by its key."""
        try:
            return self.db.query(self.model).filter(self.model.key == key).first()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting setting by key: {str(e)}")

    def set_value(self, key: str, value: str, value_type: str = "str", description: str = None) -> Settings:
        """Set a setting value (create or update)."""
        try:
            setting = self.get_by_key(key)

            if setting:
                # Update existing setting
                setting.value = value
                setting.value_type = value_type
                if description:
                    setting.description = description
            else:
                # Create new setting
                setting = self.model(
                    key=key,
                    value=value,
                    value_type=value_type,
                    description=description
                )
                self.db.add(setting)

            self.db.commit()
            self.db.refresh(setting)
            return setting

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error setting value: {str(e)}")

    def get_value(self, key: str, default: any = None) -> any:
        """Get a typed setting value with optional default."""
        try:
            setting = self.get_by_key(key)
            if setting:
                return setting.get_typed_value()
            return default

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting value: {str(e)}")

    def delete_by_key(self, key: str) -> bool:
        """Delete a setting by key."""
        try:
            setting = self.get_by_key(key)
            if setting:
                self.db.delete(setting)
                self.db.commit()
                return True
            return False

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error deleting setting: {str(e)}")

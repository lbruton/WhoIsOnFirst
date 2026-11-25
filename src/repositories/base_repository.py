"""
Base repository with common CRUD operations.

Provides generic database operations that can be inherited by specific repositories.
"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Generic type for model classes
ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.

    Provides standard database operations that can be used by all repositories.
    Handles database session management and error handling.

    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages

    Attributes:
        db: SQLAlchemy database session
        model: The model class this repository operates on
    """

    def __init__(self, db: Session, model: Type[ModelType]):
        """Initialize repository with database session and model."""
        self.db = db
        self.model = model

    def get_by_id(self, item_id: int) -> Optional[ModelType]:
        """Retrieve a single record by ID."""
        try:
            return self.db.query(self.model).filter(self.model.id == item_id).first()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting {self.model.__name__} by id: {str(e)}")

    def get_all(self, skip: int = 0, limit: Optional[int] = None) -> List[ModelType]:
        """Retrieve all records with optional pagination."""
        try:
            query = self.db.query(self.model).offset(skip)
            if limit is not None:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting all {self.model.__name__}: {str(e)}")

    def create(self, data: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        try:
            instance = self.model(**data)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error creating {self.model.__name__}: {str(e)}")

    def update(self, item_id: int, data: Dict[str, Any]) -> Optional[ModelType]:
        """Update an existing record."""
        try:
            instance = self.get_by_id(item_id)
            if instance:
                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                self.db.commit()
                self.db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error updating {self.model.__name__}: {str(e)}")

    def delete(self, item_id: int) -> bool:
        """Delete a record by ID."""
        try:
            instance = self.get_by_id(item_id)
            if instance:
                self.db.delete(instance)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error deleting {self.model.__name__}: {str(e)}")

    def count(self) -> int:
        """Count total number of records."""
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error counting {self.model.__name__}: {str(e)}")

    def exists(self, item_id: int) -> bool:
        """Check if a record exists by ID."""
        try:
            return self.db.query(self.model).filter(self.model.id == item_id).count() > 0
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error checking existence of {self.model.__name__}: {str(e)}")

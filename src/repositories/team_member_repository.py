"""
Team member repository for database operations.

Handles all database operations related to team members,
including phone validation and active member queries.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .base_repository import BaseRepository
from ..models.team_member import TeamMember


class TeamMemberRepository(BaseRepository[TeamMember]):
    """
    Repository for team member database operations.

    Extends BaseRepository with team member-specific queries:
    - Get active members
    - Get by phone number
    - Check phone uniqueness
    - Deactivate/activate members

    Attributes:
        db: SQLAlchemy database session
    """

    def __init__(self, db: Session):
        """Initialize TeamMemberRepository."""
        super().__init__(db, TeamMember)

    def get_active(self) -> List[TeamMember]:
        """Get all active team members."""
        try:
            return (
                self.db.query(self.model)
                .filter(self.model.is_active.is_(True))
                .order_by(self.model.name)
                .all()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting active team members: {str(e)}")

    def get_digest_recipients(self) -> List[TeamMember]:
        """Get active team members opted into the Monday weekly digest."""
        try:
            return (
                self.db.query(self.model)
                .filter(
                    self.model.is_active.is_(True),
                    self.model.weekly_digest_optin.is_(True)
                )
                .order_by(self.model.name)
                .all()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting digest recipients: {str(e)}")

    def get_inactive(self) -> List[TeamMember]:
        """Get all inactive team members."""
        try:
            return (
                self.db.query(self.model)
                .filter(self.model.is_active.is_(False))
                .order_by(self.model.name)
                .all()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting inactive team members: {str(e)}")

    def get_by_phone(self, phone: str) -> Optional[TeamMember]:
        """Get team member by phone number."""
        try:
            return (
                self.db.query(self.model)
                .filter(self.model.phone == phone)
                .first()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting team member by phone: {str(e)}")

    def phone_exists(self, phone: str, exclude_id: Optional[int] = None) -> bool:
        """Check if phone number already exists in database."""
        try:
            query = self.db.query(self.model).filter(self.model.phone == phone)

            if exclude_id is not None:
                query = query.filter(self.model.id != exclude_id)

            return query.count() > 0
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error checking phone existence: {str(e)}")

    def deactivate(self, member_id: int) -> Optional[TeamMember]:
        """Soft-delete a team member (is_active False) so schedule history keeps the row."""
        try:
            member = self.get_by_id(member_id)
            if member:
                member.is_active = False
                self.db.commit()
                self.db.refresh(member)
            return member
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error deactivating team member: {str(e)}")

    def activate(self, member_id: int) -> Optional[TeamMember]:
        """Activate a team member, which returns them to the rotation."""
        try:
            member = self.get_by_id(member_id)
            if member:
                member.is_active = True
                self.db.commit()
                self.db.refresh(member)
            return member
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error activating team member: {str(e)}")

    def get_count_active(self) -> int:
        """Get count of active team members."""
        try:
            return (
                self.db.query(self.model)
                .filter(self.model.is_active.is_(True))
                .count()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error counting active team members: {str(e)}")

    def search_by_name(self, name_query: str) -> List[TeamMember]:
        """Search team members by name (case-insensitive partial match)."""
        try:
            search_term = f"%{name_query}%"
            return (
                self.db.query(self.model)
                .filter(self.model.name.ilike(search_term))
                .order_by(self.model.name)
                .all()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error searching team members by name: {str(e)}")

    def get_max_rotation_order(self) -> int:
        """Get the maximum rotation_order value."""
        try:
            max_order = (
                self.db.query(self.model.rotation_order)
                .filter(self.model.rotation_order.isnot(None))
                .order_by(self.model.rotation_order.desc())
                .first()
            )
            return max_order[0] if max_order and max_order[0] is not None else 0
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting max rotation order: {str(e)}")

    def update_rotation_orders(self, order_mapping: dict) -> List[TeamMember]:
        """Update rotation_order for multiple team members."""
        try:
            updated_members = []
            for member_id, new_order in order_mapping.items():
                member = self.get_by_id(member_id)
                if member:
                    member.rotation_order = new_order
                    updated_members.append(member)

            self.db.commit()

            # Refresh all updated members
            for member in updated_members:
                self.db.refresh(member)

            return updated_members
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error updating rotation orders: {str(e)}")

    def get_ordered_for_rotation(self, active_only: bool = True) -> List[TeamMember]:
        """Get members by rotation_order (nulls last), then ID, so the order is stable when some are unset."""
        try:
            query = self.db.query(self.model)

            if active_only:
                query = query.filter(self.model.is_active.is_(True))

            # Order by rotation_order (nulls last), then by ID as fallback
            return query.order_by(
                self.model.rotation_order.nullslast(),
                self.model.id
            ).all()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error getting ordered team members: {str(e)}")

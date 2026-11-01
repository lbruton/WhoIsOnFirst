"""
Schedule Override API Routes

FastAPI router for manual schedule override management.
Admin-only endpoints for creating, listing, and canceling overrides.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import math

from src.api.dependencies import get_db
from src.api.routes.auth import require_admin, require_auth
from src.api.schemas.schedule_override import (
    ScheduleOverrideRequest,
    ScheduleOverrideResponse,
    ScheduleOverrideListResponse
)
from src.services.schedule_override_service import ScheduleOverrideService
from src.scheduler import trigger_override_completion_manually


router = APIRouter()


@router.post("/", response_model=ScheduleOverrideResponse, status_code=status.HTTP_201_CREATED)
def create_override(
    request: ScheduleOverrideRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Create schedule override (admin-only).

    Allows admin to manually override a schedule assignment for vacation,
    sick days, shift swaps, or emergency coverage. Override does not affect
    the rotation algorithm.

    Validations:
    - Schedule must exist
    - Override member must exist
    - No duplicate active override for same schedule
    - Override member must be different from original assignee

    Args:
        request: Override creation request
        db: Database session (injected)
        current_user: Current admin user (injected)

    Returns:
        Created override with snapshot data

    Raises:
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not admin

    Example:
        POST /api/v1/schedule-overrides/
        {
            "schedule_id": 123,
            "override_member_id": 5,
            "reason": "Vacation - covering for Carol"
        }
    """
    service = ScheduleOverrideService(db)

    try:
        override = service.create_override(
            schedule_id=request.schedule_id,
            override_member_id=request.override_member_id,
            reason=request.reason,
            created_by=current_user.username
        )
        return override
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=ScheduleOverrideListResponse)
def list_overrides(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=10, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, cancelled, completed"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth)
):
    """
    List all overrides with pagination (authenticated users).

    Returns paginated list of schedule overrides with metadata.
    Used for audit trail table display.
    Available to all authenticated users (admin and viewer).

    Args:
        page: Page number (1-indexed, default 1)
        per_page: Items per page (10-100, default 25)
        status_filter: Optional status filter (active, cancelled, completed)
        db: Database session (injected)
        current_user: Current authenticated user (injected)

    Returns:
        Paginated list of overrides with metadata

    Raises:
        401 Unauthorized: If not authenticated

    Example:
        GET /api/v1/schedule-overrides/?page=1&per_page=25&status_filter=active
    """
    service = ScheduleOverrideService(db)
    overrides, pagination = service.get_paginated_overrides(
        page=page,
        per_page=per_page,
        status=status_filter
    )

    return {
        "overrides": overrides,
        "pagination": pagination
    }


@router.get("/active", response_model=List[ScheduleOverrideResponse])
def get_display_overrides(
    db: Session = Depends(get_db),
    current_user = Depends(require_auth)
):
    """
    Get overrides for dashboard display (authenticated users).

    Returns both active and completed overrides (excludes cancelled).
    Used by dashboard to check for overrides when rendering calendar.
    Completed overrides are included for historical accuracy.
    Available to all authenticated users (admin and viewer).

    Args:
        db: Database session (injected)
        current_user: Current authenticated user (injected)

    Returns:
        List of overrides for display (active + completed)

    Raises:
        401 Unauthorized: If not authenticated

    Example:
        GET /api/v1/schedule-overrides/active
    """
    service = ScheduleOverrideService(db)
    return service.override_repo.get_display_overrides()


@router.get("/{override_id}", response_model=ScheduleOverrideResponse)
def get_override(
    override_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth)
):
    """
    Get single override by ID (authenticated users).

    Retrieves detailed information about a specific override.
    Available to all authenticated users (admin and viewer).

    Args:
        override_id: Override ID to retrieve
        db: Database session (injected)
        current_user: Current authenticated user (injected)

    Returns:
        Override details

    Raises:
        401 Unauthorized: If not authenticated
        404 Not Found: If override doesn't exist

    Example:
        GET /api/v1/schedule-overrides/42
    """
    service = ScheduleOverrideService(db)
    override = service.get_override_by_id(override_id)

    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Override not found: {override_id}"
        )

    return override


@router.delete("/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_override(
    override_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Cancel override (admin-only).

    Soft delete: Sets status='cancelled' and records cancelled_at timestamp.
    Does not physically delete the override from database.

    Args:
        override_id: Override ID to cancel
        db: Database session (injected)
        current_user: Current admin user (injected)

    Returns:
        No content (204)

    Raises:
        401 Unauthorized: If not authenticated
        403 Forbidden: If not admin
        404 Not Found: If override doesn't exist

    Example:
        DELETE /api/v1/schedule-overrides/42
    """
    service = ScheduleOverrideService(db)
    override = service.cancel_override(override_id)

    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Override not found: {override_id}"
        )

    return None  # 204 No Content


@router.post("/complete-past", status_code=status.HTTP_200_OK)
def complete_past_overrides(
    current_user = Depends(require_admin)
):
    """
    Manually trigger past override completion (admin-only).

    Finds all active overrides where the schedule's end_datetime has passed
    and transitions them from 'active' to 'completed' status.

    This job normally runs automatically at 8:05 AM CST daily.
    This endpoint allows manual triggering for testing or immediate cleanup.

    Args:
        current_user: Current admin user (injected)

    Returns:
        dict: Result with completed count and status
            - status: 'success' or 'error'
            - message: Human-readable result
            - timestamp: ISO timestamp of execution
            - completed_count: Number of overrides transitioned to completed

    Raises:
        401 Unauthorized: If not authenticated
        403 Forbidden: If not admin
        500 Internal Server Error: If completion fails

    Example:
        POST /api/v1/schedule-overrides/complete-past
        Response:
        {
            "status": "success",
            "message": "Override completion processed.",
            "timestamp": "2024-12-02T14:30:00-06:00",
            "completed_count": 4
        }
    """
    result = trigger_override_completion_manually()

    if result['status'] == 'error':
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result['message']
        )

    return result

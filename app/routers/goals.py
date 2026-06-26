"""Goals API — CRUD + milestones."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional
from datetime import date
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.goal import Goal, Milestone, GoalCategory, GoalStatus
from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalResponse, GoalListResponse,
    MilestoneCreate, MilestoneUpdate, MilestoneResponse,
)
from app.core.dependencies import get_current_user
from loguru import logger
from app.services.gamification_service import GamificationService
from app.config import settings


router = APIRouter()


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED, summary="Create goal")
async def create_goal(
    data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_goal = Goal(user_id=current_user.id, **data.model_dump())
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    logger.info(f"🎯 Goal created: '{new_goal.title}' by user {current_user.id}")
    return new_goal


@router.get("/", response_model=GoalListResponse, summary="List goals")
async def list_goals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[GoalCategory] = Query(None),
    status_filter: Optional[GoalStatus] = Query(None, alias="status"),
    is_favorite: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Goal).options(joinedload(Goal.milestones)).filter(
        Goal.user_id == current_user.id
    )

    if category:
        query = query.filter(Goal.category == category)
    if status_filter:
        query = query.filter(Goal.status == status_filter)
    if is_favorite is not None:
        query = query.filter(Goal.is_favorite == is_favorite)
    if is_archived is not None:
        query = query.filter(Goal.is_archived == is_archived)

    query = query.order_by(desc(Goal.created_at))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return GoalListResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("/{goal_id}", response_model=GoalResponse, summary="Get goal")
async def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = db.query(Goal).options(joinedload(Goal.milestones)).filter(
        Goal.id == goal_id, Goal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.put("/{goal_id}", response_model=GoalResponse, summary="Update goal")
async def update_goal(
    goal_id: int,
    data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id, Goal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    if update_data.get("status") == GoalStatus.COMPLETED and not goal.completed_at:
        goal.completed_at = date.today()
            # 🎮 GAMIFICATION on goal completion
    if update_data.get("status") == GoalStatus.COMPLETED and not goal.completed_at:
        goal.completed_at = date.today()
        goal.progress = 100
    
        service = GamificationService(db, current_user)
        service.award_xp(settings.XP_GOAL_COMPLETE, f"Completed goal: {goal.title}")
        service.check_achievements()

    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete goal")
async def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id, Goal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return None


# ── Milestones ──

@router.post("/{goal_id}/milestones", response_model=MilestoneResponse, status_code=201, summary="Add milestone")
async def add_milestone(
    goal_id: int,
    data: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id, Goal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    milestone = Milestone(goal_id=goal_id, **data.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.put("/{goal_id}/milestones/{milestone_id}", response_model=MilestoneResponse, summary="Update milestone")
async def update_milestone(
    goal_id: int,
    milestone_id: int,
    data: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id, Goal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    milestone = db.query(Milestone).filter(
        Milestone.id == milestone_id, Milestone.goal_id == goal_id
    ).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)

    if update_data.get("is_completed") and not milestone.completed_at:
        milestone.completed_at = date.today()
    elif update_data.get("is_completed") is False:
        milestone.completed_at = None

    db.commit()
    db.refresh(milestone)

    # Auto-update goal progress based on milestones
    total_milestones = db.query(Milestone).filter(Milestone.goal_id == goal_id).count()
    completed_milestones = db.query(Milestone).filter(
        Milestone.goal_id == goal_id, Milestone.is_completed == True
    ).count()
    if total_milestones > 0:
        goal.progress = int((completed_milestones / total_milestones) * 100)
        db.commit()

    return milestone


@router.delete("/{goal_id}/milestones/{milestone_id}", status_code=204, summary="Delete milestone")
async def delete_milestone(
    goal_id: int,
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id, Goal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    milestone = db.query(Milestone).filter(
        Milestone.id == milestone_id, Milestone.goal_id == goal_id
    ).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    db.delete(milestone)
    db.commit()
    return None
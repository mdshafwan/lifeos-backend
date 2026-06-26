"""Habits API — CRUD + complete + streak tracking."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_
from typing import Optional, List
from datetime import date, timedelta
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.habit import Habit, HabitCompletion, HabitCategory
from app.schemas.habit import (
    HabitCreate, HabitUpdate, HabitResponse, HabitListResponse,
    HabitCompletionCreate, HabitCompletionResponse,
)
from app.core.dependencies import get_current_user
from loguru import logger

from app.services.gamification_service import GamificationService
from app.config import settings

router = APIRouter()


def calculate_streak(db: Session, habit_id: int) -> tuple[int, int]:
    """Calculate current and longest streak for a habit."""
    completions = db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit_id
    ).order_by(desc(HabitCompletion.completion_date)).all()

    if not completions:
        return 0, 0

    # Get unique dates
    dates = sorted(set(c.completion_date for c in completions), reverse=True)

    # Current streak (must include today or yesterday)
    current_streak = 0
    today = date.today()
    yesterday = today - timedelta(days=1)

    if dates[0] == today or dates[0] == yesterday:
        current_streak = 1
        for i in range(1, len(dates)):
            if (dates[i-1] - dates[i]).days == 1:
                current_streak += 1
            else:
                break

    # Longest streak
    longest_streak = 1
    temp_streak = 1
    for i in range(1, len(dates)):
        if (dates[i-1] - dates[i]).days == 1:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1

    return current_streak, longest_streak


@router.post("/", response_model=HabitResponse, status_code=status.HTTP_201_CREATED, summary="Create habit")
async def create_habit(
    data: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_habit = Habit(user_id=current_user.id, **data.model_dump())
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    logger.info(f"💪 Habit created: '{new_habit.name}' by user {current_user.id}")
    return new_habit


@router.get("/", response_model=HabitListResponse, summary="List habits")
async def list_habits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[HabitCategory] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Habit).filter(Habit.user_id == current_user.id)

    if category:
        query = query.filter(Habit.category == category)
    if is_active is not None:
        query = query.filter(Habit.is_active == is_active)
    if is_archived is not None:
        query = query.filter(Habit.is_archived == is_archived)

    query = query.order_by(desc(Habit.created_at))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    # Check if each habit was completed today
    today = date.today()
    for habit in items:
        completed = db.query(HabitCompletion).filter(
            HabitCompletion.habit_id == habit.id,
            HabitCompletion.completion_date == today,
        ).first()
        habit.completed_today = completed is not None

    return HabitListResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("/{habit_id}", response_model=HabitResponse, summary="Get habit")
async def get_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    today = date.today()
    completed = db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit.id,
        HabitCompletion.completion_date == today,
    ).first()
    habit.completed_today = completed is not None
    return habit


@router.put("/{habit_id}", response_model=HabitResponse, summary="Update habit")
async def update_habit(
    habit_id: int,
    data: HabitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)
    db.commit()
    db.refresh(habit)
    return habit


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete habit")
async def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    db.delete(habit)
    db.commit()
    return None


@router.post("/{habit_id}/complete", response_model=HabitCompletionResponse, summary="Complete habit for a date")
async def complete_habit(
    habit_id: int,
    data: HabitCompletionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    completion_date = data.completion_date or date.today()

    # Check if already completed for this date
    existing = db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit_id,
        HabitCompletion.completion_date == completion_date,
    ).first()

    if existing:
        # Update count
        existing.count = data.count
        if data.notes:
            existing.notes = data.notes
        db.commit()
        db.refresh(existing)
        return existing

    # Create new completion
    new_completion = HabitCompletion(
        habit_id=habit_id,
        user_id=current_user.id,
        completion_date=completion_date,
        count=data.count,
        notes=data.notes,
    )
    db.add(new_completion)
    db.commit()
    db.refresh(new_completion)

    # Update streak + total
    current, longest = calculate_streak(db, habit_id)
    habit.current_streak = current
    habit.longest_streak = max(habit.longest_streak, longest)
    habit.total_completions += 1
    db.commit()
    service = GamificationService(db, current_user)
    service.award_xp(settings.XP_HABIT_COMPLETE, f"Completed habit: {habit.name}")
    service.check_achievements()
    
    logger.info(f"✅ Habit completed: '{habit.name}' streak={current}")
    return new_completion


@router.delete("/{habit_id}/complete/{completion_date}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove habit completion")
async def uncomplete_habit(
    habit_id: int,
    completion_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    completion = db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit_id,
        HabitCompletion.completion_date == completion_date,
    ).first()

    if completion:
        db.delete(completion)
        habit.total_completions = max(0, habit.total_completions - 1)
        current, longest = calculate_streak(db, habit_id)
        habit.current_streak = current
        db.commit()
    return None


@router.get("/{habit_id}/completions", summary="Get habit completion history")
async def get_habit_completions(
    habit_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    start_date = date.today() - timedelta(days=days)
    completions = db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit_id,
        HabitCompletion.completion_date >= start_date,
    ).order_by(desc(HabitCompletion.completion_date)).all()

    return {
        "habit_id": habit_id,
        "habit_name": habit.name,
        "days_range": days,
        "completion_count": len(completions),
        "completions": completions,
    }
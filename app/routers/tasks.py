"""
Tasks API — Full CRUD + complete/uncomplete + filters.

This router demonstrates BEST PRACTICES:
- Multi-tenancy (filter by current user)
- Pagination
- Filtering
- Sorting
- Proper HTTP status codes
- Validation via Pydantic
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional, List
from datetime import datetime, timezone
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.task import Task, TaskPriority, TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
)
from app.core.dependencies import get_current_user
from loguru import logger


router = APIRouter()


# ════════════════════════════════════════════════════════════════
# CREATE TASK
# ════════════════════════════════════════════════════════════════

@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new task for the current user.
    
    The task will be automatically linked to the authenticated user.
    """
    new_task = Task(
        user_id=current_user.id,
        **data.model_dump(),
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    logger.info(f"📝 Task created: '{new_task.title}' by user {current_user.id}")
    return new_task


# ════════════════════════════════════════════════════════════════
# LIST TASKS (with filters + pagination)
# ════════════════════════════════════════════════════════════════

@router.get(
    "/",
    response_model=TaskListResponse,
    summary="List tasks with filters & pagination",
)
async def list_tasks(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    
    # Filters
    status_filter: Optional[TaskStatus] = Query(None, alias="status", description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    is_starred: Optional[bool] = Query(None, description="Filter starred tasks"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    
    # Sorting
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all tasks for the current user with optional filters.
    
    Supports filtering by status, priority, project, starred flag,
    and full-text search in title/description.
    """
    # Base query — ALWAYS filter by current user (multi-tenancy!)
    query = db.query(Task).filter(Task.user_id == current_user.id)

    # Apply filters
    if status_filter:
        query = query.filter(Task.status == status_filter)
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    if is_starred is not None:
        query = query.filter(Task.is_starred == is_starred)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Task.title.ilike(search_term)) | (Task.description.ilike(search_term))
        )

    # Apply sorting
    sort_column = getattr(Task, sort_by, Task.created_at)
    order_fn = desc if sort_order == "desc" else asc
    query = query.order_by(order_fn(sort_column))

    # Apply pagination
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


# ════════════════════════════════════════════════════════════════
# GET SINGLE TASK
# ════════════════════════════════════════════════════════════════

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task",
)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific task by ID. User can only access their own tasks."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


# ════════════════════════════════════════════════════════════════
# UPDATE TASK
# ════════════════════════════════════════════════════════════════

@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing task. Only provided fields will be updated."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Only update fields that were explicitly provided
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # If status changed to COMPLETED, set completed_at
    if "status" in update_data and update_data["status"] == TaskStatus.COMPLETED:
        if not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    logger.info(f"✏️ Task updated: ID {task_id} by user {current_user.id}")
    return task


# ════════════════════════════════════════════════════════════════
# COMPLETE TASK (special action)
# ════════════════════════════════════════════════════════════════

@router.post(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Mark task as complete",
)
async def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task is already completed")

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)

    # 🎮 GAMIFICATION: Award XP + check achievements
    from app.services.gamification_service import GamificationService
    from app.config import settings
    
    service = GamificationService(db, current_user)
    service.award_xp(settings.XP_TASK_COMPLETE, f"Completed task: {task.title}")
    service.check_achievements()
    
    logger.info(f"✅ Task completed: '{task.title}' by user {current_user.id}")
    return task


# ════════════════════════════════════════════════════════════════
# UNCOMPLETE TASK
# ════════════════════════════════════════════════════════════════

@router.post(
    "/{task_id}/uncomplete",
    response_model=TaskResponse,
    summary="Mark task as not complete",
)
async def uncomplete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reverse the completion of a task."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    task.status = TaskStatus.TODO
    task.completed_at = None
    db.commit()
    db.refresh(task)

    return task


# ════════════════════════════════════════════════════════════════
# DELETE TASK
# ════════════════════════════════════════════════════════════════

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently delete a task."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()

    logger.info(f"🗑️ Task deleted: ID {task_id} by user {current_user.id}")
    return None


# ════════════════════════════════════════════════════════════════
# BULK DELETE
# ════════════════════════════════════════════════════════════════

@router.post(
    "/bulk-delete",
    summary="Delete multiple tasks at once",
)
async def bulk_delete_tasks(
    task_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete multiple tasks in a single request."""
    deleted = db.query(Task).filter(
        Task.id.in_(task_ids),
        Task.user_id == current_user.id,
    ).delete(synchronize_session=False)

    db.commit()

    return {"deleted_count": deleted, "message": f"Deleted {deleted} tasks"}


# ════════════════════════════════════════════════════════════════
# STATS ENDPOINT
# ════════════════════════════════════════════════════════════════

@router.get(
    "/stats/overview",
    summary="Get task statistics overview",
)
async def get_task_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get quick overview of task counts by status."""
    base_query = db.query(Task).filter(Task.user_id == current_user.id)

    total = base_query.count()
    todo = base_query.filter(Task.status == TaskStatus.TODO).count()
    in_progress = base_query.filter(Task.status == TaskStatus.IN_PROGRESS).count()
    completed = base_query.filter(Task.status == TaskStatus.COMPLETED).count()
    starred = base_query.filter(Task.is_starred == True).count()

    completion_rate = (completed / total * 100) if total > 0 else 0

    return {
        "total": total,
        "todo": todo,
        "in_progress": in_progress,
        "completed": completed,
        "starred": starred,
        "completion_rate": round(completion_rate, 2),
    }
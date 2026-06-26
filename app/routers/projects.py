"""Projects API — Full CRUD."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import Optional
from datetime import date
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.core.dependencies import get_current_user
from loguru import logger

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create project")
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_project = Project(user_id=current_user.id, **data.model_dump())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    logger.info(f"📁 Project created: '{new_project.name}' by user {current_user.id}")
    return new_project


@router.get("/", response_model=ProjectListResponse, summary="List projects")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ProjectStatus] = Query(None, alias="status"),
    is_favorite: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Project).filter(Project.user_id == current_user.id)

    if status_filter:
        query = query.filter(Project.status == status_filter)
    if is_favorite is not None:
        query = query.filter(Project.is_favorite == is_favorite)
    if is_archived is not None:
        query = query.filter(Project.is_archived == is_archived)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    sort_column = getattr(Project, sort_by, Project.created_at)
    query = query.order_by(desc(sort_column) if sort_order == "desc" else asc(sort_column))

    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    # Add task count to each project
    for proj in items:
        proj.task_count = db.query(Task).filter(Task.project_id == proj.id).count()

    return ProjectListResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project")
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.task_count = db.query(Task).filter(Task.project_id == project.id).count()
    return project


@router.put("/{project_id}", response_model=ProjectResponse, summary="Update project")
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    if update_data.get("status") == ProjectStatus.COMPLETED and not project.completed_at:
        project.completed_at = date.today()
        project.progress = 100

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete project")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None


@router.get("/{project_id}/tasks", summary="Get all tasks in a project")
async def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    return {"project_id": project_id, "task_count": len(tasks), "tasks": tasks}
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import date, timedelta
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.health import HealthLog, MetricType
from app.schemas.health import HealthLogCreate, HealthLogUpdate, HealthLogResponse, HealthLogListResponse
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=HealthLogResponse, status_code=201)
async def create_log(data: HealthLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = HealthLog(user_id=current_user.id, **data.model_dump())
    db.add(log); db.commit(); db.refresh(log)
    return log


@router.get("/", response_model=HealthLogListResponse)
async def list_logs(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    metric_type: Optional[MetricType] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    query = db.query(HealthLog).filter(HealthLog.user_id == current_user.id)
    if metric_type: query = query.filter(HealthLog.metric_type == metric_type)
    if start_date: query = query.filter(HealthLog.log_date >= start_date)
    if end_date: query = query.filter(HealthLog.log_date <= end_date)
    query = query.order_by(desc(HealthLog.log_date))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return HealthLogListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1)


@router.get("/{log_id}", response_model=HealthLogResponse)
async def get_log(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = db.query(HealthLog).filter(HealthLog.id == log_id, HealthLog.user_id == current_user.id).first()
    if not log: raise HTTPException(404, "Log not found")
    return log


@router.put("/{log_id}", response_model=HealthLogResponse)
async def update_log(log_id: int, data: HealthLogUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = db.query(HealthLog).filter(HealthLog.id == log_id, HealthLog.user_id == current_user.id).first()
    if not log: raise HTTPException(404, "Log not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(log, field, value)
    db.commit(); db.refresh(log)
    return log


@router.delete("/{log_id}", status_code=204)
async def delete_log(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = db.query(HealthLog).filter(HealthLog.id == log_id, HealthLog.user_id == current_user.id).first()
    if not log: raise HTTPException(404, "Log not found")
    db.delete(log); db.commit()
    return None


@router.get("/summary/recent")
async def get_recent_summary(days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get health summary for the last N days."""
    start = date.today() - timedelta(days=days)
    logs = db.query(HealthLog).filter(HealthLog.user_id == current_user.id, HealthLog.log_date >= start).all()
    summary = {}
    for log in logs:
        key = log.metric_type.value
        if key not in summary:
            summary[key] = {"count": 0, "total_value": 0, "logs": []}
        summary[key]["count"] += 1
        if log.value: summary[key]["total_value"] += log.value
        summary[key]["logs"].append({"date": log.log_date.isoformat(), "value": log.value})
    for key in summary:
        if summary[key]["count"] > 0 and summary[key]["total_value"]:
            summary[key]["average"] = round(summary[key]["total_value"] / summary[key]["count"], 2)
    return {"days": days, "summary": summary}
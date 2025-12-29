"""
Report management routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import os
from api.database import get_db
from api.models.report import Report, ReportStatus
from api.models.user import User, UserRole
from api.services.auth import get_current_user, require_admin

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportResponse(BaseModel):
    """Report response model."""
    id: int
    filename: str
    client_name: str
    auditor_name: Optional[str]
    client_code: Optional[str]
    industry: Optional[str]
    analysis_period_days: Optional[int]
    file_path_html: Optional[str]
    file_path_pdf: Optional[str]
    file_path_word: Optional[str]
    status: ReportStatus
    llm_provider: Optional[str]
    llm_model: Optional[str]
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Report list response with pagination."""
    reports: List[ReportResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    client_name: Optional[str] = Query(None),
    status_filter: Optional[ReportStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all reports with pagination and filters."""
    query = db.query(Report)
    
    # Filter by user role
    if current_user.role == UserRole.VIEWER:
        # Viewers can only see their own reports
        query = query.filter(Report.created_by_id == current_user.id)
    elif current_user.role == UserRole.USER:
        # Users can see their own reports
        query = query.filter(Report.created_by_id == current_user.id)
    # Admins can see all reports
    
    # Apply filters
    if client_name:
        query = query.filter(Report.client_name.ilike(f"%{client_name}%"))
    if status_filter:
        query = query.filter(Report.status == status_filter)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    reports = query.order_by(desc(Report.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return ReportListResponse(
        reports=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Check access permissions
    if current_user.role == UserRole.VIEWER or current_user.role == UserRole.USER:
        if report.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return ReportResponse.model_validate(report)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a report (admin only)."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Delete files
    for file_path in [report.file_path_html, report.file_path_pdf, report.file_path_word]:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {file_path}: {e}")
    
    # Delete from database
    db.delete(report)
    db.commit()
    
    return None


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    file_type: str = Query("html", regex="^(html|pdf|word)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a report file."""
    from fastapi.responses import FileResponse
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Check access permissions
    if current_user.role in [UserRole.VIEWER, UserRole.USER]:
        if report.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Get file path based on type
    file_path = None
    if file_type == "html":
        file_path = report.file_path_html
    elif file_type == "pdf":
        file_path = report.file_path_pdf
    elif file_type == "word":
        file_path = report.file_path_word
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{file_type.upper()} file not found"
        )
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type={
            "html": "text/html",
            "pdf": "application/pdf",
            "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }.get(file_type, "application/octet-stream")
    )


"""
Dashboard API endpoints for statistics and recent audits.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_, cast, Float
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.models.report import Report, ReportStatus
from api.services.auth import get_current_user
from api.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    audits_this_month: int
    audits_last_month: int
    audits_change_percent: float
    total_revenue_analyzed: float
    revenue_change_percent: float
    active_clients: int
    new_clients_this_week: int
    quotes_generated: int
    quotes_total_value: float


class RecentAudit(BaseModel):
    """Recent audit summary."""
    id: int
    client_name: str
    industry: Optional[str]
    status: str
    created_at: datetime
    revenue: Optional[float] = None
    flow_count: Optional[int] = None
    filename: Optional[str] = None


class RecentAuditsResponse(BaseModel):
    """Response for recent audits list."""
    audits: List[RecentAudit]
    total: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard statistics including audit counts, revenue, and client metrics.
    """
    try:
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
        end_of_last_month = start_of_month - timedelta(days=1)
        start_of_week = now - timedelta(days=7)
        
        # Audits this month
        audits_this_month = db.query(func.count(Report.id)).filter(
            Report.created_at >= start_of_month,
            Report.status == ReportStatus.COMPLETED
        ).scalar() or 0
        
        # Audits last month
        audits_last_month = db.query(func.count(Report.id)).filter(
            and_(
                Report.created_at >= start_of_last_month,
                Report.created_at <= end_of_last_month,
                Report.status == ReportStatus.COMPLETED
            )
        ).scalar() or 0
        
        # Calculate change percentage
        if audits_last_month > 0:
            audits_change_percent = ((audits_this_month - audits_last_month) / audits_last_month) * 100
        else:
            audits_change_percent = 100.0 if audits_this_month > 0 else 0.0
        
        # Total revenue analyzed - extract from actual reports
        # Handle both PostgreSQL and SQLite
        try:
            if hasattr(db, 'bind') and 'postgresql' in str(db.bind.url):
                # PostgreSQL
                revenue_query = db.query(
                    func.sum(cast(Report.total_revenue, Float))
                ).filter(
                    Report.created_at >= start_of_month,
                    Report.status == ReportStatus.COMPLETED,
                    Report.total_revenue.isnot(None)
                )
            else:
                # SQLite - use CAST
                revenue_query = db.query(
                    func.sum(cast(Report.total_revenue, Float))
                ).filter(
                    Report.created_at >= start_of_month,
                    Report.status == ReportStatus.COMPLETED,
                    Report.total_revenue.isnot(None)
                )
            total_revenue_analyzed = revenue_query.scalar() or 0.0
            if total_revenue_analyzed is None:
                total_revenue_analyzed = 0.0
            
            # Revenue from last month for comparison
            if hasattr(db, 'bind') and 'postgresql' in str(db.bind.url):
                revenue_last_month_query = db.query(
                    func.sum(cast(Report.total_revenue, Float))
                ).filter(
                    and_(
                        Report.created_at >= start_of_last_month,
                        Report.created_at <= end_of_last_month,
                        Report.status == ReportStatus.COMPLETED,
                        Report.total_revenue.isnot(None)
                    )
                )
            else:
                revenue_last_month_query = db.query(
                    func.sum(cast(Report.total_revenue, Float))
                ).filter(
                    and_(
                        Report.created_at >= start_of_last_month,
                        Report.created_at <= end_of_last_month,
                        Report.status == ReportStatus.COMPLETED,
                        Report.total_revenue.isnot(None)
                    )
                )
            total_revenue_last_month = revenue_last_month_query.scalar() or 0.0
            if total_revenue_last_month is None:
                total_revenue_last_month = 0.0
        except Exception as e:
            # Fallback to simple sum if cast fails
            print(f"Warning: Could not cast revenue values: {e}")
            total_revenue_analyzed = 0.0
            total_revenue_last_month = 0.0
        
        # Calculate revenue change percentage
        if total_revenue_last_month > 0:
            revenue_change_percent = ((total_revenue_analyzed - total_revenue_last_month) / total_revenue_last_month) * 100
        else:
            revenue_change_percent = 100.0 if total_revenue_analyzed > 0 else 0.0
        
        # Active clients (unique client names)
        active_clients = db.query(func.count(func.distinct(Report.client_name))).filter(
            Report.status == ReportStatus.COMPLETED
        ).scalar() or 0
        
        # New clients this week
        new_clients_this_week = db.query(func.count(func.distinct(Report.client_name))).filter(
            and_(
                Report.created_at >= start_of_week,
                Report.status == ReportStatus.COMPLETED
            )
        ).scalar() or 0
        
        # Quotes generated (placeholder - would need a quotes table)
        quotes_generated = 0
        quotes_total_value = 0.0
        
        return DashboardStats(
            audits_this_month=audits_this_month,
            audits_last_month=audits_last_month,
            audits_change_percent=round(audits_change_percent, 1),
            total_revenue_analyzed=round(total_revenue_analyzed, 2),
            revenue_change_percent=round(revenue_change_percent, 1),
            active_clients=active_clients,
            new_clients_this_week=new_clients_this_week,
            quotes_generated=quotes_generated,
            quotes_total_value=round(quotes_total_value, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")


@router.get("/recent-audits", response_model=RecentAuditsResponse)
async def get_recent_audits(
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent audit reports.
    
    Args:
        limit: Maximum number of audits to return (default: 10)
        status: Filter by status (optional: 'completed', 'processing', 'failed')
    """
    try:
        query = db.query(Report)
        
        # Filter by status if provided
        if status:
            try:
                status_enum = ReportStatus(status.lower())
                query = query.filter(Report.status == status_enum)
            except ValueError:
                # Invalid status, ignore filter
                pass
        
        # Order by most recent first
        query = query.order_by(Report.created_at.desc())
        
        # Limit results
        reports = query.limit(limit).all()
        
        # Convert to response model
        audits = []
        for report in reports:
            # Extract revenue from report
            revenue = None
            if report.total_revenue:
                try:
                    revenue = float(report.total_revenue)
                except (ValueError, TypeError):
                    revenue = None
            
            # Flow count would need to be extracted from HTML or stored separately
            # For now, we'll leave it as None
            flow_count = None
            
            audits.append(RecentAudit(
                id=report.id,
                client_name=report.client_name,
                industry=report.industry,
                status=report.status.value,
                created_at=report.created_at,
                revenue=revenue,
                flow_count=flow_count,
                filename=report.filename
            ))
        
        total = db.query(func.count(Report.id)).scalar() or 0
        
        return RecentAuditsResponse(
            audits=audits,
            total=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent audits: {str(e)}")


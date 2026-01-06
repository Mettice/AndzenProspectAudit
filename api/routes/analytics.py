"""
Analytics API endpoints for dashboard metrics and trends.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, extract, cast, Float
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.models.report import Report, ReportStatus
from api.services.auth import get_current_user
from api.models.user import User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class RevenueTrend(BaseModel):
    """Revenue trend data point."""
    date: str
    total_revenue: float
    attributed_revenue: float
    audit_count: int


class RevenueTrendResponse(BaseModel):
    """Revenue trends response."""
    trends: List[RevenueTrend]
    period: str


class ClientPerformance(BaseModel):
    """Client performance metrics."""
    client_name: str
    audit_count: int
    total_revenue: float
    attributed_revenue: float
    avg_revenue_per_audit: float
    last_audit_date: Optional[str]


class IndustryStats(BaseModel):
    """Industry statistics."""
    industry: str
    audit_count: int
    total_revenue: float
    avg_revenue: float


@router.get("/revenue-trends", response_model=RevenueTrendResponse)
async def get_revenue_trends(
    period: str = Query("month", regex="^(day|week|month|year)$"),
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get revenue trends over time.
    
    Args:
        period: Grouping period (day, week, month, year)
        days: Number of days to analyze (default: 90)
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query based on period
        if period == "day":
            date_group = func.date(Report.created_at)
        elif period == "week":
            date_group = func.date_trunc('week', Report.created_at) if hasattr(func, 'date_trunc') else func.date(Report.created_at)
        elif period == "month":
            date_group = func.date_trunc('month', Report.created_at) if hasattr(func, 'date_trunc') else func.date(Report.created_at)
        else:  # year
            date_group = func.date_trunc('year', Report.created_at) if hasattr(func, 'date_trunc') else func.date(Report.created_at)
        
        # Query revenue trends
        trends_query = db.query(
            date_group.label('period_date'),
            func.sum(cast(Report.total_revenue, Float)).label('total_revenue'),
            func.sum(cast(Report.attributed_revenue, Float)).label('attributed_revenue'),
            func.count(Report.id).label('audit_count')
        ).filter(
            and_(
                Report.created_at >= start_date,
                Report.status == ReportStatus.COMPLETED,
                Report.total_revenue.isnot(None)
            )
        ).group_by(date_group).order_by(date_group)
        
        results = trends_query.all()
        
        trends = []
        for row in results:
            period_date = row.period_date
            if isinstance(period_date, datetime):
                date_str = period_date.isoformat()
            else:
                date_str = str(period_date)
            
            trends.append(RevenueTrend(
                date=date_str,
                total_revenue=float(row.total_revenue or 0),
                attributed_revenue=float(row.attributed_revenue or 0),
                audit_count=int(row.audit_count or 0)
            ))
        
        return RevenueTrendResponse(
            trends=trends,
            period=period
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching revenue trends: {str(e)}")


@router.get("/client-performance", response_model=List[ClientPerformance])
async def get_client_performance(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get client performance metrics.
    """
    try:
        # Group by client name
        clients_query = db.query(
            Report.client_name,
            func.count(Report.id).label('audit_count'),
            func.sum(cast(Report.total_revenue, Float)).label('total_revenue'),
            func.sum(cast(Report.attributed_revenue, Float)).label('attributed_revenue'),
            func.max(Report.created_at).label('last_audit_date')
        ).filter(
            and_(
                Report.status == ReportStatus.COMPLETED,
                Report.total_revenue.isnot(None)
            )
        ).group_by(Report.client_name).order_by(
            func.sum(cast(Report.total_revenue, Float)).desc()
        ).limit(limit)
        
        results = clients_query.all()
        
        clients = []
        for row in results:
            audit_count = int(row.audit_count or 0)
            total_revenue = float(row.total_revenue or 0)
            avg_revenue = total_revenue / audit_count if audit_count > 0 else 0
            
            clients.append(ClientPerformance(
                client_name=row.client_name,
                audit_count=audit_count,
                total_revenue=total_revenue,
                attributed_revenue=float(row.attributed_revenue or 0),
                avg_revenue_per_audit=avg_revenue,
                last_audit_date=row.last_audit_date.isoformat() if row.last_audit_date else None
            ))
        
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching client performance: {str(e)}")


@router.get("/industry-stats", response_model=List[IndustryStats])
async def get_industry_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics by industry.
    """
    try:
        industries_query = db.query(
            Report.industry,
            func.count(Report.id).label('audit_count'),
            func.sum(cast(Report.total_revenue, Float)).label('total_revenue')
        ).filter(
            and_(
                Report.status == ReportStatus.COMPLETED,
                Report.industry.isnot(None),
                Report.total_revenue.isnot(None)
            )
        ).group_by(Report.industry).order_by(
            func.count(Report.id).desc()
        )
        
        results = industries_query.all()
        
        industries = []
        for row in results:
            audit_count = int(row.audit_count or 0)
            total_revenue = float(row.total_revenue or 0)
            avg_revenue = total_revenue / audit_count if audit_count > 0 else 0
            
            industries.append(IndustryStats(
                industry=row.industry or "Unknown",
                audit_count=audit_count,
                total_revenue=total_revenue,
                avg_revenue=avg_revenue
            ))
        
        return industries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching industry stats: {str(e)}")


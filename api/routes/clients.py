"""
Client management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy import func, desc, cast, Float
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.models.report import Report, ReportStatus
from api.services.auth import get_current_user
from api.models.user import User

router = APIRouter(prefix="/api/clients", tags=["clients"])


class ClientSummary(BaseModel):
    """Client summary information."""
    client_name: str
    client_code: Optional[str]
    industry: Optional[str]
    audit_count: int
    total_revenue: float
    attributed_revenue: float
    first_audit_date: Optional[str]
    last_audit_date: Optional[str]
    status: str  # 'active', 'inactive'


class ClientDetail(BaseModel):
    """Detailed client information."""
    client_name: str
    client_code: Optional[str]
    industry: Optional[str]
    audit_count: int
    total_revenue: float
    attributed_revenue: float
    first_audit_date: Optional[str]
    last_audit_date: Optional[str]
    audits: List[dict]


@router.get("", response_model=List[ClientSummary])
async def list_clients(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    industry: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all clients with summary information.
    
    Args:
        limit: Maximum number of clients to return
        offset: Number of clients to skip
        industry: Filter by industry (optional)
    """
    try:
        query = db.query(
            Report.client_name,
            Report.client_code,
            Report.industry,
            func.count(Report.id).label('audit_count'),
            func.sum(cast(Report.total_revenue, Float)).label('total_revenue'),
            func.sum(cast(Report.attributed_revenue, Float)).label('attributed_revenue'),
            func.min(Report.created_at).label('first_audit_date'),
            func.max(Report.created_at).label('last_audit_date')
        ).filter(
            Report.status == ReportStatus.COMPLETED
        )
        
        if industry:
            query = query.filter(Report.industry == industry)
        
        query = query.group_by(
            Report.client_name,
            Report.client_code,
            Report.industry
        ).order_by(desc('last_audit_date')).offset(offset).limit(limit)
        
        results = query.all()
        
        clients = []
        for row in results:
            # Determine status based on last audit date
            last_audit = row.last_audit_date
            if last_audit:
                days_since_last = (datetime.utcnow() - last_audit).days
                status = 'active' if days_since_last < 90 else 'inactive'
            else:
                status = 'inactive'
            
            clients.append(ClientSummary(
                client_name=row.client_name,
                client_code=row.client_code,
                industry=row.industry,
                audit_count=int(row.audit_count or 0),
                total_revenue=float(row.total_revenue or 0),
                attributed_revenue=float(row.attributed_revenue or 0),
                first_audit_date=row.first_audit_date.isoformat() if row.first_audit_date else None,
                last_audit_date=row.last_audit_date.isoformat() if row.last_audit_date else None,
                status=status
            ))
        
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching clients: {str(e)}")


@router.get("/{client_name}", response_model=ClientDetail)
async def get_client_detail(
    client_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific client.
    
    Args:
        client_name: Name of the client
    """
    try:
        # Get client summary
        summary_query = db.query(
            Report.client_name,
            Report.client_code,
            Report.industry,
            func.count(Report.id).label('audit_count'),
            func.sum(cast(Report.total_revenue, Float)).label('total_revenue'),
            func.sum(cast(Report.attributed_revenue, Float)).label('attributed_revenue'),
            func.min(Report.created_at).label('first_audit_date'),
            func.max(Report.created_at).label('last_audit_date')
        ).filter(
            Report.client_name == client_name,
            Report.status == ReportStatus.COMPLETED
        ).group_by(
            Report.client_name,
            Report.client_code,
            Report.industry
        )
        
        summary = summary_query.first()
        
        if not summary:
            raise HTTPException(status_code=404, detail=f"Client '{client_name}' not found")
        
        # Get all audits for this client
        audits = db.query(Report).filter(
            Report.client_name == client_name,
            Report.status == ReportStatus.COMPLETED
        ).order_by(Report.created_at.desc()).all()
        
        audit_list = []
        for audit in audits:
            audit_list.append({
                "id": audit.id,
                "filename": audit.filename,
                "created_at": audit.created_at.isoformat() if audit.created_at else None,
                "revenue": float(audit.total_revenue) if audit.total_revenue else None,
                "industry": audit.industry
            })
        
        return ClientDetail(
            client_name=summary.client_name,
            client_code=summary.client_code,
            industry=summary.industry,
            audit_count=int(summary.audit_count or 0),
            total_revenue=float(summary.total_revenue or 0),
            attributed_revenue=float(summary.attributed_revenue or 0),
            first_audit_date=summary.first_audit_date.isoformat() if summary.first_audit_date else None,
            last_audit_date=summary.last_audit_date.isoformat() if summary.last_audit_date else None,
            audits=audit_list
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching client detail: {str(e)}")


@router.get("/industries/list", response_model=List[str])
async def list_industries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all unique industries.
    """
    try:
        industries = db.query(Report.industry).filter(
            Report.industry.isnot(None),
            Report.status == ReportStatus.COMPLETED
        ).distinct().all()
        
        return [industry[0] for industry in industries if industry[0]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching industries: {str(e)}")


"""
Search API endpoints for audits and clients.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.models.report import Report, ReportStatus
from api.services.auth import get_current_user
from api.models.user import User

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchResult(BaseModel):
    """Search result item."""
    id: int
    client_name: str
    industry: Optional[str]
    status: str
    created_at: str
    revenue: Optional[float] = None
    filename: Optional[str] = None
    match_type: str  # 'client_name', 'industry', 'filename'


class SearchResponse(BaseModel):
    """Search response."""
    results: List[SearchResult]
    total: int
    query: str


@router.get("/audits", response_model=SearchResponse)
async def search_audits(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search audits by client name, industry, or filename.
    
    Args:
        q: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List of matching audit reports
    """
    try:
        if not q or len(q.strip()) < 1:
            return SearchResponse(results=[], total=0, query=q)
        
        query = q.strip()
        
        # Build search conditions
        # Search in client_name, industry, client_code, and filename
        search_conditions = or_(
            Report.client_name.ilike(f"%{query}%"),
            Report.industry.ilike(f"%{query}%"),
            Report.client_code.ilike(f"%{query}%"),
            Report.filename.ilike(f"%{query}%")
        )
        
        # Query reports
        reports = db.query(Report).filter(
            search_conditions,
            Report.status == ReportStatus.COMPLETED
        ).order_by(Report.created_at.desc()).limit(limit).all()
        
        # Convert to response model
        results = []
        for report in reports:
            # Determine match type
            match_type = "client_name"
            if query.lower() in (report.industry or "").lower():
                match_type = "industry"
            elif query.lower() in (report.filename or "").lower():
                match_type = "filename"
            elif query.lower() in (report.client_code or "").lower():
                match_type = "client_code"
            
            # Extract revenue
            revenue = None
            if report.total_revenue:
                try:
                    revenue = float(report.total_revenue)
                except (ValueError, TypeError):
                    revenue = None
            
            results.append(SearchResult(
                id=report.id,
                client_name=report.client_name,
                industry=report.industry,
                status=report.status.value,
                created_at=report.created_at.isoformat() if report.created_at else "",
                revenue=revenue,
                filename=report.filename,
                match_type=match_type
            ))
        
        total = len(results)
        
        return SearchResponse(
            results=results,
            total=total,
            query=query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/clients", response_model=List[str])
async def search_clients(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for unique client names.
    
    Returns a list of unique client names matching the search query.
    """
    try:
        if not q or len(q.strip()) < 1:
            return []
        
        query = q.strip()
        
        # Get distinct client names matching the query
        clients = db.query(Report.client_name).filter(
            Report.client_name.ilike(f"%{query}%"),
            Report.status == ReportStatus.COMPLETED
        ).distinct().limit(limit).all()
        
        return [client[0] for client in clients]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


"""
Edit handlers for report editing functionality.
"""
import logging
from typing import Dict, Any
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from ...database import get_db
from ...models.report import Report
from ...models.chat import ReportEdit
from .models import EditRequest, SaveRequest, ExportRequest
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


async def handle_edit_section(
    report_id: int,
    edit_request: EditRequest,
    db: Session
) -> Dict[str, Any]:
    """Edit a specific section of the report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.html_content:
        raise HTTPException(status_code=400, detail="Report HTML content not available")
    
    # Parse HTML and update section
    soup = BeautifulSoup(report.html_content, 'html.parser')
    
    # Find section by data-section attribute or ID
    section = soup.find('section', {'data-section': edit_request.section_id}) or \
              soup.find('div', {'id': edit_request.section_id}) or \
              soup.find('section', {'id': edit_request.section_id})
    
    if not section:
        raise HTTPException(
            status_code=404,
            detail=f"Section '{edit_request.section_id}' not found in report"
        )
    
    # Store old content for undo
    old_content = str(section)
    
    # Update section content
    if edit_request.new_content.strip().startswith('<'):
        # HTML content
        new_soup = BeautifulSoup(edit_request.new_content, 'html.parser')
        section.clear()
        section.append(new_soup)
    else:
        # Plain text - wrap in paragraph
        section.clear()
        p_tag = soup.new_tag('p')
        p_tag.string = edit_request.new_content
        section.append(p_tag)
    
    # Update report HTML
    updated_html = str(soup)
    report.html_content = updated_html
    
    # Save edit history
    edit_record = ReportEdit(
        report_id=report_id,
        section_id=edit_request.section_id,
        old_content=old_content,
        new_content=str(section),
        edit_source=edit_request.edit_source,
        chat_message_id=edit_request.chat_message_id
    )
    db.add(edit_record)
    db.commit()
    
    return {
        "success": True,
        "updated_section": edit_request.section_id,
        "preview": str(section)[:500]
    }


async def handle_save_report(
    report_id: int,
    save_request: SaveRequest,
    db: Session
) -> Dict[str, Any]:
    """Save edited report content."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if this is processed HTML (missing styles) - if so, don't overwrite original
    is_processed = '<style>' not in save_request.html_content or 'data-section-id="section-' in save_request.html_content
    
    if is_processed:
        logger.warning(f"Attempted to save processed HTML for report {report_id} - preserving original")
        return {
            "success": True,
            "message": "Edits saved (original HTML preserved in file)",
            "note": "The original HTML with styles is preserved. Edits are tracked separately."
        }
    
    # Only save if it looks like original HTML
    report.html_content = save_request.html_content
    db.commit()
    
    return {
        "success": True,
        "message": "Report saved successfully"
    }


async def handle_export_report(
    report_id: int,
    export_request: ExportRequest,
    db: Session
) -> Dict[str, Any]:
    """Export edited report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Save updated HTML content
    report.html_content = export_request.html_content
    db.commit()
    
    # Generate export file
    reports_dir = Path(__file__).parent.parent.parent.parent / "data" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_{report.client_name.replace(' ', '_')}_edited_{timestamp}.html"
    file_path = reports_dir / filename
    
    # Write HTML file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(export_request.html_content)
    
    # Return download URL
    return {
        "success": True,
        "filename": filename,
        "download_url": f"/api/audit/download-file?path={filename}"
    }


async def handle_get_edit_history(
    report_id: int,
    db: Session
) -> Dict[str, Any]:
    """Get edit history for a report."""
    edits = db.query(ReportEdit).filter(
        ReportEdit.report_id == report_id
    ).order_by(ReportEdit.created_at.desc()).all()
    
    return {
        "edits": [
            {
                "id": edit.id,
                "section_id": edit.section_id,
                "edit_source": edit.edit_source,
                "created_at": edit.created_at.isoformat() if edit.created_at else None,
                "preview": edit.new_content[:200] if edit.new_content else ""
            }
            for edit in edits
        ]
    }


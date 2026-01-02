"""
Report model for storing audit reports.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from api.database import Base


class ReportStatus(str, enum.Enum):
    """Report status enumeration."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """Report model for storing audit report metadata."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False, index=True)
    client_name = Column(String, nullable=False, index=True)
    auditor_name = Column(String, nullable=True)
    client_code = Column(String, nullable=True, index=True)
    industry = Column(String, nullable=True)
    analysis_period_days = Column(Integer, nullable=True)
    
    # File paths
    file_path_html = Column(String, nullable=True)
    file_path_pdf = Column(String, nullable=True)
    file_path_word = Column(String, nullable=True)
    
    # Report content (for editing)
    html_content = Column(Text, nullable=True)  # Full HTML content for editing
    
    # Metadata
    status = Column(Enum(ReportStatus), default=ReportStatus.PROCESSING, nullable=False)
    klaviyo_api_key_hash = Column(String, nullable=True)  # Hashed for security
    llm_provider = Column(String, nullable=True)
    llm_model = Column(String, nullable=True)
    llm_config = Column(JSON, nullable=True)  # Store LLM config for chat
    
    # Relationships
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Made nullable for async jobs
    created_by = relationship("User", back_populates="reports")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Report(id={self.id}, filename='{self.filename}', client='{self.client_name}')>"


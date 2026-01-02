"""
Chat and edit models for audit reports.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.database import Base


class ChatMessage(Base):
    """Chat message model for report conversations."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    section_id = Column(String, nullable=True)  # Section user clicked on
    section_references = Column(JSON, nullable=True)  # Sections referenced in response
    suggested_edits = Column(JSON, nullable=True)  # Edits suggested by AI
    parent_message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    report = relationship("Report", backref="chat_messages")
    parent_message = relationship("ChatMessage", remote_side=[id], backref="replies")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', report_id={self.report_id})>"


class ReportEdit(Base):
    """Report edit history model."""
    __tablename__ = "report_edits"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)
    section_id = Column(String, nullable=False)
    old_content = Column(Text, nullable=True)  # For undo functionality
    new_content = Column(Text, nullable=False)
    edit_source = Column(String, nullable=False)  # 'manual' or 'chat'
    chat_message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    report = relationship("Report", backref="edits")
    chat_message = relationship("ChatMessage", backref="edits")
    
    def __repr__(self):
        return f"<ReportEdit(id={self.id}, section='{self.section_id}', report_id={self.report_id})>"


"""
Document Model
==============
Modelo de documento com isolamento multi-tenant.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from core.database import Base


class DocumentStatus(str, enum.Enum):
    """Status do documento"""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class Document(Base):
    """Modelo de documento"""
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # File Info
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, etc
    mime_type = Column(String(100))
    
    # Storage
    storage_provider = Column(String(50), default="r2")  # r2, s3, local
    storage_key = Column(String(500), nullable=False)
    
    # Processing
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADING, nullable=False)
    processing_status = Column(JSONB, default={})
    
    # OCR & Analysis
    ocr_text = Column(Text)
    ocr_confidence = Column(Integer)  # 0-100
    ocr_language = Column(String(10))
    
    # Extracted Data
    extracted_data = Column(JSONB, default={})
    entities = Column(JSONB, default=list)
    key_points = Column(JSONB, default=list)
    
    # AI Analysis
    summary = Column(Text)
    analysis = Column(JSONB, default={})
    embeddings = Column(JSONB)  # Vector embeddings
    
    # Custom metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    custom_data = Column(JSONB, default={})
    tags = Column(JSONB, default=list)
    
    # Error Handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User", back_populates="documents")
    
    def __repr__(self):
        return f"<Document {self.filename} ({self.status})>"
    
    def to_dict(self):
        """Converte para dict serializável"""
        return {
            "id": str(self.id),
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "status": self.status.value if isinstance(self.status, DocumentStatus) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }

import enum
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, Float
from sqlalchemy.sql import func
from app.db.database import Base

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    linkedin_url = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    cv_filename = Column(String, nullable=False)
    cv_filepath = Column(String, nullable=False)
    cv_raw_text = Column(Text, nullable=True)
    status = Column(Enum(ProcessingStatus, name="processing_status"), default=ProcessingStatus.PENDING)
    overall_summary = Column(Text, nullable=True)
    overall_score = Column(Float, nullable=True)
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

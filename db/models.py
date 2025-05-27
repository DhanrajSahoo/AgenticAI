from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.sql import func
import uuid

from .database import Base

class DBWorkflow(Base):
    __tablename__ = "workflows"

    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    workflow_data = Column(JSON, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
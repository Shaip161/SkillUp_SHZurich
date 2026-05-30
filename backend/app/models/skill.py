import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import TIMESTAMP, Boolean, Column, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class MatchHistory(Base):
    __tablename__ = "match_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    score = Column(Float)
    matched_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    applied = Column(Boolean, server_default="false")


class MatchHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    score: float | None = None
    matched_at: datetime
    applied: bool

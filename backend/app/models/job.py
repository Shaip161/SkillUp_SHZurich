import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, ConfigDict
from sqlalchemy import ARRAY, TIMESTAMP, Column, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adzuna_id = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    company = Column(Text)
    location = Column(Text)
    category = Column(Text)
    seniority = Column(Text)
    required_skills = Column(ARRAY(Text))
    nice_to_have = Column(ARRAY(Text))
    soft_skills = Column(ARRAY(Text))
    languages = Column(ARRAY(Text))
    redirect_url = Column(Text, nullable=False)
    embedding = Column(Vector(3072))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    fetched_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True))


class JobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str | None = None
    location: str | None = None
    category: str | None = None
    seniority: str | None = None
    required_skills: list[str] = []
    redirect_url: str


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    adzuna_id: str
    title: str
    description: str
    company: str | None = None
    location: str | None = None
    category: str | None = None
    seniority: str | None = None
    required_skills: list[str] = []
    nice_to_have: list[str] = []
    soft_skills: list[str] = []
    languages: list[str] = []
    redirect_url: str
    created_at: datetime
    fetched_at: datetime | None = None
    expires_at: datetime | None = None

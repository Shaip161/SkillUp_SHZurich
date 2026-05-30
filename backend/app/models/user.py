import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, ConfigDict
from sqlalchemy import ARRAY, TIMESTAMP, Column, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cv_text = Column(Text)
    skills = Column(ARRAY(Text))
    seniority = Column(Text)
    languages = Column(ARRAY(Text))
    embedding = Column(Vector(3072))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class UserCreate(BaseModel):
    email: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    created_at: datetime


class UserProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    skills: list[str] = []
    seniority: str | None = None
    languages: list[str] = []
    updated_at: datetime

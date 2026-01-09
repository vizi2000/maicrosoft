"""User model."""

from database import Base
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    """SQLAlchemy model for users."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255))
    name = Column(String(255))
    role = Column(Enum('admin', 'owner', 'editor', 'viewer', name='enum_type'), default='viewer')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

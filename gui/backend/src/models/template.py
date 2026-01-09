"""Template model."""

from database import Base
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID


class Template(Base):
    """SQLAlchemy model for templates."""

    __tablename__ = "templates"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    plan_json = Column(JSONB, nullable=False)
    canvas_json = Column(JSONB)
    usage_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)

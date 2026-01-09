"""PlanVersion model."""

from database import Base
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID


class PlanVersion(Base):
    """SQLAlchemy model for plan_versions."""

    __tablename__ = "plan_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"))
    version_number = Column(Integer, nullable=False)
    plan_json = Column(JSONB, nullable=False)
    canvas_json = Column(JSONB)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

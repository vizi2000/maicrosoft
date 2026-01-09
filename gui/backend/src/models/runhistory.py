"""RunHistory model."""

from database import Base
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID


class RunHistory(Base):
    """SQLAlchemy model for run_history."""

    __tablename__ = "run_history"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"))
    version_id = Column(UUID(as_uuid=True), ForeignKey("planversions.id"))
    status = Column(Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='enum_type'))
    trigger_type = Column(Enum('manual', 'webhook', 'schedule', name='enum_type'))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)

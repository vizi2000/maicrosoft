"""NodeLog model."""

from database import Base
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID


class NodeLog(Base):
    """SQLAlchemy model for node_logs."""

    __tablename__ = "node_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    run_id = Column(UUID(as_uuid=True), ForeignKey("runhistorys.id", ondelete="CASCADE"))
    node_id = Column(String(255), nullable=False)
    status = Column(Enum('pending', 'running', 'completed', 'failed', 'skipped', name='enum_type'))
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    error_data = Column(JSONB)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

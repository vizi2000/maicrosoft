"""Secret model."""

from database import Base
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID


class Secret(Base):
    """SQLAlchemy model for secrets."""

    __tablename__ = "secrets"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    encrypted_value = Column(LargeBinary, nullable=False)
    secret_type = Column(Enum('api_key', 'oauth', 'password', 'connection_string', name='enum_type'))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

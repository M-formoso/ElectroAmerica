from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr, as_declarative
from sqlalchemy.sql import func
import uuid


@as_declarative()
class Base:
    """Clase base para todos los modelos SQLAlchemy."""

    id: uuid.UUID
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        """Genera el nombre de la tabla automáticamente."""
        return cls.__name__.lower()


class BaseModel:
    """Mixin con campos comunes para todos los modelos."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

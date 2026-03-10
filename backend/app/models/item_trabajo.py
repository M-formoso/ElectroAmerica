from sqlalchemy import Column, String, Numeric, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoItem(str, enum.Enum):
    """Estados posibles de un ítem de trabajo."""
    pendiente = "pendiente"
    en_curso = "en_curso"
    completado = "completado"


class ItemTrabajo(Base, BaseModel):
    """Modelo de ítem de trabajo dentro de una etapa."""
    __tablename__ = "items_trabajo"

    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=False)
    descripcion = Column(String(500), nullable=False)
    responsable = Column(String(100), nullable=True)
    cantidad = Column(Numeric(10, 2), nullable=True)
    unidad = Column(String(30), nullable=True)
    estado = Column(Enum(EstadoItem), default=EstadoItem.pendiente, nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=True)  # Solo visible admin/supervisor

    # Relaciones
    etapa = relationship("Etapa", back_populates="items_trabajo")
    precios_historial = relationship(
        "PrecioItem",
        back_populates="item_trabajo",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ItemTrabajo {self.descripcion[:50]}>"

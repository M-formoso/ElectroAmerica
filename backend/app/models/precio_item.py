from sqlalchemy import Column, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class PrecioItem(Base, BaseModel):
    """Modelo de historial de precios de ítems de trabajo."""
    __tablename__ = "precios_items"

    item_trabajo_id = Column(UUID(as_uuid=True), ForeignKey("items_trabajo.id"), nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    fecha_desde = Column(DateTime(timezone=True), nullable=False)
    fecha_hasta = Column(DateTime(timezone=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    item_trabajo = relationship("ItemTrabajo", back_populates="precios_historial")
    actualizador = relationship("Usuario")

    def __repr__(self):
        return f"<PrecioItem {self.item_trabajo_id} ${self.precio_unitario}>"

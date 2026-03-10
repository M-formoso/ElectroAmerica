from sqlalchemy import Column, String, Text, Numeric, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class TipoMovimiento(str, enum.Enum):
    """Tipos de movimiento de stock."""
    ingreso = "ingreso"
    egreso = "egreso"
    ajuste = "ajuste"


class MovimientoStock(Base, BaseModel):
    """Modelo de movimiento de stock."""
    __tablename__ = "movimientos_stock"

    material_id = Column(UUID(as_uuid=True), ForeignKey("materiales.id"), nullable=False)
    tipo = Column(Enum(TipoMovimiento), nullable=False)
    cantidad = Column(Numeric(12, 3), nullable=False)
    referencia_tipo = Column(String(50), nullable=True)  # 'asignacion', 'compra', 'ajuste_manual'
    referencia_id = Column(UUID(as_uuid=True), nullable=True)
    observaciones = Column(Text, nullable=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    material = relationship("Material", back_populates="movimientos")
    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<MovimientoStock {self.tipo} {self.cantidad}>"

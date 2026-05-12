from sqlalchemy import Column, String, Numeric, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class TipoMovimiento(str, enum.Enum):
    """Tipos de movimiento de stock."""
    entrada = "entrada"
    salida = "salida"
    ajuste = "ajuste"
    devolucion = "devolucion"
    transferencia_a_deposito = "transferencia_a_deposito"


class MovimientoStock(Base, BaseModel):
    """Modelo de movimiento de stock."""
    __tablename__ = "movimientos_stock"

    material_id = Column(UUID(as_uuid=True), ForeignKey("materiales.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(Enum(TipoMovimiento), nullable=False)
    cantidad = Column(Numeric(12, 4), nullable=False)
    stock_anterior = Column(Numeric(12, 4), nullable=False)
    stock_nuevo = Column(Numeric(12, 4), nullable=False)
    motivo = Column(String(300), nullable=True)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True)
    deposito_destino_id = Column(UUID(as_uuid=True), ForeignKey("depositos.id", ondelete="SET NULL"), nullable=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    material = relationship("Material", back_populates="movimientos")
    proyecto = relationship("Proyecto")
    deposito_destino = relationship("Deposito")
    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<MovimientoStock {self.tipo} {self.cantidad}>"

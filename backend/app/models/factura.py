from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM as PgEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoFactura(str, enum.Enum):
    """Estado de una factura a cobrar."""
    PENDIENTE = "pendiente"
    PAGADA = "pagada"


EstadoFacturaDB = PgEnum(
    'pendiente', 'pagada',
    name='estadofactura',
    create_type=False,
)


class Factura(Base, BaseModel):
    """Factura emitida a un cliente/empresa por una obra."""
    __tablename__ = "facturas"

    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True)
    # proyecto_id es opcional: la factura puede referir a una obra externa
    # (no gestionada como proyecto formal). En ese caso se usa obra_texto.
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True, index=True)
    obra_texto = Column(String(200), nullable=True)

    descripcion = Column(Text, nullable=True)
    fecha_inscripcion = Column(Date, nullable=False, index=True)
    monto = Column(Numeric(12, 2), nullable=False)

    fecha_pago = Column(Date, nullable=True, index=True)
    estado = Column(EstadoFacturaDB, nullable=False, default='pendiente', index=True)

    observaciones = Column(Text, nullable=True)

    # Transaccion INGRESO generada automaticamente al marcar como pagada
    transaccion_id = Column(UUID(as_uuid=True), ForeignKey("transacciones.id"), nullable=True)

    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    cliente = relationship("Cliente", backref="facturas")
    proyecto = relationship("Proyecto", backref="facturas")
    transaccion = relationship("Transaccion", foreign_keys=[transaccion_id])
    creador = relationship("Usuario", foreign_keys=[creado_por_id])

    def __repr__(self):
        return f"<Factura {self.id} ${self.monto} {self.estado}>"

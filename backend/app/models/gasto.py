from sqlalchemy import Column, String, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class Gasto(Base, BaseModel):
    """Modelo de gasto operativo."""
    __tablename__ = "gastos"

    descripcion = Column(String(300), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha = Column(Date, nullable=False)
    comprobante_url = Column(String(500), nullable=True)
    numero_comprobante = Column(String(100), nullable=True)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True)
    categoria_id = Column(UUID(as_uuid=True), ForeignKey("categorias_gasto.id"), nullable=True)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="gastos")
    categoria = relationship("CategoriaGasto")
    creador = relationship("Usuario", foreign_keys=[creado_por_id])

    def __repr__(self):
        return f"<Gasto {self.descripcion[:50]} ${self.monto}>"

from sqlalchemy import Column, String, Text, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class Gasto(Base, BaseModel):
    """Modelo de gasto operativo."""
    __tablename__ = "gastos"

    fecha = Column(Date, nullable=False)
    categoria = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True)  # NULL = gasto general
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    comprobante_url = Column(String(500), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="gastos")
    responsable = relationship("Usuario", foreign_keys=[responsable_id])
    creador = relationship("Usuario", foreign_keys=[created_by], back_populates="gastos_creados")

    def __repr__(self):
        return f"<Gasto {self.descripcion[:50]} ${self.monto}>"

from sqlalchemy import Column, String, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class Reporte(Base, BaseModel):
    """Modelo de reporte generado."""
    __tablename__ = "reportes"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(50), nullable=False)
    fecha_desde = Column(Date, nullable=False)
    fecha_hasta = Column(Date, nullable=False)
    pdf_url = Column(String(500), nullable=True)
    excel_url = Column(String(500), nullable=True)
    compartido_cliente = Column(Boolean, default=False, nullable=False)
    generado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="reportes")
    generado_por = relationship("Usuario", foreign_keys=[generado_por_id])

    def __repr__(self):
        return f"<Reporte {self.proyecto_id} {self.fecha_desde} - {self.fecha_hasta}>"

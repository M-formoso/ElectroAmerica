from sqlalchemy import Column, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class AsignacionEquipo(Base, BaseModel):
    """Modelo de asignación de equipo a proyecto/etapa."""
    __tablename__ = "asignaciones_equipo"

    equipo_id = Column(UUID(as_uuid=True), ForeignKey("equipos.id", ondelete="CASCADE"), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    fecha_asignacion = Column(Date, nullable=False)
    fecha_devolucion_est = Column(Date, nullable=True)
    fecha_devolucion_real = Column(Date, nullable=True)
    notas = Column(Text, nullable=True)
    asignado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    equipo = relationship("Equipo", back_populates="asignaciones")
    proyecto = relationship("Proyecto", back_populates="asignaciones_equipo")
    asignado_por = relationship("Usuario", foreign_keys=[asignado_por_id])

    def __repr__(self):
        return f"<AsignacionEquipo {self.equipo_id} -> {self.proyecto_id}>"

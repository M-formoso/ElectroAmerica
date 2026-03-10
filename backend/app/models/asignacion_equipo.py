from sqlalchemy import Column, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class AsignacionEquipo(Base, BaseModel):
    """Modelo de asignación de equipo a proyecto/etapa."""
    __tablename__ = "asignaciones_equipo"

    equipo_id = Column(UUID(as_uuid=True), ForeignKey("equipos.id"), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=True)
    fecha_desde = Column(Date, nullable=False)
    fecha_hasta = Column(Date, nullable=True)
    observaciones = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    equipo = relationship("Equipo", back_populates="asignaciones")
    proyecto = relationship("Proyecto", back_populates="asignaciones_equipo")
    etapa = relationship("Etapa", back_populates="asignaciones_equipo")
    creador = relationship("Usuario")

    def __repr__(self):
        return f"<AsignacionEquipo {self.equipo_id} -> {self.proyecto_id}>"

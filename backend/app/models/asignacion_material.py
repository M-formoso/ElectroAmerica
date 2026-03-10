from sqlalchemy import Column, Date, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class AsignacionMaterial(Base, BaseModel):
    """Modelo de asignación de material a proyecto/etapa."""
    __tablename__ = "asignaciones_material"

    material_id = Column(UUID(as_uuid=True), ForeignKey("materiales.id", ondelete="CASCADE"), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=True)
    cantidad = Column(Numeric(12, 4), nullable=False)
    fecha_asignacion = Column(Date, nullable=False)
    notas = Column(Text, nullable=True)
    asignado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    material = relationship("Material", back_populates="asignaciones")
    proyecto = relationship("Proyecto", back_populates="asignaciones_material")
    etapa = relationship("Etapa", back_populates="asignaciones_material")
    asignado_por = relationship("Usuario", foreign_keys=[asignado_por_id])

    def __repr__(self):
        return f"<AsignacionMaterial {self.material_id} -> {self.proyecto_id}>"

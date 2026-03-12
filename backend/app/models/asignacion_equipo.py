from sqlalchemy import Column, Date, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class AsignacionEquipo(Base, BaseModel):
    """Modelo de asignación de equipo a proyecto/etapa."""
    __tablename__ = "asignaciones_equipo"

    equipo_id = Column(UUID(as_uuid=True), ForeignKey("equipos.id", ondelete="CASCADE"), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id", ondelete="SET NULL"), nullable=True)

    fecha_asignacion = Column(Date, nullable=False)
    fecha_devolucion_est = Column(Date, nullable=True)
    fecha_devolucion_real = Column(Date, nullable=True)

    # Costos al momento de la asignación
    costo_hora_asignado = Column(Numeric(10, 2), nullable=True)
    costo_dia_asignado = Column(Numeric(10, 2), nullable=True)
    horas_uso = Column(Numeric(6, 2), nullable=True)

    notas = Column(Text, nullable=True)
    asignado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    equipo = relationship("Equipo", back_populates="asignaciones")
    proyecto = relationship("Proyecto", back_populates="asignaciones_equipo")
    etapa = relationship("Etapa", backref="asignaciones_equipo")
    asignado_por = relationship("Usuario", foreign_keys=[asignado_por_id])

    @property
    def costo_total(self):
        """Calcula el costo total del uso del equipo."""
        if self.horas_uso and self.costo_hora_asignado:
            return float(self.horas_uso) * float(self.costo_hora_asignado)
        elif self.fecha_asignacion and self.fecha_devolucion_real and self.costo_dia_asignado:
            dias = (self.fecha_devolucion_real - self.fecha_asignacion).days + 1
            return dias * float(self.costo_dia_asignado)
        return 0

    @property
    def esta_activa(self):
        """Indica si la asignación está activa."""
        return self.fecha_devolucion_real is None

    def __repr__(self):
        return f"<AsignacionEquipo {self.equipo_id} -> {self.proyecto_id}>"

from sqlalchemy import Column, String, Text, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class Jornada(Base, BaseModel):
    """Modelo de jornada de trabajo (mano de obra)."""
    __tablename__ = "jornadas"

    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=True)

    fecha = Column(Date, nullable=False)
    horas_trabajadas = Column(Numeric(4, 2), nullable=False)  # Ej: 8.50 horas
    horas_extra = Column(Numeric(4, 2), default=0, nullable=False)

    # Costos
    costo_hora = Column(Numeric(10, 2), nullable=False)
    costo_hora_extra = Column(Numeric(10, 2), nullable=True)

    # Descripcion del trabajo realizado
    descripcion = Column(Text, nullable=True)
    notas = Column(Text, nullable=True)

    # Quien registra la jornada
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    usuario = relationship("Usuario", foreign_keys=[usuario_id], backref="jornadas")
    proyecto = relationship("Proyecto", backref="jornadas")
    etapa = relationship("Etapa", backref="jornadas")
    registrado_por = relationship("Usuario", foreign_keys=[registrado_por_id])

    @property
    def costo_total(self):
        """Calcula el costo total de la jornada."""
        costo_normal = float(self.horas_trabajadas) * float(self.costo_hora)
        costo_extra = 0
        if self.horas_extra and self.costo_hora_extra:
            costo_extra = float(self.horas_extra) * float(self.costo_hora_extra)
        return costo_normal + costo_extra

    def __repr__(self):
        return f"<Jornada {self.usuario_id} - {self.fecha} - {self.horas_trabajadas}h>"

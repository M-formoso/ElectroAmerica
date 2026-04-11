from sqlalchemy import Column, String, Text, Date, DateTime, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ENUM as PgEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoJornada(str, enum.Enum):
    """Estados de una jornada de operario."""
    planificada = "planificada"
    iniciada = "iniciada"
    en_camino = "en_camino"
    en_obra = "en_obra"
    finalizada = "finalizada"
    cancelada = "cancelada"


# PostgreSQL ENUM
EstadoJornadaDB = PgEnum(
    'planificada', 'iniciada', 'en_camino', 'en_obra', 'finalizada', 'cancelada',
    name='estadojornada',
    create_type=False
)


class JornadaOperario(Base, BaseModel):
    """
    Modelo de jornada de operario con control de vehículo, destino y materiales.
    Extiende la funcionalidad de registro de horas con control logístico.
    """
    __tablename__ = "jornadas_operario"

    # Operario que realiza la jornada
    operario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Fecha de la jornada
    fecha = Column(Date, nullable=False)

    # Vehículo asignado (referencia a equipo tipo vehículo)
    vehiculo_id = Column(UUID(as_uuid=True), ForeignKey("equipos.id"), nullable=True)

    # Destino: proyecto y etapa/zona
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=True)

    # Kilometraje del vehículo
    km_inicial = Column(Integer, nullable=True)
    km_final = Column(Integer, nullable=True)

    # Horarios
    hora_inicio = Column(DateTime(timezone=True), nullable=True)
    hora_llegada_obra = Column(DateTime(timezone=True), nullable=True)
    hora_fin = Column(DateTime(timezone=True), nullable=True)

    # Horas trabajadas (calculado o manual)
    horas_trabajadas = Column(Numeric(4, 2), nullable=True)
    horas_extra = Column(Numeric(4, 2), default=0, nullable=True)

    # Estado de la jornada
    estado = Column(EstadoJornadaDB, default='planificada', nullable=False)

    # Observaciones
    observaciones_inicio = Column(Text, nullable=True)
    observaciones_cierre = Column(Text, nullable=True)
    novedades = Column(Text, nullable=True)

    # Referencias de planificación y registro
    asignacion_diaria_id = Column(UUID(as_uuid=True), ForeignKey("asignaciones_diarias.id"), nullable=True)
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    operario = relationship("Usuario", foreign_keys=[operario_id], backref="jornadas_operario")
    vehiculo = relationship("Equipo", foreign_keys=[vehiculo_id])
    proyecto = relationship("Proyecto", backref="jornadas_operario")
    etapa = relationship("Etapa", backref="jornadas_operario")
    asignacion_diaria = relationship("AsignacionDiaria", back_populates="jornada")
    registrado_por = relationship("Usuario", foreign_keys=[registrado_por_id])

    # Materiales de la jornada
    materiales = relationship(
        "MaterialJornada",
        back_populates="jornada",
        cascade="all, delete-orphan"
    )

    @property
    def km_recorridos(self):
        """Calcula los kilómetros recorridos en la jornada."""
        if self.km_inicial and self.km_final:
            return self.km_final - self.km_inicial
        return None

    @property
    def duracion_total(self):
        """Calcula la duración total de la jornada en horas."""
        if self.hora_inicio and self.hora_fin:
            delta = self.hora_fin - self.hora_inicio
            return round(delta.total_seconds() / 3600, 2)
        return None

    def __repr__(self):
        return f"<JornadaOperario {self.operario_id} - {self.fecha} - {self.estado}>"

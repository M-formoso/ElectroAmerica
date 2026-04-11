from sqlalchemy import Column, String, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM as PgEnum, JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoAsignacion(str, enum.Enum):
    """Estados de una asignación diaria."""
    planificada = "planificada"     # Creada por supervisor
    confirmada = "confirmada"       # Operario la vio/aceptó
    en_curso = "en_curso"          # Jornada iniciada
    completada = "completada"      # Jornada finalizada
    cancelada = "cancelada"        # Cancelada


# PostgreSQL ENUM
EstadoAsignacionDB = PgEnum(
    'planificada', 'confirmada', 'en_curso', 'completada', 'cancelada',
    name='estadoasignacion',
    create_type=False
)


class AsignacionDiaria(Base, BaseModel):
    """
    Modelo de asignación diaria creada por el supervisor.
    Define qué operario va a qué proyecto con qué vehículo y materiales.
    """
    __tablename__ = "asignaciones_diarias"

    # Fecha de la asignación
    fecha = Column(Date, nullable=False)

    # Operario asignado
    operario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Destino
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=True)

    # Vehículo asignado
    vehiculo_id = Column(UUID(as_uuid=True), ForeignKey("equipos.id"), nullable=True)

    # Estado
    estado = Column(EstadoAsignacionDB, default='planificada', nullable=False)

    # Tareas planificadas (lista de IDs de items_trabajo o descripciones)
    tareas_planificadas = Column(JSONB, nullable=True)
    # Formato: [{"item_id": "uuid", "descripcion": "texto"}, ...]

    # Materiales planificados (antes de que se cree la jornada)
    materiales_planificados = Column(JSONB, nullable=True)
    # Formato: [{"material_id": "uuid", "cantidad": 10, "notas": "..."}, ...]

    # Notas del supervisor
    notas = Column(Text, nullable=True)
    prioridad = Column(String(20), default="media", nullable=False)  # baja, media, alta, urgente

    # Quién creó la asignación
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    operario = relationship("Usuario", foreign_keys=[operario_id], backref="asignaciones_diarias")
    proyecto = relationship("Proyecto", backref="asignaciones_diarias")
    etapa = relationship("Etapa", backref="asignaciones_diarias")
    vehiculo = relationship("Equipo", foreign_keys=[vehiculo_id])
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])

    # Jornada resultante (1:1)
    jornada = relationship("JornadaOperario", back_populates="asignacion_diaria", uselist=False)

    def __repr__(self):
        return f"<AsignacionDiaria {self.fecha} - {self.operario_id} - {self.proyecto_id}>"

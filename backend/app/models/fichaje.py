from sqlalchemy import Column, String, Text, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM as PgEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoFichaje(str, enum.Enum):
    activo = "activo"
    completado = "completado"
    cancelado = "cancelado"
    inasistencia = "inasistencia"


EstadoFichajeDB = PgEnum(
    'activo', 'completado', 'cancelado', 'inasistencia',
    name='estadofichaje',
    create_type=False
)


class FichajeJornada(Base, BaseModel):
    __tablename__ = "fichajes_jornada"

    operario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(DateTime(timezone=True), nullable=False)
    hora_fin = Column(DateTime(timezone=True), nullable=True)
    horas_trabajadas = Column(Numeric(5, 2), nullable=True)
    estado = Column(EstadoFichajeDB, nullable=False, default=EstadoFichaje.activo)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True)
    notas_inicio = Column(Text, nullable=True)
    notas_fin = Column(Text, nullable=True)

    # Relationships
    operario = relationship("Usuario", foreign_keys=[operario_id])
    proyecto = relationship("Proyecto", foreign_keys=[proyecto_id])

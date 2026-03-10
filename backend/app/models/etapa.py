from sqlalchemy import Column, String, Text, Date, Integer, Enum, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoEtapa(str, enum.Enum):
    """Estados posibles de una etapa."""
    pendiente = "pendiente"
    en_curso = "en_curso"
    completada = "completada"
    pausada = "pausada"


class Etapa(Base, BaseModel):
    """Modelo de etapa dentro de un proyecto."""
    __tablename__ = "etapas"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    orden = Column(Integer, default=0, nullable=False)
    fecha_inicio_est = Column(Date, nullable=True)
    fecha_fin_est = Column(Date, nullable=True)
    fecha_inicio_real = Column(Date, nullable=True)
    fecha_fin_real = Column(Date, nullable=True)
    estado = Column(Enum(EstadoEtapa), default=EstadoEtapa.pendiente, nullable=False)
    porcentaje_avance = Column(Numeric(5, 2), default=0, nullable=False)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="etapas")
    items_trabajo = relationship(
        "ItemTrabajo",
        back_populates="etapa",
        cascade="all, delete-orphan"
    )
    fotos = relationship(
        "Foto",
        back_populates="etapa"
    )
    asignaciones_material = relationship(
        "AsignacionMaterial",
        back_populates="etapa"
    )
    asignaciones_equipo = relationship(
        "AsignacionEquipo",
        back_populates="etapa"
    )

    def __repr__(self):
        return f"<Etapa {self.nombre}>"

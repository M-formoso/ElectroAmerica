from sqlalchemy import Column, String, Text, Date, Integer, Enum, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoEtapa(str, enum.Enum):
    """Estados posibles de una etapa."""
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"
    pausada = "pausada"


class Etapa(Base, BaseModel):
    """Modelo de etapa dentro de un proyecto."""
    __tablename__ = "etapas"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)

    # Soporte para sub-etapas
    etapa_padre_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=True)

    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    orden = Column(Integer, default=0, nullable=False)
    fecha_inicio_est = Column(Date, nullable=True)
    fecha_fin_est = Column(Date, nullable=True)
    fecha_inicio_real = Column(Date, nullable=True)
    fecha_fin_real = Column(Date, nullable=True)
    estado = Column(Enum(EstadoEtapa), default=EstadoEtapa.pendiente, nullable=False)
    porcentaje_avance = Column(Numeric(5, 2), default=0, nullable=False)

    # Peso para calculo de avance (0-100, por defecto igual peso)
    peso = Column(Numeric(5, 2), default=100, nullable=False)

    # Color para timeline (hex)
    color = Column(String(7), nullable=True)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="etapas")

    # Sub-etapas
    etapa_padre = relationship("Etapa", remote_side="Etapa.id", backref="sub_etapas")

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

    @property
    def es_subetapa(self):
        """Indica si es una sub-etapa."""
        return self.etapa_padre_id is not None

    @property
    def tiene_demora(self):
        """Indica si la etapa tiene demora."""
        from datetime import date
        if self.fecha_fin_est and self.estado != EstadoEtapa.completada:
            return date.today() > self.fecha_fin_est
        return False

    def __repr__(self):
        return f"<Etapa {self.nombre}>"

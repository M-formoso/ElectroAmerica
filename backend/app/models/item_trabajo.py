from sqlalchemy import Column, String, Numeric, Enum, ForeignKey, Date, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoItem(str, enum.Enum):
    """Estados posibles de un ítem de trabajo."""
    pendiente = "pendiente"
    en_curso = "en_curso"
    completado = "completado"


class PrioridadItem(str, enum.Enum):
    """Prioridad del ítem de trabajo."""
    baja = "baja"
    media = "media"
    alta = "alta"
    urgente = "urgente"


class ItemTrabajo(Base, BaseModel):
    """Modelo de ítem de trabajo dentro de una etapa."""
    __tablename__ = "items_trabajo"

    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=False)
    descripcion = Column(String(500), nullable=False)
    notas = Column(Text, nullable=True)

    # Responsable - puede ser texto o referencia a usuario
    responsable = Column(String(100), nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # Cantidades y unidades
    cantidad = Column(Numeric(10, 2), nullable=True)
    unidad = Column(String(30), nullable=True)

    # Estado y prioridad
    estado = Column(Enum(EstadoItem), default=EstadoItem.pendiente, nullable=False)
    prioridad = Column(Enum(PrioridadItem), default=PrioridadItem.media, nullable=False)
    orden = Column(Integer, default=0, nullable=False)

    # Fechas planificadas
    fecha_inicio_est = Column(Date, nullable=True)
    fecha_fin_est = Column(Date, nullable=True)
    fecha_inicio_real = Column(Date, nullable=True)
    fecha_fin_real = Column(Date, nullable=True)

    # Porcentaje de avance del item
    porcentaje_avance = Column(Numeric(5, 2), default=0, nullable=False)

    # Precio (solo visible admin/supervisor)
    precio_unitario = Column(Numeric(12, 2), nullable=True)

    # Relaciones
    etapa = relationship("Etapa", back_populates="items_trabajo")
    responsable_usuario = relationship("Usuario", foreign_keys=[responsable_id])
    precios_historial = relationship(
        "PrecioItem",
        back_populates="item_trabajo",
        cascade="all, delete-orphan"
    )

    @property
    def tiene_demora(self):
        """Indica si el ítem tiene demora."""
        from datetime import date
        if self.fecha_fin_est and self.estado != EstadoItem.completado:
            return date.today() > self.fecha_fin_est
        return False

    @property
    def costo_total(self):
        """Calcula el costo total del ítem."""
        if self.cantidad and self.precio_unitario:
            return float(self.cantidad) * float(self.precio_unitario)
        return 0

    def __repr__(self):
        return f"<ItemTrabajo {self.descripcion[:50]}>"

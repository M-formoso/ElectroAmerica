from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID, ENUM as PgEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class TipoAlerta(str, enum.Enum):
    """Tipos de alerta del sistema."""
    STOCK_MINIMO = "stock_minimo"
    DEMORA_ETAPA = "demora_etapa"
    ETAPA_PENDIENTE = "etapa_pendiente"
    LIMITE_CREDITO = "limite_credito"
    EQUIPO_MANTENIMIENTO = "equipo_mantenimiento"
    PROYECTO_VENCIDO = "proyecto_vencido"
    PAGO_PENDIENTE = "pago_pendiente"


class PrioridadAlerta(str, enum.Enum):
    """Prioridad de la alerta."""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


# PostgreSQL ENUMs
TipoAlertaDB = PgEnum(
    'stock_minimo', 'demora_etapa', 'etapa_pendiente', 'limite_credito',
    'equipo_mantenimiento', 'proyecto_vencido', 'pago_pendiente',
    name='tipoalerta',
    create_type=False
)

PrioridadAlertaDB = PgEnum(
    'baja', 'media', 'alta', 'critica',
    name='prioridadalerta',
    create_type=False
)


class Alerta(Base, BaseModel):
    """Modelo de alerta del sistema."""
    __tablename__ = "alertas"

    tipo = Column(TipoAlertaDB, nullable=False)
    prioridad = Column(PrioridadAlertaDB, default='media', nullable=False)
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)

    # Referencia al objeto que genera la alerta
    referencia_tipo = Column(String(50), nullable=True)  # proyecto, material, equipo, cliente, etapa
    referencia_id = Column(UUID(as_uuid=True), nullable=True)

    # Estado
    leida = Column(Boolean, default=False, nullable=False)
    resuelta = Column(Boolean, default=False, nullable=False)
    fecha_resolucion = Column(DateTime(timezone=True), nullable=True)

    # Usuario destino (opcional, si es null es para todos los admins)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    resuelto_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    usuario = relationship("Usuario", foreign_keys=[usuario_id], backref="alertas")
    resuelto_por = relationship("Usuario", foreign_keys=[resuelto_por_id])

    def __repr__(self):
        return f"<Alerta {self.tipo.value}: {self.titulo[:30]}>"

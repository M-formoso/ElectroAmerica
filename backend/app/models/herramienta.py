from sqlalchemy import Column, String, Text, Enum, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoHerramienta(str, enum.Enum):
    """Estados posibles de una herramienta."""
    buen_estado = "buen_estado"
    en_reparacion = "en_reparacion"
    rota = "rota"


class EstadoPrestamo(str, enum.Enum):
    """Estados de disponibilidad para préstamo."""
    disponible = "disponible"
    en_uso = "en_uso"


class Herramienta(Base, BaseModel):
    """Modelo de herramienta para control de préstamos."""
    __tablename__ = "herramientas"

    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    estado = Column(Enum(EstadoHerramienta), default=EstadoHerramienta.buen_estado, nullable=False)
    estado_prestamo = Column(Enum(EstadoPrestamo), default=EstadoPrestamo.disponible, nullable=False)
    foto_url = Column(String(500), nullable=True)
    foto_public_id = Column(String(300), nullable=True)

    # Relaciones
    prestamos = relationship(
        "PrestamoHerramienta",
        back_populates="herramienta",
        cascade="all, delete-orphan",
        order_by="desc(PrestamoHerramienta.fecha_retiro)"
    )

    @property
    def prestamo_activo(self):
        """Retorna el préstamo activo si existe."""
        for prestamo in self.prestamos:
            if prestamo.fecha_devolucion is None:
                return prestamo
        return None

    def __repr__(self):
        return f"<Herramienta {self.nombre}>"


class PrestamoHerramienta(Base, BaseModel):
    """Modelo de préstamo de herramienta."""
    __tablename__ = "prestamos_herramienta"

    herramienta_id = Column(UUID(as_uuid=True), ForeignKey("herramientas.id"), nullable=False)
    retirado_por = Column(String(200), nullable=False)  # Nombre de quien retira
    fecha_retiro = Column(Date, nullable=False)
    fecha_devolucion = Column(Date, nullable=True)
    notas_devolucion = Column(Text, nullable=True)

    # Usuario que registró el préstamo/devolución (opcional)
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    herramienta = relationship("Herramienta", back_populates="prestamos")
    registrado_por = relationship("Usuario", foreign_keys=[registrado_por_id])

    def __repr__(self):
        return f"<PrestamoHerramienta {self.herramienta_id} - {self.retirado_por}>"

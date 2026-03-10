from sqlalchemy import Column, String, Text, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class TipoEquipo(str, enum.Enum):
    """Tipos de equipo."""
    camion = "camion"
    excavadora = "excavadora"
    compactadora = "compactadora"
    hormigonera = "hormigonera"
    grua = "grua"
    generador = "generador"
    herramienta = "herramienta"
    otro = "otro"


class EstadoEquipo(str, enum.Enum):
    """Estados de equipo."""
    disponible = "disponible"
    asignado = "asignado"
    mantenimiento = "mantenimiento"
    fuera_servicio = "fuera_servicio"


class Equipo(Base, BaseModel):
    """Modelo de equipo/maquinaria/vehículo."""
    __tablename__ = "equipos"

    nombre = Column(String(255), nullable=False)
    tipo = Column(Enum(TipoEquipo), nullable=False)
    patente = Column(String(20), nullable=True)
    codigo_interno = Column(String(50), nullable=True, unique=True)
    marca = Column(String(100), nullable=True)
    modelo = Column(String(100), nullable=True)
    anio = Column(String(4), nullable=True)
    estado = Column(Enum(EstadoEquipo), default=EstadoEquipo.disponible, nullable=False)
    observaciones = Column(Text, nullable=True)

    # Relaciones
    asignaciones = relationship(
        "AsignacionEquipo",
        back_populates="equipo",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Equipo {self.nombre}>"

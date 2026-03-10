from sqlalchemy import Column, String, Text, Date, Numeric, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class TipoEquipo(str, enum.Enum):
    """Tipos de equipo."""
    herramienta = "herramienta"
    vehiculo = "vehiculo"
    maquinaria = "maquinaria"
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

    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo = Column(Enum(TipoEquipo), nullable=False)
    marca = Column(String(100), nullable=True)
    modelo = Column(String(100), nullable=True)
    estado = Column(Enum(EstadoEquipo), default=EstadoEquipo.disponible, nullable=False)
    fecha_adquisicion = Column(Date, nullable=True)
    costo_adquisicion = Column(Numeric(12, 2), nullable=True)

    # Relaciones
    asignaciones = relationship(
        "AsignacionEquipo",
        back_populates="equipo",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Equipo {self.nombre}>"

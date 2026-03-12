from sqlalchemy import Column, String, Text, Date, Numeric, Enum, Integer
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

    # Datos de adquisicion
    fecha_adquisicion = Column(Date, nullable=True)
    costo_adquisicion = Column(Numeric(12, 2), nullable=True)

    # Costos operativos
    costo_por_hora = Column(Numeric(10, 2), nullable=True)
    costo_por_dia = Column(Numeric(10, 2), nullable=True)
    costo_mantenimiento_mensual = Column(Numeric(10, 2), nullable=True)

    # Datos del vehiculo (si aplica)
    patente = Column(String(20), nullable=True)
    numero_serie = Column(String(100), nullable=True)
    año = Column(Integer, nullable=True)

    # Mantenimiento
    fecha_ultimo_mantenimiento = Column(Date, nullable=True)
    fecha_proximo_mantenimiento = Column(Date, nullable=True)
    km_actual = Column(Integer, nullable=True)
    km_proximo_service = Column(Integer, nullable=True)
    notas_mantenimiento = Column(Text, nullable=True)

    # Relaciones
    asignaciones = relationship(
        "AsignacionEquipo",
        back_populates="equipo",
        cascade="all, delete-orphan"
    )

    @property
    def requiere_mantenimiento(self):
        """Indica si el equipo requiere mantenimiento próximamente."""
        from datetime import date, timedelta
        if self.fecha_proximo_mantenimiento:
            return self.fecha_proximo_mantenimiento <= date.today() + timedelta(days=7)
        if self.km_proximo_service and self.km_actual:
            return self.km_actual >= self.km_proximo_service - 500
        return False

    def __repr__(self):
        return f"<Equipo {self.nombre}>"

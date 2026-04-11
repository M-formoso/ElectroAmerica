from sqlalchemy import Column, String, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM as PgEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoMaterialJornada(str, enum.Enum):
    """Estados del material en una jornada."""
    asignado = "asignado"           # El supervisor lo incluyó en la lista
    pendiente_retiro = "pendiente_retiro"  # Esperando que el operario lo retire
    cargado = "cargado"             # El operario confirmó que lo cargó
    en_uso = "en_uso"               # En la obra siendo utilizado
    consumido = "consumido"         # Se usó completamente
    devuelto_deposito = "devuelto_deposito"  # Sobró y volvió al depósito
    devuelto_obra = "devuelto_obra"  # Sobró y quedó en la obra


class DestinoDevolucion(str, enum.Enum):
    """Destino de los materiales sobrantes."""
    deposito = "deposito"
    obra = "obra"
    otro_operario = "otro_operario"


# PostgreSQL ENUMs
EstadoMaterialJornadaDB = PgEnum(
    'asignado', 'pendiente_retiro', 'cargado', 'en_uso',
    'consumido', 'devuelto_deposito', 'devuelto_obra',
    name='estadomaterialjornada',
    create_type=False
)

DestinoDevolucionDB = PgEnum(
    'deposito', 'obra', 'otro_operario',
    name='destinodevolucion',
    create_type=False
)


class MaterialJornada(Base, BaseModel):
    """
    Modelo para registrar los materiales que lleva/usa un operario en cada jornada.
    Permite el seguimiento desde la asignación hasta el consumo/devolución.
    """
    __tablename__ = "materiales_jornada"

    # Referencia a la jornada
    jornada_id = Column(UUID(as_uuid=True), ForeignKey("jornadas_operario.id"), nullable=False)

    # Material
    material_id = Column(UUID(as_uuid=True), ForeignKey("materiales.id"), nullable=False)

    # Cantidades
    cantidad_asignada = Column(Numeric(12, 4), nullable=False)  # Lo que debía llevar
    cantidad_cargada = Column(Numeric(12, 4), nullable=True)    # Lo que confirmó que cargó
    cantidad_consumida = Column(Numeric(12, 4), nullable=True)  # Lo que usó efectivamente
    cantidad_devuelta = Column(Numeric(12, 4), nullable=True)   # Lo que sobró

    # Estado del material en esta jornada
    estado = Column(EstadoMaterialJornadaDB, default='asignado', nullable=False)

    # Destino de devolución (si aplica)
    destino_devolucion = Column(DestinoDevolucionDB, nullable=True)

    # Notas/observaciones
    notas = Column(Text, nullable=True)

    # Si fue asignado automáticamente desde una actividad tipo
    actividad_tipo_id = Column(UUID(as_uuid=True), ForeignKey("actividades_tipo.id"), nullable=True)

    # Relaciones
    jornada = relationship("JornadaOperario", back_populates="materiales")
    material = relationship("Material", backref="usos_jornada")
    actividad_tipo = relationship("ActividadTipo")

    @property
    def cantidad_pendiente(self):
        """Calcula la cantidad pendiente de usar/devolver."""
        cargada = float(self.cantidad_cargada or 0)
        consumida = float(self.cantidad_consumida or 0)
        devuelta = float(self.cantidad_devuelta or 0)
        return cargada - consumida - devuelta

    def __repr__(self):
        return f"<MaterialJornada {self.material_id} - Jornada {self.jornada_id}>"

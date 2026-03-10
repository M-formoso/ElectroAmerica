from sqlalchemy import Column, String, Numeric, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class Material(Base, BaseModel):
    """Modelo de material en inventario."""
    __tablename__ = "materiales"

    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    unidad = Column(String(50), nullable=False)
    stock_actual = Column(Numeric(12, 4), nullable=False, default=0)
    stock_minimo = Column(Numeric(12, 4), nullable=False, default=0)
    precio_unitario = Column(Numeric(12, 2), nullable=True)
    ubicacion_almacen = Column(String(100), nullable=True)

    # Relaciones
    movimientos = relationship(
        "MovimientoStock",
        back_populates="material",
        cascade="all, delete-orphan"
    )
    asignaciones = relationship(
        "AsignacionMaterial",
        back_populates="material"
    )

    def __repr__(self):
        return f"<Material {self.nombre}>"

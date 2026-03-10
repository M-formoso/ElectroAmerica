from sqlalchemy import Column, String, Numeric
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class Material(Base, BaseModel):
    """Modelo de material en inventario."""
    __tablename__ = "materiales"

    nombre = Column(String(255), nullable=False)
    codigo = Column(String(50), nullable=True, unique=True)
    categoria = Column(String(100), nullable=True)
    unidad = Column(String(30), nullable=False)
    stock_actual = Column(Numeric(12, 3), nullable=False, default=0)
    stock_minimo = Column(Numeric(12, 3), nullable=False, default=0)
    precio_costo = Column(Numeric(12, 2), nullable=True)
    proveedor = Column(String(255), nullable=True)

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

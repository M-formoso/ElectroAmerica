from sqlalchemy import Column, String, Text
from app.db.base_class import Base, BaseModel


class CategoriaGasto(Base, BaseModel):
    """Modelo de categoría de gasto."""
    __tablename__ = "categorias_gasto"

    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    color = Column(String(7), nullable=False, default="#E53935")  # Hex color

    def __repr__(self):
        return f"<CategoriaGasto {self.nombre}>"

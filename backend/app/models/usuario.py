from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class RolUsuario(str, enum.Enum):
    """Roles de usuario en el sistema."""
    administrador = "administrador"
    supervisor = "supervisor"
    operario = "operario"
    cliente = "cliente"


class Usuario(Base, BaseModel):
    """Modelo de usuario del sistema."""
    __tablename__ = "usuarios"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=True)
    rol = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.operario)

    # Relaciones
    proyectos_asignados = relationship(
        "Proyecto",
        back_populates="cliente",
        foreign_keys="Proyecto.cliente_id"
    )

    def __repr__(self):
        return f"<Usuario {self.email}>"

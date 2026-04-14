from sqlalchemy import Column, String, Enum, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class RolUsuario(str, enum.Enum):
    """Roles de usuario en el sistema."""
    administrador = "administrador"
    supervisor = "supervisor"
    operario = "operario"
    cliente = "cliente"


# Módulos disponibles en el sistema
MODULOS_SISTEMA = [
    "dashboard",
    "proyectos",
    "clientes",
    "materiales",
    "equipos",
    "herramientas",
    "finanzas",
    "reportes",
    "usuarios",
    "alertas",
    "auditoria",
    "jornadas_operario",
    "jornadas_gestion",
    "actividades_tipo",
]


class Usuario(Base, BaseModel):
    """Modelo de usuario del sistema."""
    __tablename__ = "usuarios"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=True)
    rol = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.operario)

    # Permisos por módulo - si es None, usa permisos por defecto del rol
    # Si es lista vacía, no tiene acceso a ningún módulo extra
    modulos_permitidos = Column(JSONB, nullable=True, default=None)

    # Flag para superadmin que ve todo
    es_superadmin = Column(Boolean, nullable=False, default=False)

    # Relaciones
    proyectos_asignados = relationship(
        "Proyecto",
        back_populates="cliente",
        foreign_keys="Proyecto.cliente_id"
    )

    def __repr__(self):
        return f"<Usuario {self.email}>"

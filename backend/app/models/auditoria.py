"""
Modelo para registro de auditoría de acciones de usuarios.
Registra todas las acciones importantes realizadas en el sistema.
"""
from sqlalchemy import Column, String, Text, ForeignKey, Enum as PgEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.db.base_class import Base, BaseModel


class TipoAccion(str, enum.Enum):
    """Tipos de acciones que se pueden auditar."""
    crear = "crear"
    actualizar = "actualizar"
    eliminar = "eliminar"
    login = "login"
    logout = "logout"
    ver = "ver"
    exportar = "exportar"
    asignar = "asignar"
    desasignar = "desasignar"
    cambiar_estado = "cambiar_estado"
    subir_archivo = "subir_archivo"


class ModuloAuditado(str, enum.Enum):
    """Módulos del sistema que se auditan."""
    auth = "auth"
    usuarios = "usuarios"
    proyectos = "proyectos"
    etapas = "etapas"
    items_trabajo = "items_trabajo"
    materiales = "materiales"
    equipos = "equipos"
    gastos = "gastos"
    clientes = "clientes"
    fotos = "fotos"
    reportes = "reportes"
    finanzas = "finanzas"
    alertas = "alertas"
    jornadas = "jornadas"


TipoAccionDB = PgEnum(
    TipoAccion,
    name='tipoaccion',
    create_type=False
)

ModuloAuditadoDB = PgEnum(
    ModuloAuditado,
    name='moduloauditado',
    create_type=False
)


class Auditoria(Base, BaseModel):
    """Modelo de auditoría para registrar acciones de usuarios."""
    __tablename__ = "auditorias"

    # Usuario que realizó la acción
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True
    )

    # Tipo de acción realizada
    accion = Column(TipoAccionDB, nullable=False)

    # Módulo donde se realizó la acción
    modulo = Column(ModuloAuditadoDB, nullable=False)

    # Descripción de la acción
    descripcion = Column(String(500), nullable=False)

    # ID del recurso afectado (proyecto, material, etc.)
    recurso_id = Column(UUID(as_uuid=True), nullable=True)

    # Tipo del recurso afectado
    recurso_tipo = Column(String(50), nullable=True)

    # Datos adicionales en formato JSON
    # Puede incluir: valores anteriores, nuevos valores, detalles del request, etc.
    datos_adicionales = Column(JSONB, nullable=True)

    # IP del usuario
    ip_address = Column(String(50), nullable=True)

    # User Agent del navegador
    user_agent = Column(String(500), nullable=True)

    # Relaciones
    usuario = relationship("Usuario", backref="auditorias")

    def __repr__(self):
        return f"<Auditoria {self.accion.value} {self.modulo.value} by {self.usuario_id}>"

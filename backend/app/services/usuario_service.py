from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.models.usuario import Usuario, RolUsuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.core.security import hashear_password, verificar_password


def obtener_usuarios(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    rol: Optional[RolUsuario] = None,
    solo_activos: bool = True
) -> List[Usuario]:
    """Obtiene lista de usuarios."""
    query = db.query(Usuario)

    if solo_activos:
        query = query.filter(Usuario.activo == True)
    if rol:
        query = query.filter(Usuario.rol == rol)

    return query.offset(skip).limit(limit).all()


def obtener_usuario(db: Session, usuario_id: UUID) -> Optional[Usuario]:
    """Obtiene un usuario por ID."""
    return db.query(Usuario).filter(
        Usuario.id == usuario_id,
        Usuario.activo == True
    ).first()


def obtener_usuario_por_email(db: Session, email: str) -> Optional[Usuario]:
    """Obtiene un usuario por email."""
    return db.query(Usuario).filter(Usuario.email == email).first()


def crear_usuario(db: Session, usuario: UsuarioCreate) -> Usuario:
    """Crea un nuevo usuario."""
    db_usuario = Usuario(
        email=usuario.email,
        password_hash=hashear_password(usuario.password),
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        telefono=usuario.telefono,
        rol=usuario.rol
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def actualizar_usuario(
    db: Session,
    usuario_id: UUID,
    usuario: UsuarioUpdate
) -> Optional[Usuario]:
    """Actualiza un usuario existente."""
    db_usuario = obtener_usuario(db, usuario_id)
    if not db_usuario:
        return None

    update_data = usuario.model_dump(exclude_unset=True)

    # Si se actualiza el password, hashearlo
    if "password" in update_data:
        update_data["password_hash"] = hashear_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(db_usuario, field, value)

    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def eliminar_usuario(db: Session, usuario_id: UUID) -> bool:
    """Soft delete de usuario."""
    usuario = obtener_usuario(db, usuario_id)
    if not usuario:
        return False

    usuario.activo = False
    db.commit()
    return True


def autenticar_usuario(db: Session, email: str, password: str) -> Optional[Usuario]:
    """Autentica un usuario por email y password."""
    usuario = db.query(Usuario).filter(
        Usuario.email == email,
        Usuario.activo == True
    ).first()

    if not usuario:
        return None

    if not verificar_password(password, usuario.password_hash):
        return None

    return usuario


def actualizar_ultimo_acceso(db: Session, usuario: Usuario) -> None:
    """Actualiza el último acceso del usuario."""
    usuario.ultimo_acceso = datetime.utcnow()
    db.commit()


def obtener_clientes(db: Session, skip: int = 0, limit: int = 100) -> List[Usuario]:
    """Obtiene lista de usuarios con rol cliente."""
    return obtener_usuarios(db, skip, limit, rol=RolUsuario.cliente)


def asignar_proyectos_a_cliente(
    db: Session,
    cliente_id: UUID,
    proyecto_ids: List[UUID]
) -> bool:
    """Asigna proyectos a un cliente."""
    from app.models.proyecto import Proyecto

    cliente = obtener_usuario(db, cliente_id)
    if not cliente or cliente.rol != RolUsuario.cliente:
        return False

    # Actualizar proyectos
    db.query(Proyecto).filter(
        Proyecto.id.in_(proyecto_ids)
    ).update({Proyecto.cliente_id: cliente_id}, synchronize_session=False)

    db.commit()
    return True

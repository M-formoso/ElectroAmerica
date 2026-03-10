from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import verificar_token
from app.models.usuario import Usuario, RolUsuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator:
    """Dependency para obtener sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_usuario_actual(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Usuario:
    """Obtiene el usuario actual a partir del token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verificar_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    usuario = db.query(Usuario).filter(
        Usuario.id == user_id,
        Usuario.activo == True
    ).first()

    if usuario is None:
        raise credentials_exception

    return usuario


def require_roles(*roles: RolUsuario):
    """Factory de dependency para requerir roles específicos."""
    async def role_checker(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta acción"
            )
        return usuario
    return role_checker


# Shortcuts para roles comunes
require_admin = require_roles(RolUsuario.administrador)

require_admin_or_supervisor = require_roles(
    RolUsuario.administrador,
    RolUsuario.supervisor
)

require_staff = require_roles(
    RolUsuario.administrador,
    RolUsuario.supervisor,
    RolUsuario.operario
)

require_any_authenticated = require_roles(
    RolUsuario.administrador,
    RolUsuario.supervisor,
    RolUsuario.operario,
    RolUsuario.cliente
)

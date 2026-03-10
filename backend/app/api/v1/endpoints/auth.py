from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_usuario_actual
from app.core.security import crear_access_token, crear_refresh_token, verificar_token
from app.schemas.usuario import Token, UsuarioResponse
from app.services import usuario_service
from app.models.usuario import Usuario

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Autenticación de usuario con email y password.
    Retorna tokens de acceso y refresco.
    """
    usuario = usuario_service.autenticar_usuario(
        db, form_data.username, form_data.password
    )

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Crear tokens
    token_data = {"sub": str(usuario.id), "rol": usuario.rol.value}

    return Token(
        access_token=crear_access_token(token_data),
        refresh_token=crear_refresh_token(token_data)
    )


@router.get("/me", response_model=UsuarioResponse)
def get_current_user(usuario: Usuario = Depends(get_usuario_actual)):
    """Obtiene el usuario autenticado actual."""
    return usuario


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresca el token de acceso usando el refresh token.
    """
    payload = verificar_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido"
        )

    usuario = usuario_service.obtener_usuario(db, payload["sub"])
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )

    token_data = {"sub": str(usuario.id), "rol": usuario.rol.value}

    return Token(
        access_token=crear_access_token(token_data),
        refresh_token=crear_refresh_token(token_data)
    )


@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Cambia la contraseña del usuario autenticado."""
    from app.core.security import verificar_password, hashear_password

    if not verificar_password(current_password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    usuario.hashed_password = hashear_password(new_password)
    db.commit()

    return {"message": "Contraseña actualizada correctamente"}

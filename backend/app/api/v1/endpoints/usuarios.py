from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual, require_admin, require_admin_or_supervisor
from app.models.usuario import Usuario, RolUsuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.services import usuario_service

router = APIRouter()


@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    rol: Optional[RolUsuario] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Lista todos los usuarios (solo admin/supervisor)."""
    return usuario_service.obtener_usuarios(db, skip, limit, rol)


@router.get("/clientes", response_model=List[UsuarioResponse])
def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Lista usuarios con rol cliente."""
    return usuario_service.obtener_clientes(db, skip, limit)


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    """Crea un nuevo usuario (solo admin)."""
    # Verificar que el email no exista
    if usuario_service.obtener_usuario_por_email(db, usuario_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    return usuario_service.crear_usuario(db, usuario_data)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene un usuario por ID."""
    db_usuario = usuario_service.obtener_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: UUID,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    """Actualiza un usuario (solo admin)."""
    # Verificar email único si se actualiza
    if usuario_data.email:
        existente = usuario_service.obtener_usuario_por_email(db, usuario_data.email)
        if existente and existente.id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )

    db_usuario = usuario_service.actualizar_usuario(db, usuario_id, usuario_data)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    """Elimina un usuario (soft delete, solo admin)."""
    if not usuario_service.eliminar_usuario(db, usuario_id):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")


@router.put("/{usuario_id}/rol")
def cambiar_rol(
    usuario_id: UUID,
    nuevo_rol: RolUsuario,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    """Cambia el rol de un usuario (solo admin)."""
    db_usuario = usuario_service.obtener_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_usuario.rol = nuevo_rol
    db.commit()

    return {"message": f"Rol actualizado a {nuevo_rol.value}"}


@router.post("/{usuario_id}/proyectos")
def asignar_proyectos(
    usuario_id: UUID,
    proyecto_ids: List[UUID],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Asigna proyectos a un cliente."""
    if not usuario_service.asignar_proyectos_a_cliente(db, usuario_id, proyecto_ids):
        raise HTTPException(
            status_code=400,
            detail="No se pudieron asignar los proyectos. Verifique que el usuario sea cliente."
        )

    return {"message": f"Proyectos asignados correctamente"}

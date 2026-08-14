from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual, require_admin, require_admin_or_supervisor
from app.models.usuario import Usuario, RolUsuario, MODULOS_SISTEMA
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, ModulosDisponibles
from app.services import usuario_service

router = APIRouter()


# Módulos por defecto según rol
MODULOS_POR_ROL = {
    "administrador": MODULOS_SISTEMA.copy(),  # Todos los módulos
    "supervisor": [
        "dashboard", "proyectos", "clientes", "materiales", "equipos",
        "herramientas", "finanzas", "reportes", "facturas_cobrar", "alertas",
        "jornadas_gestion", "actividades_tipo"
    ],
    "operario": [
        "dashboard", "proyectos", "materiales", "equipos",
        "jornadas_operario"
    ],
    "cliente": []  # Los clientes usan el portal
}


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


@router.get("/config/modulos-disponibles", response_model=ModulosDisponibles)
def obtener_modulos_disponibles(
    usuario: Usuario = Depends(require_admin)
):
    """Obtiene la lista de módulos disponibles en el sistema (solo admin)."""
    return ModulosDisponibles(modulos=MODULOS_SISTEMA)


@router.get("/config/modulos-por-rol")
def obtener_modulos_por_rol(
    usuario: Usuario = Depends(require_admin)
):
    """Obtiene los módulos por defecto para cada rol (solo admin)."""
    return MODULOS_POR_ROL


@router.put("/{usuario_id}/modulos", response_model=UsuarioResponse)
def actualizar_modulos_usuario(
    usuario_id: UUID,
    modulos: List[str],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    """Actualiza los módulos permitidos de un usuario (solo admin)."""
    # Validar que los módulos sean válidos
    modulos_invalidos = [m for m in modulos if m not in MODULOS_SISTEMA]
    if modulos_invalidos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Módulos inválidos: {', '.join(modulos_invalidos)}"
        )

    db_usuario = usuario_service.obtener_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_usuario.modulos_permitidos = modulos
    db.commit()
    db.refresh(db_usuario)

    return db_usuario


@router.get("/{usuario_id}/modulos-efectivos")
def obtener_modulos_efectivos(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene los módulos efectivos de un usuario (combinando rol + permisos personalizados)."""
    db_usuario = usuario_service.obtener_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Si es superadmin, tiene todos los módulos
    if db_usuario.es_superadmin:
        return {"modulos": MODULOS_SISTEMA, "es_superadmin": True}

    # Si tiene módulos personalizados, usar esos
    if db_usuario.modulos_permitidos is not None:
        return {"modulos": db_usuario.modulos_permitidos, "es_superadmin": False}

    # Sino, usar los del rol
    modulos_rol = MODULOS_POR_ROL.get(db_usuario.rol.value, [])
    return {"modulos": modulos_rol, "es_superadmin": False}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.deps import get_db, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.schemas.finanzas import (
    PrecioItemCreate, PrecioItemResponse,
    ResumenFinancieroProyecto, ResumenFinancieroGeneral,
    ActualizarMontoRequest
)
from app.services import finanzas_service

router = APIRouter()


@router.get("/proyecto/{proyecto_id}", response_model=ResumenFinancieroProyecto)
def obtener_finanzas_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """
    Obtiene el resumen financiero de un proyecto.
    Solo admin y supervisor tienen acceso.
    """
    resumen = finanzas_service.obtener_resumen_financiero_proyecto(db, proyecto_id)
    if not resumen:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return resumen


@router.get("/resumen-general", response_model=ResumenFinancieroGeneral)
def obtener_resumen_general(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """
    Obtiene el resumen financiero general de todos los proyectos activos.
    Solo admin y supervisor tienen acceso.
    """
    return finanzas_service.obtener_resumen_financiero_general(db)


@router.post("/precio-item", response_model=PrecioItemResponse)
def cargar_precio_item(
    precio: PrecioItemCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """
    Carga o actualiza el precio de un ítem de trabajo.
    Mantiene historial de precios.
    """
    return finanzas_service.cargar_precio_item(
        db, precio.item_trabajo_id, precio.precio_unitario, usuario.id
    )


@router.put("/proyecto/{proyecto_id}/monto")
def actualizar_monto_proyecto(
    proyecto_id: UUID,
    request: ActualizarMontoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza el monto contratado de un proyecto."""
    proyecto = finanzas_service.actualizar_monto_contratado(db, proyecto_id, request.monto)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return {
        "message": "Monto actualizado",
        "proyecto_id": str(proyecto_id),
        "monto_contratado": float(request.monto)
    }


@router.get("/rentabilidad")
def obtener_rentabilidad(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene listado de rentabilidad por proyecto."""
    resumen = finanzas_service.obtener_resumen_financiero_general(db)

    return [
        {
            "proyecto_id": str(p.proyecto_id),
            "nombre": p.nombre_proyecto,
            "monto_contratado": float(p.monto_contratado) if p.monto_contratado else None,
            "costo_total": float(p.costo_total),
            "rentabilidad": float(p.rentabilidad) if p.rentabilidad else None,
            "porcentaje_rentabilidad": float(p.porcentaje_rentabilidad) if p.porcentaje_rentabilidad else None
        }
        for p in resumen.proyectos
    ]

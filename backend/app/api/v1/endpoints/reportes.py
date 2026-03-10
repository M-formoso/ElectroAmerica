from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import date
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.schemas.reporte import ReporteCreate, ReporteResponse, CompartirReporteRequest
from app.services import reporte_service, proyecto_service

router = APIRouter()


@router.get("/proyecto/{proyecto_id}")
def obtener_datos_reporte(
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """
    Obtiene los datos para generar un reporte.
    No genera archivos, solo retorna los datos estructurados.
    """
    datos = reporte_service.obtener_datos_reporte(db, proyecto_id, fecha_desde, fecha_hasta)
    if not datos:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return datos


@router.get("/proyecto/{proyecto_id}/listado", response_model=List[ReporteResponse])
def listar_reportes_proyecto(
    proyecto_id: UUID,
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista los reportes generados de un proyecto."""
    return reporte_service.obtener_reportes_proyecto(db, proyecto_id, limit)


@router.post("/proyecto/{proyecto_id}/generar", response_model=ReporteResponse)
def generar_reporte(
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """
    Genera y guarda un reporte.
    Por ahora guarda solo los metadatos (las URLs de PDF/Excel se completarían
    cuando se implemente la generación real con WeasyPrint y OpenPyXL).
    """
    # Verificar que el proyecto existe
    proyecto = proyecto_service.obtener_proyecto(db, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Guardar reporte (sin archivos por ahora)
    reporte = reporte_service.guardar_reporte(
        db,
        proyecto_id,
        fecha_desde,
        fecha_hasta,
        pdf_url=None,
        excel_url=None,
        usuario_id=usuario.id,
        tipo="personalizado"
    )

    return reporte


@router.get("/semanal/{proyecto_id}", response_model=ReporteResponse)
def obtener_ultimo_reporte_semanal(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene el último reporte semanal de un proyecto."""
    reporte = reporte_service.obtener_ultimo_reporte_semanal(db, proyecto_id)
    if not reporte:
        raise HTTPException(status_code=404, detail="No hay reportes semanales")
    return reporte


@router.post("/compartir/{proyecto_id}")
def compartir_reporte(
    proyecto_id: UUID,
    request: CompartirReporteRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Marca un reporte como compartido con el cliente."""
    reporte = reporte_service.compartir_reporte_cliente(db, request.reporte_id)
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    return {
        "message": "Reporte compartido con el cliente",
        "reporte_id": str(reporte.id),
        "compartido_cliente": True
    }

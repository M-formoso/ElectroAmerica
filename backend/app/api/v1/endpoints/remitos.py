"""Endpoints para remitos de salida de materiales."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_usuario_actual, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.schemas.remito import (
    RemitoCreate, RemitoResponse, RemitoListResponse,
)
from app.services import remito_service
from app.services.remito_pdf_service import generar_pdf_remito


router = APIRouter()


@router.post("", response_model=RemitoResponse, status_code=status.HTTP_201_CREATED)
def crear_remito(
    data: RemitoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Crea un remito y descuenta stock del deposito indicado."""
    remito = remito_service.crear_remito(db, data, usuario.id)
    return remito_service.to_response_dict(remito)


@router.get("", response_model=List[RemitoListResponse])
def listar_remitos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    deposito_id: Optional[UUID] = None,
    proyecto_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    busqueda: Optional[str] = Query(None, max_length=200),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Lista remitos con filtros opcionales."""
    remitos = remito_service.listar_remitos(
        db,
        skip=skip,
        limit=limit,
        deposito_id=deposito_id,
        proyecto_id=proyecto_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        busqueda=busqueda,
    )
    return [remito_service.to_list_dict(r) for r in remitos]


@router.get("/{remito_id}", response_model=RemitoResponse)
def obtener_remito(
    remito_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    remito = remito_service.obtener_remito(db, remito_id)
    if not remito:
        raise HTTPException(status_code=404, detail="Remito no encontrado")
    return remito_service.to_response_dict(remito)


@router.get("/{remito_id}/pdf")
def descargar_pdf_remito(
    remito_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    remito = remito_service.obtener_remito(db, remito_id)
    if not remito:
        raise HTTPException(status_code=404, detail="Remito no encontrado")

    data = remito_service.to_response_dict(remito)
    pdf_bytes = generar_pdf_remito(data)
    filename = f"{data['numero_formateado']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

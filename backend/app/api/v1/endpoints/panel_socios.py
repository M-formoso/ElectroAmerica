from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import date

from app.core.deps import get_db, require_admin_or_supervisor, require_admin
from app.models.usuario import Usuario
from app.schemas.socio import (
    SocioCreate, SocioUpdate, SocioResponse,
    AporteSocioCreate, AporteSocioUpdate, AporteSocioResponse,
    RetiroSocioCreate, RetiroSocioUpdate, RetiroSocioResponse,
    ResumenPanelSocios,
)
from app.services import panel_socios_service

router = APIRouter()


# ============ RESUMEN ============

@router.get("/resumen", response_model=ResumenPanelSocios)
def obtener_resumen(
    fecha_desde: date,
    fecha_hasta: date,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Resumen del panel de socios en un rango de fechas."""
    if fecha_hasta < fecha_desde:
        raise HTTPException(status_code=400, detail="fecha_hasta debe ser posterior a fecha_desde")
    return panel_socios_service.obtener_resumen_panel(db, fecha_desde, fecha_hasta)


# ============ SOCIOS ============

@router.get("/socios", response_model=List[SocioResponse])
def listar_socios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    return panel_socios_service.listar_socios(db)


@router.post("/socios", response_model=SocioResponse)
def crear_socio(
    data: SocioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    return panel_socios_service.crear_socio(db, data)


@router.put("/socios/{socio_id}", response_model=SocioResponse)
def actualizar_socio(
    socio_id: UUID,
    data: SocioUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    socio = panel_socios_service.actualizar_socio(db, socio_id, data)
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    return socio


@router.delete("/socios/{socio_id}")
def eliminar_socio(
    socio_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    if not panel_socios_service.eliminar_socio(db, socio_id):
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    return {"message": "Socio eliminado"}


# ============ APORTES ============

def _serializar_aporte(a) -> dict:
    return {
        "id": a.id,
        "socio_id": a.socio_id,
        "socio_nombre": f"{a.socio.nombre} {a.socio.apellido or ''}".strip() if a.socio else None,
        "monto": float(a.monto),
        "fecha": a.fecha,
        "concepto": a.concepto,
        "observaciones": a.observaciones,
        "cuenta_id": a.cuenta_id,
        "cuenta_nombre": a.cuenta.nombre if a.cuenta else None,
        "creado_por_id": a.creado_por_id,
    }


@router.get("/aportes", response_model=List[AporteSocioResponse])
def listar_aportes(
    socio_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    aportes = panel_socios_service.listar_aportes(db, socio_id, fecha_desde, fecha_hasta)
    return [_serializar_aporte(a) for a in aportes]


@router.post("/aportes", response_model=AporteSocioResponse)
def crear_aporte(
    data: AporteSocioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    aporte = panel_socios_service.crear_aporte(db, data, usuario.id)
    db.refresh(aporte)
    return _serializar_aporte(aporte)


@router.put("/aportes/{aporte_id}", response_model=AporteSocioResponse)
def actualizar_aporte(
    aporte_id: UUID,
    data: AporteSocioUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    aporte = panel_socios_service.actualizar_aporte(db, aporte_id, data)
    if not aporte:
        raise HTTPException(status_code=404, detail="Aporte no encontrado")
    return _serializar_aporte(aporte)


@router.delete("/aportes/{aporte_id}")
def eliminar_aporte(
    aporte_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    if not panel_socios_service.eliminar_aporte(db, aporte_id):
        raise HTTPException(status_code=404, detail="Aporte no encontrado")
    return {"message": "Aporte eliminado"}


# ============ RETIROS ============

def _serializar_retiro(r) -> dict:
    return {
        "id": r.id,
        "socio_id": r.socio_id,
        "socio_nombre": f"{r.socio.nombre} {r.socio.apellido or ''}".strip() if r.socio else None,
        "monto": float(r.monto),
        "fecha": r.fecha,
        "concepto": r.concepto,
        "observaciones": r.observaciones,
        "cuenta_id": r.cuenta_id,
        "cuenta_nombre": r.cuenta.nombre if r.cuenta else None,
        "creado_por_id": r.creado_por_id,
    }


@router.get("/retiros", response_model=List[RetiroSocioResponse])
def listar_retiros(
    socio_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    retiros = panel_socios_service.listar_retiros(db, socio_id, fecha_desde, fecha_hasta)
    return [_serializar_retiro(r) for r in retiros]


@router.post("/retiros", response_model=RetiroSocioResponse)
def crear_retiro(
    data: RetiroSocioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    retiro = panel_socios_service.crear_retiro(db, data, usuario.id)
    db.refresh(retiro)
    return _serializar_retiro(retiro)


@router.put("/retiros/{retiro_id}", response_model=RetiroSocioResponse)
def actualizar_retiro(
    retiro_id: UUID,
    data: RetiroSocioUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    retiro = panel_socios_service.actualizar_retiro(db, retiro_id, data)
    if not retiro:
        raise HTTPException(status_code=404, detail="Retiro no encontrado")
    return _serializar_retiro(retiro)


@router.delete("/retiros/{retiro_id}")
def eliminar_retiro(
    retiro_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    if not panel_socios_service.eliminar_retiro(db, retiro_id):
        raise HTTPException(status_code=404, detail="Retiro no encontrado")
    return {"message": "Retiro eliminado"}

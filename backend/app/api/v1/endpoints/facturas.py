from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import date

from app.core.deps import get_db, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.schemas.factura import (
    FacturaCreate, FacturaUpdate, FacturaResponse,
    MarcarPagadaRequest,
    EmpresaFacturasResumen, EmpresaQuickCreate,
    FacturaMesItem,
)
from app.services import factura_service
from app.services.factura_service import _serializar_factura

router = APIRouter()


# ============ EMPRESAS ============

@router.get("/empresas", response_model=List[EmpresaFacturasResumen])
def listar_empresas(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Lista las empresas (clientes tipo=empresa) con resumen de sus facturas."""
    return factura_service.listar_empresas_con_resumen(db)


@router.post("/empresas", response_model=EmpresaFacturasResumen)
def crear_empresa(
    data: EmpresaQuickCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Alta rapida de empresa para el modulo de facturas."""
    cliente = factura_service.crear_empresa_rapida(db, data)
    return EmpresaFacturasResumen(
        id=cliente.id,
        nombre=cliente.nombre_fantasia or cliente.razon_social,
        cuit=cliente.cuit,
        email=cliente.email,
        telefono=cliente.telefono,
        cantidad_facturas=0,
        cantidad_pendientes=0,
        total_pendiente=0.0,
        total_pagado=0.0,
    )


@router.delete("/empresas/{cliente_id}")
def eliminar_empresa(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    if not factura_service.eliminar_empresa(db, cliente_id):
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return {"message": "Empresa eliminada"}


# ============ FACTURAS ============

@router.get("", response_model=List[FacturaResponse])
def listar_facturas(
    cliente_id: Optional[UUID] = None,
    proyecto_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    facturas = factura_service.listar_facturas(
        db, cliente_id, proyecto_id, estado, fecha_desde, fecha_hasta
    )
    return [_serializar_factura(f) for f in facturas]


@router.get("/pendientes", response_model=List[FacturaResponse])
def listar_pendientes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Todas las facturas pendientes de todas las empresas."""
    facturas = factura_service.listar_pendientes(db)
    return [_serializar_factura(f) for f in facturas]


@router.get("/por-mes", response_model=List[FacturaMesItem])
def facturas_por_mes(
    cliente_id: Optional[UUID] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Agrupa facturas por mes de pago (o inscripcion si pendiente)."""
    return factura_service.agrupar_por_mes(db, cliente_id, anio)


@router.post("", response_model=FacturaResponse)
def crear_factura(
    data: FacturaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    factura = factura_service.crear_factura(db, data, usuario.id)
    return _serializar_factura(factura)


@router.get("/{factura_id}", response_model=FacturaResponse)
def obtener_factura(
    factura_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    factura = factura_service.obtener_factura(db, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return _serializar_factura(factura)


@router.put("/{factura_id}", response_model=FacturaResponse)
def actualizar_factura(
    factura_id: UUID,
    data: FacturaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    factura = factura_service.actualizar_factura(db, factura_id, data)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return _serializar_factura(factura)


@router.delete("/{factura_id}")
def eliminar_factura(
    factura_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    if not factura_service.eliminar_factura(db, factura_id):
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return {"message": "Factura eliminada"}


@router.post("/{factura_id}/marcar-pagada", response_model=FacturaResponse)
def marcar_pagada(
    factura_id: UUID,
    data: MarcarPagadaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Marca la factura como pagada y genera la Transaccion INGRESO."""
    factura = factura_service.marcar_pagada(db, factura_id, data, usuario.id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return _serializar_factura(factura)


@router.post("/{factura_id}/marcar-pendiente", response_model=FacturaResponse)
def marcar_pendiente(
    factura_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Revierte una factura pagada a pendiente y anula la transaccion asociada."""
    factura = factura_service.marcar_pendiente(db, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return _serializar_factura(factura)

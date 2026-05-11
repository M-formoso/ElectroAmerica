"""Endpoints para depositos por cliente y su stock de materiales."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from app.core.deps import get_db, get_usuario_actual, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.deposito import Deposito, DepositoMaterial
from app.models.cliente import Cliente
from app.models.material import Material
from app.schemas.deposito import (
    DepositoCreate, DepositoUpdate, DepositoResponse, DepositoDetailResponse,
    DepositoMaterialCreate, DepositoMaterialUpdate, DepositoMaterialResponse,
)

router = APIRouter()


def _serializar_deposito(d: Deposito, cantidad_materiales: int = 0) -> DepositoResponse:
    return DepositoResponse(
        id=d.id,
        cliente_id=d.cliente_id,
        cliente_nombre=d.cliente.nombre_display if d.cliente else None,
        nombre=d.nombre,
        direccion=d.direccion,
        descripcion=d.descripcion,
        activo=d.activo,
        created_at=d.created_at,
        cantidad_materiales=cantidad_materiales,
    )


def _serializar_deposito_material(dm: DepositoMaterial) -> DepositoMaterialResponse:
    return DepositoMaterialResponse(
        id=dm.id,
        deposito_id=dm.deposito_id,
        material_id=dm.material_id,
        stock_actual=dm.stock_actual,
        stock_minimo=dm.stock_minimo,
        activo=dm.activo,
        material_codigo=dm.material.codigo if dm.material else None,
        material_nombre=dm.material.nombre if dm.material else None,
        material_unidad=dm.material.unidad if dm.material else None,
    )


# ============ CRUD Depositos ============

@router.get("", response_model=List[DepositoResponse])
def listar_depositos(
    cliente_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Lista depositos, opcionalmente filtrados por cliente."""
    query = db.query(Deposito).filter(Deposito.activo == True)
    if cliente_id:
        query = query.filter(Deposito.cliente_id == cliente_id)
    depositos = query.order_by(Deposito.nombre).all()

    # Contar materiales por deposito
    counts = dict(
        db.query(DepositoMaterial.deposito_id, func.count(DepositoMaterial.id))
        .filter(DepositoMaterial.activo == True)
        .group_by(DepositoMaterial.deposito_id)
        .all()
    )
    return [
        _serializar_deposito(d, cantidad_materiales=counts.get(d.id, 0))
        for d in depositos
    ]


@router.post("", response_model=DepositoResponse, status_code=status.HTTP_201_CREATED)
def crear_deposito(
    data: DepositoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Crea un nuevo deposito para un cliente."""
    cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    deposito = Deposito(
        cliente_id=data.cliente_id,
        nombre=data.nombre,
        direccion=data.direccion,
        descripcion=data.descripcion,
    )
    db.add(deposito)
    db.commit()
    db.refresh(deposito)
    return _serializar_deposito(deposito, 0)


@router.get("/{deposito_id}", response_model=DepositoDetailResponse)
def obtener_deposito(
    deposito_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Obtiene un deposito con sus materiales y stock."""
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    materiales = [
        _serializar_deposito_material(dm)
        for dm in deposito.materiales
        if dm.activo
    ]
    base = _serializar_deposito(deposito, len(materiales))
    return DepositoDetailResponse(**base.model_dump(), materiales=materiales)


@router.put("/{deposito_id}", response_model=DepositoResponse)
def actualizar_deposito(
    deposito_id: UUID,
    data: DepositoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Actualiza datos de un deposito."""
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deposito, field, value)
    db.commit()
    db.refresh(deposito)

    cantidad = db.query(func.count(DepositoMaterial.id)).filter(
        DepositoMaterial.deposito_id == deposito.id,
        DepositoMaterial.activo == True,
    ).scalar() or 0
    return _serializar_deposito(deposito, cantidad)


@router.delete("/{deposito_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_deposito(
    deposito_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Elimina (soft delete) un deposito."""
    deposito = db.query(Deposito).filter(Deposito.id == deposito_id).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")
    deposito.activo = False
    db.commit()


# ============ Materiales del deposito ============

@router.get("/{deposito_id}/materiales", response_model=List[DepositoMaterialResponse])
def listar_materiales_deposito(
    deposito_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Lista los materiales y stock de un deposito."""
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")
    return [
        _serializar_deposito_material(dm)
        for dm in deposito.materiales
        if dm.activo
    ]


@router.post(
    "/{deposito_id}/materiales",
    response_model=DepositoMaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
def agregar_material_a_deposito(
    deposito_id: UUID,
    data: DepositoMaterialCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Agrega un material al deposito con su stock inicial."""
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    material = db.query(Material).filter(Material.id == data.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    existente = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito_id,
        DepositoMaterial.material_id == data.material_id,
    ).first()
    if existente:
        # Reactivar y actualizar stock en lugar de duplicar
        existente.activo = True
        existente.stock_actual = data.stock_actual
        existente.stock_minimo = data.stock_minimo
        db.commit()
        db.refresh(existente)
        return _serializar_deposito_material(existente)

    dm = DepositoMaterial(
        deposito_id=deposito_id,
        material_id=data.material_id,
        stock_actual=data.stock_actual,
        stock_minimo=data.stock_minimo,
    )
    db.add(dm)
    db.commit()
    db.refresh(dm)
    return _serializar_deposito_material(dm)


@router.put(
    "/{deposito_id}/materiales/{material_id}",
    response_model=DepositoMaterialResponse,
)
def actualizar_material_deposito(
    deposito_id: UUID,
    material_id: UUID,
    data: DepositoMaterialUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Actualiza stock_actual o stock_minimo de un material en el deposito."""
    dm = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito_id,
        DepositoMaterial.material_id == material_id,
        DepositoMaterial.activo == True,
    ).first()
    if not dm:
        raise HTTPException(status_code=404, detail="Material no encontrado en deposito")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dm, field, value)
    db.commit()
    db.refresh(dm)
    return _serializar_deposito_material(dm)


@router.delete(
    "/{deposito_id}/materiales/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def quitar_material_deposito(
    deposito_id: UUID,
    material_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Quita (soft delete) un material del deposito."""
    dm = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito_id,
        DepositoMaterial.material_id == material_id,
    ).first()
    if not dm:
        raise HTTPException(status_code=404, detail="Material no encontrado en deposito")
    dm.activo = False
    db.commit()

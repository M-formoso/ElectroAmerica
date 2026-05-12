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
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.schemas.deposito import (
    DepositoCreate, DepositoUpdate, DepositoResponse, DepositoDetailResponse,
    DepositoMaterialCreate, DepositoMaterialUpdate, DepositoMaterialResponse,
    DepositoMaterialBulkCreate, DepositoMaterialNuevoCreate,
    DepositoMovimientoCreate, MaterialAgregado,
)
from app.schemas.material import MovimientoStockResponse
from decimal import Decimal
from collections import defaultdict
import re
import unicodedata

router = APIRouter()


def _serializar_deposito(
    d: Deposito,
    cantidad_materiales: int = 0,
    cantidad_subdepositos: int = 0,
) -> DepositoResponse:
    return DepositoResponse(
        id=d.id,
        cliente_id=d.cliente_id,
        cliente_nombre=d.cliente.nombre_display if d.cliente else None,
        parent_id=d.parent_id,
        nombre=d.nombre,
        direccion=d.direccion,
        descripcion=d.descripcion,
        activo=d.activo,
        created_at=d.created_at,
        cantidad_materiales=cantidad_materiales,
        cantidad_subdepositos=cantidad_subdepositos,
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
    parent_id: Optional[UUID] = Query(None, description="UUID del padre para filtrar subdepositos"),
    only_roots: bool = Query(True, description="Si True, solo depositos sin padre"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Lista depositos, filtrados por cliente y por jerarquia.

    Por default solo devuelve depositos raiz (sin parent). Para
    obtener los subdepositos de un padre puntual pasar parent_id.
    """
    query = db.query(Deposito).filter(Deposito.activo == True)
    if cliente_id:
        query = query.filter(Deposito.cliente_id == cliente_id)
    if parent_id is not None:
        query = query.filter(Deposito.parent_id == parent_id)
    elif only_roots:
        query = query.filter(Deposito.parent_id.is_(None))
    depositos = query.order_by(Deposito.nombre).all()

    counts_mat = dict(
        db.query(DepositoMaterial.deposito_id, func.count(DepositoMaterial.id))
        .filter(DepositoMaterial.activo == True)
        .group_by(DepositoMaterial.deposito_id)
        .all()
    )
    counts_sub = dict(
        db.query(Deposito.parent_id, func.count(Deposito.id))
        .filter(Deposito.activo == True, Deposito.parent_id.isnot(None))
        .group_by(Deposito.parent_id)
        .all()
    )
    return [
        _serializar_deposito(
            d,
            cantidad_materiales=counts_mat.get(d.id, 0),
            cantidad_subdepositos=counts_sub.get(d.id, 0),
        )
        for d in depositos
    ]


@router.post("", response_model=DepositoResponse, status_code=status.HTTP_201_CREATED)
def crear_deposito(
    data: DepositoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Crea un nuevo deposito o subdeposito (si se pasa parent_id)."""
    cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if data.parent_id:
        parent = db.query(Deposito).filter(
            Deposito.id == data.parent_id, Deposito.activo == True
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Deposito padre no encontrado")
        if parent.cliente_id != data.cliente_id:
            raise HTTPException(
                status_code=400,
                detail="El subdeposito debe ser del mismo cliente que su padre.",
            )
        if parent.parent_id:
            raise HTTPException(
                status_code=400,
                detail="No se permite anidar mas de un nivel (subdeposito de subdeposito).",
            )

    deposito = Deposito(
        cliente_id=data.cliente_id,
        parent_id=data.parent_id,
        nombre=data.nombre,
        direccion=data.direccion,
        descripcion=data.descripcion,
    )
    db.add(deposito)
    db.commit()
    db.refresh(deposito)
    return _serializar_deposito(deposito, 0, 0)


@router.get("/{deposito_id}", response_model=DepositoDetailResponse)
def obtener_deposito(
    deposito_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Obtiene un deposito con sus materiales, subdepositos y totales agregados."""
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    # Materiales directos
    materiales = [
        _serializar_deposito_material(dm)
        for dm in deposito.materiales
        if dm.activo
    ]

    # Subdepositos
    subdep_objs = [s for s in deposito.subdepositos if s.activo]
    counts_mat_sub = dict(
        db.query(DepositoMaterial.deposito_id, func.count(DepositoMaterial.id))
        .filter(
            DepositoMaterial.activo == True,
            DepositoMaterial.deposito_id.in_([s.id for s in subdep_objs]) if subdep_objs else False,
        )
        .group_by(DepositoMaterial.deposito_id)
        .all()
    ) if subdep_objs else {}
    subdepositos_resp = [
        _serializar_deposito(
            s,
            cantidad_materiales=counts_mat_sub.get(s.id, 0),
            cantidad_subdepositos=0,
        )
        for s in subdep_objs
    ]

    # Agregar stocks: materiales directos + materiales de subdepositos
    agg: dict = defaultdict(lambda: {"stock": Decimal("0"), "mat": None})
    for dm in deposito.materiales:
        if not dm.activo:
            continue
        agg[dm.material_id]["stock"] += Decimal(str(dm.stock_actual or 0))
        agg[dm.material_id]["mat"] = dm.material

    if subdep_objs:
        sub_ids = [s.id for s in subdep_objs]
        rows_sub = db.query(DepositoMaterial).filter(
            DepositoMaterial.deposito_id.in_(sub_ids),
            DepositoMaterial.activo == True,
        ).all()
        for dm in rows_sub:
            agg[dm.material_id]["stock"] += Decimal(str(dm.stock_actual or 0))
            if agg[dm.material_id]["mat"] is None:
                agg[dm.material_id]["mat"] = dm.material

    materiales_totales = [
        MaterialAgregado(
            material_id=mid,
            material_codigo=info["mat"].codigo if info["mat"] else None,
            material_nombre=info["mat"].nombre if info["mat"] else None,
            material_unidad=info["mat"].unidad if info["mat"] else None,
            stock_total=info["stock"],
        )
        for mid, info in agg.items()
    ]

    base = _serializar_deposito(
        deposito,
        cantidad_materiales=len(materiales),
        cantidad_subdepositos=len(subdep_objs),
    )
    return DepositoDetailResponse(
        **base.model_dump(),
        materiales=materiales,
        subdepositos=subdepositos_resp,
        materiales_totales=materiales_totales,
    )


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


# ============ Operaciones masivas y manuales sobre el stock del deposito ============

def _generar_codigo_material(db: Session, nombre: str) -> str:
    """Genera un codigo unico para Material a partir del nombre."""
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^A-Z0-9]+", "_", sin_acentos.upper()).strip("_")[:45] or "MAT"
    codigo = base
    sufijo = 1
    while db.query(Material).filter(Material.codigo == codigo).first():
        sufijo += 1
        codigo = f"{base[:45 - len(str(sufijo)) - 1]}_{sufijo}"
    return codigo


def _crear_o_reactivar_deposito_material(
    db: Session,
    deposito_id: UUID,
    material_id: UUID,
    stock_actual: Decimal,
    stock_minimo: Decimal,
) -> DepositoMaterial:
    """Crea o reactiva el DepositoMaterial con el stock indicado."""
    existente = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito_id,
        DepositoMaterial.material_id == material_id,
    ).first()
    if existente:
        existente.activo = True
        existente.stock_actual = stock_actual
        existente.stock_minimo = stock_minimo
        return existente
    dm = DepositoMaterial(
        deposito_id=deposito_id,
        material_id=material_id,
        stock_actual=stock_actual,
        stock_minimo=stock_minimo,
    )
    db.add(dm)
    return dm


@router.post(
    "/{deposito_id}/materiales/bulk",
    response_model=List[DepositoMaterialResponse],
    status_code=status.HTTP_201_CREATED,
)
def agregar_materiales_bulk(
    deposito_id: UUID,
    data: DepositoMaterialBulkCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Agrega varios materiales del catalogo al deposito en una sola operacion."""
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    if not data.items:
        raise HTTPException(status_code=400, detail="Lista de materiales vacia")

    creados: List[DepositoMaterial] = []
    for item in data.items:
        material = db.query(Material).filter(Material.id == item.material_id).first()
        if not material:
            raise HTTPException(
                status_code=404,
                detail=f"Material {item.material_id} no encontrado",
            )
        dm = _crear_o_reactivar_deposito_material(
            db, deposito_id, item.material_id, item.stock_actual, item.stock_minimo
        )
        creados.append(dm)
        # Registrar movimiento si hay stock inicial > 0
        if item.stock_actual > 0:
            db.add(MovimientoStock(
                material_id=item.material_id,
                tipo=TipoMovimiento.entrada,
                cantidad=item.stock_actual,
                stock_anterior=Decimal(0),
                stock_nuevo=item.stock_actual,
                motivo=f"Carga inicial en {deposito.nombre}",
                deposito_destino_id=deposito_id,
                usuario_id=usuario.id,
            ))

    db.commit()
    for dm in creados:
        db.refresh(dm)
    return [_serializar_deposito_material(dm) for dm in creados]


@router.post(
    "/{deposito_id}/materiales/nuevo",
    response_model=DepositoMaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
def agregar_material_nuevo_al_deposito(
    deposito_id: UUID,
    data: DepositoMaterialNuevoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Crea un material nuevo en el catalogo global y lo carga al deposito.

    El stock global del material queda en 0; el stock indicado se carga
    directamente al deposito. Si el codigo no se envia, se auto-genera.
    """
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    codigo = data.codigo or _generar_codigo_material(db, data.nombre)
    if db.query(Material).filter(Material.codigo == codigo).first():
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un material con el codigo {codigo}",
        )

    material = Material(
        codigo=codigo,
        nombre=data.nombre,
        descripcion=data.descripcion,
        unidad=data.unidad,
        stock_actual=Decimal(0),
        stock_minimo=Decimal(0),
        precio_unitario=data.precio_unitario,
    )
    db.add(material)
    db.flush()  # Para obtener el id

    dm = DepositoMaterial(
        deposito_id=deposito_id,
        material_id=material.id,
        stock_actual=data.stock_actual,
        stock_minimo=data.stock_minimo,
    )
    db.add(dm)

    if data.stock_actual > 0:
        db.add(MovimientoStock(
            material_id=material.id,
            tipo=TipoMovimiento.entrada,
            cantidad=data.stock_actual,
            stock_anterior=Decimal(0),
            stock_nuevo=data.stock_actual,
            motivo=f"Carga inicial en {deposito.nombre}",
            deposito_destino_id=deposito_id,
            usuario_id=usuario.id,
        ))

    db.commit()
    db.refresh(dm)
    return _serializar_deposito_material(dm)


@router.post(
    "/{deposito_id}/materiales/{material_id}/entrada",
    response_model=MovimientoStockResponse,
    status_code=status.HTTP_201_CREATED,
)
def entrada_material_deposito(
    deposito_id: UUID,
    material_id: UUID,
    data: DepositoMovimientoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Registra una entrada (suma) de stock para un material en el deposito."""
    dm = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito_id,
        DepositoMaterial.material_id == material_id,
        DepositoMaterial.activo == True,
    ).first()
    if not dm:
        raise HTTPException(status_code=404, detail="Material no encontrado en deposito")

    stock_anterior = Decimal(dm.stock_actual or 0)
    dm.stock_actual = stock_anterior + data.cantidad

    mov = MovimientoStock(
        material_id=material_id,
        tipo=TipoMovimiento.entrada,
        cantidad=data.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=dm.stock_actual,
        motivo=data.motivo,
        deposito_destino_id=deposito_id,
        usuario_id=usuario.id,
    )
    db.add(mov)
    db.commit()
    db.refresh(mov)
    return mov


@router.post(
    "/{deposito_id}/materiales/{material_id}/salida",
    response_model=MovimientoStockResponse,
    status_code=status.HTTP_201_CREATED,
)
def salida_material_deposito(
    deposito_id: UUID,
    material_id: UUID,
    data: DepositoMovimientoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Registra una salida (resta) de stock para un material en el deposito."""
    dm = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito_id,
        DepositoMaterial.material_id == material_id,
        DepositoMaterial.activo == True,
    ).first()
    if not dm:
        raise HTTPException(status_code=404, detail="Material no encontrado en deposito")

    stock_anterior = Decimal(dm.stock_actual or 0)
    if data.cantidad > stock_anterior:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente en el deposito. Disponible: {stock_anterior}",
        )

    dm.stock_actual = stock_anterior - data.cantidad
    mov = MovimientoStock(
        material_id=material_id,
        tipo=TipoMovimiento.salida,
        cantidad=data.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=dm.stock_actual,
        motivo=data.motivo,
        deposito_destino_id=deposito_id,
        usuario_id=usuario.id,
    )
    db.add(mov)
    db.commit()
    db.refresh(mov)
    return mov


@router.get(
    "/{deposito_id}/materiales/{material_id}/movimientos",
    response_model=List[MovimientoStockResponse],
)
def listar_movimientos_material_deposito(
    deposito_id: UUID,
    material_id: UUID,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Devuelve el historial de movimientos del material dentro del deposito."""
    return (
        db.query(MovimientoStock)
        .filter(
            MovimientoStock.material_id == material_id,
            MovimientoStock.deposito_destino_id == deposito_id,
        )
        .order_by(MovimientoStock.created_at.desc())
        .limit(limit)
        .all()
    )

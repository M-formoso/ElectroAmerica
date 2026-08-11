"""Endpoints para depositos por cliente y su stock de materiales."""
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
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
from app.models.remito import Remito, RemitoItem, RemitoDescuento, TipoRemito
from app.schemas.deposito import (
    DepositoCreate, DepositoUpdate, DepositoResponse, DepositoDetailResponse,
    DepositoMaterialCreate, DepositoMaterialUpdate, DepositoMaterialResponse,
    DepositoMaterialBulkCreate, DepositoMaterialNuevoCreate,
    DepositoMovimientoCreate, MaterialAgregado, DepositoVaciarResponse,
)
from app.schemas.material import MovimientoStockResponse
from app.services.deposito_pdf_service import (
    generar_pdf_stock_deposito,
    generar_pdf_detalle_movimientos_deposito,
)
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

    # Materiales propios por deposito (id -> set(material_id))
    materiales_por_dep: dict = {}
    for dep_id, mat_id in (
        db.query(DepositoMaterial.deposito_id, DepositoMaterial.material_id)
        .filter(DepositoMaterial.activo == True)
        .all()
    ):
        materiales_por_dep.setdefault(dep_id, set()).add(mat_id)

    # Mapa parent_id -> [ids de subdepositos]
    hijos_por_padre: dict = {}
    for sub_id, parent in (
        db.query(Deposito.id, Deposito.parent_id)
        .filter(Deposito.activo == True, Deposito.parent_id.isnot(None))
        .all()
    ):
        hijos_por_padre.setdefault(parent, []).append(sub_id)

    counts_sub = {p: len(hs) for p, hs in hijos_por_padre.items()}

    def cantidad_total(deposito_id) -> int:
        """Cantidad de materiales unicos contando el deposito + subdepositos."""
        ids_materiales = set(materiales_por_dep.get(deposito_id, ()))
        for hijo_id in hijos_por_padre.get(deposito_id, ()):
            ids_materiales |= materiales_por_dep.get(hijo_id, set())
        return len(ids_materiales)

    return [
        _serializar_deposito(
            d,
            cantidad_materiales=cantidad_total(d.id),
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


@router.get("/{deposito_id}/stock/pdf")
def descargar_pdf_stock_deposito(
    deposito_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """PDF imprimible del stock consolidado del deposito (incluye sus
    subdepositos). Pensado para control fisico contra gondola."""
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    subdep_objs = [s for s in deposito.subdepositos if s.activo]

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

    items = sorted(
        [
            {
                "material_codigo": info["mat"].codigo if info["mat"] else None,
                "material_nombre": info["mat"].nombre if info["mat"] else "-",
                "material_unidad": info["mat"].unidad if info["mat"] else "",
                "stock_total": float(info["stock"]),
            }
            for info in agg.values()
        ],
        key=lambda x: (x["material_nombre"] or "").lower(),
    )

    cliente_nombre = deposito.cliente.nombre_display if deposito.cliente else None
    data_pdf = {
        "deposito_nombre": deposito.nombre,
        "cliente_nombre": cliente_nombre,
        "fecha": datetime.now(),
        "usuario_nombre": usuario.nombre if usuario else None,
        "subdepositos": [s.nombre for s in subdep_objs],
        "items": items,
    }

    pdf_bytes = generar_pdf_stock_deposito(data_pdf)
    nombre_seguro = re.sub(r"[^A-Za-z0-9_-]+", "_", deposito.nombre)[:40] or "deposito"
    filename = f"stock_{nombre_seguro}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{deposito_id}/detalle-movimientos/pdf")
def descargar_pdf_detalle_movimientos(
    deposito_id: UUID,
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (inclusive)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (inclusive)"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """PDF con el detalle de movimientos del deposito en un rango de fechas.

    Estructura del PDF (tabla cruzada material x subdeposito):
      1. INGRESOS: filas=materiales, columnas=subdeps con movimiento + Total.
      2. EGRESOS: idem. Los egresos se atribuyen al subdeposito indicado
         en el remito (no al que descontó por cascada), para reflejar lo
         que el usuario efectivamente hizo.
      3. STOCK CALCULADO por material: total ingresado - total egresado
         del periodo, para conciliar contra lo que fisicamente deberia
         estar en gondola.
    """
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=400,
            detail="fecha_desde no puede ser mayor que fecha_hasta",
        )

    subdep_objs = [s for s in deposito.subdepositos if s.activo]
    # Grupo del deposito consultado: si es principal, incluye subdepositos;
    # si es subdeposito, solo el.
    dep_ids = [deposito.id] + [s.id for s in subdep_objs]

    def _aplicar_rango(query):
        if fecha_desde:
            query = query.filter(Remito.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Remito.fecha <= fecha_hasta)
        return query

    def _query_matriz(tipo: TipoRemito):
        """Rows: (deposito_id, material_id, codigo, nombre, unidad, cantidad_total)."""
        q = (
            db.query(
                Remito.deposito_id.label("deposito_id"),
                RemitoItem.material_id.label("material_id"),
                RemitoItem.material_codigo.label("material_codigo"),
                RemitoItem.material_nombre.label("material_nombre"),
                RemitoItem.material_unidad.label("material_unidad"),
                func.sum(RemitoItem.cantidad).label("cantidad_total"),
            )
            .join(Remito, Remito.id == RemitoItem.remito_id)
            .filter(
                Remito.tipo == tipo,
                Remito.activo == True,
                Remito.anulado_at.is_(None),
                Remito.deposito_id.in_(dep_ids),
                RemitoItem.activo == True,
            )
        )
        q = _aplicar_rango(q)
        q = q.group_by(
            Remito.deposito_id,
            RemitoItem.material_id,
            RemitoItem.material_codigo,
            RemitoItem.material_nombre,
            RemitoItem.material_unidad,
        )
        return q.all()

    def _contar_remitos(tipo: TipoRemito) -> int:
        q = db.query(func.count(func.distinct(Remito.id))).filter(
            Remito.tipo == tipo,
            Remito.activo == True,
            Remito.anulado_at.is_(None),
            Remito.deposito_id.in_(dep_ids),
        )
        q = _aplicar_rango(q)
        return int(q.scalar() or 0)

    def _armar_matriz(rows):
        """Construye columnas (solo subdeps con movimiento) y filas (materiales)."""
        deps_con_mov = set()
        materiales_info: dict = {}
        celdas: dict = defaultdict(float)
        for r in rows:
            deps_con_mov.add(r.deposito_id)
            if r.material_id not in materiales_info:
                materiales_info[r.material_id] = {
                    "material_id": r.material_id,
                    "material_codigo": r.material_codigo,
                    "material_nombre": r.material_nombre or "-",
                    "material_unidad": r.material_unidad or "",
                }
            celdas[(r.material_id, r.deposito_id)] += float(r.cantidad_total or 0)

        columnas = []
        # Principal primero si tuvo movimiento
        if deposito.id in deps_con_mov:
            columnas.append({
                "deposito_id": deposito.id,
                "nombre": deposito.nombre,
                "es_principal": True,
            })
        for s in sorted(subdep_objs, key=lambda x: (x.nombre or "").lower()):
            if s.id in deps_con_mov:
                columnas.append({
                    "deposito_id": s.id,
                    "nombre": s.nombre,
                    "es_principal": False,
                })

        filas = []
        for mid, info in sorted(
            materiales_info.items(),
            key=lambda kv: (kv[1]["material_nombre"] or "").lower(),
        ):
            por_dep = [celdas.get((mid, c["deposito_id"]), 0.0) for c in columnas]
            filas.append({
                **info,
                "por_deposito": por_dep,
                "total": sum(por_dep),
            })
        return columnas, filas

    ingresos_rows = _query_matriz(TipoRemito.ingreso)
    egresos_rows = _query_matriz(TipoRemito.egreso)

    ingresos_columnas, ingresos_filas = _armar_matriz(ingresos_rows)
    egresos_columnas, egresos_filas = _armar_matriz(egresos_rows)

    # Stock calculado por material: total ingresado - total egresado
    ingresado_por_mat: dict = {}
    egresado_por_mat: dict = {}
    info_por_mat: dict = {}
    for f in ingresos_filas:
        mid = f["material_id"]
        ingresado_por_mat[mid] = f["total"]
        info_por_mat[mid] = f
    for f in egresos_filas:
        mid = f["material_id"]
        egresado_por_mat[mid] = f["total"]
        info_por_mat.setdefault(mid, f)

    stock_filas = []
    for mid in set(ingresado_por_mat.keys()) | set(egresado_por_mat.keys()):
        info = info_por_mat[mid]
        ing = ingresado_por_mat.get(mid, 0.0)
        egr = egresado_por_mat.get(mid, 0.0)
        stock_filas.append({
            "material_codigo": info["material_codigo"],
            "material_nombre": info["material_nombre"],
            "material_unidad": info["material_unidad"],
            "total_ingresado": ing,
            "total_egresado": egr,
            "stock_calculado": ing - egr,
        })
    stock_filas.sort(key=lambda x: (x["material_nombre"] or "").lower())

    totales = {
        "ingresos_materiales": len(ingresos_filas),
        "egresos_materiales": len(egresos_filas),
        "remitos_ingreso": _contar_remitos(TipoRemito.ingreso),
        "remitos_egreso": _contar_remitos(TipoRemito.egreso),
    }

    data_pdf = {
        "deposito_nombre": deposito.nombre,
        "cliente_nombre": deposito.cliente.nombre_display if deposito.cliente else None,
        "fecha": datetime.now(),
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "usuario_nombre": usuario.nombre if usuario else None,
        "ingresos_columnas": ingresos_columnas,
        "ingresos_filas": ingresos_filas,
        "egresos_columnas": egresos_columnas,
        "egresos_filas": egresos_filas,
        "stock_filas": stock_filas,
        "totales": totales,
    }

    pdf_bytes = generar_pdf_detalle_movimientos_deposito(data_pdf)
    nombre_seguro = re.sub(r"[^A-Za-z0-9_-]+", "_", deposito.nombre)[:40] or "deposito"
    filename = f"detalle_movimientos_{nombre_seguro}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
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


def _eliminar_deposito_cascada(db: Session, deposito: Deposito) -> None:
    """Soft-delete recursivo: marca como inactivo el deposito, sus
    subdepositos, su stock (DepositoMaterial) y sus remitos (con items
    y descuentos). No revierte stock porque el deposito tambien se borra.
    """
    # Subdepositos primero (recursivo)
    for sub in list(deposito.subdepositos):
        if sub.activo:
            _eliminar_deposito_cascada(db, sub)

    # Stock del deposito
    db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito.id,
        DepositoMaterial.activo == True,
    ).update({"activo": False}, synchronize_session=False)

    # Remitos del deposito + sus items y descuentos
    remito_ids = [
        r.id for r in db.query(Remito.id).filter(
            Remito.deposito_id == deposito.id,
            Remito.activo == True,
        ).all()
    ]
    if remito_ids:
        db.query(RemitoItem).filter(
            RemitoItem.remito_id.in_(remito_ids),
            RemitoItem.activo == True,
        ).update({"activo": False}, synchronize_session=False)
        db.query(RemitoDescuento).filter(
            RemitoDescuento.remito_id.in_(remito_ids),
            RemitoDescuento.activo == True,
        ).update({"activo": False}, synchronize_session=False)
        db.query(Remito).filter(Remito.id.in_(remito_ids)).update(
            {"activo": False}, synchronize_session=False
        )

    # Descuentos huerfanos: remitos de OTROS depositos que descontaron de este
    db.query(RemitoDescuento).filter(
        RemitoDescuento.deposito_id == deposito.id,
        RemitoDescuento.activo == True,
    ).update({"activo": False}, synchronize_session=False)

    deposito.activo = False


@router.delete("/{deposito_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_deposito(
    deposito_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Elimina (soft delete) un deposito y todo lo asociado:
    subdepositos, stock y remitos (con sus items y descuentos)."""
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")
    _eliminar_deposito_cascada(db, deposito)
    db.commit()


def _vaciar_deposito_cascada(db: Session, deposito: Deposito) -> dict:
    """Reset total del deposito y sus subdepositos: pone stock en 0
    (borra los materiales cargados) y elimina remitos, descuentos y
    movimientos asociados. El deposito queda activo pero vacio, listo
    para empezar de cero. No se puede deshacer.
    """
    total_mats = 0
    total_remitos = 0
    total_movs = 0
    total_subs = 0

    # Reset recursivo de subdepositos
    for sub in list(deposito.subdepositos):
        if sub.activo:
            sub_stats = _vaciar_deposito_cascada(db, sub)
            total_mats += sub_stats["materiales"]
            total_remitos += sub_stats["remitos"]
            total_movs += sub_stats["movimientos"]
            total_subs += 1 + sub_stats["subdepositos"]

    # DepositoMaterial: soft-delete + stock a 0 (asi cuando se re-agrega
    # el material, _crear_o_reactivar_deposito_material lo resucita con
    # el nuevo stock desde 0 y no arrastra el valor viejo).
    mats_updated = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito.id,
        DepositoMaterial.activo == True,
    ).update(
        {"activo": False, "stock_actual": Decimal("0")},
        synchronize_session=False,
    )
    total_mats += mats_updated or 0

    # Remitos originados en este deposito (con items y descuentos)
    remito_ids = [
        r.id for r in db.query(Remito.id).filter(
            Remito.deposito_id == deposito.id,
            Remito.activo == True,
        ).all()
    ]
    if remito_ids:
        db.query(RemitoItem).filter(
            RemitoItem.remito_id.in_(remito_ids),
            RemitoItem.activo == True,
        ).update({"activo": False}, synchronize_session=False)
        db.query(RemitoDescuento).filter(
            RemitoDescuento.remito_id.in_(remito_ids),
            RemitoDescuento.activo == True,
        ).update({"activo": False}, synchronize_session=False)
        db.query(Remito).filter(Remito.id.in_(remito_ids)).update(
            {"activo": False}, synchronize_session=False
        )
        total_remitos += len(remito_ids)

    # Descuentos huerfanos: remitos de OTROS depositos que descontaron
    # de este (por reparto en cascada).
    db.query(RemitoDescuento).filter(
        RemitoDescuento.deposito_id == deposito.id,
        RemitoDescuento.activo == True,
    ).update({"activo": False}, synchronize_session=False)

    # MovimientoStock: hard-delete (audit records, sin FKs entrantes)
    movs_del = db.query(MovimientoStock).filter(
        (MovimientoStock.deposito_id == deposito.id)
        | (MovimientoStock.deposito_destino_id == deposito.id)
    ).delete(synchronize_session=False)
    total_movs += movs_del or 0

    return {
        "materiales": total_mats,
        "remitos": total_remitos,
        "movimientos": total_movs,
        "subdepositos": total_subs,
    }


@router.post("/{deposito_id}/vaciar", response_model=DepositoVaciarResponse)
def vaciar_deposito(
    deposito_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Vacia el deposito (y sus subdepositos): pone stock en 0 y borra
    todos los remitos y movimientos asociados. El deposito queda activo
    pero completamente limpio. No se puede deshacer.
    """
    deposito = db.query(Deposito).filter(
        Deposito.id == deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    stats = _vaciar_deposito_cascada(db, deposito)
    db.commit()
    return DepositoVaciarResponse(
        deposito_id=deposito_id,
        materiales_borrados=stats["materiales"],
        remitos_borrados=stats["remitos"],
        movimientos_borrados=stats["movimientos"],
        subdepositos_afectados=stats["subdepositos"],
    )


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
    """Registra una entrada (suma) de stock para un material en el deposito.

    Ademas del MovimientoStock, genera automaticamente un Remito de
    INGRESO asociado al deposito (visible en /remitos con PDF).
    """
    from app.models.remito import Remito, RemitoItem, RemitoDescuento, TipoRemito
    from app.models.material import Material as MaterialModel

    dm = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito_id,
        DepositoMaterial.material_id == material_id,
        DepositoMaterial.activo == True,
    ).first()
    if not dm:
        raise HTTPException(status_code=404, detail="Material no encontrado en deposito")

    deposito = db.query(Deposito).filter(Deposito.id == deposito_id).first()
    material = db.query(MaterialModel).filter(MaterialModel.id == material_id).first()

    stock_anterior = Decimal(dm.stock_actual or 0)
    dm.stock_actual = stock_anterior + data.cantidad

    # Crear remito de ingreso
    remito = Remito(
        tipo=TipoRemito.ingreso,
        fecha=datetime.now().date(),
        deposito_id=deposito_id,
        observaciones=data.motivo,
        usuario_id=usuario.id,
    )
    db.add(remito)
    db.flush()
    db.refresh(remito)

    db.add(RemitoItem(
        remito_id=remito.id,
        material_id=material_id,
        material_codigo=material.codigo if material else None,
        material_nombre=material.nombre if material else "-",
        material_unidad=material.unidad if material else "",
        cantidad=data.cantidad,
    ))
    db.add(RemitoDescuento(
        remito_id=remito.id,
        deposito_id=deposito_id,
        material_id=material_id,
        cantidad=data.cantidad,
    ))

    mov = MovimientoStock(
        material_id=material_id,
        tipo=TipoMovimiento.entrada,
        cantidad=data.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=dm.stock_actual,
        motivo=f"Ingreso por remito {remito.numero_formateado}"
               + (f" - {data.motivo}" if data.motivo else ""),
        deposito_id=deposito_id,
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

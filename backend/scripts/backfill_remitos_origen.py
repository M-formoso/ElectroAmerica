"""Backfill: convertir remitos viejos a la logica nueva de egreso.

Contexto
--------
Hasta el commit 5adfc7f, los remitos de EGRESO descontaban en cascada por
hermanos/padre del deposito origen aunque el usuario no lo pidiera. A
partir de ese commit el default es descontar TODO del origen (puede
quedar negativo).

Los remitos creados antes del cambio quedaron con RemitoDescuento
repartidos en otros depositos. Eso ensucia los consolidados:
"salio del subdeposito X pero figura descontado en Y".

Que hace este script
--------------------
Por cada remito de egreso activo y NO anulado:
  1. Detecta RemitoDescuento sobre depositos != deposito origen.
  2. Devuelve esa cantidad al stock del deposito donde se habia
     descontado (suma a DepositoMaterial + MovimientoStock devolucion).
  3. Borra esos RemitoDescuento.
  4. Aplica la logica nueva sobre el deposito origen: resta del stock
     (puede quedar negativo) + MovimientoStock salida + RemitoDescuento
     consolidado por material.

Idempotente: una segunda corrida no encuentra nada que arreglar (todos
los descuentos ya estan en el origen) y termina sin tocar nada.

Uso
---
  # Dry-run (default): no toca la DB, solo imprime el diff
  python -m scripts.backfill_remitos_origen

  # Aplicar de verdad
  python -m scripts.backfill_remitos_origen --apply

Asume que DATABASE_URL apunta a la DB sobre la que querias correr.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.deposito import Deposito, DepositoMaterial
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.models.remito import Remito, RemitoDescuento, RemitoItem, TipoRemito


SYSTEM_MOTIVO = "Backfill: ajuste a logica de egreso desde origen"


def _get_or_create_dm(
    db: Session, deposito_id: UUID, material_id: UUID
) -> DepositoMaterial:
    dm = (
        db.query(DepositoMaterial)
        .filter(
            DepositoMaterial.deposito_id == deposito_id,
            DepositoMaterial.material_id == material_id,
            DepositoMaterial.activo == True,
        )
        .first()
    )
    if dm:
        return dm
    dm = DepositoMaterial(
        deposito_id=deposito_id,
        material_id=material_id,
        stock_actual=Decimal("0"),
        stock_minimo=Decimal("0"),
    )
    db.add(dm)
    db.flush()
    return dm


def _items_por_material(remito: Remito) -> Dict[UUID, Decimal]:
    """Total esperado a descontar del origen, por material_id."""
    acumulado: Dict[UUID, Decimal] = defaultdict(lambda: Decimal("0"))
    for item in remito.items:
        if not item.material_id or item.cantidad <= 0:
            continue
        acumulado[item.material_id] += Decimal(item.cantidad)
    return acumulado


def _descuentos_por_deposito_material(
    remito: Remito,
) -> Dict[Tuple[UUID, UUID], List[RemitoDescuento]]:
    out: Dict[Tuple[UUID, UUID], List[RemitoDescuento]] = defaultdict(list)
    for d in remito.descuentos:
        out[(d.deposito_id, d.material_id)].append(d)
    return out


def _procesar_remito(
    db: Session, remito: Remito, apply: bool
) -> dict:
    """Devuelve resumen del impacto sobre este remito.

    Si apply=True, ademas modifica la DB.
    """
    resumen = {
        "remito": remito.numero_formateado,
        "deposito_origen_id": str(remito.deposito_id) if remito.deposito_id else None,
        "deposito_origen_nombre": remito.deposito.nombre if remito.deposito else None,
        "descuentos_revertidos": [],  # [(deposito_nombre, material_id, cantidad)]
        "ajuste_origen_por_material": {},  # material_id -> cantidad agregada al descuento del origen
        "ya_estaba_ok": True,
    }

    if remito.deposito_id is None:
        # Remito sin deposito (ingreso global). No aplica.
        return resumen

    descuentos_map = _descuentos_por_deposito_material(remito)

    # 1) Para cada descuento sobre un deposito != origen, devolverlo y
    #    anotar cuanto hay que agregar al descuento del origen.
    cantidad_pendiente_origen: Dict[UUID, Decimal] = defaultdict(lambda: Decimal("0"))

    for (dep_id, mat_id), descuentos in list(descuentos_map.items()):
        if dep_id == remito.deposito_id:
            continue
        resumen["ya_estaba_ok"] = False
        total = sum((Decimal(d.cantidad) for d in descuentos), Decimal("0"))

        dep = db.query(Deposito).filter(Deposito.id == dep_id).first()
        dep_nombre = dep.nombre if dep else f"<deposito {dep_id}>"
        resumen["descuentos_revertidos"].append(
            (dep_nombre, str(mat_id), float(total))
        )

        if apply:
            # Devolver al deposito donde se habia descontado mal
            dm = _get_or_create_dm(db, dep_id, mat_id)
            stock_anterior = dm.stock_actual
            dm.stock_actual = stock_anterior + total
            db.add(
                MovimientoStock(
                    material_id=mat_id,
                    tipo=TipoMovimiento.devolucion,
                    cantidad=total,
                    stock_anterior=stock_anterior,
                    stock_nuevo=stock_anterior + total,
                    motivo=f"{SYSTEM_MOTIVO} - devolucion a {dep_nombre} (remito {remito.numero_formateado})",
                    proyecto_id=remito.proyecto_id,
                    deposito_id=dep_id,
                    usuario_id=remito.usuario_id,
                )
            )
            for d in descuentos:
                db.delete(d)

        cantidad_pendiente_origen[mat_id] += total

    # 2) Para cada material con pendiente, descontar del origen y
    #    ajustar (o crear) el RemitoDescuento del origen.
    for mat_id, cantidad in cantidad_pendiente_origen.items():
        resumen["ajuste_origen_por_material"][str(mat_id)] = float(cantidad)

        if apply:
            dm_origen = _get_or_create_dm(db, remito.deposito_id, mat_id)
            stock_anterior = dm_origen.stock_actual
            dm_origen.stock_actual = stock_anterior - cantidad
            db.add(
                MovimientoStock(
                    material_id=mat_id,
                    tipo=TipoMovimiento.salida,
                    cantidad=cantidad,
                    stock_anterior=stock_anterior,
                    stock_nuevo=stock_anterior - cantidad,
                    motivo=f"{SYSTEM_MOTIVO} - descuento al origen {remito.deposito.nombre if remito.deposito else ''} (remito {remito.numero_formateado})",
                    proyecto_id=remito.proyecto_id,
                    deposito_id=remito.deposito_id,
                    usuario_id=remito.usuario_id,
                )
            )

            # Acumular en el RemitoDescuento del origen si ya existe,
            # sino crear uno nuevo.
            existente = (
                db.query(RemitoDescuento)
                .filter(
                    RemitoDescuento.remito_id == remito.id,
                    RemitoDescuento.deposito_id == remito.deposito_id,
                    RemitoDescuento.material_id == mat_id,
                )
                .first()
            )
            if existente:
                existente.cantidad = Decimal(existente.cantidad) + cantidad
            else:
                db.add(
                    RemitoDescuento(
                        remito_id=remito.id,
                        deposito_id=remito.deposito_id,
                        material_id=mat_id,
                        cantidad=cantidad,
                    )
                )

    return resumen


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill remitos a logica nueva de origen.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplicar los cambios. Sin este flag es dry-run.",
    )
    args = parser.parse_args()

    apply = args.apply
    modo = "APLICAR" if apply else "DRY-RUN"
    print(f"=== Backfill remitos a logica de origen [{modo}] ===\n")

    db: Session = SessionLocal()
    try:
        remitos = (
            db.query(Remito)
            .filter(
                Remito.activo == True,
                Remito.tipo == TipoRemito.egreso,
                Remito.anulado_at.is_(None),
            )
            .order_by(Remito.numero.asc())
            .all()
        )

        total = len(remitos)
        afectados = 0
        movs_devolucion = 0
        movs_salida = 0

        print(f"Remitos de egreso activos no anulados: {total}\n")

        for r in remitos:
            resumen = _procesar_remito(db, r, apply=apply)
            if resumen["ya_estaba_ok"]:
                continue
            afectados += 1
            movs_devolucion += len(resumen["descuentos_revertidos"])
            movs_salida += len(resumen["ajuste_origen_por_material"])

            print(
                f"- {resumen['remito']} (origen: {resumen['deposito_origen_nombre']})"
            )
            for dep_nombre, mat_id, cant in resumen["descuentos_revertidos"]:
                print(f"    devuelve {cant} a {dep_nombre}  [material {mat_id}]")
            for mat_id, cant in resumen["ajuste_origen_por_material"].items():
                print(f"    descuenta {cant} de origen        [material {mat_id}]")

        if apply:
            db.commit()
            print(f"\nOK. Commit aplicado.")
        else:
            db.rollback()
            print(f"\nDry-run. No se modifico la DB.")

        print(f"\nResumen:")
        print(f"  Remitos revisados: {total}")
        print(f"  Remitos modificados: {afectados}")
        print(f"  Lineas de devolucion: {movs_devolucion}")
        print(f"  Lineas de descuento al origen: {movs_salida}")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

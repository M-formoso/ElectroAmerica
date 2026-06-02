"""Endpoints para listas de precios y precios por actividad."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID
from decimal import Decimal

from app.core.deps import get_db, get_usuario_actual, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.lista_precio import ListaPrecio, PrecioListaActividad
from app.models.actividad_tipo import ActividadTipo
from app.models.proyecto import Proyecto
from app.models.proyecto_actividad import ProyectoActividad
from app.models.cliente import Cliente
from app.schemas.lista_precio import (
    ListaPrecioCreate, ListaPrecioUpdate, ListaPrecioResponse,
    ListaPrecioDetailResponse, PrecioActividadItem, PrecioBulkSet,
    TotalProyectoItem,
)

router = APIRouter()


def _serializar_lista(lista: ListaPrecio, cantidad_con_precio: int = 0) -> ListaPrecioResponse:
    return ListaPrecioResponse(
        id=lista.id,
        nombre=lista.nombre,
        descripcion=lista.descripcion,
        activo=lista.activo,
        created_at=lista.created_at,
        cantidad_actividades_con_precio=cantidad_con_precio,
    )


@router.get("", response_model=List[ListaPrecioResponse])
def listar_listas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Lista todas las listas de precios activas."""
    listas = db.query(ListaPrecio).filter(ListaPrecio.activo == True).order_by(ListaPrecio.nombre).all()
    counts = dict(
        db.query(PrecioListaActividad.lista_precio_id, func.count(PrecioListaActividad.id))
        .filter(PrecioListaActividad.activo == True, PrecioListaActividad.precio_unitario > 0)
        .group_by(PrecioListaActividad.lista_precio_id)
        .all()
    )
    return [_serializar_lista(l, counts.get(l.id, 0)) for l in listas]


@router.post("", response_model=ListaPrecioResponse, status_code=status.HTTP_201_CREATED)
def crear_lista(
    data: ListaPrecioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Crea una nueva lista de precios."""
    existente = db.query(ListaPrecio).filter(
        func.lower(ListaPrecio.nombre) == data.nombre.strip().lower(),
        ListaPrecio.activo == True,
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una lista con ese nombre")

    lista = ListaPrecio(nombre=data.nombre.strip(), descripcion=data.descripcion)
    db.add(lista)
    db.commit()
    db.refresh(lista)
    return _serializar_lista(lista, 0)


@router.get("/{lista_id}", response_model=ListaPrecioDetailResponse)
def obtener_lista(
    lista_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Obtiene una lista con todas las actividades tipo y su precio
    (las actividades sin precio cargado en esta lista aparecen con 0)."""
    lista = db.query(ListaPrecio).filter(
        ListaPrecio.id == lista_id, ListaPrecio.activo == True
    ).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista no encontrada")

    actividades = db.query(ActividadTipo).filter(
        ActividadTipo.activo == True
    ).order_by(ActividadTipo.nombre).all()

    precios = {
        p.actividad_tipo_id: p.precio_unitario
        for p in db.query(PrecioListaActividad).filter(
            PrecioListaActividad.lista_precio_id == lista_id,
            PrecioListaActividad.activo == True,
        ).all()
    }

    items = [
        PrecioActividadItem(
            actividad_tipo_id=a.id,
            actividad_codigo=a.codigo,
            actividad_nombre=a.nombre,
            actividad_unidad=a.unidad_trabajo,
            precio_unitario=precios.get(a.id, Decimal("0")),
        )
        for a in actividades
    ]

    base = _serializar_lista(lista, sum(1 for p in precios.values() if p and p > 0))
    return ListaPrecioDetailResponse(**base.model_dump(), items=items)


@router.put("/{lista_id}", response_model=ListaPrecioResponse)
def actualizar_lista(
    lista_id: UUID,
    data: ListaPrecioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    lista = db.query(ListaPrecio).filter(
        ListaPrecio.id == lista_id, ListaPrecio.activo == True
    ).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista no encontrada")

    update = data.model_dump(exclude_unset=True)
    if "nombre" in update:
        nuevo = update["nombre"].strip()
        otro = db.query(ListaPrecio).filter(
            ListaPrecio.id != lista_id,
            func.lower(ListaPrecio.nombre) == nuevo.lower(),
            ListaPrecio.activo == True,
        ).first()
        if otro:
            raise HTTPException(status_code=400, detail="Ya existe una lista con ese nombre")
        lista.nombre = nuevo
    if "descripcion" in update:
        lista.descripcion = update["descripcion"]

    db.commit()
    db.refresh(lista)
    return _serializar_lista(lista, 0)


@router.delete("/{lista_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_lista(
    lista_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Soft-delete de la lista. No afecta los proyectos que ya tienen
    precios congelados via snapshot."""
    lista = db.query(ListaPrecio).filter(ListaPrecio.id == lista_id).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    lista.activo = False
    db.commit()


@router.put("/{lista_id}/precios", response_model=ListaPrecioDetailResponse)
def setear_precios_bulk(
    lista_id: UUID,
    data: PrecioBulkSet,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Setea/actualiza precios de varias actividades de una lista en una
    sola llamada. Si una actividad no tenia precio, lo crea. Si ya tenia,
    lo actualiza. Pasar precio_unitario=0 deja la actividad sin precio
    efectivo (se ignora al snapshotear).
    """
    lista = db.query(ListaPrecio).filter(
        ListaPrecio.id == lista_id, ListaPrecio.activo == True
    ).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista no encontrada")

    actividad_ids = [it.actividad_tipo_id for it in data.items]
    existentes = {
        p.actividad_tipo_id: p
        for p in db.query(PrecioListaActividad).filter(
            PrecioListaActividad.lista_precio_id == lista_id,
            PrecioListaActividad.actividad_tipo_id.in_(actividad_ids),
        ).all()
    }

    for item in data.items:
        actual = existentes.get(item.actividad_tipo_id)
        if actual:
            actual.precio_unitario = item.precio_unitario
            actual.activo = True
        else:
            db.add(PrecioListaActividad(
                lista_precio_id=lista_id,
                actividad_tipo_id=item.actividad_tipo_id,
                precio_unitario=item.precio_unitario,
            ))

    db.commit()
    return obtener_lista(lista_id, db, usuario)


@router.get("/finanzas/totales-proyectos", response_model=List[TotalProyectoItem])
def listar_totales_proyectos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Total presupuestado por proyecto: SUM(snapshot * cantidad_planificada).
    Total ejecutado: SUM(snapshot * cantidad_ejecutada).
    Solo admin / supervisor.
    """
    proyectos = db.query(Proyecto).order_by(Proyecto.nombre).all()

    # Precargar agregados por proyecto
    agg_rows = db.query(
        ProyectoActividad.proyecto_id,
        func.count(ProyectoActividad.id).label("cant"),
        func.coalesce(
            func.sum(
                func.coalesce(ProyectoActividad.precio_unitario_snapshot, 0)
                * ProyectoActividad.cantidad_planificada
            ),
            0,
        ).label("presup"),
        func.coalesce(
            func.sum(
                func.coalesce(ProyectoActividad.precio_unitario_snapshot, 0)
                * ProyectoActividad.cantidad_ejecutada
            ),
            0,
        ).label("ejec"),
    ).filter(
        ProyectoActividad.activo == True,
    ).group_by(ProyectoActividad.proyecto_id).all()
    agg = {
        r.proyecto_id: {"cant": r.cant, "presup": r.presup, "ejec": r.ejec}
        for r in agg_rows
    }

    return [
        TotalProyectoItem(
            proyecto_id=p.id,
            proyecto_nombre=p.nombre,
            cliente_nombre=p.cliente.nombre_display if p.cliente else None,
            estado=p.estado.value if p.estado else None,
            lista_precio_id=p.lista_precio_id,
            lista_precio_nombre=p.lista_precio.nombre if p.lista_precio else None,
            cantidad_actividades=agg.get(p.id, {}).get("cant", 0),
            total_presupuestado=agg.get(p.id, {}).get("presup", Decimal("0")),
            total_ejecutado=agg.get(p.id, {}).get("ejec", Decimal("0")),
        )
        for p in proyectos
    ]

"""Endpoints para listas de precios y precios por actividad."""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date

from app.core.deps import get_db, get_usuario_actual, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.lista_precio import ListaPrecio, PrecioListaActividad
from app.models.actividad_tipo import ActividadTipo
from app.models.proyecto import Proyecto, EstadoProyecto, EstadoFacturacion
from app.models.proyecto_actividad import ProyectoActividad
from app.models.cliente import Cliente
from app.schemas.lista_precio import (
    ListaPrecioCreate, ListaPrecioUpdate, ListaPrecioResponse,
    ListaPrecioDetailResponse, PrecioActividadItem, PrecioBulkSet,
    TotalProyectoItem, DetallePresupuestoProyecto, DetalleActividadPresupuesto,
    FacturacionProyectoItem, FacturarProyectoBody, CobrarProyectoBody,
)
from app.services.pdf_service import generar_pdf_facturacion_proyecto

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
    Excluye proyectos finalizados (esos se ven en Facturación).
    Solo admin / supervisor.
    """
    proyectos = (
        db.query(Proyecto)
        .filter(Proyecto.estado != EstadoProyecto.finalizado)
        .order_by(Proyecto.nombre)
        .all()
    )

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

    # Auto-finalizar proyectos que ya estan al 100% (ejecutado >= presupuestado).
    # Esto cubre proyectos que se cargaron al 100% antes de tener la logica
    # de auto-finalizacion en _actualizar_avance_proyecto.
    autofinalizados = set()
    for p in proyectos:
        info = agg.get(p.id, {})
        presup = Decimal(info.get("presup", 0) or 0)
        ejec = Decimal(info.get("ejec", 0) or 0)
        if presup > 0 and ejec >= presup:
            p.estado = EstadoProyecto.finalizado
            if not p.fecha_fin_real:
                p.fecha_fin_real = date.today()
            if p.porcentaje_avance is None or p.porcentaje_avance < Decimal("100"):
                p.porcentaje_avance = Decimal("100")
            autofinalizados.add(p.id)
    if autofinalizados:
        db.commit()

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
        if p.id not in autofinalizados
    ]


@router.get(
    "/finanzas/totales-proyectos/{proyecto_id}/detalle",
    response_model=DetallePresupuestoProyecto,
)
def detalle_presupuesto_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Detalle del presupuesto de un proyecto: linea por actividad con
    cantidad planificada/ejecutada, precio snapshot y subtotales.
    """
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    actividades = (
        db.query(ProyectoActividad)
        .filter(
            ProyectoActividad.proyecto_id == proyecto_id,
            ProyectoActividad.activo == True,
        )
        .order_by(ProyectoActividad.orden.asc(), ProyectoActividad.created_at.asc())
        .all()
    )

    items: List[DetalleActividadPresupuesto] = []
    total_presup = Decimal("0")
    total_ejec = Decimal("0")
    for a in actividades:
        precio = a.precio_unitario_snapshot or Decimal("0")
        cant_plan = a.cantidad_planificada or Decimal("0")
        cant_ejec = a.cantidad_ejecutada or Decimal("0")
        sub_presup = precio * cant_plan
        sub_ejec = precio * cant_ejec
        total_presup += sub_presup
        total_ejec += sub_ejec
        items.append(
            DetalleActividadPresupuesto(
                proyecto_actividad_id=a.id,
                actividad_tipo_id=a.actividad_tipo_id,
                actividad_codigo=a.actividad_tipo.codigo if a.actividad_tipo else None,
                actividad_nombre=a.actividad_tipo.nombre if a.actividad_tipo else "(sin nombre)",
                unidad=a.actividad_tipo.unidad_trabajo if a.actividad_tipo else None,
                cantidad_planificada=cant_plan,
                cantidad_ejecutada=cant_ejec,
                precio_unitario_snapshot=precio,
                subtotal_presupuestado=sub_presup,
                subtotal_ejecutado=sub_ejec,
            )
        )

    return DetallePresupuestoProyecto(
        proyecto_id=proyecto.id,
        proyecto_nombre=proyecto.nombre,
        cliente_nombre=proyecto.cliente.nombre_display if proyecto.cliente else None,
        lista_precio_nombre=proyecto.lista_precio.nombre if proyecto.lista_precio else None,
        total_presupuestado=total_presup,
        total_ejecutado=total_ejec,
        items=items,
    )


def _agregados_por_proyecto(db: Session, proyecto_ids):
    """Devuelve dict {proyecto_id: {presup, ejec}} para los proyectos dados."""
    if not proyecto_ids:
        return {}
    rows = db.query(
        ProyectoActividad.proyecto_id,
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
        ProyectoActividad.proyecto_id.in_(proyecto_ids),
    ).group_by(ProyectoActividad.proyecto_id).all()
    return {r.proyecto_id: {"presup": r.presup, "ejec": r.ejec} for r in rows}


@router.get("/finanzas/facturacion", response_model=List[FacturacionProyectoItem])
def listar_facturacion_proyectos(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Proyectos finalizados con su estado de facturación/cobro.
    Filtro opcional por estado: pendiente | facturado | cobrado.
    """
    q = db.query(Proyecto).filter(Proyecto.estado == EstadoProyecto.finalizado)
    if estado:
        try:
            estado_enum = EstadoFacturacion(estado)
        except ValueError:
            raise HTTPException(status_code=400, detail="Estado de facturación inválido")
        q = q.filter(Proyecto.estado_facturacion == estado_enum)

    proyectos = q.order_by(Proyecto.fecha_fin_real.desc().nullslast(), Proyecto.nombre).all()
    agg = _agregados_por_proyecto(db, [p.id for p in proyectos])

    return [
        FacturacionProyectoItem(
            proyecto_id=p.id,
            proyecto_nombre=p.nombre,
            cliente_nombre=p.cliente.nombre_display if p.cliente else None,
            fecha_fin_real=p.fecha_fin_real,
            estado_facturacion=(p.estado_facturacion.value if p.estado_facturacion else "pendiente"),
            numero_factura=p.numero_factura,
            fecha_facturacion=p.fecha_facturacion,
            fecha_cobro=p.fecha_cobro,
            monto_facturado=p.monto_facturado,
            total_presupuestado=agg.get(p.id, {}).get("presup", Decimal("0")),
            total_ejecutado=agg.get(p.id, {}).get("ejec", Decimal("0")),
        )
        for p in proyectos
    ]


@router.patch(
    "/finanzas/facturacion/{proyecto_id}/facturar",
    response_model=FacturacionProyectoItem,
)
def marcar_facturado(
    proyecto_id: UUID,
    data: FacturarProyectoBody,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Marca un proyecto finalizado como facturado."""
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if proyecto.estado != EstadoProyecto.finalizado:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden facturar proyectos finalizados",
        )

    proyecto.numero_factura = data.numero_factura.strip()
    proyecto.fecha_facturacion = data.fecha_facturacion
    proyecto.monto_facturado = data.monto_facturado
    if proyecto.estado_facturacion != EstadoFacturacion.cobrado:
        proyecto.estado_facturacion = EstadoFacturacion.facturado

    db.commit()
    db.refresh(proyecto)
    agg = _agregados_por_proyecto(db, [proyecto.id])
    return FacturacionProyectoItem(
        proyecto_id=proyecto.id,
        proyecto_nombre=proyecto.nombre,
        cliente_nombre=proyecto.cliente.nombre_display if proyecto.cliente else None,
        fecha_fin_real=proyecto.fecha_fin_real,
        estado_facturacion=proyecto.estado_facturacion.value,
        numero_factura=proyecto.numero_factura,
        fecha_facturacion=proyecto.fecha_facturacion,
        fecha_cobro=proyecto.fecha_cobro,
        monto_facturado=proyecto.monto_facturado,
        total_presupuestado=agg.get(proyecto.id, {}).get("presup", Decimal("0")),
        total_ejecutado=agg.get(proyecto.id, {}).get("ejec", Decimal("0")),
    )


@router.patch(
    "/finanzas/facturacion/{proyecto_id}/cobrar",
    response_model=FacturacionProyectoItem,
)
def marcar_cobrado(
    proyecto_id: UUID,
    data: CobrarProyectoBody,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Marca un proyecto facturado como cobrado."""
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if proyecto.estado_facturacion != EstadoFacturacion.facturado:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden cobrar proyectos ya facturados",
        )

    proyecto.fecha_cobro = data.fecha_cobro
    proyecto.estado_facturacion = EstadoFacturacion.cobrado

    db.commit()
    db.refresh(proyecto)
    agg = _agregados_por_proyecto(db, [proyecto.id])
    return FacturacionProyectoItem(
        proyecto_id=proyecto.id,
        proyecto_nombre=proyecto.nombre,
        cliente_nombre=proyecto.cliente.nombre_display if proyecto.cliente else None,
        fecha_fin_real=proyecto.fecha_fin_real,
        estado_facturacion=proyecto.estado_facturacion.value,
        numero_factura=proyecto.numero_factura,
        fecha_facturacion=proyecto.fecha_facturacion,
        fecha_cobro=proyecto.fecha_cobro,
        monto_facturado=proyecto.monto_facturado,
        total_presupuestado=agg.get(proyecto.id, {}).get("presup", Decimal("0")),
        total_ejecutado=agg.get(proyecto.id, {}).get("ejec", Decimal("0")),
    )


@router.patch(
    "/finanzas/facturacion/{proyecto_id}/revertir",
    response_model=FacturacionProyectoItem,
)
def revertir_facturacion(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Revierte el estado de facturación al paso anterior.
    cobrado -> facturado | facturado -> pendiente (limpia datos del paso revertido).
    """
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    if proyecto.estado_facturacion == EstadoFacturacion.cobrado:
        proyecto.estado_facturacion = EstadoFacturacion.facturado
        proyecto.fecha_cobro = None
    elif proyecto.estado_facturacion == EstadoFacturacion.facturado:
        proyecto.estado_facturacion = EstadoFacturacion.pendiente
        proyecto.numero_factura = None
        proyecto.fecha_facturacion = None
        proyecto.monto_facturado = None
    else:
        raise HTTPException(status_code=400, detail="Nada para revertir")

    db.commit()
    db.refresh(proyecto)
    agg = _agregados_por_proyecto(db, [proyecto.id])
    return FacturacionProyectoItem(
        proyecto_id=proyecto.id,
        proyecto_nombre=proyecto.nombre,
        cliente_nombre=proyecto.cliente.nombre_display if proyecto.cliente else None,
        fecha_fin_real=proyecto.fecha_fin_real,
        estado_facturacion=proyecto.estado_facturacion.value,
        numero_factura=proyecto.numero_factura,
        fecha_facturacion=proyecto.fecha_facturacion,
        fecha_cobro=proyecto.fecha_cobro,
        monto_facturado=proyecto.monto_facturado,
        total_presupuestado=agg.get(proyecto.id, {}).get("presup", Decimal("0")),
        total_ejecutado=agg.get(proyecto.id, {}).get("ejec", Decimal("0")),
    )


@router.get("/finanzas/facturacion/{proyecto_id}/pdf")
def descargar_pdf_facturacion(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Genera el PDF "super remito" del proyecto: datos del cliente,
    listado de actividades ejecutadas con precios snapshot, totales y
    estado de facturación / cobro.
    """
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    actividades = (
        db.query(ProyectoActividad)
        .filter(
            ProyectoActividad.proyecto_id == proyecto_id,
            ProyectoActividad.activo == True,
        )
        .order_by(ProyectoActividad.orden.asc(), ProyectoActividad.created_at.asc())
        .all()
    )

    items = []
    total_presup = Decimal("0")
    total_ejec = Decimal("0")
    for a in actividades:
        precio = a.precio_unitario_snapshot or Decimal("0")
        cant_plan = a.cantidad_planificada or Decimal("0")
        cant_ejec = a.cantidad_ejecutada or Decimal("0")
        sub_presup = precio * cant_plan
        sub_ejec = precio * cant_ejec
        total_presup += sub_presup
        total_ejec += sub_ejec
        items.append({
            "actividad_codigo": a.actividad_tipo.codigo if a.actividad_tipo else None,
            "actividad_nombre": a.actividad_tipo.nombre if a.actividad_tipo else "(sin nombre)",
            "unidad": a.actividad_tipo.unidad_trabajo if a.actividad_tipo else None,
            "cantidad_planificada": cant_plan,
            "cantidad_ejecutada": cant_ejec,
            "precio_unitario_snapshot": precio,
            "subtotal_presupuestado": sub_presup,
            "subtotal_ejecutado": sub_ejec,
        })

    datos = {
        "fecha_emision": date.today(),
        "proyecto_nombre": proyecto.nombre,
        "cliente_nombre": (proyecto.cliente.nombre_display if proyecto.cliente else None),
        "ubicacion": proyecto.ubicacion,
        "lista_precio_nombre": proyecto.lista_precio.nombre if proyecto.lista_precio else None,
        "fecha_inicio": proyecto.fecha_inicio,
        "fecha_fin_real": proyecto.fecha_fin_real,
        "estado_facturacion": (
            proyecto.estado_facturacion.value if proyecto.estado_facturacion else "pendiente"
        ),
        "numero_factura": proyecto.numero_factura,
        "fecha_facturacion": proyecto.fecha_facturacion,
        "monto_facturado": proyecto.monto_facturado,
        "fecha_cobro": proyecto.fecha_cobro,
        "items": items,
        "total_presupuestado": total_presup,
        "total_ejecutado": total_ejec,
    }

    pdf_bytes = generar_pdf_facturacion_proyecto(datos)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in proyecto.nombre)[:60]
    filename = f"detalle_{safe_name}_{date.today().isoformat()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

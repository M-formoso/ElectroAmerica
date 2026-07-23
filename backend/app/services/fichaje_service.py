from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime, timezone

from app.models.fichaje import FichajeJornada, EstadoFichaje
from app.schemas.fichaje import (
    IniciarFichajeRequest, IniciarFichajeAdminRequest, FinalizarFichajeRequest,
    FichajeResponse, FichajeListResponse, ResumenFichajes,
)


def _to_response(fichaje: FichajeJornada) -> FichajeResponse:
    return FichajeResponse(
        id=fichaje.id,
        operario_id=fichaje.operario_id,
        operario_nombre=fichaje.operario.nombre if fichaje.operario else None,
        operario_apellido=fichaje.operario.apellido if fichaje.operario else None,
        fecha=fichaje.fecha,
        hora_inicio=fichaje.hora_inicio,
        hora_fin=fichaje.hora_fin,
        horas_trabajadas=fichaje.horas_trabajadas,
        estado=fichaje.estado,
        proyecto_id=fichaje.proyecto_id,
        proyecto_nombre=fichaje.proyecto.nombre if fichaje.proyecto else None,
        notas_inicio=fichaje.notas_inicio,
        notas_fin=fichaje.notas_fin,
        created_at=fichaje.created_at,
        updated_at=fichaje.updated_at,
    )


def _to_list_response(fichaje: FichajeJornada) -> FichajeListResponse:
    return FichajeListResponse(
        id=fichaje.id,
        operario_id=fichaje.operario_id,
        operario_nombre=fichaje.operario.nombre if fichaje.operario else None,
        operario_apellido=fichaje.operario.apellido if fichaje.operario else None,
        fecha=fichaje.fecha,
        hora_inicio=fichaje.hora_inicio,
        hora_fin=fichaje.hora_fin,
        horas_trabajadas=fichaje.horas_trabajadas,
        estado=fichaje.estado,
        proyecto_id=fichaje.proyecto_id,
        proyecto_nombre=fichaje.proyecto.nombre if fichaje.proyecto else None,
    )


def obtener_fichaje_activo(db: Session, operario_id: UUID) -> Optional[FichajeJornada]:
    return (
        db.query(FichajeJornada)
        .filter(
            FichajeJornada.operario_id == operario_id,
            FichajeJornada.estado == EstadoFichaje.activo,
            FichajeJornada.activo == True,
        )
        .first()
    )


def iniciar_fichaje(db: Session, operario_id: UUID, data: IniciarFichajeRequest) -> FichajeResponse:
    activo = obtener_fichaje_activo(db, operario_id)
    if activo:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Ya tenés un fichaje activo. Primero finalizá el turno actual.")

    ahora = datetime.now(timezone.utc)
    fichaje = FichajeJornada(
        operario_id=operario_id,
        fecha=ahora.date(),
        hora_inicio=ahora,
        estado=EstadoFichaje.activo,
        proyecto_id=data.proyecto_id,
        notas_inicio=data.notas_inicio,
    )
    db.add(fichaje)
    db.commit()
    db.refresh(fichaje)
    return _to_response(fichaje)


def finalizar_fichaje(db: Session, fichaje_id: UUID, operario_id: UUID, data: FinalizarFichajeRequest) -> FichajeResponse:
    fichaje = (
        db.query(FichajeJornada)
        .filter(FichajeJornada.id == fichaje_id, FichajeJornada.activo == True)
        .first()
    )
    if not fichaje:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Fichaje no encontrado")

    if str(fichaje.operario_id) != str(operario_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No podés finalizar un fichaje que no es tuyo")

    if fichaje.estado != EstadoFichaje.activo:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="El fichaje no está activo")

    ahora = datetime.now(timezone.utc)
    diferencia = ahora - fichaje.hora_inicio.replace(tzinfo=timezone.utc) if fichaje.hora_inicio.tzinfo is None else ahora - fichaje.hora_inicio
    horas = Decimal(str(round(diferencia.total_seconds() / 3600, 2)))

    fichaje.hora_fin = ahora
    fichaje.horas_trabajadas = horas
    fichaje.estado = EstadoFichaje.completado
    fichaje.notas_fin = data.notas_fin
    db.commit()
    db.refresh(fichaje)
    return _to_response(fichaje)


def cancelar_fichaje(db: Session, fichaje_id: UUID, operario_id: UUID) -> FichajeResponse:
    fichaje = (
        db.query(FichajeJornada)
        .filter(FichajeJornada.id == fichaje_id, FichajeJornada.activo == True)
        .first()
    )
    if not fichaje:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Fichaje no encontrado")

    if str(fichaje.operario_id) != str(operario_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No podés cancelar un fichaje que no es tuyo")

    if fichaje.estado != EstadoFichaje.activo:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Solo se pueden cancelar fichajes activos")

    fichaje.estado = EstadoFichaje.cancelado
    db.commit()
    db.refresh(fichaje)
    return _to_response(fichaje)


def listar_fichajes(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    operario_id: Optional[UUID] = None,
    estado: Optional[EstadoFichaje] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[FichajeListResponse]:
    q = db.query(FichajeJornada).filter(FichajeJornada.activo == True)

    if fecha_desde:
        q = q.filter(FichajeJornada.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(FichajeJornada.fecha <= fecha_hasta)
    if operario_id:
        q = q.filter(FichajeJornada.operario_id == operario_id)
    if estado:
        q = q.filter(FichajeJornada.estado == estado)

    fichajes = q.order_by(FichajeJornada.hora_inicio.desc()).offset(skip).limit(limit).all()
    return [_to_list_response(f) for f in fichajes]


def obtener_mis_fichajes(db: Session, operario_id: UUID, limit: int = 30) -> List[FichajeListResponse]:
    fichajes = (
        db.query(FichajeJornada)
        .filter(FichajeJornada.operario_id == operario_id, FichajeJornada.activo == True)
        .order_by(FichajeJornada.hora_inicio.desc())
        .limit(limit)
        .all()
    )
    return [_to_list_response(f) for f in fichajes]


def obtener_todos_activos(db: Session) -> List[FichajeListResponse]:
    """Devuelve todos los fichajes activos en este momento (para panel admin)."""
    fichajes = (
        db.query(FichajeJornada)
        .filter(FichajeJornada.estado == EstadoFichaje.activo, FichajeJornada.activo == True)
        .order_by(FichajeJornada.hora_inicio.asc())
        .all()
    )
    return [_to_list_response(f) for f in fichajes]


def iniciar_fichaje_admin(db: Session, operario_id: UUID, data: IniciarFichajeAdminRequest) -> FichajeResponse:
    """Admin ficha la entrada de un operario específico."""
    activo = obtener_fichaje_activo(db, operario_id)
    if activo:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="El operario ya tiene un fichaje activo.")

    ahora = datetime.now(timezone.utc)
    fichaje = FichajeJornada(
        operario_id=operario_id,
        fecha=ahora.date(),
        hora_inicio=ahora,
        estado=EstadoFichaje.activo,
        proyecto_id=data.proyecto_id,
        notas_inicio=data.notas_inicio,
    )
    db.add(fichaje)
    db.commit()
    db.refresh(fichaje)
    return _to_response(fichaje)


def finalizar_fichaje_admin(db: Session, fichaje_id: UUID, data: FinalizarFichajeRequest) -> FichajeResponse:
    """Admin ficha la salida de cualquier fichaje activo."""
    fichaje = (
        db.query(FichajeJornada)
        .filter(FichajeJornada.id == fichaje_id, FichajeJornada.activo == True)
        .first()
    )
    if not fichaje:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Fichaje no encontrado")

    if fichaje.estado != EstadoFichaje.activo:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="El fichaje no está activo")

    ahora = datetime.now(timezone.utc)
    inicio = fichaje.hora_inicio.replace(tzinfo=timezone.utc) if fichaje.hora_inicio.tzinfo is None else fichaje.hora_inicio
    diferencia = ahora - inicio
    horas = Decimal(str(round(diferencia.total_seconds() / 3600, 2)))

    fichaje.hora_fin = ahora
    fichaje.horas_trabajadas = horas
    fichaje.estado = EstadoFichaje.completado
    fichaje.notas_fin = data.notas_fin
    db.commit()
    db.refresh(fichaje)
    return _to_response(fichaje)


def resumen_fichajes(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    operario_id: Optional[UUID] = None,
) -> ResumenFichajes:
    q = db.query(FichajeJornada).filter(FichajeJornada.activo == True)

    if fecha_desde:
        q = q.filter(FichajeJornada.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(FichajeJornada.fecha <= fecha_hasta)
    if operario_id:
        q = q.filter(FichajeJornada.operario_id == operario_id)

    todos = q.all()
    activos = [f for f in todos if f.estado == EstadoFichaje.activo]
    completados = [f for f in todos if f.estado == EstadoFichaje.completado]
    horas = sum((f.horas_trabajadas or Decimal('0')) for f in completados)
    promedio = (horas / len(completados)) if completados else Decimal('0')

    return ResumenFichajes(
        total_fichajes=len(todos),
        fichajes_activos=len(activos),
        fichajes_completados=len(completados),
        horas_totales=round(horas, 2),
        promedio_horas=round(promedio, 2),
    )

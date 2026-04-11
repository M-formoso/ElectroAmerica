from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timezone
from decimal import Decimal

from app.models.jornada_operario import JornadaOperario, EstadoJornada
from app.models.material_jornada import MaterialJornada, EstadoMaterialJornada, DestinoDevolucion
from app.models.asignacion_diaria import AsignacionDiaria, EstadoAsignacion
from app.models.material import Material
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.models.equipo import Equipo, EstadoEquipo
from app.models.proyecto import Proyecto
from app.models.etapa import Etapa
from app.models.usuario import Usuario
from app.models.alerta import Alerta, TipoAlerta, PrioridadAlerta
from app.schemas.jornada_operario import (
    IniciarJornadaRequest, MarcarLlegadaRequest, CerrarJornadaRequest,
    MaterialJornadaCargar, MaterialJornadaRendir
)


# ============== JORNADA OPERARIO ==============

def get_jornada_activa_operario(db: Session, operario_id: UUID) -> Optional[JornadaOperario]:
    """Obtiene la jornada activa del operario (no finalizada)."""
    return db.query(JornadaOperario).filter(
        JornadaOperario.operario_id == operario_id,
        JornadaOperario.activo == True,
        JornadaOperario.estado.notin_([EstadoJornada.finalizada, EstadoJornada.cancelada])
    ).first()


def get_jornada_operario(db: Session, jornada_id: UUID) -> Optional[JornadaOperario]:
    """Obtiene una jornada por ID."""
    return db.query(JornadaOperario).filter(
        JornadaOperario.id == jornada_id,
        JornadaOperario.activo == True
    ).first()


def get_jornadas_operario(
    db: Session,
    operario_id: Optional[UUID] = None,
    proyecto_id: Optional[UUID] = None,
    fecha: Optional[date] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    estado: Optional[EstadoJornada] = None,
    skip: int = 0,
    limit: int = 100
) -> List[JornadaOperario]:
    """Obtiene jornadas con filtros."""
    query = db.query(JornadaOperario).filter(JornadaOperario.activo == True)

    if operario_id:
        query = query.filter(JornadaOperario.operario_id == operario_id)
    if proyecto_id:
        query = query.filter(JornadaOperario.proyecto_id == proyecto_id)
    if fecha:
        query = query.filter(JornadaOperario.fecha == fecha)
    if fecha_desde:
        query = query.filter(JornadaOperario.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(JornadaOperario.fecha <= fecha_hasta)
    if estado:
        query = query.filter(JornadaOperario.estado == estado)

    return query.order_by(JornadaOperario.fecha.desc(), JornadaOperario.hora_inicio.desc()).offset(skip).limit(limit).all()


def get_jornadas_activas(db: Session) -> List[JornadaOperario]:
    """Obtiene todas las jornadas activas (en curso)."""
    return db.query(JornadaOperario).filter(
        JornadaOperario.activo == True,
        JornadaOperario.estado.in_([
            EstadoJornada.iniciada,
            EstadoJornada.en_camino,
            EstadoJornada.en_obra
        ])
    ).all()


def iniciar_jornada(
    db: Session,
    operario_id: UUID,
    data: IniciarJornadaRequest,
    asignacion_id: Optional[UUID] = None
) -> JornadaOperario:
    """
    Inicia una nueva jornada para el operario.

    - Verifica que no tenga jornada activa
    - Verifica disponibilidad del vehículo
    - Crea la jornada con estado INICIADA
    - Registra los materiales cargados
    - Actualiza el estado del vehículo
    """
    # Verificar que no tenga jornada activa
    jornada_activa = get_jornada_activa_operario(db, operario_id)
    if jornada_activa:
        raise ValueError("El operario ya tiene una jornada activa. Debe cerrarla primero.")

    # Verificar disponibilidad del vehículo
    vehiculo = db.query(Equipo).filter(Equipo.id == data.vehiculo_id).first()
    if not vehiculo:
        raise ValueError("Vehículo no encontrado")
    if vehiculo.estado == EstadoEquipo.asignado:
        raise ValueError("El vehículo ya está asignado a otra jornada")
    if vehiculo.estado == EstadoEquipo.mantenimiento:
        raise ValueError("El vehículo está en mantenimiento")

    # Crear la jornada
    ahora = datetime.now(timezone.utc)
    jornada = JornadaOperario(
        operario_id=operario_id,
        fecha=date.today(),
        vehiculo_id=data.vehiculo_id,
        proyecto_id=data.proyecto_id,
        etapa_id=data.etapa_id,
        km_inicial=data.km_inicial,
        hora_inicio=ahora,
        estado=EstadoJornada.iniciada,
        observaciones_inicio=data.observaciones,
        asignacion_diaria_id=asignacion_id
    )
    db.add(jornada)

    # Actualizar estado del vehículo
    vehiculo.estado = EstadoEquipo.asignado
    if data.km_inicial:
        vehiculo.km_actual = data.km_inicial

    # Si viene de una asignación, actualizarla
    if asignacion_id:
        asignacion = db.query(AsignacionDiaria).filter(AsignacionDiaria.id == asignacion_id).first()
        if asignacion:
            asignacion.estado = EstadoAsignacion.en_curso

    db.flush()  # Para obtener el ID de la jornada

    # Registrar materiales cargados
    for mat in data.materiales:
        material_jornada = MaterialJornada(
            jornada_id=jornada.id,
            material_id=mat.material_id,
            cantidad_asignada=Decimal(str(mat.cantidad_cargada)),
            cantidad_cargada=Decimal(str(mat.cantidad_cargada)),
            estado=EstadoMaterialJornada.cargado,
            notas=mat.notas
        )
        db.add(material_jornada)

        # Descontar del stock
        material = db.query(Material).filter(Material.id == mat.material_id).first()
        if material:
            stock_anterior = float(material.stock_actual)
            material.stock_actual = Decimal(str(stock_anterior - mat.cantidad_cargada))

            # Registrar movimiento de stock
            movimiento = MovimientoStock(
                material_id=mat.material_id,
                tipo=TipoMovimiento.salida,
                cantidad=Decimal(str(mat.cantidad_cargada)),
                stock_anterior=Decimal(str(stock_anterior)),
                stock_nuevo=material.stock_actual,
                motivo=f"Jornada operario - Proyecto: {jornada.proyecto_id}",
                proyecto_id=data.proyecto_id,
                usuario_id=operario_id
            )
            db.add(movimiento)

    db.commit()
    db.refresh(jornada)
    return jornada


def marcar_llegada_obra(
    db: Session,
    jornada_id: UUID,
    data: MarcarLlegadaRequest
) -> JornadaOperario:
    """Marca la llegada del operario a la obra."""
    jornada = get_jornada_operario(db, jornada_id)
    if not jornada:
        raise ValueError("Jornada no encontrada")

    if jornada.estado not in [EstadoJornada.iniciada, EstadoJornada.en_camino]:
        raise ValueError("La jornada no está en un estado válido para marcar llegada")

    jornada.estado = EstadoJornada.en_obra
    jornada.hora_llegada_obra = datetime.now(timezone.utc)
    if data.observaciones:
        jornada.novedades = (jornada.novedades or "") + f"\n[Llegada] {data.observaciones}"

    # Actualizar estado de materiales
    for mat in jornada.materiales:
        if mat.estado == EstadoMaterialJornada.cargado:
            mat.estado = EstadoMaterialJornada.en_uso

    db.commit()
    db.refresh(jornada)
    return jornada


def marcar_en_camino(db: Session, jornada_id: UUID) -> JornadaOperario:
    """Marca que el operario está en camino a la obra."""
    jornada = get_jornada_operario(db, jornada_id)
    if not jornada:
        raise ValueError("Jornada no encontrada")

    if jornada.estado != EstadoJornada.iniciada:
        raise ValueError("La jornada debe estar iniciada para marcar en camino")

    jornada.estado = EstadoJornada.en_camino
    db.commit()
    db.refresh(jornada)
    return jornada


def reportar_novedad(
    db: Session,
    jornada_id: UUID,
    novedad: str,
    es_urgente: bool = False,
    usuario_id: Optional[UUID] = None
) -> JornadaOperario:
    """Registra una novedad durante la jornada."""
    jornada = get_jornada_operario(db, jornada_id)
    if not jornada:
        raise ValueError("Jornada no encontrada")

    ahora = datetime.now(timezone.utc).strftime("%H:%M")
    nueva_novedad = f"[{ahora}] {novedad}"
    jornada.novedades = (jornada.novedades or "") + "\n" + nueva_novedad

    # Si es urgente, crear una alerta
    if es_urgente:
        alerta = Alerta(
            tipo=TipoAlerta.ETAPA_PENDIENTE,  # Usar tipo existente o crear NOVEDAD_URGENTE
            prioridad=PrioridadAlerta.ALTA,
            titulo=f"Novedad urgente en obra",
            mensaje=f"Operario reporta: {novedad}",
            referencia_tipo="jornada_operario",
            referencia_id=jornada_id
        )
        db.add(alerta)

    db.commit()
    db.refresh(jornada)
    return jornada


def cerrar_jornada(
    db: Session,
    jornada_id: UUID,
    data: CerrarJornadaRequest
) -> JornadaOperario:
    """
    Cierra una jornada y procesa la rendición de materiales.

    - Actualiza el estado a FINALIZADA
    - Registra km final y horas trabajadas
    - Procesa la rendición de cada material
    - Devuelve stock si corresponde
    - Libera el vehículo
    """
    jornada = get_jornada_operario(db, jornada_id)
    if not jornada:
        raise ValueError("Jornada no encontrada")

    if jornada.estado == EstadoJornada.finalizada:
        raise ValueError("La jornada ya está finalizada")

    ahora = datetime.now(timezone.utc)

    # Actualizar datos de cierre
    jornada.hora_fin = ahora
    jornada.km_final = data.km_final
    jornada.observaciones_cierre = data.observaciones
    jornada.estado = EstadoJornada.finalizada

    # Calcular horas trabajadas si no se especificaron
    if data.horas_trabajadas:
        jornada.horas_trabajadas = Decimal(str(data.horas_trabajadas))
    elif jornada.hora_inicio:
        delta = ahora - jornada.hora_inicio
        jornada.horas_trabajadas = Decimal(str(round(delta.total_seconds() / 3600, 2)))

    if data.horas_extra:
        jornada.horas_extra = Decimal(str(data.horas_extra))

    # Procesar rendición de materiales
    for mat_rendicion in data.materiales:
        mat_jornada = db.query(MaterialJornada).filter(
            MaterialJornada.jornada_id == jornada_id,
            MaterialJornada.material_id == mat_rendicion.material_id
        ).first()

        if mat_jornada:
            mat_jornada.cantidad_consumida = Decimal(str(mat_rendicion.cantidad_consumida))
            mat_jornada.cantidad_devuelta = Decimal(str(mat_rendicion.cantidad_devuelta))
            mat_jornada.notas = mat_rendicion.notas

            # Determinar estado final y procesar devolución
            if mat_rendicion.cantidad_devuelta > 0:
                if mat_rendicion.destino_devolucion == DestinoDevolucion.deposito:
                    mat_jornada.estado = EstadoMaterialJornada.devuelto_deposito
                    mat_jornada.destino_devolucion = DestinoDevolucion.deposito

                    # Devolver al stock
                    material = db.query(Material).filter(Material.id == mat_rendicion.material_id).first()
                    if material:
                        stock_anterior = float(material.stock_actual)
                        material.stock_actual = Decimal(str(stock_anterior + mat_rendicion.cantidad_devuelta))

                        # Registrar movimiento
                        movimiento = MovimientoStock(
                            material_id=mat_rendicion.material_id,
                            tipo=TipoMovimiento.devolucion,
                            cantidad=Decimal(str(mat_rendicion.cantidad_devuelta)),
                            stock_anterior=Decimal(str(stock_anterior)),
                            stock_nuevo=material.stock_actual,
                            motivo=f"Devolución jornada - {jornada.proyecto_id}",
                            proyecto_id=jornada.proyecto_id,
                            usuario_id=jornada.operario_id
                        )
                        db.add(movimiento)

                elif mat_rendicion.destino_devolucion == DestinoDevolucion.obra:
                    mat_jornada.estado = EstadoMaterialJornada.devuelto_obra
                    mat_jornada.destino_devolucion = DestinoDevolucion.obra
            else:
                mat_jornada.estado = EstadoMaterialJornada.consumido

    # Liberar vehículo
    if jornada.vehiculo_id:
        vehiculo = db.query(Equipo).filter(Equipo.id == jornada.vehiculo_id).first()
        if vehiculo:
            vehiculo.estado = EstadoEquipo.disponible
            if data.km_final:
                vehiculo.km_actual = data.km_final

    # Actualizar asignación si existe
    if jornada.asignacion_diaria_id:
        asignacion = db.query(AsignacionDiaria).filter(
            AsignacionDiaria.id == jornada.asignacion_diaria_id
        ).first()
        if asignacion:
            asignacion.estado = EstadoAsignacion.completada

    db.commit()
    db.refresh(jornada)
    return jornada


def cancelar_jornada(db: Session, jornada_id: UUID, motivo: str) -> JornadaOperario:
    """Cancela una jornada y devuelve materiales al stock."""
    jornada = get_jornada_operario(db, jornada_id)
    if not jornada:
        raise ValueError("Jornada no encontrada")

    if jornada.estado == EstadoJornada.finalizada:
        raise ValueError("No se puede cancelar una jornada finalizada")

    # Devolver todos los materiales cargados
    for mat_jornada in jornada.materiales:
        if mat_jornada.cantidad_cargada and mat_jornada.cantidad_cargada > 0:
            material = db.query(Material).filter(Material.id == mat_jornada.material_id).first()
            if material:
                stock_anterior = float(material.stock_actual)
                cantidad_devolver = float(mat_jornada.cantidad_cargada)
                material.stock_actual = Decimal(str(stock_anterior + cantidad_devolver))

                movimiento = MovimientoStock(
                    material_id=mat_jornada.material_id,
                    tipo=TipoMovimiento.devolucion,
                    cantidad=Decimal(str(cantidad_devolver)),
                    stock_anterior=Decimal(str(stock_anterior)),
                    stock_nuevo=material.stock_actual,
                    motivo=f"Cancelación jornada: {motivo}",
                    proyecto_id=jornada.proyecto_id,
                    usuario_id=jornada.operario_id
                )
                db.add(movimiento)

    # Liberar vehículo
    if jornada.vehiculo_id:
        vehiculo = db.query(Equipo).filter(Equipo.id == jornada.vehiculo_id).first()
        if vehiculo:
            vehiculo.estado = EstadoEquipo.disponible

    jornada.estado = EstadoJornada.cancelada
    jornada.novedades = (jornada.novedades or "") + f"\n[CANCELADA] {motivo}"

    db.commit()
    db.refresh(jornada)
    return jornada


# ============== HELPERS PARA RESPUESTAS ==============

def enrich_jornada_response(db: Session, jornada: JornadaOperario) -> dict:
    """Enriquece una jornada con datos relacionados para la respuesta."""
    operario = db.query(Usuario).filter(Usuario.id == jornada.operario_id).first()
    vehiculo = db.query(Equipo).filter(Equipo.id == jornada.vehiculo_id).first() if jornada.vehiculo_id else None
    proyecto = db.query(Proyecto).filter(Proyecto.id == jornada.proyecto_id).first()
    etapa = db.query(Etapa).filter(Etapa.id == jornada.etapa_id).first() if jornada.etapa_id else None

    materiales_enriched = []
    for mat in jornada.materiales:
        material = db.query(Material).filter(Material.id == mat.material_id).first()
        materiales_enriched.append({
            **mat.__dict__,
            "material_codigo": material.codigo if material else None,
            "material_nombre": material.nombre if material else None,
            "material_unidad": material.unidad if material else None
        })

    return {
        **jornada.__dict__,
        "operario_nombre": f"{operario.nombre} {operario.apellido}" if operario else None,
        "vehiculo_nombre": vehiculo.nombre if vehiculo else None,
        "vehiculo_patente": vehiculo.patente if vehiculo else None,
        "proyecto_nombre": proyecto.nombre if proyecto else None,
        "etapa_nombre": etapa.nombre if etapa else None,
        "km_recorridos": jornada.km_recorridos,
        "duracion_total": jornada.duracion_total,
        "materiales": materiales_enriched
    }


# ============== ESTADÍSTICAS ==============

def get_estadisticas_dia(db: Session, fecha: date) -> dict:
    """Obtiene estadísticas de jornadas de un día."""
    jornadas = get_jornadas_operario(db, fecha=fecha, limit=1000)

    por_estado = {}
    for jornada in jornadas:
        estado = jornada.estado.value
        por_estado[estado] = por_estado.get(estado, 0) + 1

    operarios = set(j.operario_id for j in jornadas)

    return {
        "fecha": fecha,
        "total_operarios": len(operarios),
        "jornadas_planificadas": por_estado.get("planificada", 0),
        "jornadas_iniciadas": por_estado.get("iniciada", 0) + por_estado.get("en_camino", 0),
        "jornadas_en_obra": por_estado.get("en_obra", 0),
        "jornadas_finalizadas": por_estado.get("finalizada", 0)
    }

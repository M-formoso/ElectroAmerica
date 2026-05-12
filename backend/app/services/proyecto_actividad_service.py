"""
Servicio para gestionar actividades de proyecto y avances.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import date
from fastapi import HTTPException

from app.models.proyecto_actividad import ProyectoActividad, AvanceActividad, ProyectoHerramienta
from app.models.actividad_tipo import ActividadTipo, MaterialActividadTipo
from app.models.proyecto import Proyecto
from app.models.herramienta import Herramienta
from app.models.material import Material
from app.models.deposito import DepositoMaterial
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.schemas.proyecto_actividad import (
    ProyectoActividadCreate,
    ProyectoActividadUpdate,
    AvanceActividadCreate,
    AvanceActividadUpdate,
    MaterialCalculado,
    MaterialConsumido,
    ResumenActividadesProyecto,
)


class ProyectoActividadService:
    """Servicio para gestionar actividades de proyecto."""

    def __init__(self, db: Session):
        self.db = db

    # ============ Cálculo de Materiales ============

    def calcular_materiales_actividad(
        self,
        actividad_tipo_id: UUID,
        cantidad: Decimal,
        deposito_id: Optional[UUID] = None,
    ) -> List[MaterialCalculado]:
        """
        Calcula los materiales necesarios para una cantidad de actividad.

        Si deposito_id esta seteado, el stock_actual mostrado corresponde
        al stock de ese deposito para cada material (DepositoMaterial). Si
        es None, se usa el stock global (Material.stock_actual).

        Ejemplo: Si la actividad "Contrabases" requiere 7.14kg de cemento por unidad
        y se planifican 10 unidades, calcula 71.4kg de cemento.
        """
        materiales_actividad = self.db.query(MaterialActividadTipo).filter(
            MaterialActividadTipo.actividad_tipo_id == actividad_tipo_id,
            MaterialActividadTipo.activo == True
        ).all()

        # Precargar stocks del deposito en una sola query si aplica
        stocks_deposito = {}
        if deposito_id and materiales_actividad:
            material_ids = [mat.material_id for mat in materiales_actividad]
            rows = self.db.query(DepositoMaterial).filter(
                DepositoMaterial.deposito_id == deposito_id,
                DepositoMaterial.material_id.in_(material_ids),
                DepositoMaterial.activo == True,
            ).all()
            stocks_deposito = {dm.material_id: dm.stock_actual for dm in rows}

        materiales_calculados = []
        for mat in materiales_actividad:
            material = self.db.query(Material).filter(Material.id == mat.material_id).first()
            if material:
                cantidad_total = mat.cantidad_por_unidad * cantidad
                if deposito_id:
                    stock = stocks_deposito.get(material.id, Decimal("0"))
                else:
                    stock = material.stock_actual
                materiales_calculados.append(MaterialCalculado(
                    material_id=material.id,
                    material_nombre=material.nombre,
                    material_codigo=material.codigo,
                    cantidad_total=cantidad_total,
                    unidad=material.unidad,
                    stock_actual=stock,
                ))

        return materiales_calculados

    # ============ CRUD ProyectoActividad ============

    def crear_actividad_proyecto(
        self,
        proyecto_id: UUID,
        actividad_data: ProyectoActividadCreate
    ) -> ProyectoActividad:
        """Asigna una actividad tipo a un proyecto con cantidad planificada."""
        # Verificar que el proyecto existe
        proyecto = self.db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")

        # Verificar que la actividad tipo existe
        actividad_tipo = self.db.query(ActividadTipo).filter(
            ActividadTipo.id == actividad_data.actividad_tipo_id
        ).first()
        if not actividad_tipo:
            raise ValueError(f"Actividad tipo {actividad_data.actividad_tipo_id} no encontrada")

        # Calcular materiales necesarios
        materiales_calculados = self.calcular_materiales_actividad(
            actividad_data.actividad_tipo_id,
            actividad_data.cantidad_planificada
        )

        # Crear la actividad de proyecto
        actividad = ProyectoActividad(
            proyecto_id=proyecto_id,
            actividad_tipo_id=actividad_data.actividad_tipo_id,
            cantidad_planificada=actividad_data.cantidad_planificada,
            cantidad_ejecutada=Decimal("0"),
            orden=actividad_data.orden or 0,
            observaciones=actividad_data.observaciones,
            materiales_calculados=[m.model_dump(mode='json') for m in materiales_calculados] if materiales_calculados else None
        )

        self.db.add(actividad)
        self.db.commit()
        self.db.refresh(actividad)

        return actividad

    def asignar_actividades_bulk(
        self,
        proyecto_id: UUID,
        actividades_tipo_ids: List[UUID]
    ) -> List[ProyectoActividad]:
        """Asigna múltiples actividades tipo a un proyecto (cantidad inicial = 1)."""
        actividades_creadas = []
        orden = 0

        for actividad_tipo_id in actividades_tipo_ids:
            actividad_data = ProyectoActividadCreate(
                actividad_tipo_id=actividad_tipo_id,
                cantidad_planificada=Decimal("1"),
                orden=orden
            )
            actividad = self.crear_actividad_proyecto(proyecto_id, actividad_data)
            actividades_creadas.append(actividad)
            orden += 1

        return actividades_creadas

    def obtener_actividades_proyecto(
        self,
        proyecto_id: UUID
    ) -> List[ProyectoActividad]:
        """Obtiene todas las actividades de un proyecto."""
        return self.db.query(ProyectoActividad).filter(
            ProyectoActividad.proyecto_id == proyecto_id,
            ProyectoActividad.activo == True
        ).order_by(ProyectoActividad.orden).all()

    def obtener_actividad(self, actividad_id: UUID) -> Optional[ProyectoActividad]:
        """Obtiene una actividad de proyecto por ID."""
        return self.db.query(ProyectoActividad).filter(
            ProyectoActividad.id == actividad_id
        ).first()

    def actualizar_actividad(
        self,
        actividad_id: UUID,
        actividad_data: ProyectoActividadUpdate
    ) -> ProyectoActividad:
        """Actualiza una actividad de proyecto."""
        actividad = self.obtener_actividad(actividad_id)
        if not actividad:
            raise ValueError(f"Actividad {actividad_id} no encontrada")

        # Si cambia la cantidad planificada, recalcular materiales
        if actividad_data.cantidad_planificada is not None:
            actividad.cantidad_planificada = actividad_data.cantidad_planificada
            materiales_calculados = self.calcular_materiales_actividad(
                actividad.actividad_tipo_id,
                actividad_data.cantidad_planificada
            )
            actividad.materiales_calculados = [m.model_dump(mode='json') for m in materiales_calculados]

        if actividad_data.observaciones is not None:
            actividad.observaciones = actividad_data.observaciones
        if actividad_data.orden is not None:
            actividad.orden = actividad_data.orden

        self.db.commit()
        self.db.refresh(actividad)
        return actividad

    def eliminar_actividad(self, actividad_id: UUID) -> bool:
        """Elimina (soft delete) una actividad de proyecto."""
        actividad = self.obtener_actividad(actividad_id)
        if not actividad:
            return False

        actividad.activo = False
        self.db.commit()
        return True

    # ============ Avances ============

    def registrar_avance(
        self,
        actividad_id: UUID,
        avance_data: AvanceActividadCreate,
        registrado_por_id: Optional[UUID] = None
    ) -> AvanceActividad:
        """
        Registra un avance en una actividad de proyecto.
        Actualiza la cantidad ejecutada y descuenta del stock los materiales
        consumidos (registrando movimientos).
        """
        actividad = self.obtener_actividad(actividad_id)
        if not actividad:
            raise ValueError(f"Actividad {actividad_id} no encontrada")

        proyecto = self.db.query(Proyecto).filter(
            Proyecto.id == actividad.proyecto_id
        ).first()
        deposito_id = proyecto.deposito_id if proyecto else None

        # Validar stock antes de descontar nada
        if avance_data.materiales_consumidos:
            for consumo in avance_data.materiales_consumidos:
                if consumo.cantidad <= 0:
                    continue
                material = self.db.query(Material).filter(
                    Material.id == consumo.material_id
                ).first()
                if not material:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Material {consumo.material_id} no encontrado"
                    )
                # Validar contra deposito si esta configurado, sino global
                if deposito_id:
                    dm = self.db.query(DepositoMaterial).filter(
                        DepositoMaterial.deposito_id == deposito_id,
                        DepositoMaterial.material_id == material.id,
                        DepositoMaterial.activo == True,
                    ).first()
                    stock_disp = dm.stock_actual if dm else Decimal("0")
                else:
                    stock_disp = material.stock_actual
                if stock_disp < consumo.cantidad:
                    fuente = "el deposito del proyecto" if deposito_id else "el stock global"
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Stock insuficiente de '{material.nombre}' en {fuente}. "
                            f"Disponible: {stock_disp} {material.unidad}, "
                            f"requerido: {consumo.cantidad}"
                        )
                    )

        # Crear el registro de avance
        avance = AvanceActividad(
            proyecto_actividad_id=actividad_id,
            fecha=avance_data.fecha,
            cantidad=avance_data.cantidad,
            observaciones=avance_data.observaciones,
            registrado_por_id=registrado_por_id,
            materiales_consumidos=[m.model_dump(mode='json') for m in avance_data.materiales_consumidos] if avance_data.materiales_consumidos else None
        )
        self.db.add(avance)

        # Actualizar cantidad ejecutada de la actividad
        actividad.cantidad_ejecutada = actividad.cantidad_ejecutada + avance_data.cantidad

        # Descontar stock y registrar movimientos. Si el proyecto tiene
        # deposito_id, se descuenta del DepositoMaterial; si no, del
        # stock global Material.stock_actual.
        if avance_data.materiales_consumidos:
            for consumo in avance_data.materiales_consumidos:
                if consumo.cantidad <= 0:
                    continue
                material = self.db.query(Material).filter(
                    Material.id == consumo.material_id
                ).first()
                if deposito_id:
                    dm = self.db.query(DepositoMaterial).filter(
                        DepositoMaterial.deposito_id == deposito_id,
                        DepositoMaterial.material_id == material.id,
                        DepositoMaterial.activo == True,
                    ).first()
                    if not dm:
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                f"El material '{material.nombre}' no esta cargado "
                                f"en el deposito del proyecto."
                            )
                        )
                    stock_anterior = dm.stock_actual
                    dm.stock_actual = stock_anterior - consumo.cantidad
                else:
                    stock_anterior = material.stock_actual
                    material.stock_actual = stock_anterior - consumo.cantidad

                self.db.add(MovimientoStock(
                    material_id=material.id,
                    tipo=TipoMovimiento.salida,
                    cantidad=consumo.cantidad,
                    stock_anterior=stock_anterior,
                    stock_nuevo=stock_anterior - consumo.cantidad,
                    motivo=(
                        f"Consumo en avance de tarea "
                        f"{actividad.actividad_tipo.nombre if actividad.actividad_tipo else ''}"
                        + (f" (deposito {deposito_id})" if deposito_id else "")
                    ).strip(),
                    proyecto_id=actividad.proyecto_id,
                    usuario_id=registrado_por_id
                ))

        self.db.commit()
        self.db.refresh(avance)

        # Actualizar porcentaje de avance del proyecto
        self._actualizar_avance_proyecto(actividad.proyecto_id)

        return avance

    def obtener_avances_actividad(
        self,
        actividad_id: UUID
    ) -> List[AvanceActividad]:
        """Obtiene todos los avances de una actividad."""
        return self.db.query(AvanceActividad).filter(
            AvanceActividad.proyecto_actividad_id == actividad_id,
            AvanceActividad.activo == True
        ).order_by(AvanceActividad.fecha.desc()).all()

    def actualizar_avance(
        self,
        avance_id: UUID,
        avance_data: AvanceActividadUpdate
    ) -> AvanceActividad:
        """Actualiza un registro de avance."""
        avance = self.db.query(AvanceActividad).filter(AvanceActividad.id == avance_id).first()
        if not avance:
            raise ValueError(f"Avance {avance_id} no encontrado")

        actividad = self.obtener_actividad(avance.proyecto_actividad_id)

        # Si cambia la cantidad, recalcular cantidad ejecutada
        if avance_data.cantidad is not None:
            diferencia = avance_data.cantidad - avance.cantidad
            avance.cantidad = avance_data.cantidad
            actividad.cantidad_ejecutada = actividad.cantidad_ejecutada + diferencia

        if avance_data.observaciones is not None:
            avance.observaciones = avance_data.observaciones
        if avance_data.materiales_consumidos is not None:
            avance.materiales_consumidos = [m.model_dump(mode='json') for m in avance_data.materiales_consumidos]

        self.db.commit()
        self.db.refresh(avance)

        # Actualizar porcentaje de avance del proyecto
        self._actualizar_avance_proyecto(actividad.proyecto_id)

        return avance

    def eliminar_avance(self, avance_id: UUID) -> bool:
        """Elimina un avance y resta la cantidad de la actividad."""
        avance = self.db.query(AvanceActividad).filter(AvanceActividad.id == avance_id).first()
        if not avance:
            return False

        actividad = self.obtener_actividad(avance.proyecto_actividad_id)

        # Restar cantidad del avance eliminado
        actividad.cantidad_ejecutada = actividad.cantidad_ejecutada - avance.cantidad
        if actividad.cantidad_ejecutada < 0:
            actividad.cantidad_ejecutada = Decimal("0")

        avance.activo = False
        self.db.commit()

        # Actualizar porcentaje de avance del proyecto
        self._actualizar_avance_proyecto(actividad.proyecto_id)

        return True

    # ============ Cálculo de Avance del Proyecto ============

    def _actualizar_avance_proyecto(self, proyecto_id: UUID):
        """
        Calcula y actualiza el porcentaje de avance global del proyecto
        basado en el avance de todas sus actividades.
        """
        actividades = self.obtener_actividades_proyecto(proyecto_id)

        if not actividades:
            return

        total_planificado = sum(a.cantidad_planificada for a in actividades)
        total_ejecutado = sum(a.cantidad_ejecutada for a in actividades)

        if total_planificado > 0:
            porcentaje = (total_ejecutado / total_planificado) * 100
        else:
            porcentaje = Decimal("0")

        # Actualizar el proyecto
        proyecto = self.db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.porcentaje_avance = min(porcentaje, Decimal("100"))
            self.db.commit()

    def obtener_resumen_proyecto(self, proyecto_id: UUID) -> ResumenActividadesProyecto:
        """Obtiene un resumen de todas las actividades del proyecto.

        Los materiales totales se recalculan en vivo a partir de la
        cantidad_por_unidad actual en actividades-tipo, asi cualquier
        cambio en el catalogo se refleja inmediatamente en el proyecto.

        Si el proyecto tiene deposito_id, el stock_actual viene de ese
        deposito; sino, del stock global.
        """
        actividades = self.obtener_actividades_proyecto(proyecto_id)
        proyecto = self.db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        deposito_id = proyecto.deposito_id if proyecto else None

        total = len(actividades)
        completadas = sum(1 for a in actividades if a.porcentaje_avance >= 100)
        en_progreso = sum(1 for a in actividades if 0 < a.porcentaje_avance < 100)
        pendientes = sum(1 for a in actividades if a.porcentaje_avance == 0)

        # Calcular avance global
        total_planificado = sum(a.cantidad_planificada for a in actividades)
        total_ejecutado = sum(a.cantidad_ejecutada for a in actividades)
        porcentaje_global = (total_ejecutado / total_planificado * 100) if total_planificado > 0 else Decimal("0")

        # Consolidar materiales totales (recalculo en vivo) y armar el
        # desglose por tarea: para cada material, lista de tareas que aportan.
        materiales_dict = {}
        for actividad in actividades:
            materiales_live = self.calcular_materiales_actividad(
                actividad.actividad_tipo_id,
                actividad.cantidad_planificada,
                deposito_id=deposito_id,
            )
            actividad_nombre = (
                actividad.actividad_tipo.nombre if actividad.actividad_tipo else ''
            )
            unidad_trabajo = (
                actividad.actividad_tipo.unidad_trabajo if actividad.actividad_tipo else None
            )
            for mat in materiales_live:
                mat_id = str(mat.material_id)
                aporte = {
                    'proyecto_actividad_id': actividad.id,
                    'actividad_tipo_id': actividad.actividad_tipo_id,
                    'actividad_nombre': actividad_nombre,
                    'cantidad_planificada': Decimal(str(actividad.cantidad_planificada)),
                    'unidad_trabajo': unidad_trabajo,
                    'cantidad_aporte': Decimal(str(mat.cantidad_total)),
                }
                if mat_id in materiales_dict:
                    materiales_dict[mat_id]['cantidad_total'] += Decimal(str(mat.cantidad_total))
                    materiales_dict[mat_id]['desglose_por_tarea'].append(aporte)
                else:
                    materiales_dict[mat_id] = {
                        'material_id': mat.material_id,
                        'material_nombre': mat.material_nombre,
                        'material_codigo': mat.material_codigo,
                        'cantidad_total': Decimal(str(mat.cantidad_total)),
                        'unidad': mat.unidad,
                        'desglose_por_tarea': [aporte],
                    }

        materiales_totales = [MaterialCalculado(**m) for m in materiales_dict.values()]

        return ResumenActividadesProyecto(
            total_actividades=total,
            actividades_completadas=completadas,
            actividades_en_progreso=en_progreso,
            actividades_pendientes=pendientes,
            porcentaje_avance_global=porcentaje_global,
            materiales_totales=materiales_totales
        )

    # ============ Herramientas de Proyecto ============

    def asignar_herramienta(
        self,
        proyecto_id: UUID,
        herramienta_id: UUID,
        fecha_asignacion: Optional[date] = None,
        observaciones: Optional[str] = None
    ) -> ProyectoHerramienta:
        """Asigna una herramienta a un proyecto."""
        # Verificar que existe la herramienta
        herramienta = self.db.query(Herramienta).filter(Herramienta.id == herramienta_id).first()
        if not herramienta:
            raise ValueError(f"Herramienta {herramienta_id} no encontrada")

        asignacion = ProyectoHerramienta(
            proyecto_id=proyecto_id,
            herramienta_id=herramienta_id,
            fecha_asignacion=fecha_asignacion or date.today(),
            observaciones=observaciones
        )

        self.db.add(asignacion)
        self.db.commit()
        self.db.refresh(asignacion)
        return asignacion

    def asignar_herramientas_bulk(
        self,
        proyecto_id: UUID,
        herramientas_ids: List[UUID]
    ) -> List[ProyectoHerramienta]:
        """Asigna múltiples herramientas a un proyecto."""
        asignaciones = []
        for herramienta_id in herramientas_ids:
            asignacion = self.asignar_herramienta(proyecto_id, herramienta_id)
            asignaciones.append(asignacion)
        return asignaciones

    def obtener_herramientas_proyecto(
        self,
        proyecto_id: UUID
    ) -> List[ProyectoHerramienta]:
        """Obtiene todas las herramientas asignadas a un proyecto."""
        return self.db.query(ProyectoHerramienta).filter(
            ProyectoHerramienta.proyecto_id == proyecto_id,
            ProyectoHerramienta.activo == True
        ).all()

    def desasignar_herramienta(
        self,
        proyecto_id: UUID,
        herramienta_id: UUID
    ) -> bool:
        """Desasigna una herramienta de un proyecto."""
        asignacion = self.db.query(ProyectoHerramienta).filter(
            ProyectoHerramienta.proyecto_id == proyecto_id,
            ProyectoHerramienta.herramienta_id == herramienta_id,
            ProyectoHerramienta.activo == True
        ).first()

        if not asignacion:
            return False

        asignacion.activo = False
        self.db.commit()
        return True

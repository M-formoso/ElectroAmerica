from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from app.models.actividad_tipo import ActividadTipo, MaterialActividadTipo
from app.models.material import Material
from app.schemas.actividad_tipo import (
    ActividadTipoCreate, ActividadTipoUpdate,
    MaterialActividadTipoCreate, MaterialActividadTipoUpdate
)


# ============== ACTIVIDADES TIPO ==============

def get_actividad_tipo(db: Session, actividad_id: UUID) -> Optional[ActividadTipo]:
    """Obtiene una actividad tipo por ID."""
    return db.query(ActividadTipo).filter(
        ActividadTipo.id == actividad_id,
        ActividadTipo.activo == True
    ).first()


def get_actividad_tipo_by_codigo(db: Session, codigo: str) -> Optional[ActividadTipo]:
    """Obtiene una actividad tipo por código."""
    return db.query(ActividadTipo).filter(
        ActividadTipo.codigo == codigo,
        ActividadTipo.activo == True
    ).first()


def get_actividades_tipo(
    db: Session,
    categoria: Optional[str] = None,
    busqueda: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[ActividadTipo]:
    """Obtiene actividades tipo con filtros."""
    query = db.query(ActividadTipo).filter(ActividadTipo.activo == True)

    if categoria:
        query = query.filter(ActividadTipo.categoria == categoria)
    if busqueda:
        query = query.filter(
            (ActividadTipo.nombre.ilike(f"%{busqueda}%")) |
            (ActividadTipo.codigo.ilike(f"%{busqueda}%")) |
            (ActividadTipo.descripcion.ilike(f"%{busqueda}%"))
        )

    return query.order_by(ActividadTipo.categoria, ActividadTipo.nombre).offset(skip).limit(limit).all()


def get_categorias(db: Session) -> List[dict]:
    """Obtiene las categorías existentes con cantidad de actividades."""
    results = db.query(
        ActividadTipo.categoria,
        func.count(ActividadTipo.id).label('cantidad')
    ).filter(
        ActividadTipo.activo == True,
        ActividadTipo.categoria.isnot(None)
    ).group_by(ActividadTipo.categoria).all()

    return [{"nombre": r.categoria, "cantidad_actividades": r.cantidad} for r in results]


def create_actividad_tipo(db: Session, actividad: ActividadTipoCreate) -> ActividadTipo:
    """Crea una nueva actividad tipo con sus materiales."""
    # Verificar que no exista el código
    existente = get_actividad_tipo_by_codigo(db, actividad.codigo)
    if existente:
        raise ValueError(f"Ya existe una actividad con el código {actividad.codigo}")

    # Crear actividad
    db_actividad = ActividadTipo(
        codigo=actividad.codigo,
        nombre=actividad.nombre,
        descripcion=actividad.descripcion,
        categoria=actividad.categoria,
        unidad_trabajo=actividad.unidad_trabajo,
        tiempo_estimado=Decimal(str(actividad.tiempo_estimado)) if actividad.tiempo_estimado else None
    )
    db.add(db_actividad)
    db.flush()  # Para obtener el ID

    # Agregar materiales
    for mat in actividad.materiales:
        db_material = MaterialActividadTipo(
            actividad_tipo_id=db_actividad.id,
            material_id=mat.material_id,
            cantidad_por_unidad=Decimal(str(mat.cantidad_por_unidad)),
            es_opcional=mat.es_opcional,
            notas=mat.notas
        )
        db.add(db_material)

    db.commit()
    db.refresh(db_actividad)
    return db_actividad


def update_actividad_tipo(
    db: Session,
    actividad_id: UUID,
    actividad: ActividadTipoUpdate
) -> Optional[ActividadTipo]:
    """Actualiza una actividad tipo."""
    db_actividad = get_actividad_tipo(db, actividad_id)
    if not db_actividad:
        return None

    update_data = actividad.model_dump(exclude_unset=True)

    # Verificar código único si se está cambiando
    if 'codigo' in update_data:
        existente = get_actividad_tipo_by_codigo(db, update_data['codigo'])
        if existente and existente.id != actividad_id:
            raise ValueError(f"Ya existe una actividad con el código {update_data['codigo']}")

    for field, value in update_data.items():
        if value is not None:
            if field == 'tiempo_estimado':
                value = Decimal(str(value))
            setattr(db_actividad, field, value)

    db.commit()
    db.refresh(db_actividad)
    return db_actividad


def delete_actividad_tipo(db: Session, actividad_id: UUID) -> bool:
    """Elimina una actividad tipo (soft delete)."""
    db_actividad = get_actividad_tipo(db, actividad_id)
    if not db_actividad:
        return False

    db_actividad.activo = False
    db.commit()
    return True


# ============== MATERIALES DE ACTIVIDAD ==============

def get_materiales_actividad(db: Session, actividad_id: UUID) -> List[MaterialActividadTipo]:
    """Obtiene los materiales de una actividad tipo."""
    return db.query(MaterialActividadTipo).filter(
        MaterialActividadTipo.actividad_tipo_id == actividad_id,
        MaterialActividadTipo.activo == True
    ).all()


def add_material_actividad(
    db: Session,
    actividad_id: UUID,
    material: MaterialActividadTipoCreate
) -> MaterialActividadTipo:
    """Agrega un material a una actividad tipo."""
    # Verificar que la actividad existe
    actividad = get_actividad_tipo(db, actividad_id)
    if not actividad:
        raise ValueError("Actividad tipo no encontrada")

    # Verificar que el material existe
    mat = db.query(Material).filter(Material.id == material.material_id).first()
    if not mat:
        raise ValueError("Material no encontrado")

    # Verificar que no esté duplicado
    existente = db.query(MaterialActividadTipo).filter(
        MaterialActividadTipo.actividad_tipo_id == actividad_id,
        MaterialActividadTipo.material_id == material.material_id,
        MaterialActividadTipo.activo == True
    ).first()
    if existente:
        raise ValueError("El material ya está asociado a esta actividad")

    db_material = MaterialActividadTipo(
        actividad_tipo_id=actividad_id,
        material_id=material.material_id,
        cantidad_por_unidad=Decimal(str(material.cantidad_por_unidad)),
        es_opcional=material.es_opcional,
        notas=material.notas
    )
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


def update_material_actividad(
    db: Session,
    material_actividad_id: UUID,
    material: MaterialActividadTipoUpdate
) -> Optional[MaterialActividadTipo]:
    """Actualiza un material de una actividad tipo."""
    db_material = db.query(MaterialActividadTipo).filter(
        MaterialActividadTipo.id == material_actividad_id,
        MaterialActividadTipo.activo == True
    ).first()

    if not db_material:
        return None

    update_data = material.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == 'cantidad_por_unidad':
                value = Decimal(str(value))
            setattr(db_material, field, value)

    db.commit()
    db.refresh(db_material)
    return db_material


def remove_material_actividad(db: Session, material_actividad_id: UUID) -> bool:
    """Elimina un material de una actividad tipo (soft delete)."""
    db_material = db.query(MaterialActividadTipo).filter(
        MaterialActividadTipo.id == material_actividad_id,
        MaterialActividadTipo.activo == True
    ).first()

    if not db_material:
        return False

    db_material.activo = False
    db.commit()
    return True


# ============== CÁLCULO DE MATERIALES ==============

def calcular_materiales_actividad(
    db: Session,
    actividad_id: UUID,
    cantidad_trabajo: float
) -> dict:
    """
    Calcula los materiales necesarios para una cantidad de trabajo dada.

    Args:
        actividad_id: ID de la actividad tipo
        cantidad_trabajo: Cantidad de unidades de trabajo (ej: 3 tableros)

    Returns:
        Diccionario con los materiales calculados y alertas de stock
    """
    actividad = get_actividad_tipo(db, actividad_id)
    if not actividad:
        raise ValueError("Actividad tipo no encontrada")

    materiales_calculados = []
    alertas_stock = []

    for mat_actividad in actividad.materiales:
        if not mat_actividad.activo:
            continue

        material = db.query(Material).filter(Material.id == mat_actividad.material_id).first()
        if not material:
            continue

        cantidad_calculada = float(mat_actividad.cantidad_por_unidad) * cantidad_trabajo
        stock_actual = float(material.stock_actual) if material.stock_actual else 0
        stock_suficiente = stock_actual >= cantidad_calculada

        if not stock_suficiente and not mat_actividad.es_opcional:
            alertas_stock.append(
                f"{material.nombre}: Se necesitan {cantidad_calculada} {material.unidad}, "
                f"stock disponible: {stock_actual}"
            )

        materiales_calculados.append({
            "material_id": material.id,
            "material_codigo": material.codigo,
            "material_nombre": material.nombre,
            "material_unidad": material.unidad,
            "cantidad_calculada": cantidad_calculada,
            "es_opcional": mat_actividad.es_opcional,
            "stock_actual": stock_actual,
            "stock_suficiente": stock_suficiente,
            "notas": mat_actividad.notas
        })

    tiempo_total = None
    if actividad.tiempo_estimado:
        tiempo_total = float(actividad.tiempo_estimado) * cantidad_trabajo

    return {
        "actividad_tipo_id": actividad.id,
        "actividad_nombre": actividad.nombre,
        "cantidad_trabajo": cantidad_trabajo,
        "unidad_trabajo": actividad.unidad_trabajo,
        "tiempo_estimado_total": tiempo_total,
        "materiales": materiales_calculados,
        "alertas_stock": alertas_stock
    }


# ============== HELPERS ==============

def enrich_actividad_response(db: Session, actividad: ActividadTipo) -> dict:
    """Enriquece una actividad con datos de materiales."""
    materiales_enriched = []

    for mat in actividad.materiales:
        if not mat.activo:
            continue
        material = db.query(Material).filter(Material.id == mat.material_id).first()
        materiales_enriched.append({
            "id": mat.id,
            "actividad_tipo_id": mat.actividad_tipo_id,
            "material_id": mat.material_id,
            "cantidad_por_unidad": float(mat.cantidad_por_unidad),
            "es_opcional": mat.es_opcional,
            "notas": mat.notas,
            "activo": mat.activo,
            "material_codigo": material.codigo if material else None,
            "material_nombre": material.nombre if material else None,
            "material_unidad": material.unidad if material else None,
            "material_stock_actual": float(material.stock_actual) if material else None
        })

    return {
        **actividad.__dict__,
        "cantidad_materiales": len(materiales_enriched),
        "materiales": materiales_enriched
    }

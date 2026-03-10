from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from app.models.gasto import Gasto
from app.models.categoria_gasto import CategoriaGasto
from app.models.proyecto import Proyecto
from app.schemas.gasto import GastoCreate, GastoUpdate, CategoriaGastoCreate


def obtener_gastos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    proyecto_id: Optional[UUID] = None,
    categoria: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Gasto]:
    """Obtiene lista de gastos con filtros."""
    query = db.query(Gasto).filter(Gasto.activo == True)

    if proyecto_id:
        query = query.filter(Gasto.proyecto_id == proyecto_id)
    if categoria:
        query = query.filter(Gasto.categoria == categoria)
    if fecha_desde:
        query = query.filter(Gasto.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Gasto.fecha <= fecha_hasta)

    return query.order_by(Gasto.fecha.desc()).offset(skip).limit(limit).all()


def obtener_gasto(db: Session, gasto_id: UUID) -> Optional[Gasto]:
    """Obtiene un gasto por ID."""
    return db.query(Gasto).filter(
        Gasto.id == gasto_id,
        Gasto.activo == True
    ).first()


def crear_gasto(db: Session, gasto: GastoCreate, usuario_id: UUID) -> Gasto:
    """Crea un nuevo gasto."""
    db_gasto = Gasto(
        fecha=gasto.fecha,
        categoria=gasto.categoria,
        descripcion=gasto.descripcion,
        monto=gasto.monto,
        proyecto_id=gasto.proyecto_id,
        responsable_id=gasto.responsable_id,
        comprobante_url=gasto.comprobante_url,
        created_by=usuario_id
    )
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto


def actualizar_gasto(
    db: Session,
    gasto_id: UUID,
    gasto: GastoUpdate
) -> Optional[Gasto]:
    """Actualiza un gasto existente."""
    db_gasto = obtener_gasto(db, gasto_id)
    if not db_gasto:
        return None

    update_data = gasto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_gasto, field, value)

    db.commit()
    db.refresh(db_gasto)
    return db_gasto


def eliminar_gasto(db: Session, gasto_id: UUID) -> bool:
    """Soft delete de gasto."""
    gasto = obtener_gasto(db, gasto_id)
    if not gasto:
        return False

    gasto.activo = False
    db.commit()
    return True


def obtener_resumen_gastos(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date,
    proyecto_id: Optional[UUID] = None
) -> dict:
    """Genera un resumen de gastos por período."""
    base_filter = [
        Gasto.activo == True,
        Gasto.fecha >= fecha_desde,
        Gasto.fecha <= fecha_hasta
    ]

    if proyecto_id:
        base_filter.append(Gasto.proyecto_id == proyecto_id)

    # Total
    total = db.query(func.coalesce(func.sum(Gasto.monto), 0)).filter(
        *base_filter
    ).scalar()

    # Por categoría
    por_categoria_query = db.query(
        Gasto.categoria,
        func.sum(Gasto.monto)
    ).filter(*base_filter).group_by(Gasto.categoria).all()

    por_categoria = {cat: float(monto or 0) for cat, monto in por_categoria_query}

    # Por proyecto
    por_proyecto_query = db.query(
        Proyecto.nombre,
        func.sum(Gasto.monto)
    ).join(Proyecto, Gasto.proyecto_id == Proyecto.id).filter(
        *base_filter,
        Gasto.proyecto_id.isnot(None)
    ).group_by(Proyecto.nombre).all()

    por_proyecto = {nombre: float(monto or 0) for nombre, monto in por_proyecto_query}

    # Gastos generales
    gastos_generales = db.query(func.sum(Gasto.monto)).filter(
        *base_filter,
        Gasto.proyecto_id.is_(None)
    ).scalar()

    if gastos_generales:
        por_proyecto["General (sin proyecto)"] = float(gastos_generales)

    return {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "total": float(total or 0),
        "por_categoria": por_categoria,
        "por_proyecto": por_proyecto
    }


# Categorías
def obtener_categorias(db: Session) -> List[CategoriaGasto]:
    """Obtiene las categorías de gasto."""
    return db.query(CategoriaGasto).filter(CategoriaGasto.activo == True).all()


def crear_categoria(db: Session, categoria: CategoriaGastoCreate) -> CategoriaGasto:
    """Crea una nueva categoría de gasto."""
    db_categoria = CategoriaGasto(
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        color=categoria.color
    )
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


def inicializar_categorias(db: Session) -> None:
    """Crea las categorías por defecto si no existen."""
    categorias_default = [
        ("Combustible", "Gastos de nafta, gasoil, etc.", "#F97316"),
        ("Viáticos", "Gastos de alimentación y transporte del personal", "#3B82F6"),
        ("Herramientas", "Compra y reparación de herramientas", "#8B5CF6"),
        ("Servicios", "Servicios contratados (fletes, etc.)", "#10B981"),
        ("Materiales menores", "Materiales de bajo costo no inventariados", "#EC4899"),
        ("Otros", "Gastos varios", "#6B7280"),
    ]

    for nombre, descripcion, color in categorias_default:
        existe = db.query(CategoriaGasto).filter(CategoriaGasto.nombre == nombre).first()
        if not existe:
            db.add(CategoriaGasto(nombre=nombre, descripcion=descripcion, color=color))

    db.commit()

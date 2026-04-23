"""Agregar material cemento y asociaciones para contrabases

Revision ID: 013
Revises: 012
Create Date: 2024-01-01 00:00:12.000000

CONTRABASES necesita por unidad:
- 7.14 kg de Cemento
- 27.5 kg de Arena
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ID fijo para el material cemento
CEMENTO_ID = str(uuid.uuid4())


def upgrade() -> None:
    # ==========================================
    # PARTE 1: INSERTAR MATERIAL CEMENTO
    # ==========================================
    materiales = table(
        'materiales',
        column('id', sa.dialects.postgresql.UUID),
        column('codigo', sa.String),
        column('nombre', sa.String),
        column('descripcion', sa.String),
        column('unidad', sa.String),
        column('stock_actual', sa.Numeric),
        column('stock_minimo', sa.Numeric),
        column('precio_unitario', sa.Numeric),
        column('ubicacion_almacen', sa.String),
        column('activo', sa.Boolean),
    )

    op.bulk_insert(materiales, [
        {
            'id': CEMENTO_ID,
            'codigo': 'CEMENTO',
            'nombre': 'Cemento',
            'descripcion': 'Cemento para contrabases y hormigón',
            'unidad': 'kg',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito materiales',
            'activo': True,
        },
    ])

    # ==========================================
    # PARTE 2: ASOCIAR MATERIALES A CONTRABASES
    # ==========================================
    conn = op.get_bind()

    # Obtener ID de la actividad BASE-CONTRA (Contrabases)
    result = conn.execute(
        sa.text("SELECT id FROM actividades_tipo WHERE codigo = 'BASE-CONTRA' AND activo = true")
    )
    row = result.fetchone()
    if not row:
        print("ADVERTENCIA: No se encontró la actividad BASE-CONTRA")
        return

    contrabases_id = str(row[0])

    # Obtener ID del material ARENA
    result = conn.execute(
        sa.text("SELECT id FROM materiales WHERE codigo = 'ARENA' AND activo = true")
    )
    row = result.fetchone()
    if not row:
        print("ADVERTENCIA: No se encontró el material ARENA")
        return

    arena_id = str(row[0])

    materiales_actividad_tipo = table(
        'materiales_actividad_tipo',
        column('id', sa.dialects.postgresql.UUID),
        column('actividad_tipo_id', sa.dialects.postgresql.UUID),
        column('material_id', sa.dialects.postgresql.UUID),
        column('cantidad_por_unidad', sa.Numeric),
        column('es_opcional', sa.Boolean),
        column('notas', sa.String),
        column('activo', sa.Boolean),
    )

    asociaciones = [
        # Cemento: 7.14 kg por contrabase
        {
            'id': str(uuid.uuid4()),
            'actividad_tipo_id': contrabases_id,
            'material_id': CEMENTO_ID,
            'cantidad_por_unidad': 7.14,
            'es_opcional': False,
            'notas': '7.14 kg de cemento por contrabase',
            'activo': True,
        },
        # Arena: 27.5 kg por contrabase
        {
            'id': str(uuid.uuid4()),
            'actividad_tipo_id': contrabases_id,
            'material_id': arena_id,
            'cantidad_por_unidad': 27.5,
            'es_opcional': False,
            'notas': '27.5 kg de arena por contrabase',
            'activo': True,
        },
    ]

    op.bulk_insert(materiales_actividad_tipo, asociaciones)


def downgrade() -> None:
    conn = op.get_bind()

    # Obtener ID de la actividad BASE-CONTRA
    result = conn.execute(
        sa.text("SELECT id FROM actividades_tipo WHERE codigo = 'BASE-CONTRA'")
    )
    row = result.fetchone()
    if row:
        contrabases_id = str(row[0])
        # Eliminar asociaciones de materiales con contrabases
        conn.execute(
            sa.text(f"DELETE FROM materiales_actividad_tipo WHERE actividad_tipo_id = '{contrabases_id}'")
        )

    # Eliminar material cemento
    conn.execute(
        sa.text("DELETE FROM materiales WHERE codigo = 'CEMENTO'")
    )

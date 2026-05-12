"""Normalize strings vacios en clientes a NULL

Revision ID: 020
Revises: 019
Create Date: 2026-05-12 14:00:00

Algunos clientes existentes quedaron con strings vacios en cuit y otros
campos opcionales. Para cuit es critico porque la columna es unique:
dos cadenas vacias violan el indice (NULL no). Normalizamos a NULL
todos los strings opcionales vacios.
"""
from alembic import op


revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


COLUMNAS = [
    'cuit', 'nombre_fantasia', 'email', 'telefono', 'celular',
    'contacto_nombre', 'contacto_cargo', 'direccion', 'ciudad',
    'codigo_postal', 'notas', 'notas_internas',
]


def upgrade():
    for col in COLUMNAS:
        op.execute(
            f"UPDATE clientes SET {col} = NULL "
            f"WHERE {col} IS NOT NULL AND TRIM({col}) = ''"
        )


def downgrade():
    # No tiene sentido revertir esta limpieza.
    pass

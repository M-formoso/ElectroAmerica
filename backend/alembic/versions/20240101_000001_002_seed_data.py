"""Seed initial data

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    # Definir tablas para insertar datos
    usuarios = table(
        'usuarios',
        column('id', sa.String),
        column('email', sa.String),
        column('hashed_password', sa.String),
        column('nombre', sa.String),
        column('apellido', sa.String),
        column('telefono', sa.String),
        column('rol', sa.String),
        column('activo', sa.Boolean),
    )

    categorias_gasto = table(
        'categorias_gasto',
        column('id', sa.String),
        column('nombre', sa.String),
        column('descripcion', sa.String),
        column('color', sa.String),
        column('activo', sa.Boolean),
    )

    # Crear usuario administrador por defecto
    # Contraseña: admin123 (cambiar en producción)
    admin_password = pwd_context.hash("admin123")

    op.bulk_insert(usuarios, [
        {
            'id': 'a0000000-0000-0000-0000-000000000001',
            'email': 'admin@electroamerica.com',
            'hashed_password': admin_password,
            'nombre': 'Administrador',
            'apellido': 'Sistema',
            'telefono': None,
            'rol': 'administrador',
            'activo': True,
        }
    ])

    # Crear categorías de gasto por defecto
    op.bulk_insert(categorias_gasto, [
        {
            'id': 'c0000000-0000-0000-0000-000000000001',
            'nombre': 'Materiales',
            'descripcion': 'Compra de materiales de construcción',
            'color': '#4CAF50',
            'activo': True,
        },
        {
            'id': 'c0000000-0000-0000-0000-000000000002',
            'nombre': 'Mano de Obra',
            'descripcion': 'Pagos de mano de obra y jornales',
            'color': '#2196F3',
            'activo': True,
        },
        {
            'id': 'c0000000-0000-0000-0000-000000000003',
            'nombre': 'Transporte',
            'descripcion': 'Fletes, combustible y transporte',
            'color': '#FF9800',
            'activo': True,
        },
        {
            'id': 'c0000000-0000-0000-0000-000000000004',
            'nombre': 'Equipos',
            'descripcion': 'Alquiler y compra de equipos',
            'color': '#9C27B0',
            'activo': True,
        },
        {
            'id': 'c0000000-0000-0000-0000-000000000005',
            'nombre': 'Servicios',
            'descripcion': 'Servicios profesionales y subcontratos',
            'color': '#00BCD4',
            'activo': True,
        },
        {
            'id': 'c0000000-0000-0000-0000-000000000006',
            'nombre': 'Administrativos',
            'descripcion': 'Gastos administrativos y oficina',
            'color': '#607D8B',
            'activo': True,
        },
        {
            'id': 'c0000000-0000-0000-0000-000000000007',
            'nombre': 'Otros',
            'descripcion': 'Otros gastos no categorizados',
            'color': '#795548',
            'activo': True,
        },
    ])


def downgrade() -> None:
    # Eliminar datos de seed
    op.execute("DELETE FROM categorias_gasto WHERE id LIKE 'c0000000-0000-0000-0000-00000000000%'")
    op.execute("DELETE FROM usuarios WHERE id = 'a0000000-0000-0000-0000-000000000001'")

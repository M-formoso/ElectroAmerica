"""Agregar tipo (egreso/ingreso) a los remitos

Revision ID: 024
Revises: 023
Create Date: 2026-05-21 10:00:00

Permite que un mismo remito sea de egreso (salida de stock, lo unico
que existia hasta ahora) o de ingreso (entrada de stock a un deposito).
La numeracion correlativa es compartida (REM-XXXX) y el tipo se
distingue en el listado y en el PDF.
"""
import sqlalchemy as sa
from alembic import op


revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade():
    # Crear el ENUM
    op.execute("CREATE TYPE tiporemito AS ENUM ('egreso', 'ingreso')")
    # Agregar la columna con default 'egreso' (todos los remitos existentes
    # son de egreso)
    op.add_column(
        'remitos',
        sa.Column(
            'tipo',
            sa.Enum('egreso', 'ingreso', name='tiporemito'),
            nullable=False,
            server_default='egreso',
        ),
    )
    op.create_index('ix_remitos_tipo', 'remitos', ['tipo'])


def downgrade():
    op.drop_index('ix_remitos_tipo', table_name='remitos')
    op.drop_column('remitos', 'tipo')
    op.execute("DROP TYPE IF EXISTS tiporemito")

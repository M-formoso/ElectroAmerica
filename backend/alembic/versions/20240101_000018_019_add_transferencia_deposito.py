"""Add transferencia_a_deposito a movimientos_stock

Revision ID: 019
Revises: 018
Create Date: 2026-05-12 12:00:00

- Agrega valor 'transferencia_a_deposito' al enum tipomovimiento.
- Agrega columna deposito_destino_id (nullable) a movimientos_stock,
  para registrar a que deposito/subdeposito se transfirio el stock.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar valor al enum tipomovimiento (idempotente)
    op.execute("ALTER TYPE tipomovimiento ADD VALUE IF NOT EXISTS 'transferencia_a_deposito'")

    # Agregar columna deposito_destino_id
    op.add_column(
        'movimientos_stock',
        sa.Column(
            'deposito_destino_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('depositos.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),
    )


def downgrade():
    op.drop_column('movimientos_stock', 'deposito_destino_id')
    # No se puede quitar un valor de un enum en PostgreSQL sin recrearlo.

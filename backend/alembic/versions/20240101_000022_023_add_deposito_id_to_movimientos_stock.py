"""Agregar deposito_id a movimientos_stock

Revision ID: 023
Revises: 022
Create Date: 2026-05-19 14:00:00

Permite que cada MovimientoStock indique el deposito donde ocurrio el
movimiento (origen para salidas, deposito afectado para entradas/ajustes).
Antes esa info solo estaba en el string `motivo`. NULL = movimiento
sobre stock global.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'movimientos_stock',
        sa.Column('deposito_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_movimientos_stock_deposito_id_depositos',
        'movimientos_stock', 'depositos', ['deposito_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('ix_movimientos_stock_deposito_id', 'movimientos_stock', ['deposito_id'])


def downgrade():
    op.drop_index('ix_movimientos_stock_deposito_id', table_name='movimientos_stock')
    op.drop_constraint('fk_movimientos_stock_deposito_id_depositos', 'movimientos_stock', type_='foreignkey')
    op.drop_column('movimientos_stock', 'deposito_id')

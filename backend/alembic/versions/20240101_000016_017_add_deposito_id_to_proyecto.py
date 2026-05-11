"""Add deposito_id to proyectos for material source routing

Revision ID: 017
Revises: 016
Create Date: 2026-05-11 17:00:00

Si proyectos.deposito_id es null, los materiales se leen y descuentan
del stock global (Material.stock_actual). Si esta seteado, se opera
sobre DepositoMaterial del deposito elegido.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'proyectos',
        sa.Column(
            'deposito_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('depositos.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column('proyectos', 'deposito_id')

"""Add parent_id to depositos for subdepositos

Revision ID: 018
Revises: 017
Create Date: 2026-05-11 18:00:00

Un deposito puede tener depositos hijos (subdepositos) referenciados
por parent_id. El stock se mantiene en cada (sub)deposito y se puede
agregar en el padre.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'depositos',
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('depositos.id', ondelete='CASCADE'),
            nullable=True,
            index=True,
        ),
    )


def downgrade():
    op.drop_column('depositos', 'parent_id')

"""Add depositos and deposito_materiales

Revision ID: 016
Revises: 015
Create Date: 2026-05-11 16:00:00

Cada cliente puede tener uno o varios depositos. Cada deposito tiene
su propio stock por material.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    # Los indices se crean automaticamente por index=True en cada columna.
    op.create_table(
        'depositos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('clientes.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('direccion', sa.String(255), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'deposito_materiales',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('deposito_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('depositos.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('material_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('materiales.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('stock_actual', sa.Numeric(12, 4), nullable=False, server_default='0'),
        sa.Column('stock_minimo', sa.Numeric(12, 4), nullable=False, server_default='0'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('deposito_id', 'material_id', name='uq_deposito_material'),
    )


def downgrade():
    # Los indices se eliminan con la tabla.
    op.drop_table('deposito_materiales')
    op.drop_table('depositos')

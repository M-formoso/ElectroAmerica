"""Agregar foto a herramienta

Revision ID: 028
Revises: 027
Create Date: 2026-06-23 12:00:00

Agrega al modelo Herramienta los campos para almacenar una foto subida a Cloudinary:
- foto_url
- foto_public_id (para poder eliminar la foto cuando se quita)
"""
from alembic import op
import sqlalchemy as sa


revision = '028'
down_revision = '027'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'herramientas',
        sa.Column('foto_url', sa.String(length=500), nullable=True),
    )
    op.add_column(
        'herramientas',
        sa.Column('foto_public_id', sa.String(length=300), nullable=True),
    )


def downgrade():
    op.drop_column('herramientas', 'foto_public_id')
    op.drop_column('herramientas', 'foto_url')

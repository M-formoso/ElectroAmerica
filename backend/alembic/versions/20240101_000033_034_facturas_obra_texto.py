"""034 facturas obra_texto

Revision ID: 034
Revises: 033
Create Date: 2026-08-18 12:00:00

Permite cargar facturas sin proyecto formal en el sistema. Se hace
`proyecto_id` nullable y se agrega `obra_texto` para escribir el nombre
de la obra a mano. La factura queda valida si tiene proyecto_id o si
tiene obra_texto.
"""
import sqlalchemy as sa
from alembic import op


revision = '034'
down_revision = '033'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'facturas',
        sa.Column('obra_texto', sa.String(length=200), nullable=True),
    )
    op.alter_column(
        'facturas', 'proyecto_id',
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade():
    # Antes de volver a NOT NULL hay que asegurarse de que no queden filas
    # con proyecto_id NULL. Si las hay, esta downgrade fallara (a proposito).
    op.alter_column(
        'facturas', 'proyecto_id',
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.drop_column('facturas', 'obra_texto')

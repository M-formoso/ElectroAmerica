"""Add permisos por modulos a usuarios

Revision ID: 010
Revises: 009
Create Date: 2024-01-01 00:00:10.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columna modulos_permitidos (JSONB para lista de strings)
    op.add_column(
        'usuarios',
        sa.Column('modulos_permitidos', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # Agregar columna es_superadmin
    op.add_column(
        'usuarios',
        sa.Column('es_superadmin', sa.Boolean(), nullable=False, server_default='false')
    )

    # Marcar al admin existente como superadmin
    op.execute("""
        UPDATE usuarios
        SET es_superadmin = true
        WHERE email = 'admin@electroamerica.com'
    """)


def downgrade() -> None:
    op.drop_column('usuarios', 'es_superadmin')
    op.drop_column('usuarios', 'modulos_permitidos')

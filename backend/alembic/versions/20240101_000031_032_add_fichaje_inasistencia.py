"""032 add inasistencia estado to fichajes

Revision ID: 032_add_fichaje_inasistencia
Revises: 031
Create Date: 2024-01-01 00:00:31

"""
from alembic import op


revision = '032'
down_revision = '031'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar el valor 'inasistencia' al enum estadofichaje si no existe
    op.execute("""
        DO $$ BEGIN
            ALTER TYPE estadofichaje ADD VALUE IF NOT EXISTS 'inasistencia';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade():
    # Postgres no soporta remover valores de un ENUM sin recrearlo.
    # Se deja como no-op para no arriesgar borrar datos.
    pass

"""031 add fichaje jornada

Revision ID: 031_add_fichaje_jornada
Revises: 030_tipos_ingreso_dinamicos
Create Date: 2024-01-01 00:00:30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '031'
down_revision = '030'
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM type
    op.execute("CREATE TYPE estadofichaje AS ENUM ('activo', 'completado', 'cancelado')")

    op.create_table(
        'fichajes_jornada',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, default=True),
        sa.Column('operario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('hora_inicio', sa.DateTime(timezone=True), nullable=False),
        sa.Column('hora_fin', sa.DateTime(timezone=True), nullable=True),
        sa.Column('horas_trabajadas', sa.Numeric(5, 2), nullable=True),
        sa.Column('estado', postgresql.ENUM('activo', 'completado', 'cancelado', name='estadofichaje', create_type=False), nullable=False),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notas_inicio', sa.Text(), nullable=True),
        sa.Column('notas_fin', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['operario_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fichajes_jornada_operario_id', 'fichajes_jornada', ['operario_id'])
    op.create_index('ix_fichajes_jornada_fecha', 'fichajes_jornada', ['fecha'])
    op.create_index('ix_fichajes_jornada_estado', 'fichajes_jornada', ['estado'])


def downgrade():
    op.drop_index('ix_fichajes_jornada_estado', 'fichajes_jornada')
    op.drop_index('ix_fichajes_jornada_fecha', 'fichajes_jornada')
    op.drop_index('ix_fichajes_jornada_operario_id', 'fichajes_jornada')
    op.drop_table('fichajes_jornada')
    op.execute("DROP TYPE estadofichaje")

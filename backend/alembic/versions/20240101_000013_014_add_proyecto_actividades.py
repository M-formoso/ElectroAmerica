"""Add proyecto_actividades, avances_actividad, proyecto_herramientas tables

Revision ID: 014_proyecto_actividades
Revises: 013_materiales_contrabases
Create Date: 2024-04-24 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic
revision = '014_proyecto_actividades'
down_revision = '013_materiales_contrabases'
branch_labels = None
depends_on = None


def upgrade():
    # Tabla proyecto_actividades
    op.create_table(
        'proyecto_actividades',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('proyecto_id', UUID(as_uuid=True), sa.ForeignKey('proyectos.id'), nullable=False),
        sa.Column('actividad_tipo_id', UUID(as_uuid=True), sa.ForeignKey('actividades_tipo.id'), nullable=False),
        sa.Column('cantidad_planificada', sa.Numeric(10, 2), nullable=False, server_default='1'),
        sa.Column('cantidad_ejecutada', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('materiales_calculados', JSONB, nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Índices para proyecto_actividades
    op.create_index('ix_proyecto_actividades_proyecto_id', 'proyecto_actividades', ['proyecto_id'])
    op.create_index('ix_proyecto_actividades_actividad_tipo_id', 'proyecto_actividades', ['actividad_tipo_id'])

    # Tabla avances_actividad
    op.create_table(
        'avances_actividad',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('proyecto_actividad_id', UUID(as_uuid=True), sa.ForeignKey('proyecto_actividades.id'), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('cantidad', sa.Numeric(10, 2), nullable=False),
        sa.Column('materiales_consumidos', JSONB, nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('registrado_por_id', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Índices para avances_actividad
    op.create_index('ix_avances_actividad_proyecto_actividad_id', 'avances_actividad', ['proyecto_actividad_id'])
    op.create_index('ix_avances_actividad_fecha', 'avances_actividad', ['fecha'])
    op.create_index('ix_avances_actividad_registrado_por_id', 'avances_actividad', ['registrado_por_id'])

    # Tabla proyecto_herramientas
    op.create_table(
        'proyecto_herramientas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('proyecto_id', UUID(as_uuid=True), sa.ForeignKey('proyectos.id'), nullable=False),
        sa.Column('herramienta_id', UUID(as_uuid=True), sa.ForeignKey('herramientas.id'), nullable=False),
        sa.Column('fecha_asignacion', sa.Date(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Índices para proyecto_herramientas
    op.create_index('ix_proyecto_herramientas_proyecto_id', 'proyecto_herramientas', ['proyecto_id'])
    op.create_index('ix_proyecto_herramientas_herramienta_id', 'proyecto_herramientas', ['herramienta_id'])


def downgrade():
    # Eliminar índices y tablas en orden inverso
    op.drop_index('ix_proyecto_herramientas_herramienta_id', table_name='proyecto_herramientas')
    op.drop_index('ix_proyecto_herramientas_proyecto_id', table_name='proyecto_herramientas')
    op.drop_table('proyecto_herramientas')

    op.drop_index('ix_avances_actividad_registrado_por_id', table_name='avances_actividad')
    op.drop_index('ix_avances_actividad_fecha', table_name='avances_actividad')
    op.drop_index('ix_avances_actividad_proyecto_actividad_id', table_name='avances_actividad')
    op.drop_table('avances_actividad')

    op.drop_index('ix_proyecto_actividades_actividad_tipo_id', table_name='proyecto_actividades')
    op.drop_index('ix_proyecto_actividades_proyecto_id', table_name='proyecto_actividades')
    op.drop_table('proyecto_actividades')

"""Add auditoría table

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:06.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear enum tipoaccion
    tipoaccion_enum = postgresql.ENUM(
        'crear', 'actualizar', 'eliminar', 'login', 'logout',
        'ver', 'exportar', 'asignar', 'desasignar', 'cambiar_estado', 'subir_archivo',
        name='tipoaccion'
    )
    tipoaccion_enum.create(op.get_bind())

    # Crear enum moduloauditado
    moduloauditado_enum = postgresql.ENUM(
        'auth', 'usuarios', 'proyectos', 'etapas', 'items_trabajo',
        'materiales', 'equipos', 'gastos', 'clientes', 'fotos',
        'reportes', 'finanzas', 'alertas', 'jornadas',
        name='moduloauditado'
    )
    moduloauditado_enum.create(op.get_bind())

    # Crear tabla auditorias
    op.create_table(
        'auditorias',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accion', sa.Enum(
            'crear', 'actualizar', 'eliminar', 'login', 'logout',
            'ver', 'exportar', 'asignar', 'desasignar', 'cambiar_estado', 'subir_archivo',
            name='tipoaccion', create_type=False
        ), nullable=False),
        sa.Column('modulo', sa.Enum(
            'auth', 'usuarios', 'proyectos', 'etapas', 'items_trabajo',
            'materiales', 'equipos', 'gastos', 'clientes', 'fotos',
            'reportes', 'finanzas', 'alertas', 'jornadas',
            name='moduloauditado', create_type=False
        ), nullable=False),
        sa.Column('descripcion', sa.String(500), nullable=False),
        sa.Column('recurso_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recurso_tipo', sa.String(50), nullable=True),
        sa.Column('datos_adicionales', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear índices para búsquedas comunes
    op.create_index('ix_auditorias_usuario_id', 'auditorias', ['usuario_id'])
    op.create_index('ix_auditorias_accion', 'auditorias', ['accion'])
    op.create_index('ix_auditorias_modulo', 'auditorias', ['modulo'])
    op.create_index('ix_auditorias_recurso_id', 'auditorias', ['recurso_id'])
    op.create_index('ix_auditorias_created_at', 'auditorias', ['created_at'])


def downgrade() -> None:
    # Eliminar índices
    op.drop_index('ix_auditorias_created_at', table_name='auditorias')
    op.drop_index('ix_auditorias_recurso_id', table_name='auditorias')
    op.drop_index('ix_auditorias_modulo', table_name='auditorias')
    op.drop_index('ix_auditorias_accion', table_name='auditorias')
    op.drop_index('ix_auditorias_usuario_id', table_name='auditorias')

    # Eliminar tabla
    op.drop_table('auditorias')

    # Eliminar enums
    op.execute('DROP TYPE IF EXISTS moduloauditado')
    op.execute('DROP TYPE IF EXISTS tipoaccion')

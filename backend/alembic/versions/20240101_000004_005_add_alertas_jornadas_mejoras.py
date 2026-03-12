"""Add alertas, jornadas y mejoras a modelos existentes

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:05.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============ CREAR ENUMS ============
    op.execute("""
        CREATE TYPE tipoalerta AS ENUM (
            'stock_minimo', 'demora_etapa', 'etapa_pendiente', 'limite_credito',
            'equipo_mantenimiento', 'proyecto_vencido', 'pago_pendiente'
        )
    """)
    op.execute("CREATE TYPE prioridadalerta AS ENUM ('baja', 'media', 'alta', 'critica')")
    op.execute("CREATE TYPE prioridaditem AS ENUM ('baja', 'media', 'alta', 'urgente')")

    # ============ TABLA ALERTAS ============
    op.create_table(
        'alertas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tipo', postgresql.ENUM('stock_minimo', 'demora_etapa', 'etapa_pendiente', 'limite_credito', 'equipo_mantenimiento', 'proyecto_vencido', 'pago_pendiente', name='tipoalerta', create_type=False), nullable=False),
        sa.Column('prioridad', postgresql.ENUM('baja', 'media', 'alta', 'critica', name='prioridadalerta', create_type=False), default='media', nullable=False),
        sa.Column('titulo', sa.String(200), nullable=False),
        sa.Column('mensaje', sa.Text(), nullable=False),
        sa.Column('referencia_tipo', sa.String(50), nullable=True),
        sa.Column('referencia_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('leida', sa.Boolean(), default=False, nullable=False),
        sa.Column('resuelta', sa.Boolean(), default=False, nullable=False),
        sa.Column('fecha_resolucion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
        sa.Column('resuelto_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_alertas_tipo', 'alertas', ['tipo'])
    op.create_index('ix_alertas_usuario_id', 'alertas', ['usuario_id'])
    op.create_index('ix_alertas_leida', 'alertas', ['leida'])

    # ============ TABLA JORNADAS ============
    op.create_table(
        'jornadas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id'), nullable=False),
        sa.Column('etapa_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('etapas.id'), nullable=True),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('horas_trabajadas', sa.Numeric(4, 2), nullable=False),
        sa.Column('horas_extra', sa.Numeric(4, 2), default=0, nullable=False),
        sa.Column('costo_hora', sa.Numeric(10, 2), nullable=False),
        sa.Column('costo_hora_extra', sa.Numeric(10, 2), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('registrado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_jornadas_usuario_id', 'jornadas', ['usuario_id'])
    op.create_index('ix_jornadas_proyecto_id', 'jornadas', ['proyecto_id'])
    op.create_index('ix_jornadas_fecha', 'jornadas', ['fecha'])

    # ============ MODIFICAR ETAPAS (sub-etapas) ============
    op.add_column('etapas', sa.Column('etapa_padre_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('etapas.id'), nullable=True))
    op.add_column('etapas', sa.Column('peso', sa.Numeric(5, 2), default=100, nullable=True))
    op.add_column('etapas', sa.Column('color', sa.String(7), nullable=True))

    # ============ MODIFICAR ITEMS_TRABAJO ============
    op.add_column('items_trabajo', sa.Column('notas', sa.Text(), nullable=True))
    op.add_column('items_trabajo', sa.Column('responsable_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True))
    op.add_column('items_trabajo', sa.Column('prioridad', postgresql.ENUM('baja', 'media', 'alta', 'urgente', name='prioridaditem', create_type=False), default='media', nullable=True))
    op.add_column('items_trabajo', sa.Column('orden', sa.Integer(), default=0, nullable=True))
    op.add_column('items_trabajo', sa.Column('fecha_inicio_est', sa.Date(), nullable=True))
    op.add_column('items_trabajo', sa.Column('fecha_fin_est', sa.Date(), nullable=True))
    op.add_column('items_trabajo', sa.Column('fecha_inicio_real', sa.Date(), nullable=True))
    op.add_column('items_trabajo', sa.Column('fecha_fin_real', sa.Date(), nullable=True))
    op.add_column('items_trabajo', sa.Column('porcentaje_avance', sa.Numeric(5, 2), default=0, nullable=True))

    # ============ MODIFICAR EQUIPOS ============
    op.add_column('equipos', sa.Column('costo_por_hora', sa.Numeric(10, 2), nullable=True))
    op.add_column('equipos', sa.Column('costo_por_dia', sa.Numeric(10, 2), nullable=True))
    op.add_column('equipos', sa.Column('costo_mantenimiento_mensual', sa.Numeric(10, 2), nullable=True))
    op.add_column('equipos', sa.Column('patente', sa.String(20), nullable=True))
    op.add_column('equipos', sa.Column('numero_serie', sa.String(100), nullable=True))
    op.add_column('equipos', sa.Column('año', sa.Integer(), nullable=True))
    op.add_column('equipos', sa.Column('fecha_ultimo_mantenimiento', sa.Date(), nullable=True))
    op.add_column('equipos', sa.Column('fecha_proximo_mantenimiento', sa.Date(), nullable=True))
    op.add_column('equipos', sa.Column('km_actual', sa.Integer(), nullable=True))
    op.add_column('equipos', sa.Column('km_proximo_service', sa.Integer(), nullable=True))
    op.add_column('equipos', sa.Column('notas_mantenimiento', sa.Text(), nullable=True))

    # ============ MODIFICAR ASIGNACIONES_EQUIPO ============
    op.add_column('asignaciones_equipo', sa.Column('etapa_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('etapas.id', ondelete='SET NULL'), nullable=True))
    op.add_column('asignaciones_equipo', sa.Column('costo_hora_asignado', sa.Numeric(10, 2), nullable=True))
    op.add_column('asignaciones_equipo', sa.Column('costo_dia_asignado', sa.Numeric(10, 2), nullable=True))
    op.add_column('asignaciones_equipo', sa.Column('horas_uso', sa.Numeric(6, 2), nullable=True))


def downgrade() -> None:
    # Quitar columnas de asignaciones_equipo
    op.drop_column('asignaciones_equipo', 'horas_uso')
    op.drop_column('asignaciones_equipo', 'costo_dia_asignado')
    op.drop_column('asignaciones_equipo', 'costo_hora_asignado')
    op.drop_column('asignaciones_equipo', 'etapa_id')

    # Quitar columnas de equipos
    op.drop_column('equipos', 'notas_mantenimiento')
    op.drop_column('equipos', 'km_proximo_service')
    op.drop_column('equipos', 'km_actual')
    op.drop_column('equipos', 'fecha_proximo_mantenimiento')
    op.drop_column('equipos', 'fecha_ultimo_mantenimiento')
    op.drop_column('equipos', 'año')
    op.drop_column('equipos', 'numero_serie')
    op.drop_column('equipos', 'patente')
    op.drop_column('equipos', 'costo_mantenimiento_mensual')
    op.drop_column('equipos', 'costo_por_dia')
    op.drop_column('equipos', 'costo_por_hora')

    # Quitar columnas de items_trabajo
    op.drop_column('items_trabajo', 'porcentaje_avance')
    op.drop_column('items_trabajo', 'fecha_fin_real')
    op.drop_column('items_trabajo', 'fecha_inicio_real')
    op.drop_column('items_trabajo', 'fecha_fin_est')
    op.drop_column('items_trabajo', 'fecha_inicio_est')
    op.drop_column('items_trabajo', 'orden')
    op.drop_column('items_trabajo', 'prioridad')
    op.drop_column('items_trabajo', 'responsable_id')
    op.drop_column('items_trabajo', 'notas')

    # Quitar columnas de etapas
    op.drop_column('etapas', 'color')
    op.drop_column('etapas', 'peso')
    op.drop_column('etapas', 'etapa_padre_id')

    # Eliminar tablas
    op.drop_table('jornadas')
    op.drop_table('alertas')

    # Eliminar enums
    op.execute('DROP TYPE prioridaditem')
    op.execute('DROP TYPE prioridadalerta')
    op.execute('DROP TYPE tipoalerta')

"""Initial migration - Create all tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear enum types
    op.execute("CREATE TYPE rolusuario AS ENUM ('administrador', 'supervisor', 'operario', 'cliente')")
    op.execute("CREATE TYPE estadoproyecto AS ENUM ('planificacion', 'en_ejecucion', 'pausado', 'finalizado')")
    op.execute("CREATE TYPE estadoetapa AS ENUM ('pendiente', 'en_progreso', 'completada', 'pausada')")
    op.execute("CREATE TYPE estadoequipo AS ENUM ('disponible', 'asignado', 'mantenimiento', 'fuera_servicio')")
    op.execute("CREATE TYPE tipoequipo AS ENUM ('herramienta', 'vehiculo', 'maquinaria', 'otro')")
    op.execute("CREATE TYPE tipomovimiento AS ENUM ('entrada', 'salida', 'ajuste', 'devolucion')")

    # Tabla usuarios
    op.create_table(
        'usuarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('apellido', sa.String(100), nullable=False),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('rol', postgresql.ENUM('administrador', 'supervisor', 'operario', 'cliente', name='rolusuario', create_type=False), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Tabla proyectos
    op.create_table(
        'proyectos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('ubicacion', sa.String(300), nullable=True),
        sa.Column('fecha_inicio', sa.Date(), nullable=True),
        sa.Column('fecha_fin_estimada', sa.Date(), nullable=True),
        sa.Column('fecha_fin_real', sa.Date(), nullable=True),
        sa.Column('estado', postgresql.ENUM('planificacion', 'en_ejecucion', 'pausado', 'finalizado', name='estadoproyecto', create_type=False), default='planificacion', nullable=False),
        sa.Column('porcentaje_avance', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('monto_contratado', sa.Numeric(15, 2), nullable=True),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
        sa.Column('supervisor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_proyectos_estado', 'proyectos', ['estado'])
    op.create_index('ix_proyectos_cliente_id', 'proyectos', ['cliente_id'])

    # Tabla etapas
    op.create_table(
        'etapas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('orden', sa.Integer(), default=0, nullable=False),
        sa.Column('fecha_inicio_est', sa.Date(), nullable=True),
        sa.Column('fecha_fin_est', sa.Date(), nullable=True),
        sa.Column('fecha_inicio_real', sa.Date(), nullable=True),
        sa.Column('fecha_fin_real', sa.Date(), nullable=True),
        sa.Column('estado', postgresql.ENUM('pendiente', 'en_progreso', 'completada', 'pausada', name='estadoetapa', create_type=False), default='pendiente', nullable=False),
        sa.Column('porcentaje_avance', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_etapas_proyecto_id', 'etapas', ['proyecto_id'])

    # Tabla items_trabajo
    op.create_table(
        'items_trabajo',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('unidad', sa.String(50), nullable=False),
        sa.Column('cantidad_estimada', sa.Numeric(12, 4), nullable=False),
        sa.Column('cantidad_ejecutada', sa.Numeric(12, 4), default=0, nullable=False),
        sa.Column('precio_unitario', sa.Numeric(12, 2), nullable=True),
        sa.Column('etapa_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('etapas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_items_trabajo_etapa_id', 'items_trabajo', ['etapa_id'])

    # Tabla materiales
    op.create_table(
        'materiales',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('codigo', sa.String(50), unique=True, nullable=False),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('unidad', sa.String(50), nullable=False),
        sa.Column('stock_actual', sa.Numeric(12, 4), default=0, nullable=False),
        sa.Column('stock_minimo', sa.Numeric(12, 4), default=0, nullable=False),
        sa.Column('precio_unitario', sa.Numeric(12, 2), nullable=True),
        sa.Column('ubicacion_almacen', sa.String(100), nullable=True),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_materiales_codigo', 'materiales', ['codigo'])

    # Tabla movimientos_stock
    op.create_table(
        'movimientos_stock',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materiales.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tipo', postgresql.ENUM('entrada', 'salida', 'ajuste', 'devolucion', name='tipomovimiento', create_type=False), nullable=False),
        sa.Column('cantidad', sa.Numeric(12, 4), nullable=False),
        sa.Column('stock_anterior', sa.Numeric(12, 4), nullable=False),
        sa.Column('stock_nuevo', sa.Numeric(12, 4), nullable=False),
        sa.Column('motivo', sa.String(300), nullable=True),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id'), nullable=True),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_movimientos_stock_material_id', 'movimientos_stock', ['material_id'])

    # Tabla asignaciones_material
    op.create_table(
        'asignaciones_material',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materiales.id', ondelete='CASCADE'), nullable=False),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('etapa_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('etapas.id'), nullable=True),
        sa.Column('cantidad', sa.Numeric(12, 4), nullable=False),
        sa.Column('fecha_asignacion', sa.Date(), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('asignado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_asignaciones_material_proyecto_id', 'asignaciones_material', ['proyecto_id'])

    # Tabla equipos
    op.create_table(
        'equipos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('codigo', sa.String(50), unique=True, nullable=False),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('tipo', postgresql.ENUM('herramienta', 'vehiculo', 'maquinaria', 'otro', name='tipoequipo', create_type=False), nullable=False),
        sa.Column('marca', sa.String(100), nullable=True),
        sa.Column('modelo', sa.String(100), nullable=True),
        sa.Column('estado', postgresql.ENUM('disponible', 'asignado', 'mantenimiento', 'fuera_servicio', name='estadoequipo', create_type=False), default='disponible', nullable=False),
        sa.Column('fecha_adquisicion', sa.Date(), nullable=True),
        sa.Column('costo_adquisicion', sa.Numeric(12, 2), nullable=True),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_equipos_codigo', 'equipos', ['codigo'])
    op.create_index('ix_equipos_estado', 'equipos', ['estado'])

    # Tabla asignaciones_equipo
    op.create_table(
        'asignaciones_equipo',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('equipo_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('equipos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fecha_asignacion', sa.Date(), nullable=False),
        sa.Column('fecha_devolucion_est', sa.Date(), nullable=True),
        sa.Column('fecha_devolucion_real', sa.Date(), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('asignado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_asignaciones_equipo_proyecto_id', 'asignaciones_equipo', ['proyecto_id'])
    op.create_index('ix_asignaciones_equipo_equipo_id', 'asignaciones_equipo', ['equipo_id'])

    # Tabla categorias_gasto
    op.create_table(
        'categorias_gasto',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nombre', sa.String(100), unique=True, nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Tabla gastos
    op.create_table(
        'gastos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('descripcion', sa.String(300), nullable=False),
        sa.Column('monto', sa.Numeric(12, 2), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('comprobante_url', sa.String(500), nullable=True),
        sa.Column('numero_comprobante', sa.String(100), nullable=True),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id'), nullable=True),
        sa.Column('categoria_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categorias_gasto.id'), nullable=True),
        sa.Column('creado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_gastos_proyecto_id', 'gastos', ['proyecto_id'])
    op.create_index('ix_gastos_fecha', 'gastos', ['fecha'])
    op.create_index('ix_gastos_categoria_id', 'gastos', ['categoria_id'])

    # Tabla fotos
    op.create_table(
        'fotos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('visible_cliente', sa.Boolean(), default=False, nullable=False),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('etapa_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('etapas.id'), nullable=True),
        sa.Column('subido_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_fotos_proyecto_id', 'fotos', ['proyecto_id'])
    op.create_index('ix_fotos_fecha', 'fotos', ['fecha'])

    # Tabla reportes
    op.create_table(
        'reportes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tipo', sa.String(50), nullable=False),
        sa.Column('fecha_desde', sa.Date(), nullable=False),
        sa.Column('fecha_hasta', sa.Date(), nullable=False),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('excel_url', sa.String(500), nullable=True),
        sa.Column('compartido_cliente', sa.Boolean(), default=False, nullable=False),
        sa.Column('generado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_reportes_proyecto_id', 'reportes', ['proyecto_id'])

    # Tabla precios_item
    op.create_table(
        'precios_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('item_trabajo_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('items_trabajo.id', ondelete='CASCADE'), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(12, 2), nullable=False),
        sa.Column('fecha_vigencia', sa.Date(), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('cargado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_precios_item_item_trabajo_id', 'precios_item', ['item_trabajo_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('precios_item')
    op.drop_table('reportes')
    op.drop_table('fotos')
    op.drop_table('gastos')
    op.drop_table('categorias_gasto')
    op.drop_table('asignaciones_equipo')
    op.drop_table('equipos')
    op.drop_table('asignaciones_material')
    op.drop_table('movimientos_stock')
    op.drop_table('materiales')
    op.drop_table('items_trabajo')
    op.drop_table('etapas')
    op.drop_table('proyectos')
    op.drop_table('usuarios')

    # Drop enum types
    op.execute('DROP TYPE tipomovimiento')
    op.execute('DROP TYPE tipoequipo')
    op.execute('DROP TYPE estadoequipo')
    op.execute('DROP TYPE estadoetapa')
    op.execute('DROP TYPE estadoproyecto')
    op.execute('DROP TYPE rolusuario')

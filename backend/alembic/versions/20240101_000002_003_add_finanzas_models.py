"""Add finance models - transacciones, cuentas, clientes_proveedores, presupuestos

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear enum types para finanzas
    op.execute("CREATE TYPE tipotransaccion AS ENUM ('ingreso', 'egreso')")
    op.execute("CREATE TYPE metodopago AS ENUM ('efectivo', 'transferencia', 'tarjeta_debito', 'tarjeta_credito', 'cheque', 'mercado_pago', 'otro')")
    op.execute("CREATE TYPE estadotransaccion AS ENUM ('pendiente', 'confirmada', 'anulada')")
    op.execute("CREATE TYPE tipocuenta AS ENUM ('caja', 'banco', 'mercado_pago', 'otro')")
    op.execute("CREATE TYPE tipoclienteproveedor AS ENUM ('cliente', 'proveedor', 'ambos')")

    # Tabla cuentas (debe crearse antes de transacciones por FK)
    op.create_table(
        'cuentas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('tipo', postgresql.ENUM('caja', 'banco', 'mercado_pago', 'otro', name='tipocuenta', create_type=False), default='caja', nullable=False),
        sa.Column('descripcion', sa.String(300), nullable=True),
        sa.Column('numero_cuenta', sa.String(50), nullable=True),
        sa.Column('banco', sa.String(100), nullable=True),
        sa.Column('cbu', sa.String(30), nullable=True),
        sa.Column('alias', sa.String(50), nullable=True),
        sa.Column('saldo_inicial', sa.Numeric(12, 2), default=0, nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Tabla clientes_proveedores (debe crearse antes de transacciones por FK)
    op.create_table(
        'clientes_proveedores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tipo', postgresql.ENUM('cliente', 'proveedor', 'ambos', name='tipoclienteproveedor', create_type=False), default='cliente', nullable=False),
        sa.Column('razon_social', sa.String(200), nullable=False),
        sa.Column('nombre_fantasia', sa.String(200), nullable=True),
        sa.Column('cuit', sa.String(15), nullable=True),
        sa.Column('direccion', sa.String(300), nullable=True),
        sa.Column('telefono', sa.String(50), nullable=True),
        sa.Column('email', sa.String(150), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('condicion_iva', sa.String(50), nullable=True),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True, unique=True),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_clientes_proveedores_cuit', 'clientes_proveedores', ['cuit'])
    op.create_index('ix_clientes_proveedores_tipo', 'clientes_proveedores', ['tipo'])

    # Tabla transacciones
    op.create_table(
        'transacciones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tipo', postgresql.ENUM('ingreso', 'egreso', name='tipotransaccion', create_type=False), nullable=False),
        sa.Column('concepto', sa.String(300), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('monto', sa.Numeric(12, 2), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('metodo_pago', postgresql.ENUM('efectivo', 'transferencia', 'tarjeta_debito', 'tarjeta_credito', 'cheque', 'mercado_pago', 'otro', name='metodopago', create_type=False), default='efectivo', nullable=False),
        sa.Column('referencia_pago', sa.String(100), nullable=True),
        sa.Column('estado', postgresql.ENUM('pendiente', 'confirmada', 'anulada', name='estadotransaccion', create_type=False), default='confirmada', nullable=False),
        sa.Column('numero_comprobante', sa.String(100), nullable=True),
        sa.Column('tipo_comprobante', sa.String(50), nullable=True),
        sa.Column('comprobante_url', sa.String(500), nullable=True),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id'), nullable=True),
        sa.Column('categoria_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categorias_gasto.id'), nullable=True),
        sa.Column('cuenta_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cuentas.id'), nullable=True),
        sa.Column('cliente_proveedor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clientes_proveedores.id'), nullable=True),
        sa.Column('creado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_transacciones_tipo', 'transacciones', ['tipo'])
    op.create_index('ix_transacciones_fecha', 'transacciones', ['fecha'])
    op.create_index('ix_transacciones_estado', 'transacciones', ['estado'])
    op.create_index('ix_transacciones_proyecto_id', 'transacciones', ['proyecto_id'])
    op.create_index('ix_transacciones_cuenta_id', 'transacciones', ['cuenta_id'])
    op.create_index('ix_transacciones_cliente_proveedor_id', 'transacciones', ['cliente_proveedor_id'])

    # Tabla presupuestos
    op.create_table(
        'presupuestos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('monto_total', sa.Numeric(12, 2), nullable=False),
        sa.Column('fecha_inicio', sa.Date(), nullable=True),
        sa.Column('fecha_fin', sa.Date(), nullable=True),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('proyectos.id'), nullable=True),
        sa.Column('categoria_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categorias_gasto.id'), nullable=True),
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_presupuestos_proyecto_id', 'presupuestos', ['proyecto_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('presupuestos')
    op.drop_table('transacciones')
    op.drop_table('clientes_proveedores')
    op.drop_table('cuentas')

    # Drop enum types
    op.execute('DROP TYPE tipoclienteproveedor')
    op.execute('DROP TYPE tipocuenta')
    op.execute('DROP TYPE estadotransaccion')
    op.execute('DROP TYPE metodopago')
    op.execute('DROP TYPE tipotransaccion')

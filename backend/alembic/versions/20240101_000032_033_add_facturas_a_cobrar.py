"""033 add facturas a cobrar

Revision ID: 033
Revises: 032
Create Date: 2026-08-14 12:00:00

Agrega la tabla `facturas` para el modulo "Facturas a cobrar".
Cada factura pertenece a un cliente (empresa) y a un proyecto (obra).
Cuando se marca como pagada, se genera automaticamente una Transaccion
INGRESO con tipo_ingreso "Cobro factura obras".
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = '033'
down_revision = '032'
branch_labels = None
depends_on = None


ESTADO_FACTURA_VALUES = ('pendiente', 'pagada')


def upgrade():
    # 1) Enum estadofactura
    op.execute(
        "CREATE TYPE estadofactura AS ENUM ('pendiente', 'pagada')"
    )

    # 2) Tabla facturas
    op.create_table(
        'facturas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('fecha_inscripcion', sa.Date(), nullable=False),
        sa.Column('monto', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('fecha_pago', sa.Date(), nullable=True),
        sa.Column(
            'estado',
            postgresql.ENUM(*ESTADO_FACTURA_VALUES, name='estadofactura', create_type=False),
            nullable=False,
            server_default='pendiente',
        ),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('transaccion_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('creado_por_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['transaccion_id'], ['transacciones.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['creado_por_id'], ['usuarios.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_facturas_cliente_id', 'facturas', ['cliente_id'])
    op.create_index('ix_facturas_proyecto_id', 'facturas', ['proyecto_id'])
    op.create_index('ix_facturas_estado', 'facturas', ['estado'])
    op.create_index('ix_facturas_fecha_inscripcion', 'facturas', ['fecha_inscripcion'])
    op.create_index('ix_facturas_fecha_pago', 'facturas', ['fecha_pago'])


def downgrade():
    op.drop_index('ix_facturas_fecha_pago', table_name='facturas')
    op.drop_index('ix_facturas_fecha_inscripcion', table_name='facturas')
    op.drop_index('ix_facturas_estado', table_name='facturas')
    op.drop_index('ix_facturas_proyecto_id', table_name='facturas')
    op.drop_index('ix_facturas_cliente_id', table_name='facturas')
    op.drop_table('facturas')
    op.execute("DROP TYPE IF EXISTS estadofactura")

"""Facturación y cobro de proyectos finalizados

Revision ID: 027
Revises: 026
Create Date: 2026-06-18 16:45:00

Agrega al modelo Proyecto los campos de facturacion y cobro:
- estado_facturacion (pendiente | facturado | cobrado)
- numero_factura
- fecha_facturacion
- fecha_cobro
- monto_facturado
"""
from alembic import op
import sqlalchemy as sa


revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None


estado_facturacion_enum = sa.Enum(
    'pendiente', 'facturado', 'cobrado',
    name='estadofacturacion',
)


def upgrade():
    estado_facturacion_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'proyectos',
        sa.Column(
            'estado_facturacion',
            estado_facturacion_enum,
            nullable=False,
            server_default='pendiente',
        ),
    )
    op.add_column(
        'proyectos',
        sa.Column('numero_factura', sa.String(length=60), nullable=True),
    )
    op.add_column(
        'proyectos',
        sa.Column('fecha_facturacion', sa.Date(), nullable=True),
    )
    op.add_column(
        'proyectos',
        sa.Column('fecha_cobro', sa.Date(), nullable=True),
    )
    op.add_column(
        'proyectos',
        sa.Column('monto_facturado', sa.Numeric(15, 2), nullable=True),
    )


def downgrade():
    op.drop_column('proyectos', 'monto_facturado')
    op.drop_column('proyectos', 'fecha_cobro')
    op.drop_column('proyectos', 'fecha_facturacion')
    op.drop_column('proyectos', 'numero_factura')
    op.drop_column('proyectos', 'estado_facturacion')
    estado_facturacion_enum.drop(op.get_bind(), checkfirst=True)

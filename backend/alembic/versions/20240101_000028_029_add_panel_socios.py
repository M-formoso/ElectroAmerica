"""Panel de Socios: tablas de socios/aportes/retiros y tipo_ingreso en transacciones

Revision ID: 029
Revises: 028
Create Date: 2026-07-20 18:00:00

Agrega la infraestructura para el modulo "Panel de Socios":
- Enum `tipoingreso` para subtipar ingresos (cobro obra, cobro venta, aporte, otro)
- Columna `tipo_ingreso` en `transacciones`
- Tablas: `socios`, `aportes_socio`, `retiros_socio`
- Seed de categorias de gasto adicionales (Sueldos, Impuestos, IVA, Vehiculos)
- Seed de Socio A y Socio B con 50/50 cada uno si no existen socios
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
import uuid


revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


TIPO_INGRESO_VALUES = ('cobro_factura_obra', 'cobro_factura_venta', 'aporte_socio', 'otro')


def upgrade():
    # 1) Enum tipoingreso
    op.execute(
        "CREATE TYPE tipoingreso AS ENUM ("
        "'cobro_factura_obra', 'cobro_factura_venta', 'aporte_socio', 'otro'"
        ")"
    )

    # 2) Columna tipo_ingreso en transacciones (nullable, solo aplica a ingresos)
    op.add_column(
        'transacciones',
        sa.Column(
            'tipo_ingreso',
            postgresql.ENUM(*TIPO_INGRESO_VALUES, name='tipoingreso', create_type=False),
            nullable=True,
        ),
    )
    op.create_index('ix_transacciones_tipo_ingreso', 'transacciones', ['tipo_ingreso'])

    # 3) Tabla socios
    op.create_table(
        'socios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('apellido', sa.String(length=150), nullable=True),
        sa.Column('porcentaje_participacion', sa.Numeric(precision=5, scale=2), nullable=False, server_default='50'),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=True, unique=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_socios_nombre', 'socios', ['nombre'])

    # 4) Tabla aportes_socio
    op.create_table(
        'aportes_socio',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('socio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('monto', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('concepto', sa.String(length=300), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('cuenta_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('creado_por_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['socio_id'], ['socios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cuenta_id'], ['cuentas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['creado_por_id'], ['usuarios.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_aportes_socio_socio_id', 'aportes_socio', ['socio_id'])
    op.create_index('ix_aportes_socio_fecha', 'aportes_socio', ['fecha'])

    # 5) Tabla retiros_socio
    op.create_table(
        'retiros_socio',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('socio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('monto', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('concepto', sa.String(length=300), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('cuenta_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('creado_por_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['socio_id'], ['socios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cuenta_id'], ['cuentas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['creado_por_id'], ['usuarios.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_retiros_socio_socio_id', 'retiros_socio', ['socio_id'])
    op.create_index('ix_retiros_socio_fecha', 'retiros_socio', ['fecha'])

    # 6) Seed de categorias adicionales
    categorias_default = [
        ('Sueldos', 'Sueldos, jornales y cargas sociales', '#0EA5E9'),
        ('Impuestos', 'Impuestos municipales, provinciales y nacionales', '#DC2626'),
        ('IVA', 'IVA a pagar / retenciones', '#F59E0B'),
        ('Vehiculos', 'Mantenimiento, patente y seguro de vehiculos', '#7C3AED'),
    ]
    conn = op.get_bind()
    for nombre, descripcion, color in categorias_default:
        existe = conn.execute(
            sa.text("SELECT 1 FROM categorias_gasto WHERE nombre = :n"),
            {"n": nombre},
        ).scalar()
        if not existe:
            conn.execute(
                sa.text(
                    "INSERT INTO categorias_gasto (id, nombre, descripcion, color, activo) "
                    "VALUES (:id, :n, :d, :c, true)"
                ),
                {"id": str(uuid.uuid4()), "n": nombre, "d": descripcion, "c": color},
            )

    # 7) Seed de Socio A / Socio B si no hay socios
    cantidad_socios = conn.execute(sa.text("SELECT COUNT(*) FROM socios")).scalar() or 0
    if cantidad_socios == 0:
        for nombre in ("Socio A", "Socio B"):
            conn.execute(
                sa.text(
                    "INSERT INTO socios (id, nombre, porcentaje_participacion, activo) "
                    "VALUES (:id, :n, 50, true)"
                ),
                {"id": str(uuid.uuid4()), "n": nombre},
            )


def downgrade():
    op.drop_index('ix_retiros_socio_fecha', table_name='retiros_socio')
    op.drop_index('ix_retiros_socio_socio_id', table_name='retiros_socio')
    op.drop_table('retiros_socio')

    op.drop_index('ix_aportes_socio_fecha', table_name='aportes_socio')
    op.drop_index('ix_aportes_socio_socio_id', table_name='aportes_socio')
    op.drop_table('aportes_socio')

    op.drop_index('ix_socios_nombre', table_name='socios')
    op.drop_table('socios')

    op.drop_index('ix_transacciones_tipo_ingreso', table_name='transacciones')
    op.drop_column('transacciones', 'tipo_ingreso')

    op.execute("DROP TYPE IF EXISTS tipoingreso")

"""Planillas de ingreso dinamicas: tabla tipos_ingreso + FK en transacciones

Revision ID: 030
Revises: 029
Create Date: 2026-07-21 10:00:00

Reemplaza el enum tipoingreso (4 valores fijos) por una tabla configurable
que permite agregar, renombrar y eliminar planillas de ingreso desde la UI.

- Crea tabla tipos_ingreso
- Seed de las 4 planillas por defecto (equivalentes al enum viejo)
- Agrega columna tipo_ingreso_id (FK) a transacciones
- Migra datos: mapea el enum viejo a los IDs nuevos
- Dropea la columna vieja tipo_ingreso y el tipo enum tipoingreso
- Seed adicional: categoria de gasto "Gastos diarios"
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
import uuid


revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None


# Los 4 tipos originales del enum
TIPOS_DEFAULT = [
    ('cobro_factura_obra', 'Cobro factura obras', '#22C55E', 1, False),
    ('cobro_factura_venta', 'Cobro factura ventas', '#3B82F6', 2, False),
    ('aporte_socio', 'Aportes de socios', '#8B5CF6', 3, True),
    ('otro', 'Otros ingresos', '#94A3B8', 4, False),
]


def upgrade():
    # 1) Tabla tipos_ingreso
    op.create_table(
        'tipos_ingreso',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('nombre', sa.String(length=100), nullable=False, unique=True),
        sa.Column('color', sa.String(length=7), nullable=False, server_default='#10B981'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('es_aporte_socio', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index('ix_tipos_ingreso_orden', 'tipos_ingreso', ['orden'])

    # 2) Seed de los 4 tipos por defecto
    conn = op.get_bind()
    enum_a_id: dict[str, str] = {}
    for enum_valor, nombre, color, orden, es_aporte in TIPOS_DEFAULT:
        nuevo_id = str(uuid.uuid4())
        enum_a_id[enum_valor] = nuevo_id
        conn.execute(
            sa.text(
                "INSERT INTO tipos_ingreso "
                "(id, nombre, color, orden, es_aporte_socio, activo) "
                "VALUES (:id, :n, :c, :o, :ea, true)"
            ),
            {"id": nuevo_id, "n": nombre, "c": color, "o": orden, "ea": es_aporte},
        )

    # 3) Nueva columna FK en transacciones
    op.add_column(
        'transacciones',
        sa.Column('tipo_ingreso_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_transacciones_tipo_ingreso',
        'transacciones', 'tipos_ingreso',
        ['tipo_ingreso_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_transacciones_tipo_ingreso_id', 'transacciones', ['tipo_ingreso_id'])

    # 4) Migrar datos: convertir enum viejo a UUID nuevo
    for enum_valor, nuevo_id in enum_a_id.items():
        conn.execute(
            sa.text(
                "UPDATE transacciones SET tipo_ingreso_id = :id "
                "WHERE tipo_ingreso = :ev"
            ),
            {"id": nuevo_id, "ev": enum_valor},
        )

    # 5) Dropear columna y enum viejos
    op.drop_index('ix_transacciones_tipo_ingreso', table_name='transacciones')
    op.drop_column('transacciones', 'tipo_ingreso')
    op.execute("DROP TYPE IF EXISTS tipoingreso")

    # 6) Seed extra: categoria de gasto "Gastos diarios"
    existe = conn.execute(
        sa.text("SELECT 1 FROM categorias_gasto WHERE nombre = :n"),
        {"n": "Gastos diarios"},
    ).scalar()
    if not existe:
        conn.execute(
            sa.text(
                "INSERT INTO categorias_gasto (id, nombre, descripcion, color, activo) "
                "VALUES (:id, :n, :d, :c, true)"
            ),
            {
                "id": str(uuid.uuid4()),
                "n": "Gastos diarios",
                "d": "Gastos varios del dia a dia",
                "c": "#64748B",
            },
        )


def downgrade():
    # Recrear enum viejo
    op.execute(
        "CREATE TYPE tipoingreso AS ENUM ("
        "'cobro_factura_obra', 'cobro_factura_venta', 'aporte_socio', 'otro'"
        ")"
    )
    op.add_column(
        'transacciones',
        sa.Column(
            'tipo_ingreso',
            postgresql.ENUM(
                'cobro_factura_obra', 'cobro_factura_venta', 'aporte_socio', 'otro',
                name='tipoingreso',
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.create_index('ix_transacciones_tipo_ingreso', 'transacciones', ['tipo_ingreso'])

    # Reversion best-effort: mapear por nombre exacto de los tipos default
    conn = op.get_bind()
    for enum_valor, nombre, _color, _orden, _ea in TIPOS_DEFAULT:
        conn.execute(
            sa.text(
                "UPDATE transacciones SET tipo_ingreso = :ev "
                "WHERE tipo_ingreso_id IN (SELECT id FROM tipos_ingreso WHERE nombre = :n)"
            ),
            {"ev": enum_valor, "n": nombre},
        )

    op.drop_index('ix_transacciones_tipo_ingreso_id', table_name='transacciones')
    op.drop_constraint('fk_transacciones_tipo_ingreso', 'transacciones', type_='foreignkey')
    op.drop_column('transacciones', 'tipo_ingreso_id')

    op.drop_index('ix_tipos_ingreso_orden', table_name='tipos_ingreso')
    op.drop_table('tipos_ingreso')

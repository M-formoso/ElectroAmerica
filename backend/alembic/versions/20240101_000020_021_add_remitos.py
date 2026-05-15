"""Agregar tablas de remitos de salida

Revision ID: 021
Revises: 020
Create Date: 2026-05-14 14:00:00

Crea las tablas `remitos` y `remito_items` para registrar las salidas de
materiales con su correspondiente remito (descargable en PDF).

El numero correlativo de remito viene de una sequence dedicada
(`remito_numero_seq`) para garantizar unicidad bajo concurrencia.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade():
    # Sequence para el numero correlativo
    op.execute("CREATE SEQUENCE IF NOT EXISTS remito_numero_seq START 1 INCREMENT 1")

    op.create_table(
        'remitos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('numero', sa.Integer(),
                  server_default=sa.text("nextval('remito_numero_seq')"),
                  nullable=False, unique=True),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('deposito_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('destinatario_texto', sa.String(length=255), nullable=True),
        sa.Column('responsable_retira', sa.String(length=255), nullable=True),
        sa.Column('direccion_entrega', sa.String(length=255), nullable=True),
        sa.Column('transportista', sa.String(length=255), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['deposito_id'], ['depositos.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_remitos_numero', 'remitos', ['numero'])
    op.create_index('ix_remitos_fecha', 'remitos', ['fecha'])
    op.create_index('ix_remitos_deposito_id', 'remitos', ['deposito_id'])
    op.create_index('ix_remitos_proyecto_id', 'remitos', ['proyecto_id'])
    op.create_index('ix_remitos_usuario_id', 'remitos', ['usuario_id'])

    op.create_table(
        'remito_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('remito_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('material_codigo', sa.String(length=50), nullable=True),
        sa.Column('material_nombre', sa.String(length=200), nullable=False),
        sa.Column('material_unidad', sa.String(length=50), nullable=False),
        sa.Column('cantidad', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.ForeignKeyConstraint(['remito_id'], ['remitos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materiales.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_remito_items_remito_id', 'remito_items', ['remito_id'])
    op.create_index('ix_remito_items_material_id', 'remito_items', ['material_id'])


def downgrade():
    op.drop_index('ix_remito_items_material_id', table_name='remito_items')
    op.drop_index('ix_remito_items_remito_id', table_name='remito_items')
    op.drop_table('remito_items')

    op.drop_index('ix_remitos_usuario_id', table_name='remitos')
    op.drop_index('ix_remitos_proyecto_id', table_name='remitos')
    op.drop_index('ix_remitos_deposito_id', table_name='remitos')
    op.drop_index('ix_remitos_fecha', table_name='remitos')
    op.drop_index('ix_remitos_numero', table_name='remitos')
    op.drop_table('remitos')

    op.execute("DROP SEQUENCE IF EXISTS remito_numero_seq")

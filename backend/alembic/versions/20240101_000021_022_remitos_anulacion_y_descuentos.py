"""Agregar auditoria de anulacion/edicion y tabla de descuentos al remito

Revision ID: 022
Revises: 021
Create Date: 2026-05-19 10:00:00

Cambios:
- Columnas nuevas en `remitos`: editado_at, editado_por_id, anulado_at,
  anulado_por_id, motivo_anulacion.
- Tabla `remito_descuentos` con el detalle fino de cuanto se descontó de
  cada deposito para cada material del remito (necesario para revertir
  al anular o editar).
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    # Columnas de auditoria en remitos
    op.add_column('remitos', sa.Column('editado_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('remitos', sa.Column('editado_por_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('remitos', sa.Column('anulado_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('remitos', sa.Column('anulado_por_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('remitos', sa.Column('motivo_anulacion', sa.Text(), nullable=True))
    op.create_foreign_key(
        'fk_remitos_editado_por_id_usuarios',
        'remitos', 'usuarios', ['editado_por_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_remitos_anulado_por_id_usuarios',
        'remitos', 'usuarios', ['anulado_por_id'], ['id'], ondelete='SET NULL'
    )

    # Tabla de descuentos
    op.create_table(
        'remito_descuentos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('remito_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deposito_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cantidad', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.ForeignKeyConstraint(['remito_id'], ['remitos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deposito_id'], ['depositos.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['material_id'], ['materiales.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_remito_descuentos_remito_id', 'remito_descuentos', ['remito_id'])
    op.create_index('ix_remito_descuentos_deposito_id', 'remito_descuentos', ['deposito_id'])
    op.create_index('ix_remito_descuentos_material_id', 'remito_descuentos', ['material_id'])


def downgrade():
    op.drop_index('ix_remito_descuentos_material_id', table_name='remito_descuentos')
    op.drop_index('ix_remito_descuentos_deposito_id', table_name='remito_descuentos')
    op.drop_index('ix_remito_descuentos_remito_id', table_name='remito_descuentos')
    op.drop_table('remito_descuentos')

    op.drop_constraint('fk_remitos_anulado_por_id_usuarios', 'remitos', type_='foreignkey')
    op.drop_constraint('fk_remitos_editado_por_id_usuarios', 'remitos', type_='foreignkey')
    op.drop_column('remitos', 'motivo_anulacion')
    op.drop_column('remitos', 'anulado_por_id')
    op.drop_column('remitos', 'anulado_at')
    op.drop_column('remitos', 'editado_por_id')
    op.drop_column('remitos', 'editado_at')

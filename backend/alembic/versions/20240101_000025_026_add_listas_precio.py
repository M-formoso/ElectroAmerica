"""Listas de precios + snapshot en proyecto actividad

Revision ID: 026
Revises: 025
Create Date: 2026-06-02 18:40:00

Crea las tablas listas_precio y precios_lista_actividad. Agrega
lista_precio_id a proyectos y precio_unitario_snapshot a
proyecto_actividades. Inserta las tres listas iniciales: EMA,
MANTELECTRIC y ELECTROAMERICA.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'listas_precio',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )
    op.create_index('ix_listas_precio_nombre', 'listas_precio', ['nombre'])

    op.create_table(
        'precios_lista_actividad',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('lista_precio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actividad_tipo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(12, 2), server_default=sa.text('0'), nullable=False),
        sa.Column('activo', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lista_precio_id'], ['listas_precio.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actividad_tipo_id'], ['actividades_tipo.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lista_precio_id', 'actividad_tipo_id', name='uq_precio_lista_actividad'),
    )
    op.create_index('ix_precios_lista_actividad_lista', 'precios_lista_actividad', ['lista_precio_id'])
    op.create_index('ix_precios_lista_actividad_actividad', 'precios_lista_actividad', ['actividad_tipo_id'])

    op.add_column(
        'proyectos',
        sa.Column('lista_precio_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_proyectos_lista_precio',
        'proyectos',
        'listas_precio',
        ['lista_precio_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_proyectos_lista_precio_id', 'proyectos', ['lista_precio_id'])

    op.add_column(
        'proyecto_actividades',
        sa.Column('precio_unitario_snapshot', sa.Numeric(12, 2), nullable=True),
    )

    # Seed inicial de las tres listas
    op.execute(
        """
        INSERT INTO listas_precio (nombre, descripcion)
        VALUES
            ('EMA', 'Lista de precios EMA'),
            ('MANTELECTRIC', 'Lista de precios MANTELECTRIC'),
            ('ELECTROAMERICA', 'Lista de precios ELECTROAMERICA')
        ON CONFLICT (nombre) DO NOTHING;
        """
    )


def downgrade():
    op.drop_column('proyecto_actividades', 'precio_unitario_snapshot')
    op.drop_index('ix_proyectos_lista_precio_id', table_name='proyectos')
    op.drop_constraint('fk_proyectos_lista_precio', 'proyectos', type_='foreignkey')
    op.drop_column('proyectos', 'lista_precio_id')
    op.drop_index('ix_precios_lista_actividad_actividad', table_name='precios_lista_actividad')
    op.drop_index('ix_precios_lista_actividad_lista', table_name='precios_lista_actividad')
    op.drop_table('precios_lista_actividad')
    op.drop_index('ix_listas_precio_nombre', table_name='listas_precio')
    op.drop_table('listas_precio')

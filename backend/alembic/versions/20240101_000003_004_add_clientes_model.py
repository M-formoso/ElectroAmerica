"""Add clientes model

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear enum types
    op.execute("CREATE TYPE tipocliente AS ENUM ('particular', 'empresa', 'gobierno', 'constructora', 'consorcio', 'otro')")
    op.execute("CREATE TYPE condicioniva AS ENUM ('responsable_inscripto', 'monotributo', 'exento', 'consumidor_final', 'no_responsable')")

    # Tabla clientes
    op.create_table(
        'clientes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('codigo', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('tipo', postgresql.ENUM('particular', 'empresa', 'gobierno', 'constructora', 'consorcio', 'otro', name='tipocliente', create_type=False), default='particular', nullable=False),

        # Datos basicos
        sa.Column('razon_social', sa.String(200), nullable=False),
        sa.Column('nombre_fantasia', sa.String(200), nullable=True),

        # Datos fiscales
        sa.Column('cuit', sa.String(15), unique=True, nullable=True, index=True),
        sa.Column('condicion_iva', postgresql.ENUM('responsable_inscripto', 'monotributo', 'exento', 'consumidor_final', 'no_responsable', name='condicioniva', create_type=False), default='consumidor_final', nullable=False),

        # Contacto
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('telefono', sa.String(50), nullable=True),
        sa.Column('celular', sa.String(50), nullable=True),
        sa.Column('contacto_nombre', sa.String(100), nullable=True),
        sa.Column('contacto_cargo', sa.String(100), nullable=True),

        # Direccion
        sa.Column('direccion', sa.String(300), nullable=True),
        sa.Column('ciudad', sa.String(100), nullable=True),
        sa.Column('provincia', sa.String(100), default='Buenos Aires'),
        sa.Column('codigo_postal', sa.String(10), nullable=True),

        # Comercial
        sa.Column('descuento_general', sa.Numeric(5, 2), default=0),
        sa.Column('limite_credito', sa.Numeric(12, 2), nullable=True),
        sa.Column('dias_credito', sa.Numeric(3, 0), default=0),

        # Estado de cuenta
        sa.Column('saldo_cuenta_corriente', sa.Numeric(12, 2), default=0),

        # Preferencias
        sa.Column('enviar_notificaciones', sa.Boolean(), default=True),

        # Notas
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('notas_internas', sa.Text(), nullable=True),

        # Fechas
        sa.Column('fecha_alta', sa.Date(), nullable=True),
        sa.Column('fecha_ultimo_proyecto', sa.Date(), nullable=True),

        # Usuario vinculado
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True, unique=True),

        # Control
        sa.Column('activo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Indices
    op.create_index('ix_clientes_tipo', 'clientes', ['tipo'])
    op.create_index('ix_clientes_razon_social', 'clientes', ['razon_social'])


def downgrade() -> None:
    op.drop_table('clientes')
    op.execute('DROP TYPE condicioniva')
    op.execute('DROP TYPE tipocliente')

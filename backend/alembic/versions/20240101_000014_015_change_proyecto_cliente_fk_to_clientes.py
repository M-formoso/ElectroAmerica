"""Change proyectos.cliente_id FK from usuarios to clientes

Revision ID: 015
Revises: 014
Create Date: 2026-05-06 14:50:00

El campo cliente_id en proyectos apuntaba a usuarios, pero conceptualmente
debe apuntar a la tabla clientes (entidad comercial). Esta migracion:
1. Limpia los cliente_id existentes que no correspondan a un cliente valido
   (porque originalmente apuntaban a usuarios)
2. Cambia el FK constraint para que apunte a clientes.id
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Setear a NULL los cliente_id que no correspondan a clientes existentes
    #    (eran usuarios.id de la version anterior).
    op.execute("""
        UPDATE proyectos
        SET cliente_id = NULL
        WHERE cliente_id IS NOT NULL
          AND cliente_id NOT IN (SELECT id FROM clientes)
    """)

    # 2. Drop el FK viejo a usuarios
    op.drop_constraint('proyectos_cliente_id_fkey', 'proyectos', type_='foreignkey')

    # 3. Crear FK nuevo a clientes
    op.create_foreign_key(
        'proyectos_cliente_id_fkey',
        'proyectos',
        'clientes',
        ['cliente_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Revertir el FK
    op.drop_constraint('proyectos_cliente_id_fkey', 'proyectos', type_='foreignkey')
    op.execute("UPDATE proyectos SET cliente_id = NULL")
    op.create_foreign_key(
        'proyectos_cliente_id_fkey',
        'proyectos',
        'usuarios',
        ['cliente_id'],
        ['id']
    )

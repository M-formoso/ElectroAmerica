"""Add auditoría table

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:06.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear enums usando DO block para evitar error si ya existen
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tipoaccion AS ENUM (
                'crear', 'actualizar', 'eliminar', 'login', 'logout',
                'ver', 'exportar', 'asignar', 'desasignar', 'cambiar_estado', 'subir_archivo'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE moduloauditado AS ENUM (
                'auth', 'usuarios', 'proyectos', 'etapas', 'items_trabajo',
                'materiales', 'equipos', 'gastos', 'clientes', 'fotos',
                'reportes', 'finanzas', 'alertas', 'jornadas'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Crear tabla auditorias usando SQL directo para IF NOT EXISTS
    op.execute("""
        CREATE TABLE IF NOT EXISTS auditorias (
            id UUID PRIMARY KEY,
            usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            accion tipoaccion NOT NULL,
            modulo moduloauditado NOT NULL,
            descripcion VARCHAR(500) NOT NULL,
            recurso_id UUID,
            recurso_tipo VARCHAR(50),
            datos_adicionales JSONB,
            ip_address VARCHAR(50),
            user_agent VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # Crear índices si no existen
    op.execute("CREATE INDEX IF NOT EXISTS ix_auditorias_usuario_id ON auditorias(usuario_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_auditorias_accion ON auditorias(accion);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_auditorias_modulo ON auditorias(modulo);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_auditorias_recurso_id ON auditorias(recurso_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_auditorias_created_at ON auditorias(created_at);")


def downgrade() -> None:
    # Eliminar índices
    op.execute('DROP INDEX IF EXISTS ix_auditorias_created_at')
    op.execute('DROP INDEX IF EXISTS ix_auditorias_recurso_id')
    op.execute('DROP INDEX IF EXISTS ix_auditorias_modulo')
    op.execute('DROP INDEX IF EXISTS ix_auditorias_accion')
    op.execute('DROP INDEX IF EXISTS ix_auditorias_usuario_id')

    # Eliminar tabla
    op.execute('DROP TABLE IF EXISTS auditorias')

    # Eliminar enums
    op.execute('DROP TYPE IF EXISTS moduloauditado')
    op.execute('DROP TYPE IF EXISTS tipoaccion')

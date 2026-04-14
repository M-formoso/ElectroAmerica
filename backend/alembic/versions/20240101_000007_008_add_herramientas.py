"""Add herramientas y prestamos

Revision ID: 008
Revises: 007
Create Date: 2024-01-01 00:00:08.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== CREAR ENUMS ==============

    # Estado de herramienta (condición física)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE estadoherramienta AS ENUM (
                'buen_estado', 'en_reparacion', 'rota'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Estado de préstamo (disponibilidad)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE estadoprestamo AS ENUM (
                'disponible', 'en_uso'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ============== CREAR TABLA HERRAMIENTAS ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS herramientas (
            id UUID PRIMARY KEY,
            nombre VARCHAR(200) NOT NULL,
            descripcion TEXT,
            estado estadoherramienta NOT NULL DEFAULT 'buen_estado',
            estado_prestamo estadoprestamo NOT NULL DEFAULT 'disponible',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR TABLA PRESTAMOS_HERRAMIENTA ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS prestamos_herramienta (
            id UUID PRIMARY KEY,
            herramienta_id UUID NOT NULL REFERENCES herramientas(id) ON DELETE CASCADE,
            retirado_por VARCHAR(200) NOT NULL,
            fecha_retiro DATE NOT NULL,
            fecha_devolucion DATE,
            notas_devolucion TEXT,
            registrado_por_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR ÍNDICES ==============

    op.execute("CREATE INDEX IF NOT EXISTS ix_herramientas_nombre ON herramientas(nombre);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_herramientas_estado ON herramientas(estado);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_herramientas_estado_prestamo ON herramientas(estado_prestamo);")

    op.execute("CREATE INDEX IF NOT EXISTS ix_prestamos_herr_herramienta_id ON prestamos_herramienta(herramienta_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prestamos_herr_fecha_retiro ON prestamos_herramienta(fecha_retiro);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prestamos_herr_retirado_por ON prestamos_herramienta(retirado_por);")

    # ============== AGREGAR MÓDULO A AUDITORÍA ==============

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE moduloauditado ADD VALUE IF NOT EXISTS 'herramientas';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    # Eliminar índices
    op.execute("DROP INDEX IF EXISTS ix_prestamos_herr_retirado_por;")
    op.execute("DROP INDEX IF EXISTS ix_prestamos_herr_fecha_retiro;")
    op.execute("DROP INDEX IF EXISTS ix_prestamos_herr_herramienta_id;")
    op.execute("DROP INDEX IF EXISTS ix_herramientas_estado_prestamo;")
    op.execute("DROP INDEX IF EXISTS ix_herramientas_estado;")
    op.execute("DROP INDEX IF EXISTS ix_herramientas_nombre;")

    # Eliminar tablas
    op.execute("DROP TABLE IF EXISTS prestamos_herramienta;")
    op.execute("DROP TABLE IF EXISTS herramientas;")

    # Eliminar enums
    op.execute("DROP TYPE IF EXISTS estadoprestamo;")
    op.execute("DROP TYPE IF EXISTS estadoherramienta;")

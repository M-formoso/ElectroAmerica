"""Add requerimientos material y empresas proveedoras

Revision ID: 009
Revises: 008
Create Date: 2024-01-01 00:00:09.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== CREAR ENUMS ==============

    # Estado del requerimiento
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE estadorequerimiento AS ENUM (
                'estimado', 'aprobado', 'pendiente_compra', 'en_proceso_compra',
                'pendiente_entrega', 'pendiente_retiro', 'entregado_obra', 'consumido', 'cancelado'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Origen del material
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE origenmaterial AS ENUM (
                'stock_propio', 'compra', 'entrega_cliente'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Prioridad del requerimiento
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE prioridadrequerimiento AS ENUM (
                'critica', 'alta', 'media', 'baja'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ============== CREAR TABLA EMPRESAS_PROVEEDORAS ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS empresas_proveedoras (
            id UUID PRIMARY KEY,
            nombre VARCHAR(200) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            cuit VARCHAR(20),
            telefono VARCHAR(50),
            email VARCHAR(200),
            direccion TEXT,
            contacto_nombre VARCHAR(200),
            notas TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR TABLA REQUERIMIENTOS_MATERIAL ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS requerimientos_material (
            id UUID PRIMARY KEY,
            proyecto_id UUID NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
            etapa_id UUID REFERENCES etapas(id) ON DELETE SET NULL,
            material_id UUID NOT NULL REFERENCES materiales(id) ON DELETE CASCADE,

            cantidad_estimada NUMERIC(12, 4) NOT NULL,
            cantidad_aprobada NUMERIC(12, 4),
            cantidad_entregada NUMERIC(12, 4) DEFAULT 0,
            cantidad_consumida NUMERIC(12, 4) DEFAULT 0,

            estado estadorequerimiento NOT NULL DEFAULT 'estimado',
            prioridad prioridadrequerimiento NOT NULL DEFAULT 'media',

            origen origenmaterial,
            empresa_origen_id UUID REFERENCES empresas_proveedoras(id) ON DELETE SET NULL,

            actividad_tipo_id UUID REFERENCES actividades_tipo(id) ON DELETE SET NULL,
            cantidad_trabajo NUMERIC(12, 4),

            fecha_necesidad DATE,
            fecha_solicitud TIMESTAMP WITH TIME ZONE,
            fecha_entrega TIMESTAMP WITH TIME ZONE,

            notas TEXT,
            notas_aprobacion TEXT,

            creado_por_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            aprobado_por_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            fecha_aprobacion TIMESTAMP WITH TIME ZONE,

            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR TABLA HISTORIAL_REQUERIMIENTO ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS historial_requerimiento (
            id UUID PRIMARY KEY,
            requerimiento_id UUID NOT NULL REFERENCES requerimientos_material(id) ON DELETE CASCADE,
            usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            campo_modificado VARCHAR(100) NOT NULL,
            valor_anterior TEXT,
            valor_nuevo TEXT,
            motivo TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR ÍNDICES ==============

    # Índices para empresas_proveedoras
    op.execute("CREATE INDEX IF NOT EXISTS ix_emp_prov_nombre ON empresas_proveedoras(nombre);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_emp_prov_tipo ON empresas_proveedoras(tipo);")

    # Índices para requerimientos_material
    op.execute("CREATE INDEX IF NOT EXISTS ix_req_mat_proyecto_id ON requerimientos_material(proyecto_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_req_mat_etapa_id ON requerimientos_material(etapa_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_req_mat_material_id ON requerimientos_material(material_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_req_mat_estado ON requerimientos_material(estado);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_req_mat_prioridad ON requerimientos_material(prioridad);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_req_mat_fecha_necesidad ON requerimientos_material(fecha_necesidad);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_req_mat_actividad_tipo_id ON requerimientos_material(actividad_tipo_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_req_mat_empresa_origen_id ON requerimientos_material(empresa_origen_id);")

    # Índices para historial_requerimiento
    op.execute("CREATE INDEX IF NOT EXISTS ix_hist_req_requerimiento_id ON historial_requerimiento(requerimiento_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_hist_req_usuario_id ON historial_requerimiento(usuario_id);")

    # ============== AGREGAR NUEVOS TIPOS DE ALERTA ==============

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE tipoalerta ADD VALUE IF NOT EXISTS 'material_pendiente_aprobar';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE tipoalerta ADD VALUE IF NOT EXISTS 'material_sin_stock';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE tipoalerta ADD VALUE IF NOT EXISTS 'material_pendiente_entrega';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ============== AGREGAR MÓDULO A AUDITORÍA ==============

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE moduloauditado ADD VALUE IF NOT EXISTS 'requerimientos_material';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE moduloauditado ADD VALUE IF NOT EXISTS 'empresas_proveedoras';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    # Eliminar índices
    op.execute("DROP INDEX IF EXISTS ix_hist_req_usuario_id;")
    op.execute("DROP INDEX IF EXISTS ix_hist_req_requerimiento_id;")
    op.execute("DROP INDEX IF EXISTS ix_req_mat_empresa_origen_id;")
    op.execute("DROP INDEX IF EXISTS ix_req_mat_actividad_tipo_id;")
    op.execute("DROP INDEX IF EXISTS ix_req_mat_fecha_necesidad;")
    op.execute("DROP INDEX IF EXISTS ix_req_mat_prioridad;")
    op.execute("DROP INDEX IF EXISTS ix_req_mat_estado;")
    op.execute("DROP INDEX IF EXISTS ix_req_mat_material_id;")
    op.execute("DROP INDEX IF EXISTS ix_req_mat_etapa_id;")
    op.execute("DROP INDEX IF EXISTS ix_req_mat_proyecto_id;")
    op.execute("DROP INDEX IF EXISTS ix_emp_prov_tipo;")
    op.execute("DROP INDEX IF EXISTS ix_emp_prov_nombre;")

    # Eliminar tablas
    op.execute("DROP TABLE IF EXISTS historial_requerimiento;")
    op.execute("DROP TABLE IF EXISTS requerimientos_material;")
    op.execute("DROP TABLE IF EXISTS empresas_proveedoras;")

    # Eliminar enums
    op.execute("DROP TYPE IF EXISTS prioridadrequerimiento;")
    op.execute("DROP TYPE IF EXISTS origenmaterial;")
    op.execute("DROP TYPE IF EXISTS estadorequerimiento;")

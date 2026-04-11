"""Add jornadas operario, asignaciones diarias y actividades tipo

Revision ID: 007
Revises: 006
Create Date: 2024-01-01 00:00:07.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== CREAR ENUMS ==============

    # Estado de jornada
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE estadojornada AS ENUM (
                'planificada', 'iniciada', 'en_camino', 'en_obra', 'finalizada', 'cancelada'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Estado de material en jornada
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE estadomaterialjornada AS ENUM (
                'asignado', 'pendiente_retiro', 'cargado', 'en_uso',
                'consumido', 'devuelto_deposito', 'devuelto_obra'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Destino de devolución
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE destinodevolucion AS ENUM (
                'deposito', 'obra', 'otro_operario'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Estado de asignación
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE estadoasignacion AS ENUM (
                'planificada', 'confirmada', 'en_curso', 'completada', 'cancelada'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ============== CREAR TABLA ACTIVIDADES_TIPO ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS actividades_tipo (
            id UUID PRIMARY KEY,
            codigo VARCHAR(50) UNIQUE NOT NULL,
            nombre VARCHAR(200) NOT NULL,
            descripcion TEXT,
            categoria VARCHAR(100),
            unidad_trabajo VARCHAR(50),
            tiempo_estimado NUMERIC(6, 2),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR TABLA MATERIALES_ACTIVIDAD_TIPO ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS materiales_actividad_tipo (
            id UUID PRIMARY KEY,
            actividad_tipo_id UUID NOT NULL REFERENCES actividades_tipo(id) ON DELETE CASCADE,
            material_id UUID NOT NULL REFERENCES materiales(id) ON DELETE CASCADE,
            cantidad_por_unidad NUMERIC(12, 4) NOT NULL,
            es_opcional BOOLEAN NOT NULL DEFAULT false,
            notas TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR TABLA ASIGNACIONES_DIARIAS ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones_diarias (
            id UUID PRIMARY KEY,
            fecha DATE NOT NULL,
            operario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            proyecto_id UUID NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
            etapa_id UUID REFERENCES etapas(id) ON DELETE SET NULL,
            vehiculo_id UUID REFERENCES equipos(id) ON DELETE SET NULL,
            estado estadoasignacion NOT NULL DEFAULT 'planificada',
            tareas_planificadas JSONB,
            materiales_planificados JSONB,
            notas TEXT,
            prioridad VARCHAR(20) NOT NULL DEFAULT 'media',
            creado_por_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR TABLA JORNADAS_OPERARIO ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS jornadas_operario (
            id UUID PRIMARY KEY,
            operario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            fecha DATE NOT NULL,
            vehiculo_id UUID REFERENCES equipos(id) ON DELETE SET NULL,
            proyecto_id UUID NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
            etapa_id UUID REFERENCES etapas(id) ON DELETE SET NULL,
            km_inicial INTEGER,
            km_final INTEGER,
            hora_inicio TIMESTAMP WITH TIME ZONE,
            hora_llegada_obra TIMESTAMP WITH TIME ZONE,
            hora_fin TIMESTAMP WITH TIME ZONE,
            horas_trabajadas NUMERIC(4, 2),
            horas_extra NUMERIC(4, 2) DEFAULT 0,
            estado estadojornada NOT NULL DEFAULT 'planificada',
            observaciones_inicio TEXT,
            observaciones_cierre TEXT,
            novedades TEXT,
            asignacion_diaria_id UUID REFERENCES asignaciones_diarias(id) ON DELETE SET NULL,
            registrado_por_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR TABLA MATERIALES_JORNADA ==============

    op.execute("""
        CREATE TABLE IF NOT EXISTS materiales_jornada (
            id UUID PRIMARY KEY,
            jornada_id UUID NOT NULL REFERENCES jornadas_operario(id) ON DELETE CASCADE,
            material_id UUID NOT NULL REFERENCES materiales(id) ON DELETE CASCADE,
            cantidad_asignada NUMERIC(12, 4) NOT NULL,
            cantidad_cargada NUMERIC(12, 4),
            cantidad_consumida NUMERIC(12, 4),
            cantidad_devuelta NUMERIC(12, 4),
            estado estadomaterialjornada NOT NULL DEFAULT 'asignado',
            destino_devolucion destinodevolucion,
            notas TEXT,
            actividad_tipo_id UUID REFERENCES actividades_tipo(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            activo BOOLEAN NOT NULL DEFAULT true
        );
    """)

    # ============== CREAR ÍNDICES ==============

    # Índices para actividades_tipo
    op.execute("CREATE INDEX IF NOT EXISTS ix_actividades_tipo_codigo ON actividades_tipo(codigo);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_actividades_tipo_categoria ON actividades_tipo(categoria);")

    # Índices para materiales_actividad_tipo
    op.execute("CREATE INDEX IF NOT EXISTS ix_mat_act_tipo_actividad_id ON materiales_actividad_tipo(actividad_tipo_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mat_act_tipo_material_id ON materiales_actividad_tipo(material_id);")

    # Índices para asignaciones_diarias
    op.execute("CREATE INDEX IF NOT EXISTS ix_asig_diarias_fecha ON asignaciones_diarias(fecha);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_asig_diarias_operario_id ON asignaciones_diarias(operario_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_asig_diarias_proyecto_id ON asignaciones_diarias(proyecto_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_asig_diarias_estado ON asignaciones_diarias(estado);")

    # Índices para jornadas_operario
    op.execute("CREATE INDEX IF NOT EXISTS ix_jorn_oper_operario_id ON jornadas_operario(operario_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jorn_oper_fecha ON jornadas_operario(fecha);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jorn_oper_proyecto_id ON jornadas_operario(proyecto_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jorn_oper_estado ON jornadas_operario(estado);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jorn_oper_vehiculo_id ON jornadas_operario(vehiculo_id);")

    # Índices para materiales_jornada
    op.execute("CREATE INDEX IF NOT EXISTS ix_mat_jorn_jornada_id ON materiales_jornada(jornada_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mat_jorn_material_id ON materiales_jornada(material_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mat_jorn_estado ON materiales_jornada(estado);")

    # ============== AGREGAR NUEVOS TIPOS DE ALERTA ==============

    # Agregar nuevos valores al enum tipoalerta si existe
    op.execute("""
        DO $$ BEGIN
            ALTER TYPE tipoalerta ADD VALUE IF NOT EXISTS 'material_pendiente_retiro';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE tipoalerta ADD VALUE IF NOT EXISTS 'material_faltante_jornada';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE tipoalerta ADD VALUE IF NOT EXISTS 'tarea_urgente';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE tipoalerta ADD VALUE IF NOT EXISTS 'jornada_sin_cerrar';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE tipoalerta ADD VALUE IF NOT EXISTS 'vehiculo_sin_devolver';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ============== AGREGAR NUEVO MÓDULO A AUDITORÍA ==============

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE moduloauditado ADD VALUE IF NOT EXISTS 'jornadas_operario';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE moduloauditado ADD VALUE IF NOT EXISTS 'asignaciones_diarias';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TYPE moduloauditado ADD VALUE IF NOT EXISTS 'actividades_tipo';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    # Eliminar índices
    op.execute("DROP INDEX IF EXISTS ix_mat_jorn_estado;")
    op.execute("DROP INDEX IF EXISTS ix_mat_jorn_material_id;")
    op.execute("DROP INDEX IF EXISTS ix_mat_jorn_jornada_id;")
    op.execute("DROP INDEX IF EXISTS ix_jorn_oper_vehiculo_id;")
    op.execute("DROP INDEX IF EXISTS ix_jorn_oper_estado;")
    op.execute("DROP INDEX IF EXISTS ix_jorn_oper_proyecto_id;")
    op.execute("DROP INDEX IF EXISTS ix_jorn_oper_fecha;")
    op.execute("DROP INDEX IF EXISTS ix_jorn_oper_operario_id;")
    op.execute("DROP INDEX IF EXISTS ix_asig_diarias_estado;")
    op.execute("DROP INDEX IF EXISTS ix_asig_diarias_proyecto_id;")
    op.execute("DROP INDEX IF EXISTS ix_asig_diarias_operario_id;")
    op.execute("DROP INDEX IF EXISTS ix_asig_diarias_fecha;")
    op.execute("DROP INDEX IF EXISTS ix_mat_act_tipo_material_id;")
    op.execute("DROP INDEX IF EXISTS ix_mat_act_tipo_actividad_id;")
    op.execute("DROP INDEX IF EXISTS ix_actividades_tipo_categoria;")
    op.execute("DROP INDEX IF EXISTS ix_actividades_tipo_codigo;")

    # Eliminar tablas (en orden inverso por las FK)
    op.execute("DROP TABLE IF EXISTS materiales_jornada;")
    op.execute("DROP TABLE IF EXISTS jornadas_operario;")
    op.execute("DROP TABLE IF EXISTS asignaciones_diarias;")
    op.execute("DROP TABLE IF EXISTS materiales_actividad_tipo;")
    op.execute("DROP TABLE IF EXISTS actividades_tipo;")

    # Eliminar enums
    op.execute("DROP TYPE IF EXISTS estadoasignacion;")
    op.execute("DROP TYPE IF EXISTS destinodevolucion;")
    op.execute("DROP TYPE IF EXISTS estadomaterialjornada;")
    op.execute("DROP TYPE IF EXISTS estadojornada;")

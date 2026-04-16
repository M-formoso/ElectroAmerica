"""Seed actividades tipo de obras

Revision ID: 011
Revises: 010
Create Date: 2024-01-01 00:00:10.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Definir tabla de actividades tipo
    actividades_tipo = table(
        'actividades_tipo',
        column('id', sa.String),
        column('codigo', sa.String),
        column('nombre', sa.String),
        column('descripcion', sa.String),
        column('categoria', sa.String),
        column('unidad_trabajo', sa.String),
        column('tiempo_estimado', sa.Numeric),
        column('activo', sa.Boolean),
    )

    # Insertar actividades tipo organizadas por categoría
    actividades = [
        # ============== BASES ==============
        {
            'id': 'act00000-0000-0000-0000-000000000001',
            'codigo': 'BASE-CAV-CH',
            'nombre': 'Cavado de base chica',
            'descripcion': 'Excavación manual o mecánica para base de columna chica',
            'categoria': 'bases',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 2.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000002',
            'codigo': 'BASE-CAV-GR',
            'nombre': 'Cavado de base grande',
            'descripcion': 'Excavación manual o mecánica para base de columna grande',
            'categoria': 'bases',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 3.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000003',
            'codigo': 'BASE-ROMP-VER',
            'nombre': 'Romper vereda',
            'descripcion': 'Rotura de vereda existente para instalación',
            'categoria': 'bases',
            'unidad_trabajo': 'm2',
            'tiempo_estimado': 1.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000004',
            'codigo': 'BASE-LLEN-CH',
            'nombre': 'Llenado de base chica',
            'descripcion': 'Hormigonado de base chica con mezcla',
            'categoria': 'bases',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 1.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000005',
            'codigo': 'BASE-LLEN-GR',
            'nombre': 'Llenado de base grande',
            'descripcion': 'Hormigonado de base grande con mezcla',
            'categoria': 'bases',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 2.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000006',
            'codigo': 'BASE-CONTRA',
            'nombre': 'Contrabases',
            'descripcion': 'Instalación de contrabases',
            'categoria': 'bases',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 1.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000007',
            'codigo': 'BASE-LIMP',
            'nombre': 'Limpieza x bases cavadas',
            'descripcion': 'Limpieza y retiro de escombros de bases excavadas',
            'categoria': 'bases',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 0.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000008',
            'codigo': 'BASE-REACON-PAT',
            'nombre': 'Reacondicionamiento PAT (romper+jab+contrabase)',
            'descripcion': 'Reacondicionamiento completo de puesta a tierra incluyendo rotura, jabalina y contrabase',
            'categoria': 'bases',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 3.0,
            'activo': True,
        },

        # ============== COLUMNAS ==============
        {
            'id': 'act00000-0000-0000-0000-000000000010',
            'codigo': 'COL-AEREA-770',
            'nombre': 'Colocación y aplomado de columna Aérea 7,70',
            'descripcion': 'Instalación y aplomado de columna aérea de 7,70 metros',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 3.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000011',
            'codigo': 'COL-AEREA-880',
            'nombre': 'Colocación y aplomado de columna Aérea 8,80',
            'descripcion': 'Instalación y aplomado de columna aérea de 8,80 metros',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 3.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000012',
            'codigo': 'COL-SUBT-770',
            'nombre': 'Colocación y aplomado de columna Subterra 7,70',
            'descripcion': 'Instalación y aplomado de columna subterránea de 7,70 metros',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 3.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000013',
            'codigo': 'COL-SUBT-880',
            'nombre': 'Colocación y aplomado de columna Subterra 8,80',
            'descripcion': 'Instalación y aplomado de columna subterránea de 8,80 metros',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 3.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000014',
            'codigo': 'COL-CURVA',
            'nombre': 'Colocación de columna curva',
            'descripcion': 'Instalación de columna con brazo curvo',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 2.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000015',
            'codigo': 'COL-POSTE-RET',
            'nombre': 'Colocación y aplomado de poste retención',
            'descripcion': 'Instalación de poste de retención para cables',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 3.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000016',
            'codigo': 'COL-PRFV',
            'nombre': 'Colocación de poste PRFV',
            'descripcion': 'Instalación de poste de plástico reforzado con fibra de vidrio',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 2.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000017',
            'codigo': 'COL-PERF',
            'nombre': 'Perforación de columna',
            'descripcion': 'Perforación de columna para instalaciones',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 0.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000018',
            'codigo': 'COL-RETIRO',
            'nombre': 'Retirar columna vieja',
            'descripcion': 'Retiro y disposición de columna existente',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 2.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000019',
            'codigo': 'COL-PINTAR-CURVA',
            'nombre': 'Pintar columnas curvas',
            'descripcion': 'Pintura de columnas con brazo curvo',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 1.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000020',
            'codigo': 'COL-NORM-CURVA',
            'nombre': 'Normalizado de columnas curvas',
            'descripcion': 'Trabajo de normalización en columnas curvas existentes',
            'categoria': 'columnas',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 1.5,
            'activo': True,
        },

        # ============== ACOPLES ==============
        {
            'id': 'act00000-0000-0000-0000-000000000025',
            'codigo': 'ACOP-SIMPLE',
            'nombre': 'Colocación de acople simple',
            'descripcion': 'Instalación de acople simple para luminaria',
            'categoria': 'acoples',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 0.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000026',
            'codigo': 'ACOP-DOBLE-180',
            'nombre': 'Colocación de acople doble 180°',
            'descripcion': 'Instalación de acople doble a 180 grados',
            'categoria': 'acoples',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 0.75,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000027',
            'codigo': 'ACOP-DOBLE-120',
            'nombre': 'Colocación de acople doble 120°',
            'descripcion': 'Instalación de acople doble a 120 grados',
            'categoria': 'acoples',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 0.75,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000028',
            'codigo': 'ACOP-TRIPLE',
            'nombre': 'Colocación de acople triple',
            'descripcion': 'Instalación de acople triple para luminarias',
            'categoria': 'acoples',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 1.0,
            'activo': True,
        },

        # ============== SISTEMA PAT ==============
        {
            'id': 'act00000-0000-0000-0000-000000000030',
            'codigo': 'PAT-SISTEMA',
            'nombre': 'Sistema PAT',
            'descripcion': 'Instalación completa de sistema de puesta a tierra',
            'categoria': 'sistema_pat',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 2.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000031',
            'codigo': 'PAT-MEDICION',
            'nombre': 'Medición PAT',
            'descripcion': 'Medición y verificación del sistema de puesta a tierra',
            'categoria': 'sistema_pat',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 0.5,
            'activo': True,
        },

        # ============== TENDIDO ==============
        {
            'id': 'act00000-0000-0000-0000-000000000035',
            'codigo': 'TEND-LINEA-DED',
            'nombre': 'Tendido de línea dedicada x metro',
            'descripcion': 'Tendido de línea eléctrica dedicada por metro lineal',
            'categoria': 'tendido',
            'unidad_trabajo': 'metro',
            'tiempo_estimado': 0.1,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000036',
            'codigo': 'TEND-CABLE-ZANJA',
            'nombre': 'Tendido de cable en zanja',
            'descripcion': 'Tendido de cable subterráneo en zanja preparada',
            'categoria': 'tendido',
            'unidad_trabajo': 'metro',
            'tiempo_estimado': 0.15,
            'activo': True,
        },

        # ============== LUMINARIAS ==============
        {
            'id': 'act00000-0000-0000-0000-000000000040',
            'codigo': 'LUMIN-CABLE',
            'nombre': 'Cableado de luminaria (lo hace EMA)',
            'descripcion': 'Cableado interno de luminaria - realizado por EMA',
            'categoria': 'luminarias',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 0.5,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000041',
            'codigo': 'LUMIN-CONEX-RED',
            'nombre': 'Conexión de luminaria a red (lo hace EMA)',
            'descripcion': 'Conexión de luminaria a la red eléctrica - realizado por EMA',
            'categoria': 'luminarias',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 0.5,
            'activo': True,
        },

        # ============== SUBTERRÁNEO ==============
        {
            'id': 'act00000-0000-0000-0000-000000000045',
            'codigo': 'SUBT-ZANJEO',
            'nombre': 'Zanjeo',
            'descripcion': 'Excavación de zanja para cableado subterráneo',
            'categoria': 'subterraneo',
            'unidad_trabajo': 'metro',
            'tiempo_estimado': 0.3,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000046',
            'codigo': 'SUBT-ARENA',
            'nombre': 'Arena',
            'descripcion': 'Colocación de cama de arena en zanja',
            'categoria': 'subterraneo',
            'unidad_trabajo': 'metro',
            'tiempo_estimado': 0.1,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000047',
            'codigo': 'SUBT-CEMENT',
            'nombre': 'Cementado en cable subterráneo - pegotes',
            'descripcion': 'Cementado de protección para cable subterráneo con pegotes',
            'categoria': 'subterraneo',
            'unidad_trabajo': 'metro',
            'tiempo_estimado': 0.2,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000048',
            'codigo': 'SUBT-LIMP-ZANJA',
            'nombre': 'Limpieza x metros de zanja',
            'descripcion': 'Limpieza y retiro de escombros de zanja',
            'categoria': 'subterraneo',
            'unidad_trabajo': 'metro',
            'tiempo_estimado': 0.1,
            'activo': True,
        },

        # ============== TABLEROS ==============
        {
            'id': 'act00000-0000-0000-0000-000000000050',
            'codigo': 'TAB-ARM-COL',
            'nombre': 'Armado, colocación y conexionado de tableros de columnas',
            'descripcion': 'Armado completo, instalación y conexionado de tableros en columnas',
            'categoria': 'tableros',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 2.0,
            'activo': True,
        },
        {
            'id': 'act00000-0000-0000-0000-000000000051',
            'codigo': 'TAB-GENERAL',
            'nombre': 'Colocación de tablero general',
            'descripcion': 'Instalación de tablero general de distribución',
            'categoria': 'tableros',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 4.0,
            'activo': True,
        },

        # ============== MANTENIMIENTO ==============
        {
            'id': 'act00000-0000-0000-0000-000000000055',
            'codigo': 'MANT-PODA',
            'nombre': 'Poda',
            'descripcion': 'Poda de árboles y vegetación cercana a líneas',
            'categoria': 'mantenimiento',
            'unidad_trabajo': 'unidad',
            'tiempo_estimado': 1.0,
            'activo': True,
        },

        # ============== LOGÍSTICA ==============
        {
            'id': 'act00000-0000-0000-0000-000000000060',
            'codigo': 'LOG-MATERIALES',
            'nombre': 'Logística de materiales a obra',
            'descripcion': 'Transporte y distribución de materiales en obra',
            'categoria': 'logistica',
            'unidad_trabajo': 'viaje',
            'tiempo_estimado': 2.0,
            'activo': True,
        },
    ]

    op.bulk_insert(actividades_tipo, actividades)


def downgrade() -> None:
    # Eliminar actividades tipo insertadas
    op.execute("DELETE FROM actividades_tipo WHERE id LIKE 'act00000-0000-0000-0000-00000000%'")

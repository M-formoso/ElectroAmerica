"""Seed materiales base y asociaciones con actividades tipo

Revision ID: 012
Revises: 011
Create Date: 2024-01-01 00:00:11.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# IDs fijos para poder referenciarlos en las asociaciones
MATERIAL_IDS = {
    # ========== COLUMNAS ==========
    'COL-AEREA-770': str(uuid.uuid4()),
    'COL-AEREA-880': str(uuid.uuid4()),
    'COL-SUBT-770': str(uuid.uuid4()),
    'COL-SUBT-880': str(uuid.uuid4()),
    'COL-CURVA': str(uuid.uuid4()),
    'POSTE-RET': str(uuid.uuid4()),
    'POSTE-PRFV': str(uuid.uuid4()),

    # ========== ACCESORIOS COLUMNAS ==========
    'CURVA-GALV': str(uuid.uuid4()),
    'PERNO-AISL-MN16': str(uuid.uuid4()),

    # ========== ACOPLES ==========
    'ACOPLE-SIMPLE': str(uuid.uuid4()),
    'ACOPLE-DOBLE-180': str(uuid.uuid4()),
    'ACOPLE-DOBLE-120': str(uuid.uuid4()),
    'ACOPLE-TRIPLE': str(uuid.uuid4()),
    'BRAZO-1M': str(uuid.uuid4()),
    'BRAZO-040': str(uuid.uuid4()),

    # ========== LUMINARIAS ==========
    'LUMINARIA-ARM': str(uuid.uuid4()),
    'PRISIONERO': str(uuid.uuid4()),

    # ========== SISTEMA PAT ==========
    'JABALINA-ARM': str(uuid.uuid4()),
    'CABLE-VA-1X10': str(uuid.uuid4()),
    'TERMINAL-CMC7': str(uuid.uuid4()),
    'TERMINAL-BAND': str(uuid.uuid4()),
    'BLOQUETE': str(uuid.uuid4()),

    # ========== ZANJEO ==========
    'LADRILLO': str(uuid.uuid4()),
    'ARENA': str(uuid.uuid4()),
    'FAJA-SEG': str(uuid.uuid4()),

    # ========== CABLES SUBTERRÁNEOS ==========
    'CABLE-SUBT-4X25': str(uuid.uuid4()),
    'CABLE-SUBT-4X4': str(uuid.uuid4()),

    # ========== TABLEROS ==========
    'FONDO-TABLERO': str(uuid.uuid4()),
    'PORTAFUSIBLE': str(uuid.uuid4()),
    'FUSIBLE-85X315': str(uuid.uuid4()),
    'BPN-6MM-GRIS': str(uuid.uuid4()),
    'BPN-6MM-AZUL': str(uuid.uuid4()),
    'BPN-6MM-VERDE': str(uuid.uuid4()),
    'PUENTE-FIJO-6MM': str(uuid.uuid4()),
    'TERMINAL-TIFF-2X25': str(uuid.uuid4()),
    'TERMINAL-TIFF-1X25': str(uuid.uuid4()),
    'TERMINAL-TIFF-1X15': str(uuid.uuid4()),
    'TERMINAL-C6': str(uuid.uuid4()),
    'TERMINAL-C1013': str(uuid.uuid4()),
    'TERMINAL-TIFF-6MM': str(uuid.uuid4()),
    'SEPARADOR-BPN': str(uuid.uuid4()),
    'CABLE-1X6': str(uuid.uuid4()),

    # ========== HORMIGÓN ==========
    'HORMIGON-M3': str(uuid.uuid4()),
}


def upgrade() -> None:
    # ==========================================
    # PARTE 1: INSERTAR MATERIALES
    # ==========================================
    materiales = table(
        'materiales',
        column('id', sa.dialects.postgresql.UUID),
        column('codigo', sa.String),
        column('nombre', sa.String),
        column('descripcion', sa.String),
        column('unidad', sa.String),
        column('stock_actual', sa.Numeric),
        column('stock_minimo', sa.Numeric),
        column('precio_unitario', sa.Numeric),
        column('ubicacion_almacen', sa.String),
        column('activo', sa.Boolean),
    )

    lista_materiales = [
        # ========== COLUMNAS ==========
        {
            'id': MATERIAL_IDS['COL-AEREA-770'],
            'codigo': 'COL-AEREA-770',
            'nombre': 'Columna aérea 7,70m',
            'descripcion': 'Columna de alumbrado público aérea de 7,70 metros',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 5,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito columnas',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['COL-AEREA-880'],
            'codigo': 'COL-AEREA-880',
            'nombre': 'Columna aérea 8,80m',
            'descripcion': 'Columna de alumbrado público aérea de 8,80 metros',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 5,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito columnas',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['COL-SUBT-770'],
            'codigo': 'COL-SUBT-770',
            'nombre': 'Columna subterránea 7,70m',
            'descripcion': 'Columna de alumbrado público subterránea de 7,70 metros',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 5,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito columnas',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['COL-SUBT-880'],
            'codigo': 'COL-SUBT-880',
            'nombre': 'Columna subterránea 8,80m',
            'descripcion': 'Columna de alumbrado público subterránea de 8,80 metros',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 5,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito columnas',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['COL-CURVA'],
            'codigo': 'COL-CURVA',
            'nombre': 'Columna curva',
            'descripcion': 'Columna con brazo curvo para luminaria',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 3,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito columnas',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['POSTE-RET'],
            'codigo': 'POSTE-RET',
            'nombre': 'Poste de retención',
            'descripcion': 'Poste de retención para cables',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 2,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito columnas',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['POSTE-PRFV'],
            'codigo': 'POSTE-PRFV',
            'nombre': 'Poste PRFV',
            'descripcion': 'Poste de plástico reforzado con fibra de vidrio',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 2,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito columnas',
            'activo': True,
        },

        # ========== ACCESORIOS COLUMNAS ==========
        {
            'id': MATERIAL_IDS['CURVA-GALV'],
            'codigo': 'CURVA-GALV',
            'nombre': 'Curva galvanizada',
            'descripcion': 'Curva galvanizada para columna aérea',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 10,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['PERNO-AISL-MN16'],
            'codigo': 'PERNO-AISL-MN16',
            'nombre': 'Perno p/ aislador MN16',
            'descripcion': 'Perno para aislador MN16',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 20,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },

        # ========== ACOPLES ==========
        {
            'id': MATERIAL_IDS['ACOPLE-SIMPLE'],
            'codigo': 'ACOPLE-SIMPLE',
            'nombre': 'Acople simple',
            'descripcion': 'Acople simple para una luminaria',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 10,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['ACOPLE-DOBLE-180'],
            'codigo': 'ACOPLE-DOBLE-180',
            'nombre': 'Acople doble 180°',
            'descripcion': 'Acople doble a 180 grados para dos luminarias',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 5,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['ACOPLE-DOBLE-120'],
            'codigo': 'ACOPLE-DOBLE-120',
            'nombre': 'Acople doble 120°',
            'descripcion': 'Acople doble a 120 grados para dos luminarias',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 5,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['ACOPLE-TRIPLE'],
            'codigo': 'ACOPLE-TRIPLE',
            'nombre': 'Acople triple',
            'descripcion': 'Acople triple para tres luminarias',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 3,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['BRAZO-1M'],
            'codigo': 'BRAZO-1M',
            'nombre': 'Brazo 1m',
            'descripcion': 'Brazo de 1 metro para luminaria',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 10,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['BRAZO-040'],
            'codigo': 'BRAZO-040',
            'nombre': 'Brazo 0,40m',
            'descripcion': 'Brazo de 0,40 metros para luminaria',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 10,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },

        # ========== LUMINARIAS ==========
        {
            'id': MATERIAL_IDS['LUMINARIA-ARM'],
            'codigo': 'LUMINARIA-ARM',
            'nombre': 'Luminaria armada',
            'descripcion': 'Luminaria de alumbrado público armada lista para instalar',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 10,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito luminarias',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['PRISIONERO'],
            'codigo': 'PRISIONERO',
            'nombre': 'Prisionero',
            'descripcion': 'Prisionero de fijación para luminaria',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 50,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },

        # ========== SISTEMA PAT ==========
        {
            'id': MATERIAL_IDS['JABALINA-ARM'],
            'codigo': 'JABALINA-ARM',
            'nombre': 'Jabalina armada',
            'descripcion': 'Jabalina de puesta a tierra armada',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 20,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito PAT',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['CABLE-VA-1X10'],
            'codigo': 'CABLE-VA-1X10',
            'nombre': 'Cable V/A 1x10mm',
            'descripcion': 'Cable verde/amarillo 1x10mm para puesta a tierra',
            'unidad': 'metro',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito cables',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['TERMINAL-CMC7'],
            'codigo': 'TERMINAL-CMC7',
            'nombre': 'Terminal CMC7',
            'descripcion': 'Terminal de compresión CMC7',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 50,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['TERMINAL-BAND'],
            'codigo': 'TERMINAL-BAND',
            'nombre': 'Terminal banderita',
            'descripcion': 'Terminal tipo banderita',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 50,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['BLOQUETE'],
            'codigo': 'BLOQUETE',
            'nombre': 'Bloquete',
            'descripcion': 'Bloquete para puesta a tierra',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 50,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito PAT',
            'activo': True,
        },

        # ========== ZANJEO ==========
        {
            'id': MATERIAL_IDS['LADRILLO'],
            'codigo': 'LADRILLO',
            'nombre': 'Ladrillo',
            'descripcion': 'Ladrillo común para protección de cables',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 500,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito materiales',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['ARENA'],
            'codigo': 'ARENA',
            'nombre': 'Arena',
            'descripcion': 'Arena para cama de cables y hormigón',
            'unidad': 'kg',
            'stock_actual': 0,
            'stock_minimo': 1000,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito materiales',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['FAJA-SEG'],
            'codigo': 'FAJA-SEG',
            'nombre': 'Faja de seguridad',
            'descripcion': 'Faja de señalización de seguridad para cables',
            'unidad': 'metro',
            'stock_actual': 0,
            'stock_minimo': 200,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito materiales',
            'activo': True,
        },

        # ========== CABLES SUBTERRÁNEOS ==========
        {
            'id': MATERIAL_IDS['CABLE-SUBT-4X25'],
            'codigo': 'CABLE-SUBT-4X25',
            'nombre': 'Cable subterráneo 4x2,5mm',
            'descripcion': 'Cable subterráneo 4 conductores de 2,5mm²',
            'unidad': 'metro',
            'stock_actual': 0,
            'stock_minimo': 500,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito cables',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['CABLE-SUBT-4X4'],
            'codigo': 'CABLE-SUBT-4X4',
            'nombre': 'Cable subterráneo 4x4mm',
            'descripcion': 'Cable subterráneo 4 conductores de 4mm²',
            'unidad': 'metro',
            'stock_actual': 0,
            'stock_minimo': 500,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito cables',
            'activo': True,
        },

        # ========== TABLEROS ==========
        {
            'id': MATERIAL_IDS['FONDO-TABLERO'],
            'codigo': 'FONDO-TABLERO',
            'nombre': 'Fondo de tablero',
            'descripcion': 'Fondo para tablero de columna subterránea',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 20,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito tableros',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['PORTAFUSIBLE'],
            'codigo': 'PORTAFUSIBLE',
            'nombre': 'Portafusible',
            'descripcion': 'Portafusible para tablero',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 50,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito tableros',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['FUSIBLE-85X315'],
            'codigo': 'FUSIBLE-85X315',
            'nombre': 'Fusible 8,5x31,5',
            'descripcion': 'Fusible cilíndrico 8,5x31,5mm',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito tableros',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['BPN-6MM-GRIS'],
            'codigo': 'BPN-6MM-GRIS',
            'nombre': 'BPN 6mm gris',
            'descripcion': 'Borne porta número 6mm gris (fase)',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito tableros',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['BPN-6MM-AZUL'],
            'codigo': 'BPN-6MM-AZUL',
            'nombre': 'BPN 6mm azul',
            'descripcion': 'Borne porta número 6mm azul (neutro)',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito tableros',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['BPN-6MM-VERDE'],
            'codigo': 'BPN-6MM-VERDE',
            'nombre': 'BPN 6mm verde',
            'descripcion': 'Borne porta número 6mm verde (tierra)',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito tableros',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['PUENTE-FIJO-6MM'],
            'codigo': 'PUENTE-FIJO-6MM',
            'nombre': 'Puente fijo 6mm',
            'descripcion': 'Puente fijo para bornes de 6mm',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito tableros',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['TERMINAL-TIFF-2X25'],
            'codigo': 'TERMINAL-TIFF-2X25',
            'nombre': 'Terminal Tiff 2x2,5mm',
            'descripcion': 'Terminal Tiff para cable 2x2,5mm',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['TERMINAL-TIFF-1X25'],
            'codigo': 'TERMINAL-TIFF-1X25',
            'nombre': 'Terminal Tiff 1x2,5mm',
            'descripcion': 'Terminal Tiff para cable 1x2,5mm',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['TERMINAL-TIFF-1X15'],
            'codigo': 'TERMINAL-TIFF-1X15',
            'nombre': 'Terminal Tiff 1x1,5mm',
            'descripcion': 'Terminal Tiff para cable 1x1,5mm',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['TERMINAL-C6'],
            'codigo': 'TERMINAL-C6',
            'nombre': 'Terminal C6',
            'descripcion': 'Terminal tipo C6',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 50,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['TERMINAL-C1013'],
            'codigo': 'TERMINAL-C1013',
            'nombre': 'Terminal C1013',
            'descripcion': 'Terminal tipo C1013',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 50,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['TERMINAL-TIFF-6MM'],
            'codigo': 'TERMINAL-TIFF-6MM',
            'nombre': 'Terminal Tiff 6mm',
            'descripcion': 'Terminal Tiff para cable 6mm',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 50,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito accesorios',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['SEPARADOR-BPN'],
            'codigo': 'SEPARADOR-BPN',
            'nombre': 'Separador BPN',
            'descripcion': 'Separador para bornes BPN',
            'unidad': 'unidad',
            'stock_actual': 0,
            'stock_minimo': 50,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito tableros',
            'activo': True,
        },
        {
            'id': MATERIAL_IDS['CABLE-1X6'],
            'codigo': 'CABLE-1X6',
            'nombre': 'Cable 1x6mm',
            'descripcion': 'Cable unipolar 1x6mm',
            'unidad': 'metro',
            'stock_actual': 0,
            'stock_minimo': 100,
            'precio_unitario': None,
            'ubicacion_almacen': 'Depósito cables',
            'activo': True,
        },

        # ========== HORMIGÓN ==========
        {
            'id': MATERIAL_IDS['HORMIGON-M3'],
            'codigo': 'HORMIGON-M3',
            'nombre': 'Hormigón',
            'descripcion': 'Hormigón elaborado',
            'unidad': 'm3',
            'stock_actual': 0,
            'stock_minimo': 0,
            'precio_unitario': None,
            'ubicacion_almacen': 'N/A',
            'activo': True,
        },
    ]

    op.bulk_insert(materiales, lista_materiales)

    # ==========================================
    # PARTE 2: ASOCIAR MATERIALES A ACTIVIDADES TIPO
    # ==========================================

    # Primero necesitamos obtener los IDs de las actividades tipo existentes
    # Usamos una conexión para consultar
    conn = op.get_bind()

    # Obtener IDs de actividades por código
    actividades_result = conn.execute(
        sa.text("SELECT id, codigo FROM actividades_tipo WHERE activo = true")
    )
    actividades_map = {row[1]: str(row[0]) for row in actividades_result}

    materiales_actividad_tipo = table(
        'materiales_actividad_tipo',
        column('id', sa.dialects.postgresql.UUID),
        column('actividad_tipo_id', sa.dialects.postgresql.UUID),
        column('material_id', sa.dialects.postgresql.UUID),
        column('cantidad_por_unidad', sa.Numeric),
        column('es_opcional', sa.Boolean),
        column('notas', sa.String),
        column('activo', sa.Boolean),
    )

    asociaciones = []

    # ========== BASE-LLEN-CH: Llenado de base chica (0,29 m3) ==========
    if 'BASE-LLEN-CH' in actividades_map:
        asociaciones.append({
            'id': str(uuid.uuid4()),
            'actividad_tipo_id': actividades_map['BASE-LLEN-CH'],
            'material_id': MATERIAL_IDS['HORMIGON-M3'],
            'cantidad_por_unidad': 0.29,
            'es_opcional': False,
            'notas': 'Hormigón para base chica',
            'activo': True,
        })

    # ========== BASE-LLEN-GR: Llenado de base grande (1,20 m3) ==========
    if 'BASE-LLEN-GR' in actividades_map:
        asociaciones.append({
            'id': str(uuid.uuid4()),
            'actividad_tipo_id': actividades_map['BASE-LLEN-GR'],
            'material_id': MATERIAL_IDS['HORMIGON-M3'],
            'cantidad_por_unidad': 1.20,
            'es_opcional': False,
            'notas': 'Hormigón para base grande',
            'activo': True,
        })

    # ========== COL-AEREA-770: Columna aérea 7,70m ==========
    if 'COL-AEREA-770' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['COL-AEREA-770'],
                'material_id': MATERIAL_IDS['COL-AEREA-770'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['COL-AEREA-770'],
                'material_id': MATERIAL_IDS['CURVA-GALV'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['COL-AEREA-770'],
                'material_id': MATERIAL_IDS['PERNO-AISL-MN16'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
        ])

    # ========== COL-AEREA-880: Columna aérea 8,80m ==========
    if 'COL-AEREA-880' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['COL-AEREA-880'],
                'material_id': MATERIAL_IDS['COL-AEREA-880'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': 'El Excel indica columna 7,70 pero debería ser 8,80',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['COL-AEREA-880'],
                'material_id': MATERIAL_IDS['CURVA-GALV'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['COL-AEREA-880'],
                'material_id': MATERIAL_IDS['PERNO-AISL-MN16'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
        ])

    # ========== COL-SUBT-770: Columna subterránea 7,70m ==========
    if 'COL-SUBT-770' in actividades_map:
        asociaciones.append({
            'id': str(uuid.uuid4()),
            'actividad_tipo_id': actividades_map['COL-SUBT-770'],
            'material_id': MATERIAL_IDS['COL-SUBT-770'],
            'cantidad_por_unidad': 1,
            'es_opcional': False,
            'notas': None,
            'activo': True,
        })

    # ========== COL-SUBT-880: Columna subterránea 8,80m ==========
    if 'COL-SUBT-880' in actividades_map:
        asociaciones.append({
            'id': str(uuid.uuid4()),
            'actividad_tipo_id': actividades_map['COL-SUBT-880'],
            'material_id': MATERIAL_IDS['COL-SUBT-880'],
            'cantidad_por_unidad': 1,
            'es_opcional': False,
            'notas': None,
            'activo': True,
        })

    # ========== COL-CURVA: Columna curva ==========
    if 'COL-CURVA' in actividades_map:
        asociaciones.append({
            'id': str(uuid.uuid4()),
            'actividad_tipo_id': actividades_map['COL-CURVA'],
            'material_id': MATERIAL_IDS['COL-CURVA'],
            'cantidad_por_unidad': 1,
            'es_opcional': False,
            'notas': None,
            'activo': True,
        })

    # ========== COL-POSTE-RET: Poste de retención ==========
    if 'COL-POSTE-RET' in actividades_map:
        asociaciones.append({
            'id': str(uuid.uuid4()),
            'actividad_tipo_id': actividades_map['COL-POSTE-RET'],
            'material_id': MATERIAL_IDS['POSTE-RET'],
            'cantidad_por_unidad': 1,
            'es_opcional': False,
            'notas': None,
            'activo': True,
        })

    # ========== COL-PRFV: Poste PRFV ==========
    if 'COL-PRFV' in actividades_map:
        asociaciones.append({
            'id': str(uuid.uuid4()),
            'actividad_tipo_id': actividades_map['COL-PRFV'],
            'material_id': MATERIAL_IDS['POSTE-PRFV'],
            'cantidad_por_unidad': 1,
            'es_opcional': False,
            'notas': None,
            'activo': True,
        })

    # ========== ACOP-SIMPLE: Acople simple ==========
    if 'ACOP-SIMPLE' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-SIMPLE'],
                'material_id': MATERIAL_IDS['ACOPLE-SIMPLE'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-SIMPLE'],
                'material_id': MATERIAL_IDS['LUMINARIA-ARM'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-SIMPLE'],
                'material_id': MATERIAL_IDS['PRISIONERO'],
                'cantidad_por_unidad': 3,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
        ])

    # ========== ACOP-DOBLE-180: Acople doble 180° ==========
    if 'ACOP-DOBLE-180' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-180'],
                'material_id': MATERIAL_IDS['ACOPLE-DOBLE-180'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-180'],
                'material_id': MATERIAL_IDS['LUMINARIA-ARM'],
                'cantidad_por_unidad': 2,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-180'],
                'material_id': MATERIAL_IDS['PRISIONERO'],
                'cantidad_por_unidad': 3,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-180'],
                'material_id': MATERIAL_IDS['BRAZO-1M'],
                'cantidad_por_unidad': 1,
                'es_opcional': True,
                'notas': 'Puede ser brazo de 1m o 0,40cm',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-180'],
                'material_id': MATERIAL_IDS['BRAZO-040'],
                'cantidad_por_unidad': 1,
                'es_opcional': True,
                'notas': 'Puede ser brazo de 1m o 0,40cm',
                'activo': True,
            },
        ])

    # ========== ACOP-DOBLE-120: Acople doble 120° ==========
    if 'ACOP-DOBLE-120' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-120'],
                'material_id': MATERIAL_IDS['ACOPLE-DOBLE-120'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-120'],
                'material_id': MATERIAL_IDS['LUMINARIA-ARM'],
                'cantidad_por_unidad': 2,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-120'],
                'material_id': MATERIAL_IDS['PRISIONERO'],
                'cantidad_por_unidad': 3,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-120'],
                'material_id': MATERIAL_IDS['BRAZO-1M'],
                'cantidad_por_unidad': 1,
                'es_opcional': True,
                'notas': 'Puede ser brazo de 1m o 0,40cm',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-DOBLE-120'],
                'material_id': MATERIAL_IDS['BRAZO-040'],
                'cantidad_por_unidad': 1,
                'es_opcional': True,
                'notas': 'Puede ser brazo de 1m o 0,40cm',
                'activo': True,
            },
        ])

    # ========== ACOP-TRIPLE: Acople triple ==========
    if 'ACOP-TRIPLE' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-TRIPLE'],
                'material_id': MATERIAL_IDS['ACOPLE-TRIPLE'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-TRIPLE'],
                'material_id': MATERIAL_IDS['LUMINARIA-ARM'],
                'cantidad_por_unidad': 3,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-TRIPLE'],
                'material_id': MATERIAL_IDS['BRAZO-1M'],
                'cantidad_por_unidad': 1,
                'es_opcional': True,
                'notas': 'Puede ser brazo de 1m o 0,40cm',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['ACOP-TRIPLE'],
                'material_id': MATERIAL_IDS['BRAZO-040'],
                'cantidad_por_unidad': 1,
                'es_opcional': True,
                'notas': 'Puede ser brazo de 1m o 0,40cm',
                'activo': True,
            },
        ])

    # ========== PAT-SISTEMA: Sistema de puesta a tierra ==========
    if 'PAT-SISTEMA' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['PAT-SISTEMA'],
                'material_id': MATERIAL_IDS['JABALINA-ARM'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['PAT-SISTEMA'],
                'material_id': MATERIAL_IDS['CABLE-VA-1X10'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': 'Puede ser 1mt o 4mt según la obra',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['PAT-SISTEMA'],
                'material_id': MATERIAL_IDS['TERMINAL-CMC7'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['PAT-SISTEMA'],
                'material_id': MATERIAL_IDS['TERMINAL-BAND'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['PAT-SISTEMA'],
                'material_id': MATERIAL_IDS['BLOQUETE'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
        ])

    # ========== BASE-REACON-PAT: Reacondicionamiento PAT ==========
    if 'BASE-REACON-PAT' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['BASE-REACON-PAT'],
                'material_id': MATERIAL_IDS['JABALINA-ARM'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['BASE-REACON-PAT'],
                'material_id': MATERIAL_IDS['CABLE-VA-1X10'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': 'Puede ser 1mt o 4mt según la obra',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['BASE-REACON-PAT'],
                'material_id': MATERIAL_IDS['TERMINAL-CMC7'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['BASE-REACON-PAT'],
                'material_id': MATERIAL_IDS['TERMINAL-BAND'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['BASE-REACON-PAT'],
                'material_id': MATERIAL_IDS['BLOQUETE'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': None,
                'activo': True,
            },
        ])

    # ========== SUBT-ZANJEO: Zanjeo (por metro) ==========
    if 'SUBT-ZANJEO' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['SUBT-ZANJEO'],
                'material_id': MATERIAL_IDS['LADRILLO'],
                'cantidad_por_unidad': 5,
                'es_opcional': False,
                'notas': '5 ladrillos por metro de zanja',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['SUBT-ZANJEO'],
                'material_id': MATERIAL_IDS['ARENA'],
                'cantidad_por_unidad': 25,
                'es_opcional': False,
                'notas': '25kg de arena por metro de zanja',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['SUBT-ZANJEO'],
                'material_id': MATERIAL_IDS['FAJA-SEG'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': '1 metro de faja de seguridad por metro de zanja',
                'activo': True,
            },
        ])

    # ========== TAB-ARM-COL: Armado tablero columna subterránea ==========
    if 'TAB-ARM-COL' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['FONDO-TABLERO'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': '1 fondo de tablero por columna subterránea',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['BPN-6MM-GRIS'],
                'cantidad_por_unidad': 3,
                'es_opcional': False,
                'notas': '3 BPN gris por tablero',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['BPN-6MM-AZUL'],
                'cantidad_por_unidad': 2,
                'es_opcional': False,
                'notas': '2 BPN azul por tablero',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['BPN-6MM-VERDE'],
                'cantidad_por_unidad': 2,
                'es_opcional': False,
                'notas': '2 BPN verde por tablero',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['PUENTE-FIJO-6MM'],
                'cantidad_por_unidad': 4,
                'es_opcional': False,
                'notas': '4 puentes fijos por tablero',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['TERMINAL-C6'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': '1 terminal C6 por tablero',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['TERMINAL-C1013'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': '1 terminal C1013 por tablero',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['TERMINAL-TIFF-6MM'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': '1 terminal Tiff 6mm por tablero',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['SEPARADOR-BPN'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': '1 separador BPN por tablero',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-ARM-COL'],
                'material_id': MATERIAL_IDS['CABLE-1X6'],
                'cantidad_por_unidad': 0.5,
                'es_opcional': False,
                'notas': '0,5 metros de cable 1x6mm por tablero',
                'activo': True,
            },
        ])

    # ========== TAB-GENERAL: Tablero general (materiales por luminaria) ==========
    # Nota: Estos materiales varían según cantidad de luminarias
    if 'TAB-GENERAL' in actividades_map:
        asociaciones.extend([
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-GENERAL'],
                'material_id': MATERIAL_IDS['PORTAFUSIBLE'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': '1 portafusible por luminaria conectada',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-GENERAL'],
                'material_id': MATERIAL_IDS['FUSIBLE-85X315'],
                'cantidad_por_unidad': 1,
                'es_opcional': False,
                'notas': '1 fusible por luminaria',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-GENERAL'],
                'material_id': MATERIAL_IDS['TERMINAL-TIFF-2X25'],
                'cantidad_por_unidad': 3,
                'es_opcional': False,
                'notas': '3 terminales Tiff 2x2,5 por luminaria',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-GENERAL'],
                'material_id': MATERIAL_IDS['TERMINAL-TIFF-1X25'],
                'cantidad_por_unidad': 3,
                'es_opcional': False,
                'notas': '3 terminales Tiff 1x2,5 por luminaria',
                'activo': True,
            },
            {
                'id': str(uuid.uuid4()),
                'actividad_tipo_id': actividades_map['TAB-GENERAL'],
                'material_id': MATERIAL_IDS['TERMINAL-TIFF-1X15'],
                'cantidad_por_unidad': 3,
                'es_opcional': False,
                'notas': '3 terminales Tiff 1x1,5 por luminaria',
                'activo': True,
            },
        ])

    # Insertar todas las asociaciones
    if asociaciones:
        op.bulk_insert(materiales_actividad_tipo, asociaciones)


def downgrade() -> None:
    # Eliminar asociaciones de materiales con actividades
    op.execute("DELETE FROM materiales_actividad_tipo WHERE activo = true")

    # Eliminar materiales insertados por código
    codigos = list(MATERIAL_IDS.keys())
    codigos_str = "', '".join(codigos)
    op.execute(f"DELETE FROM materiales WHERE codigo IN ('{codigos_str}')")

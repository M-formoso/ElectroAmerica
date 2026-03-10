# Importar todos los modelos para que Alembic los detecte
from app.models.usuario import Usuario, RolUsuario
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa, EstadoEtapa
from app.models.item_trabajo import ItemTrabajo, EstadoItem
from app.models.material import Material
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.models.asignacion_material import AsignacionMaterial
from app.models.equipo import Equipo, TipoEquipo, EstadoEquipo
from app.models.asignacion_equipo import AsignacionEquipo
from app.models.gasto import Gasto
from app.models.categoria_gasto import CategoriaGasto
from app.models.foto import Foto
from app.models.reporte import Reporte
from app.models.precio_item import PrecioItem

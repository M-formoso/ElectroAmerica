# Importar todos los modelos para que Alembic los detecte
from app.models.usuario import Usuario, RolUsuario
from app.models.cliente import Cliente, TipoCliente, CondicionIVA
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa, EstadoEtapa
from app.models.item_trabajo import ItemTrabajo, EstadoItem, PrioridadItem
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
from app.models.transaccion import (
    Transaccion, TipoTransaccion, MetodoPago, EstadoTransaccion,
    Cuenta, TipoCuenta,
    ClienteProveedor, TipoClienteProveedor,
    Presupuesto
)
from app.models.alerta import Alerta, TipoAlerta, PrioridadAlerta
from app.models.jornada import Jornada
from app.models.auditoria import Auditoria, TipoAccion, ModuloAuditado

# Nuevos modelos de Jornadas de Operarios
from app.models.actividad_tipo import ActividadTipo, MaterialActividadTipo
from app.models.asignacion_diaria import AsignacionDiaria, EstadoAsignacion
from app.models.jornada_operario import JornadaOperario, EstadoJornada
from app.models.material_jornada import MaterialJornada, EstadoMaterialJornada, DestinoDevolucion

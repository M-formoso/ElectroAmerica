# Importar todos los modelos para que Alembic los detecte
from app.models.usuario import Usuario, RolUsuario
from app.models.cliente import Cliente, TipoCliente, CondicionIVA
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa, EstadoEtapa
from app.models.item_trabajo import ItemTrabajo, EstadoItem, PrioridadItem
from app.models.material import Material
from app.models.deposito import Deposito, DepositoMaterial
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.models.asignacion_material import AsignacionMaterial
from app.models.equipo import Equipo, TipoEquipo, EstadoEquipo
from app.models.asignacion_equipo import AsignacionEquipo
from app.models.gasto import Gasto
from app.models.categoria_gasto import CategoriaGasto
from app.models.foto import Foto
from app.models.reporte import Reporte
from app.models.precio_item import PrecioItem
from app.models.lista_precio import ListaPrecio, PrecioListaActividad
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

# Herramientas y Préstamos
from app.models.herramienta import Herramienta, PrestamoHerramienta, EstadoHerramienta, EstadoPrestamo

# Requerimientos de Material
from app.models.requerimiento_material import (
    RequerimientoMaterial, HistorialRequerimiento, EmpresaProveedora,
    EstadoRequerimiento, OrigenMaterial, PrioridadRequerimiento
)

# Actividades de Proyecto y Avances
from app.models.proyecto_actividad import ProyectoActividad, AvanceActividad, ProyectoHerramienta

# Remitos de salida e ingreso
from app.models.remito import Remito, RemitoItem, RemitoDescuento, TipoRemito

# Socios y aportes/retiros
from app.models.socio import Socio, AporteSocio, RetiroSocio

# Planillas de ingreso dinamicas (reemplaza el enum tipoingreso)
from app.models.tipo_ingreso import TipoIngresoConfig

# Fichaje de jornadas (entrada/salida)
from app.models.fichaje import FichajeJornada, EstadoFichaje

# Facturas a cobrar
from app.models.factura import Factura, EstadoFactura

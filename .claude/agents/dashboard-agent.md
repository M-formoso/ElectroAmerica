# Agente: Dashboard Principal

## Rol
Implementar el dashboard con widgets, alertas y gráficos para la vista general operativa del sistema.

## Endpoints del Dashboard

### api/v1/endpoints/dashboard.py
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import date, timedelta
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario, RolUsuario
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa, EstadoEtapa
from app.models.material import Material
from app.models.equipo import Equipo, EstadoEquipo
from app.models.gasto import Gasto
from app.models.foto import Foto

router = APIRouter()

@router.get("/resumen")
def resumen_general(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Resumen general del día para el dashboard."""

    # Proyectos activos
    proyectos_activos = db.query(Proyecto).filter(
        Proyecto.activo == True,
        Proyecto.estado.in_([EstadoProyecto.en_ejecucion, EstadoProyecto.planificacion])
    ).count()

    # Proyectos por estado
    proyectos_por_estado = dict(
        db.query(Proyecto.estado, func.count(Proyecto.id)).filter(
            Proyecto.activo == True
        ).group_by(Proyecto.estado).all()
    )

    # Materiales con stock bajo
    materiales_stock_bajo = db.query(Material).filter(
        Material.activo == True,
        Material.stock_actual <= Material.stock_minimo
    ).count()

    # Equipos por estado
    equipos_disponibles = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado == EstadoEquipo.disponible
    ).count()

    equipos_asignados = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado == EstadoEquipo.asignado
    ).count()

    equipos_mantenimiento = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado == EstadoEquipo.mantenimiento
    ).count()

    # Gastos del mes actual
    primer_dia_mes = date.today().replace(day=1)
    gastos_mes = db.query(func.coalesce(func.sum(Gasto.monto), 0)).filter(
        Gasto.activo == True,
        Gasto.fecha >= primer_dia_mes
    ).scalar()

    # Gastos del mes anterior
    primer_dia_mes_anterior = (primer_dia_mes - timedelta(days=1)).replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes - timedelta(days=1)
    gastos_mes_anterior = db.query(func.coalesce(func.sum(Gasto.monto), 0)).filter(
        Gasto.activo == True,
        Gasto.fecha >= primer_dia_mes_anterior,
        Gasto.fecha <= ultimo_dia_mes_anterior
    ).scalar()

    return {
        "proyectos": {
            "activos": proyectos_activos,
            "por_estado": {k.value: v for k, v in proyectos_por_estado.items()}
        },
        "materiales": {
            "stock_bajo": materiales_stock_bajo
        },
        "equipos": {
            "disponibles": equipos_disponibles,
            "asignados": equipos_asignados,
            "mantenimiento": equipos_mantenimiento
        },
        "gastos": {
            "mes_actual": float(gastos_mes),
            "mes_anterior": float(gastos_mes_anterior),
            "variacion_porcentaje": round(
                ((float(gastos_mes) - float(gastos_mes_anterior)) / float(gastos_mes_anterior) * 100)
                if gastos_mes_anterior > 0 else 0, 2
            )
        }
    }

@router.get("/alertas")
def obtener_alertas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene las alertas activas del sistema."""
    alertas = []

    # Materiales con stock bajo
    materiales_bajo = db.query(Material).filter(
        Material.activo == True,
        Material.stock_actual <= Material.stock_minimo
    ).all()

    for material in materiales_bajo:
        alertas.append({
            "tipo": "stock_bajo",
            "severidad": "warning",
            "mensaje": f"Stock bajo: {material.nombre} ({material.stock_actual} {material.unidad})",
            "recurso_id": str(material.id),
            "recurso_tipo": "material"
        })

    # Etapas demoradas (fecha estimada vencida y no completada)
    hoy = date.today()
    etapas_demoradas = db.query(Etapa).filter(
        Etapa.activo == True,
        Etapa.fecha_fin_est < hoy,
        Etapa.estado.notin_([EstadoEtapa.completada])
    ).all()

    for etapa in etapas_demoradas:
        dias_demora = (hoy - etapa.fecha_fin_est).days
        alertas.append({
            "tipo": "etapa_demorada",
            "severidad": "error" if dias_demora > 7 else "warning",
            "mensaje": f"Etapa demorada ({dias_demora} días): {etapa.nombre}",
            "recurso_id": str(etapa.id),
            "recurso_tipo": "etapa",
            "proyecto_id": str(etapa.proyecto_id)
        })

    # Equipos en mantenimiento por más de 7 días
    equipos_mant = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado == EstadoEquipo.mantenimiento
    ).all()

    for equipo in equipos_mant:
        alertas.append({
            "tipo": "equipo_mantenimiento",
            "severidad": "info",
            "mensaje": f"Equipo en mantenimiento: {equipo.nombre}",
            "recurso_id": str(equipo.id),
            "recurso_tipo": "equipo"
        })

    return alertas

@router.get("/proyectos-activos")
def proyectos_activos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Estado de todos los proyectos activos."""
    proyectos = db.query(Proyecto).filter(
        Proyecto.activo == True,
        Proyecto.estado.in_([EstadoProyecto.en_ejecucion, EstadoProyecto.planificacion])
    ).all()

    return [
        {
            "id": str(p.id),
            "nombre": p.nombre,
            "estado": p.estado.value,
            "porcentaje_avance": float(p.porcentaje_avance),
            "fecha_fin_estimada": p.fecha_fin_estimada.isoformat() if p.fecha_fin_estimada else None,
            "dias_restantes": (p.fecha_fin_estimada - date.today()).days if p.fecha_fin_estimada else None
        }
        for p in proyectos
    ]

@router.get("/financiero")
def resumen_financiero(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """
    Resumen financiero para el dashboard.
    Solo admin y supervisor.
    """
    from app.services import finanzas_service
    return finanzas_service.obtener_resumen_financiero_general(db)

@router.get("/ultimas-fotos")
def ultimas_fotos(
    limit: int = 6,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Últimas fotos subidas al sistema."""
    fotos = db.query(Foto).filter(
        Foto.activo == True
    ).order_by(Foto.created_at.desc()).limit(limit).all()

    return [
        {
            "id": str(f.id),
            "url": f.url,
            "descripcion": f.descripcion,
            "fecha": f.fecha.isoformat(),
            "proyecto_id": str(f.proyecto_id),
            "proyecto_nombre": f.proyecto.nombre if f.proyecto else None
        }
        for f in fotos
    ]

@router.get("/actividad-reciente")
def actividad_reciente(
    limit: int = 10,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Actividad reciente del sistema."""
    actividades = []

    # Últimos gastos
    gastos = db.query(Gasto).filter(Gasto.activo == True).order_by(
        Gasto.created_at.desc()
    ).limit(5).all()

    for g in gastos:
        actividades.append({
            "tipo": "gasto",
            "mensaje": f"Gasto registrado: {g.descripcion[:50]}",
            "monto": float(g.monto),
            "fecha": g.created_at.isoformat(),
            "usuario": g.creador.nombre if g.creador else None
        })

    # Últimas fotos
    fotos = db.query(Foto).filter(Foto.activo == True).order_by(
        Foto.created_at.desc()
    ).limit(5).all()

    for f in fotos:
        actividades.append({
            "tipo": "foto",
            "mensaje": f"Foto subida: {f.descripcion or 'Sin descripción'}",
            "fecha": f.created_at.isoformat(),
            "proyecto": f.proyecto.nombre if f.proyecto else None
        })

    # Ordenar por fecha
    actividades.sort(key=lambda x: x['fecha'], reverse=True)

    return actividades[:limit]
```

## Frontend: Dashboard Page

### pages/dashboard/Dashboard.tsx
```typescript
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/authStore';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { formatearMonto, formatearPorcentaje } from '@/utils/formatters';
import {
  Briefcase,
  Package,
  Truck,
  DollarSign,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Camera
} from 'lucide-react';
import { ProyectosChart } from '@/components/dashboard/ProyectosChart';
import { AlertasList } from '@/components/dashboard/AlertasList';
import { ActividadReciente } from '@/components/dashboard/ActividadReciente';
import api from '@/services/api';

export default function Dashboard() {
  const { usuario } = useAuthStore();
  const isFinanceRole = usuario?.rol === 'administrador' || usuario?.rol === 'supervisor';

  const { data: resumen, isLoading } = useQuery({
    queryKey: ['dashboard', 'resumen'],
    queryFn: () => api.get('/dashboard/resumen').then(res => res.data),
  });

  const { data: alertas } = useQuery({
    queryKey: ['dashboard', 'alertas'],
    queryFn: () => api.get('/dashboard/alertas').then(res => res.data),
  });

  const { data: proyectos } = useQuery({
    queryKey: ['dashboard', 'proyectos-activos'],
    queryFn: () => api.get('/dashboard/proyectos-activos').then(res => res.data),
  });

  const { data: financiero, enabled: isFinanceRole } = useQuery({
    queryKey: ['dashboard', 'financiero'],
    queryFn: () => api.get('/dashboard/financiero').then(res => res.data),
    enabled: isFinanceRole,
  });

  const { data: fotos } = useQuery({
    queryKey: ['dashboard', 'ultimas-fotos'],
    queryFn: () => api.get('/dashboard/ultimas-fotos').then(res => res.data),
  });

  if (isLoading) return <div>Cargando dashboard...</div>;

  const gastosVariacion = resumen?.gastos?.variacion_porcentaje || 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Métricas principales */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted">Proyectos Activos</p>
                <p className="text-3xl font-bold">{resumen?.proyectos?.activos || 0}</p>
              </div>
              <Briefcase className="h-10 w-10 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted">Stock Bajo</p>
                <p className="text-3xl font-bold">{resumen?.materiales?.stock_bajo || 0}</p>
              </div>
              <Package className="h-10 w-10 text-yellow-500" />
            </div>
            {resumen?.materiales?.stock_bajo > 0 && (
              <Badge variant="destructive" className="mt-2">
                <AlertTriangle className="h-3 w-3 mr-1" />
                Requiere atención
              </Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted">Equipos Disponibles</p>
                <p className="text-3xl font-bold">
                  {resumen?.equipos?.disponibles || 0}
                  <span className="text-sm text-muted font-normal">
                    /{(resumen?.equipos?.disponibles || 0) + (resumen?.equipos?.asignados || 0)}
                  </span>
                </p>
              </div>
              <Truck className="h-10 w-10 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted">Gastos del Mes</p>
                <p className="text-2xl font-bold">
                  {formatearMonto(resumen?.gastos?.mes_actual || 0)}
                </p>
              </div>
              <DollarSign className="h-10 w-10 text-primary" />
            </div>
            <div className={`flex items-center text-sm mt-2 ${gastosVariacion >= 0 ? 'text-red-500' : 'text-green-500'}`}>
              {gastosVariacion >= 0 ? (
                <TrendingUp className="h-4 w-4 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 mr-1" />
              )}
              {Math.abs(gastosVariacion)}% vs mes anterior
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alertas */}
      {alertas && alertas.length > 0 && (
        <Card className="border-yellow-500">
          <CardHeader>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Alertas Activas ({alertas.length})
            </h2>
          </CardHeader>
          <CardContent>
            <AlertasList alertas={alertas} />
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Proyectos activos */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Proyectos en Curso</h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {proyectos?.slice(0, 5).map((proyecto: any) => (
                <div key={proyecto.id} className="space-y-2">
                  <div className="flex justify-between">
                    <span className="font-medium">{proyecto.nombre}</span>
                    <span className="text-sm text-muted">
                      {formatearPorcentaje(proyecto.porcentaje_avance)}
                    </span>
                  </div>
                  <Progress value={proyecto.porcentaje_avance} className="h-2" />
                  {proyecto.dias_restantes !== null && (
                    <p className="text-xs text-muted">
                      {proyecto.dias_restantes > 0
                        ? `${proyecto.dias_restantes} días restantes`
                        : `${Math.abs(proyecto.dias_restantes)} días de demora`}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Gráfico de proyectos por estado */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Proyectos por Estado</h2>
          </CardHeader>
          <CardContent>
            <ProyectosChart data={resumen?.proyectos?.por_estado || {}} />
          </CardContent>
        </Card>
      </div>

      {/* Solo para admin/supervisor */}
      {isFinanceRole && financiero && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Resumen Financiero</h2>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-sm text-muted">Total Contratado</p>
                <p className="text-xl font-bold">{formatearMonto(financiero.total_contratado)}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Total Costos</p>
                <p className="text-xl font-bold">{formatearMonto(financiero.total_costos)}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Rentabilidad</p>
                <p className={`text-xl font-bold ${financiero.total_rentabilidad >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatearMonto(financiero.total_rentabilidad)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Últimas fotos */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Camera className="h-5 w-5" />
            Últimas Fotos
          </h2>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {fotos?.map((foto: any) => (
              <div key={foto.id} className="relative aspect-square">
                <img
                  src={foto.url}
                  alt={foto.descripcion || 'Foto de proyecto'}
                  className="w-full h-full object-cover rounded-lg"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1 rounded-b-lg truncate">
                  {foto.proyecto_nombre}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### components/dashboard/ProyectosChart.tsx
```typescript
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface Props {
  data: Record<string, number>;
}

const COLORS = {
  planificacion: '#6B7280',
  en_ejecucion: '#E53935',
  pausado: '#F59E0B',
  finalizado: '#10B981',
};

const LABELS = {
  planificacion: 'Planificación',
  en_ejecucion: 'En Ejecución',
  pausado: 'Pausado',
  finalizado: 'Finalizado',
};

export function ProyectosChart({ data }: Props) {
  const chartData = Object.entries(data).map(([key, value]) => ({
    name: LABELS[key as keyof typeof LABELS] || key,
    value,
    color: COLORS[key as keyof typeof COLORS] || '#6B7280',
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={80}
          label
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
```

### components/dashboard/AlertasList.tsx
```typescript
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { Link } from 'react-router-dom';

interface Alerta {
  tipo: string;
  severidad: 'error' | 'warning' | 'info';
  mensaje: string;
  recurso_id: string;
  recurso_tipo: string;
}

interface Props {
  alertas: Alerta[];
}

const severidadIcons = {
  error: <AlertCircle className="h-4 w-4 text-red-500" />,
  warning: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
  info: <Info className="h-4 w-4 text-blue-500" />,
};

const severidadColors = {
  error: 'bg-red-100 text-red-800',
  warning: 'bg-yellow-100 text-yellow-800',
  info: 'bg-blue-100 text-blue-800',
};

export function AlertasList({ alertas }: Props) {
  return (
    <div className="space-y-2">
      {alertas.map((alerta, index) => (
        <div
          key={index}
          className={`flex items-center gap-3 p-3 rounded-lg ${severidadColors[alerta.severidad]}`}
        >
          {severidadIcons[alerta.severidad]}
          <span className="flex-1">{alerta.mensaje}</span>
          <Link
            to={`/${alerta.recurso_tipo}s/${alerta.recurso_id}`}
            className="text-sm underline"
          >
            Ver
          </Link>
        </div>
      ))}
    </div>
  );
}
```

## Checklist de Completado
- [ ] Endpoint resumen general
- [ ] Endpoint alertas
- [ ] Endpoint proyectos activos
- [ ] Endpoint financiero (solo admin/supervisor)
- [ ] Endpoint últimas fotos
- [ ] Endpoint actividad reciente
- [ ] Dashboard page
- [ ] ProyectosChart component
- [ ] AlertasList component
- [ ] ResumenFinanciero widget
- [ ] UltimasFotos grid
- [ ] ActividadReciente component
- [ ] Responsive design para móviles

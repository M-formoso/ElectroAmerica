import { useQuery } from '@tanstack/react-query'
import {
  FolderKanban,
  Package,
  Wrench,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Clock,
  DollarSign,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { dashboardService } from '@/services/dashboard'
import { formatCurrency, formatDate } from '@/lib/utils'
import { useUser, useIsAdmin } from '@/store/auth'

export function DashboardPage() {
  const user = useUser()
  const isAdmin = useIsAdmin()

  const { data: resumen, isLoading: loadingResumen } = useQuery({
    queryKey: ['dashboard-resumen'],
    queryFn: dashboardService.getResumen,
  })

  const { data: alertas } = useQuery({
    queryKey: ['dashboard-alertas'],
    queryFn: dashboardService.getAlertas,
  })

  const { data: proyectosActivos } = useQuery({
    queryKey: ['dashboard-proyectos-activos'],
    queryFn: dashboardService.getProyectosActivos,
  })

  const { data: actividad } = useQuery({
    queryKey: ['dashboard-actividad'],
    queryFn: () => dashboardService.getActividadReciente(10),
  })

  const { data: finanzas, isLoading: loadingFinanzas } = useQuery({
    queryKey: ['dashboard-finanzas'],
    queryFn: dashboardService.getResumenFinanciero,
    enabled: isAdmin,
  })

  const variacionPositiva = (resumen?.gastos.variacion_porcentaje || 0) < 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Bienvenido, {user?.nombre}. Aquí está el resumen de hoy.
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Proyectos Activos</CardTitle>
            <FolderKanban className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{resumen?.proyectos.activos || 0}</div>
            <p className="text-xs text-muted-foreground">
              {resumen?.proyectos.por_estado?.en_ejecucion || 0} en ejecución
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Materiales</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {resumen?.materiales.stock_bajo || 0}
            </div>
            <p className="text-xs text-muted-foreground">con stock bajo</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Equipos</CardTitle>
            <Wrench className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{resumen?.equipos.disponibles || 0}</div>
            <p className="text-xs text-muted-foreground">
              disponibles / {resumen?.equipos.asignados || 0} asignados
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Gastos del Mes</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(resumen?.gastos.mes_actual || 0)}
            </div>
            <div className="flex items-center text-xs">
              {variacionPositiva ? (
                <TrendingDown className="h-3 w-3 text-green-600 mr-1" />
              ) : (
                <TrendingUp className="h-3 w-3 text-red-600 mr-1" />
              )}
              <span className={variacionPositiva ? 'text-green-600' : 'text-red-600'}>
                {Math.abs(resumen?.gastos.variacion_porcentaje || 0).toFixed(1)}%
              </span>
              <span className="text-muted-foreground ml-1">vs mes anterior</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Proyectos activos */}
        <Card>
          <CardHeader>
            <CardTitle>Proyectos en Curso</CardTitle>
            <CardDescription>Estado de los proyectos activos</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-4">
                {proyectosActivos?.map((proyecto) => (
                  <div key={proyecto.id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">{proyecto.nombre}</span>
                      <Badge variant={
                        proyecto.estado === 'en_ejecucion' ? 'default' :
                        proyecto.estado === 'pausado' ? 'warning' : 'secondary'
                      }>
                        {proyecto.estado.replace('_', ' ')}
                      </Badge>
                    </div>
                    <Progress value={proyecto.porcentaje_avance} className="h-2" />
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{proyecto.porcentaje_avance.toFixed(0)}% completado</span>
                      {proyecto.dias_restantes != null && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {proyecto.dias_restantes > 0
                            ? `${proyecto.dias_restantes} días restantes`
                            : `${Math.abs(proyecto.dias_restantes)} días de retraso`
                          }
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {(!proyectosActivos || proyectosActivos.length === 0) && (
                  <p className="text-center text-muted-foreground py-4">
                    No hay proyectos activos
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Alertas */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Alertas
            </CardTitle>
            <CardDescription>Situaciones que requieren atención</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-3">
                {alertas?.map((alerta, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${
                      alerta.severidad === 'error'
                        ? 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800'
                        : alerta.severidad === 'warning'
                        ? 'bg-yellow-50 border-yellow-200 dark:bg-yellow-950 dark:border-yellow-800'
                        : 'bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800'
                    }`}
                  >
                    <p className="text-sm">{alerta.mensaje}</p>
                    <Badge
                      variant={
                        alerta.severidad === 'error' ? 'destructive' :
                        alerta.severidad === 'warning' ? 'warning' : 'info'
                      }
                      className="mt-2"
                    >
                      {alerta.tipo.replace('_', ' ')}
                    </Badge>
                  </div>
                ))}
                {(!alertas || alertas.length === 0) && (
                  <p className="text-center text-muted-foreground py-4">
                    No hay alertas activas
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Actividad reciente */}
      <Card>
        <CardHeader>
          <CardTitle>Actividad Reciente</CardTitle>
          <CardDescription>Últimos movimientos en el sistema</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {actividad?.slice(0, 5).map((item, index) => (
              <div key={index} className="flex items-center gap-4">
                <div className={`w-2 h-2 rounded-full ${
                  item.tipo === 'gasto' ? 'bg-red-500' :
                  item.tipo === 'foto' ? 'bg-blue-500' : 'bg-green-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{item.mensaje}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(item.fecha)}
                    {item.usuario && ` • ${item.usuario}`}
                  </p>
                </div>
                {item.monto && (
                  <span className="text-sm font-medium text-red-600">
                    -{formatCurrency(item.monto)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

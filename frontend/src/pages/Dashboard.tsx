import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  FolderKanban,
  Package,
  Wrench,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Clock,
  DollarSign,
  Image as ImageIcon,
  ArrowRight,
  Bell,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { dashboardService } from '@/services/dashboard'
import { materialesService } from '@/services/materiales'
import { alertasService } from '@/services/alertas'
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

  const { data: gastosMensuales } = useQuery({
    queryKey: ['dashboard-gastos-mensuales'],
    queryFn: () => dashboardService.getGastosMensuales(6),
  })

  const { data: proyectosPorEstado } = useQuery({
    queryKey: ['dashboard-proyectos-estado'],
    queryFn: dashboardService.getProyectosPorEstado,
  })

  const { data: equiposPorEstado } = useQuery({
    queryKey: ['dashboard-equipos-estado'],
    queryFn: dashboardService.getEquiposPorEstado,
  })

  const { data: ultimasFotos } = useQuery({
    queryKey: ['dashboard-ultimas-fotos'],
    queryFn: () => dashboardService.getUltimasFotos(6),
  })

  const { data: stockBajo } = useQuery({
    queryKey: ['materiales-stock-bajo'],
    queryFn: materialesService.getStockBajo,
  })

  const { data: alertasConteo } = useQuery({
    queryKey: ['alertas-conteo'],
    queryFn: alertasService.getConteo,
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

        <Card className={(resumen?.materiales.stock_bajo || 0) > 0 ? 'border-yellow-500' : ''}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Materiales</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {resumen?.materiales.stock_bajo || 0}
            </div>
            <p className="text-xs text-muted-foreground">con stock bajo</p>
            {(resumen?.materiales.stock_bajo || 0) > 0 && (
              <Link to="/materiales" className="text-xs text-primary hover:underline mt-1 inline-block">
                Ver materiales
              </Link>
            )}
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

      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Gastos mensuales */}
        <Card>
          <CardHeader>
            <CardTitle>Gastos por Mes</CardTitle>
            <CardDescription>Evolución de gastos en los últimos 6 meses</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              {gastosMensuales && gastosMensuales.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={gastosMensuales}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis
                      dataKey="mes"
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    />
                    <YAxis
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(value) => [formatCurrency(Number(value)), 'Total']}
                      labelFormatter={(label) => `Mes: ${label}`}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                      }}
                    />
                    <Bar dataKey="total" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  No hay datos de gastos
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Proyectos por estado */}
        <Card>
          <CardHeader>
            <CardTitle>Proyectos por Estado</CardTitle>
            <CardDescription>Distribución actual de proyectos</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              {proyectosPorEstado && proyectosPorEstado.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={proyectosPorEstado}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="cantidad"
                      nameKey="estado"
                      label={({ name, value }) => `${name}: ${value}`}
                      labelLine={false}
                    >
                      {proyectosPorEstado.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value, name) => [value, name]}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                      }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  No hay proyectos
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Proyectos activos */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Proyectos en Curso</CardTitle>
              <CardDescription>Estado de los proyectos activos</CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link to="/proyectos">
                Ver todos
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[280px] pr-4">
              <div className="space-y-4">
                {proyectosActivos?.map((proyecto) => (
                  <Link
                    key={proyecto.id}
                    to={`/proyectos/${proyecto.id}`}
                    className="block hover:bg-muted/50 rounded-lg p-2 -mx-2 transition-colors"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{proyecto.nombre}</span>
                        <Badge variant={
                          proyecto.estado === 'en_ejecucion' ? 'default' :
                          proyecto.estado === 'pausado' ? 'warning' : 'secondary'
                        }>
                          {proyecto.estado.replace('_', ' ')}
                        </Badge>
                      </div>
                      <Progress value={Number(proyecto.porcentaje_avance)} className="h-2" />
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{Number(proyecto.porcentaje_avance).toFixed(0)}% completado</span>
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
                  </Link>
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

        {/* Equipos por estado */}
        <Card>
          <CardHeader>
            <CardTitle>Equipos</CardTitle>
            <CardDescription>Distribución por estado</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              {equiposPorEstado && equiposPorEstado.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={equiposPorEstado}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={70}
                      paddingAngle={2}
                      dataKey="cantidad"
                      nameKey="estado"
                    >
                      {equiposPorEstado.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value, name) => [value, name]}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                      }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  No hay equipos
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stock Crítico */}
      {stockBajo && stockBajo.length > 0 && (
        <Card className="border-yellow-500 bg-yellow-50/50 dark:bg-yellow-950/20">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-yellow-700 dark:text-yellow-400">
                <AlertTriangle className="h-5 w-5" />
                Stock Crítico
                <Badge variant="warning">{stockBajo.length}</Badge>
              </CardTitle>
              <CardDescription>Materiales que necesitan reposición urgente</CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link to="/materiales">
                Ver todos
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {stockBajo.slice(0, 6).map((material) => (
                <div
                  key={material.id}
                  className="p-3 bg-background rounded-lg border flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-sm">{material.nombre}</p>
                    <p className="text-xs text-muted-foreground">{material.codigo}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-red-600">
                      {material.stock_actual} {material.unidad}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Mín: {material.stock_minimo}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Alertas del Sistema */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" />
                Alertas del Sistema
                {alertasConteo && alertasConteo.total > 0 && (
                  <Badge variant={alertasConteo.criticas > 0 ? 'destructive' : 'warning'}>
                    {alertasConteo.total}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                {alertasConteo?.criticas || 0} críticas, {alertasConteo?.altas || 0} altas
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link to="/alertas">
                Ver todas
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[250px] pr-4">
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
                  <div className="text-center py-8">
                    <div className="text-green-500 mb-2">
                      <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <p className="text-muted-foreground">No hay alertas activas</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Últimas fotos */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5" />
              Últimas Fotos
            </CardTitle>
            <CardDescription>Fotos recientes de los proyectos</CardDescription>
          </CardHeader>
          <CardContent>
            {ultimasFotos && ultimasFotos.length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {ultimasFotos.map((foto) => (
                  <Link
                    key={foto.id}
                    to={`/proyectos/${foto.proyecto_id}`}
                    className="relative aspect-square rounded-lg overflow-hidden border hover:opacity-80 transition-opacity group"
                  >
                    <img
                      src={foto.url}
                      alt={foto.descripcion || 'Foto de proyecto'}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                      <span className="text-white text-xs truncate">
                        {foto.proyecto_nombre}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <ImageIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No hay fotos recientes</p>
              </div>
            )}
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
                    {formatDate(item.fecha, true)}
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
            {(!actividad || actividad.length === 0) && (
              <p className="text-center text-muted-foreground py-4">
                No hay actividad reciente
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

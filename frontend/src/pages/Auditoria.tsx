import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  Search,
  Filter,
  User,
  Calendar,
  LogIn,
  LogOut,
  Plus,
  Edit,
  Trash2,
  Eye,
  Download,
  Link as LinkIcon,
  Loader2,
  Clock,
  ChevronDown,
  ChevronUp,
  BarChart3,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  auditoriaService,
  type Auditoria,
  type TipoAccion,
  type ModuloAuditado,
  getAccionColor,
  getAccionLabel,
  getModuloLabel,
} from '@/services/auditoria'
import { formatDate } from '@/lib/utils'
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns'

const accionIcons: Record<TipoAccion, React.ComponentType<{ className?: string }>> = {
  crear: Plus,
  actualizar: Edit,
  eliminar: Trash2,
  login: LogIn,
  logout: LogOut,
  ver: Eye,
  exportar: Download,
  asignar: LinkIcon,
  desasignar: LinkIcon,
  cambiar_estado: Activity,
  subir_archivo: Download,
}

export function AuditoriaPage() {
  const [filtroModulo, setFiltroModulo] = useState<string>('todos')
  const [filtroAccion, setFiltroAccion] = useState<string>('todas')
  const [filtroFechaDesde, setFiltroFechaDesde] = useState<string>(
    format(subDays(new Date(), 30), 'yyyy-MM-dd')
  )
  const [filtroFechaHasta, setFiltroFechaHasta] = useState<string>(
    format(new Date(), 'yyyy-MM-dd')
  )
  const [expandedRow, setExpandedRow] = useState<string | null>(null)

  const { data: auditorias, isLoading } = useQuery({
    queryKey: ['auditorias', filtroModulo, filtroAccion, filtroFechaDesde, filtroFechaHasta],
    queryFn: () =>
      auditoriaService.getAuditorias({
        modulo: filtroModulo !== 'todos' ? (filtroModulo as ModuloAuditado) : undefined,
        accion: filtroAccion !== 'todas' ? (filtroAccion as TipoAccion) : undefined,
        fecha_desde: filtroFechaDesde,
        fecha_hasta: filtroFechaHasta,
        limit: 100,
      }),
  })

  const { data: resumen, isLoading: isLoadingResumen } = useQuery({
    queryKey: ['auditoria-resumen', filtroFechaDesde, filtroFechaHasta],
    queryFn: () => auditoriaService.getResumenActividad(filtroFechaDesde, filtroFechaHasta),
  })

  const { data: actividadReciente } = useQuery({
    queryKey: ['auditoria-reciente'],
    queryFn: () => auditoriaService.getActividadReciente(10),
  })

  const setPresetFecha = (preset: 'hoy' | 'semana' | 'mes') => {
    const hoy = new Date()
    switch (preset) {
      case 'hoy':
        setFiltroFechaDesde(format(hoy, 'yyyy-MM-dd'))
        setFiltroFechaHasta(format(hoy, 'yyyy-MM-dd'))
        break
      case 'semana':
        setFiltroFechaDesde(format(subDays(hoy, 7), 'yyyy-MM-dd'))
        setFiltroFechaHasta(format(hoy, 'yyyy-MM-dd'))
        break
      case 'mes':
        setFiltroFechaDesde(format(startOfMonth(hoy), 'yyyy-MM-dd'))
        setFiltroFechaHasta(format(endOfMonth(hoy), 'yyyy-MM-dd'))
        break
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Activity className="h-6 w-6" />
          Auditoria del Sistema
        </h1>
        <p className="text-muted-foreground">
          Registro de todas las acciones realizadas en el sistema
        </p>
      </div>

      <Tabs defaultValue="registros">
        <TabsList>
          <TabsTrigger value="registros">Registros</TabsTrigger>
          <TabsTrigger value="resumen">Resumen</TabsTrigger>
        </TabsList>

        <TabsContent value="registros" className="space-y-4">
          {/* Filtros */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Filter className="h-4 w-4" />
                  Filtros
                </CardTitle>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setPresetFecha('hoy')}>
                    Hoy
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setPresetFecha('semana')}>
                    Ultima semana
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setPresetFecha('mes')}>
                    Este mes
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Modulo</label>
                  <Select value={filtroModulo} onValueChange={setFiltroModulo}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todos">Todos los modulos</SelectItem>
                      <SelectItem value="auth">Autenticacion</SelectItem>
                      <SelectItem value="usuarios">Usuarios</SelectItem>
                      <SelectItem value="proyectos">Proyectos</SelectItem>
                      <SelectItem value="materiales">Materiales</SelectItem>
                      <SelectItem value="equipos">Equipos</SelectItem>
                      <SelectItem value="gastos">Gastos</SelectItem>
                      <SelectItem value="clientes">Clientes</SelectItem>
                      <SelectItem value="finanzas">Finanzas</SelectItem>
                      <SelectItem value="alertas">Alertas</SelectItem>
                      <SelectItem value="jornadas">Jornadas</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Accion</label>
                  <Select value={filtroAccion} onValueChange={setFiltroAccion}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todas">Todas las acciones</SelectItem>
                      <SelectItem value="crear">Creacion</SelectItem>
                      <SelectItem value="actualizar">Actualizacion</SelectItem>
                      <SelectItem value="eliminar">Eliminacion</SelectItem>
                      <SelectItem value="login">Login</SelectItem>
                      <SelectItem value="logout">Logout</SelectItem>
                      <SelectItem value="asignar">Asignacion</SelectItem>
                      <SelectItem value="exportar">Exportacion</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Desde</label>
                  <Input
                    type="date"
                    value={filtroFechaDesde}
                    onChange={(e) => setFiltroFechaDesde(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Hasta</label>
                  <Input
                    type="date"
                    value={filtroFechaHasta}
                    onChange={(e) => setFiltroFechaHasta(e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabla de registros */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Registros de Auditoria ({auditorias?.length || 0})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center h-40">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : auditorias?.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No hay registros de auditoria para los filtros seleccionados</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]">Accion</TableHead>
                      <TableHead>Descripcion</TableHead>
                      <TableHead>Usuario</TableHead>
                      <TableHead>Modulo</TableHead>
                      <TableHead>Fecha</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditorias?.map((auditoria) => {
                      const Icon = accionIcons[auditoria.accion] || Activity
                      const isExpanded = expandedRow === auditoria.id

                      return (
                        <Collapsible
                          key={auditoria.id}
                          open={isExpanded}
                          onOpenChange={() =>
                            setExpandedRow(isExpanded ? null : auditoria.id)
                          }
                          asChild
                        >
                          <>
                            <TableRow className="cursor-pointer hover:bg-muted/50">
                              <TableCell>
                                <div
                                  className={`p-2 rounded-full inline-flex ${getAccionColor(
                                    auditoria.accion
                                  )}`}
                                >
                                  <Icon className="h-4 w-4" />
                                </div>
                              </TableCell>
                              <TableCell>
                                <p className="font-medium">{auditoria.descripcion}</p>
                                {auditoria.recurso_tipo && (
                                  <p className="text-xs text-muted-foreground">
                                    {auditoria.recurso_tipo}
                                  </p>
                                )}
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <User className="h-4 w-4 text-muted-foreground" />
                                  <span>{auditoria.usuario_nombre || 'Sistema'}</span>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline">
                                  {getModuloLabel(auditoria.modulo)}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1 text-sm">
                                  <Clock className="h-3 w-3 text-muted-foreground" />
                                  {formatDate(auditoria.created_at)}
                                </div>
                              </TableCell>
                              <TableCell>
                                <CollapsibleTrigger asChild>
                                  <Button variant="ghost" size="sm">
                                    {isExpanded ? (
                                      <ChevronUp className="h-4 w-4" />
                                    ) : (
                                      <ChevronDown className="h-4 w-4" />
                                    )}
                                  </Button>
                                </CollapsibleTrigger>
                              </TableCell>
                            </TableRow>
                            <CollapsibleContent asChild>
                              <TableRow className="bg-muted/30">
                                <TableCell colSpan={6}>
                                  <div className="p-4 space-y-3">
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                      <div>
                                        <span className="text-muted-foreground">Accion:</span>
                                        <p className="font-medium">
                                          {getAccionLabel(auditoria.accion)}
                                        </p>
                                      </div>
                                      <div>
                                        <span className="text-muted-foreground">IP:</span>
                                        <p className="font-mono text-sm">
                                          {auditoria.ip_address || '-'}
                                        </p>
                                      </div>
                                      <div>
                                        <span className="text-muted-foreground">
                                          ID Recurso:
                                        </span>
                                        <p className="font-mono text-xs break-all">
                                          {auditoria.recurso_id || '-'}
                                        </p>
                                      </div>
                                      <div>
                                        <span className="text-muted-foreground">
                                          Tipo Recurso:
                                        </span>
                                        <p>{auditoria.recurso_tipo || '-'}</p>
                                      </div>
                                    </div>
                                    {auditoria.user_agent && (
                                      <div>
                                        <span className="text-muted-foreground text-sm">
                                          User Agent:
                                        </span>
                                        <p className="text-xs text-muted-foreground truncate">
                                          {auditoria.user_agent}
                                        </p>
                                      </div>
                                    )}
                                    {auditoria.datos_adicionales && (
                                      <div>
                                        <span className="text-muted-foreground text-sm">
                                          Datos Adicionales:
                                        </span>
                                        <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-x-auto">
                                          {JSON.stringify(
                                            auditoria.datos_adicionales,
                                            null,
                                            2
                                          )}
                                        </pre>
                                      </div>
                                    )}
                                  </div>
                                </TableCell>
                              </TableRow>
                            </CollapsibleContent>
                          </>
                        </Collapsible>
                      )
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resumen" className="space-y-4">
          {/* Cards de resumen */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Acciones
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{resumen?.total_acciones || 0}</div>
                <p className="text-xs text-muted-foreground">
                  en el periodo seleccionado
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Usuarios Activos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {resumen?.usuarios_mas_activos?.length || 0}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Modulos Usados
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Object.keys(resumen?.acciones_por_modulo || {}).length}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Periodo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm">
                  {resumen?.periodo.desde} - {resumen?.periodo.hasta}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {/* Acciones por tipo */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Acciones por Tipo</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {resumen?.acciones_por_tipo &&
                    Object.entries(resumen.acciones_por_tipo)
                      .sort(([, a], [, b]) => b - a)
                      .map(([tipo, cantidad]) => (
                        <div key={tipo} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge
                              className={getAccionColor(tipo as TipoAccion)}
                              variant="outline"
                            >
                              {getAccionLabel(tipo as TipoAccion)}
                            </Badge>
                          </div>
                          <span className="font-medium">{cantidad}</span>
                        </div>
                      ))}
                </div>
              </CardContent>
            </Card>

            {/* Acciones por módulo */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Acciones por Modulo</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {resumen?.acciones_por_modulo &&
                    Object.entries(resumen.acciones_por_modulo)
                      .sort(([, a], [, b]) => b - a)
                      .map(([modulo, cantidad]) => (
                        <div key={modulo} className="flex items-center justify-between">
                          <Badge variant="outline">
                            {getModuloLabel(modulo as ModuloAuditado)}
                          </Badge>
                          <span className="font-medium">{cantidad}</span>
                        </div>
                      ))}
                </div>
              </CardContent>
            </Card>

            {/* Usuarios más activos */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base">Usuarios Mas Activos</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Usuario</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {resumen?.usuarios_mas_activos?.map((usuario) => (
                      <TableRow key={usuario.usuario_id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <User className="h-4 w-4 text-muted-foreground" />
                            {usuario.usuario_nombre}
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {usuario.cantidad}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

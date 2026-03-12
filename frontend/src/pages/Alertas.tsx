import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Bell,
  Check,
  CheckCheck,
  Clock,
  Package,
  AlertTriangle,
  CreditCard,
  Wrench,
  Calendar,
  DollarSign,
  Loader2,
  Filter,
  RefreshCw,
  Search,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
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
import {
  alertasService,
  type Alerta,
  type TipoAlerta,
  type PrioridadAlerta,
  getPrioridadColor,
  getTipoLabel,
} from '@/services/alertas'
import { formatDistanceToNow, format } from 'date-fns'
import { es } from 'date-fns/locale'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

const tipoIcons: Record<TipoAlerta, React.ComponentType<{ className?: string }>> = {
  stock_minimo: Package,
  demora_etapa: Clock,
  etapa_pendiente: AlertTriangle,
  limite_credito: CreditCard,
  equipo_mantenimiento: Wrench,
  proyecto_vencido: Calendar,
  pago_pendiente: DollarSign,
}

const prioridadLabels: Record<PrioridadAlerta, string> = {
  baja: 'Baja',
  media: 'Media',
  alta: 'Alta',
  critica: 'Critica',
}

const prioridadBadgeVariants: Record<PrioridadAlerta, string> = {
  baja: 'secondary',
  media: 'default',
  alta: 'warning',
  critica: 'destructive',
}

export function AlertasPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [filtroTipo, setFiltroTipo] = useState<string>('todas')
  const [filtroPrioridad, setFiltroPrioridad] = useState<string>('todas')
  const [filtroEstado, setFiltroEstado] = useState<string>('no_resueltas')
  const [busqueda, setBusqueda] = useState('')

  const { data: conteo, isLoading: isLoadingConteo } = useQuery({
    queryKey: ['alertas-conteo'],
    queryFn: alertasService.getConteo,
  })

  const { data: alertas, isLoading: isLoadingAlertas, refetch } = useQuery({
    queryKey: ['alertas', filtroTipo, filtroPrioridad, filtroEstado],
    queryFn: () =>
      alertasService.getAlertas({
        tipo: filtroTipo !== 'todas' ? (filtroTipo as TipoAlerta) : undefined,
        prioridad: filtroPrioridad !== 'todas' ? (filtroPrioridad as PrioridadAlerta) : undefined,
        solo_no_resueltas: filtroEstado === 'no_resueltas',
        limit: 100,
      }),
  })

  const marcarLeidaMutation = useMutation({
    mutationFn: alertasService.marcarLeida,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertas'] })
      queryClient.invalidateQueries({ queryKey: ['alertas-conteo'] })
    },
  })

  const marcarTodasLeidasMutation = useMutation({
    mutationFn: alertasService.marcarTodasLeidas,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertas'] })
      queryClient.invalidateQueries({ queryKey: ['alertas-conteo'] })
      toast({ title: 'Todas las alertas marcadas como leidas' })
    },
  })

  const resolverAlertaMutation = useMutation({
    mutationFn: alertasService.resolverAlerta,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertas'] })
      queryClient.invalidateQueries({ queryKey: ['alertas-conteo'] })
      toast({ title: 'Alerta resuelta' })
    },
  })

  const ejecutarVerificacionesMutation = useMutation({
    mutationFn: alertasService.ejecutarVerificaciones,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['alertas'] })
      queryClient.invalidateQueries({ queryKey: ['alertas-conteo'] })
      toast({
        title: 'Verificaciones completadas',
        description: `Se encontraron ${data.total} nuevas alertas`,
      })
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al ejecutar verificaciones' })
    },
  })

  const getAlertaLink = (alerta: Alerta): string | null => {
    if (!alerta.referencia_tipo || !alerta.referencia_id) return null

    switch (alerta.referencia_tipo) {
      case 'proyecto':
        return `/proyectos/${alerta.referencia_id}`
      case 'material':
        return `/materiales?id=${alerta.referencia_id}`
      case 'equipo':
        return `/equipos?id=${alerta.referencia_id}`
      case 'cliente':
        return `/clientes?id=${alerta.referencia_id}`
      default:
        return null
    }
  }

  const alertasFiltradas = alertas?.filter((alerta) =>
    busqueda
      ? alerta.titulo.toLowerCase().includes(busqueda.toLowerCase()) ||
        alerta.mensaje.toLowerCase().includes(busqueda.toLowerCase())
      : true
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Alertas del Sistema</h1>
          <p className="text-muted-foreground">
            Gestiona las alertas y notificaciones del sistema
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => ejecutarVerificacionesMutation.mutate()}
            disabled={ejecutarVerificacionesMutation.isPending}
          >
            {ejecutarVerificacionesMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Verificar ahora
          </Button>
        </div>
      </div>

      {/* Resumen Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Pendientes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{conteo?.total || 0}</div>
          </CardContent>
        </Card>

        <Card className="border-red-200 bg-red-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-red-700">
              Criticas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-700">{conteo?.criticas || 0}</div>
          </CardContent>
        </Card>

        <Card className="border-orange-200 bg-orange-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-orange-700">
              Altas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-700">{conteo?.altas || 0}</div>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">
              Medias
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-700">{conteo?.medias || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              No Leidas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{conteo?.no_leidas || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">Filtros</CardTitle>
            </div>
            {(conteo?.no_leidas || 0) > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => marcarTodasLeidasMutation.mutate()}
                disabled={marcarTodasLeidasMutation.isPending}
              >
                <CheckCheck className="h-4 w-4 mr-2" />
                Marcar todas como leidas
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Buscar</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar en alertas..."
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo</label>
              <Select value={filtroTipo} onValueChange={setFiltroTipo}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todas">Todos los tipos</SelectItem>
                  <SelectItem value="stock_minimo">Stock Minimo</SelectItem>
                  <SelectItem value="demora_etapa">Demora en Etapa</SelectItem>
                  <SelectItem value="etapa_pendiente">Etapa Pendiente</SelectItem>
                  <SelectItem value="limite_credito">Limite de Credito</SelectItem>
                  <SelectItem value="equipo_mantenimiento">Mantenimiento Equipo</SelectItem>
                  <SelectItem value="proyecto_vencido">Proyecto Vencido</SelectItem>
                  <SelectItem value="pago_pendiente">Pago Pendiente</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Prioridad</label>
              <Select value={filtroPrioridad} onValueChange={setFiltroPrioridad}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todas">Todas las prioridades</SelectItem>
                  <SelectItem value="critica">Critica</SelectItem>
                  <SelectItem value="alta">Alta</SelectItem>
                  <SelectItem value="media">Media</SelectItem>
                  <SelectItem value="baja">Baja</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Estado</label>
              <Select value={filtroEstado} onValueChange={setFiltroEstado}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="no_resueltas">No resueltas</SelectItem>
                  <SelectItem value="todas">Todas</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Alertas */}
      <Card>
        <CardHeader>
          <CardTitle>Alertas</CardTitle>
          <CardDescription>
            {alertasFiltradas?.length || 0} alerta(s) encontrada(s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingAlertas ? (
            <div className="flex items-center justify-center h-40">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : alertasFiltradas?.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
              <Bell className="h-12 w-12 mb-4 opacity-50" />
              <p>No hay alertas que mostrar</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">Tipo</TableHead>
                  <TableHead>Alerta</TableHead>
                  <TableHead className="w-[100px]">Prioridad</TableHead>
                  <TableHead className="w-[150px]">Fecha</TableHead>
                  <TableHead className="w-[100px]">Estado</TableHead>
                  <TableHead className="w-[150px] text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alertasFiltradas?.map((alerta) => {
                  const Icon = tipoIcons[alerta.tipo] || Bell
                  const link = getAlertaLink(alerta)

                  return (
                    <TableRow
                      key={alerta.id}
                      className={cn(!alerta.leida && "bg-muted/30")}
                    >
                      <TableCell>
                        <div
                          className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center",
                            getPrioridadColor(alerta.prioridad)
                          )}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium flex items-center gap-2">
                            {alerta.titulo}
                            {!alerta.leida && (
                              <span className="w-2 h-2 bg-blue-500 rounded-full" />
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            {alerta.mensaje}
                          </p>
                          <Badge variant="outline" className="mt-1 text-xs">
                            {getTipoLabel(alerta.tipo)}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={prioridadBadgeVariants[alerta.prioridad] as any}
                        >
                          {prioridadLabels[alerta.prioridad]}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {format(new Date(alerta.created_at), "dd/MM/yyyy HH:mm")}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(alerta.created_at), {
                            addSuffix: true,
                            locale: es,
                          })}
                        </div>
                      </TableCell>
                      <TableCell>
                        {alerta.resuelta ? (
                          <Badge variant="success">Resuelta</Badge>
                        ) : (
                          <Badge variant="secondary">Pendiente</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          {!alerta.leida && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => marcarLeidaMutation.mutate(alerta.id)}
                              disabled={marcarLeidaMutation.isPending}
                              title="Marcar como leida"
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                          )}
                          {!alerta.resuelta && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => resolverAlertaMutation.mutate(alerta.id)}
                              disabled={resolverAlertaMutation.isPending}
                              title="Resolver alerta"
                            >
                              <CheckCheck className="h-4 w-4" />
                            </Button>
                          )}
                          {link && (
                            <Button variant="outline" size="sm" asChild>
                              <Link to={link}>Ver</Link>
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

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
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  alertasService,
  type Alerta,
  type TipoAlerta,
  type PrioridadAlerta,
  getPrioridadColor,
} from '@/services/alertas'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
import { cn } from '@/lib/utils'

const tipoIcons: Record<TipoAlerta, React.ComponentType<{ className?: string }>> = {
  stock_minimo: Package,
  demora_etapa: Clock,
  etapa_pendiente: AlertTriangle,
  limite_credito: CreditCard,
  equipo_mantenimiento: Wrench,
  proyecto_vencido: Calendar,
  pago_pendiente: DollarSign,
}

const prioridadColors: Record<PrioridadAlerta, string> = {
  baja: 'border-l-gray-400',
  media: 'border-l-blue-500',
  alta: 'border-l-orange-500',
  critica: 'border-l-red-500',
}

export function AlertasDropdown() {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: conteo } = useQuery({
    queryKey: ['alertas-conteo'],
    queryFn: alertasService.getConteo,
    refetchInterval: 30000, // Refrescar cada 30 segundos
  })

  const { data: alertas, isLoading } = useQuery({
    queryKey: ['alertas-recientes'],
    queryFn: () => alertasService.getAlertas({ solo_no_resueltas: true, limit: 10 }),
    enabled: open,
  })

  const marcarLeidaMutation = useMutation({
    mutationFn: alertasService.marcarLeida,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertas-conteo'] })
      queryClient.invalidateQueries({ queryKey: ['alertas-recientes'] })
    },
  })

  const marcarTodasLeidasMutation = useMutation({
    mutationFn: alertasService.marcarTodasLeidas,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertas-conteo'] })
      queryClient.invalidateQueries({ queryKey: ['alertas-recientes'] })
    },
  })

  const resolverAlertaMutation = useMutation({
    mutationFn: alertasService.resolverAlerta,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertas-conteo'] })
      queryClient.invalidateQueries({ queryKey: ['alertas-recientes'] })
    },
  })

  const totalNoLeidas = conteo?.no_leidas || 0
  const hasCriticas = (conteo?.criticas || 0) > 0

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
      case 'etapa':
        return null // Las etapas se ven dentro de proyectos
      default:
        return null
    }
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className={cn("h-5 w-5", hasCriticas && "text-red-500")} />
          {totalNoLeidas > 0 && (
            <span className={cn(
              "absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] text-xs font-medium rounded-full flex items-center justify-center",
              hasCriticas ? "bg-red-500 text-white" : "bg-primary text-primary-foreground"
            )}>
              {totalNoLeidas > 99 ? '99+' : totalNoLeidas}
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent align="end" className="w-96 p-0">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="font-semibold">Alertas</div>
          {totalNoLeidas > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => marcarTodasLeidasMutation.mutate()}
              disabled={marcarTodasLeidasMutation.isPending}
            >
              <CheckCheck className="h-4 w-4 mr-1" />
              Marcar todas leidas
            </Button>
          )}
        </div>

        {/* Resumen de conteo */}
        {conteo && (conteo.criticas > 0 || conteo.altas > 0) && (
          <div className="px-4 py-2 bg-muted/50 border-b flex gap-4 text-xs">
            {conteo.criticas > 0 && (
              <span className="text-red-600 font-medium">
                {conteo.criticas} critica{conteo.criticas > 1 ? 's' : ''}
              </span>
            )}
            {conteo.altas > 0 && (
              <span className="text-orange-600 font-medium">
                {conteo.altas} alta{conteo.altas > 1 ? 's' : ''}
              </span>
            )}
          </div>
        )}

        <ScrollArea className="h-80">
          {isLoading ? (
            <div className="flex items-center justify-center h-40">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : alertas?.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
              <Bell className="h-10 w-10 mb-2 opacity-50" />
              <p>No hay alertas pendientes</p>
            </div>
          ) : (
            <div className="divide-y">
              {alertas?.map((alerta) => {
                const Icon = tipoIcons[alerta.tipo] || Bell
                const link = getAlertaLink(alerta)

                return (
                  <div
                    key={alerta.id}
                    className={cn(
                      "p-4 hover:bg-muted/50 transition-colors border-l-4",
                      prioridadColors[alerta.prioridad],
                      !alerta.leida && "bg-muted/30"
                    )}
                  >
                    <div className="flex gap-3">
                      <div className={cn(
                        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                        getPrioridadColor(alerta.prioridad)
                      )}>
                        <Icon className="h-4 w-4" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p className="font-medium text-sm leading-tight">
                            {alerta.titulo}
                          </p>
                          <div className="flex gap-1 flex-shrink-0">
                            {!alerta.leida && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => marcarLeidaMutation.mutate(alerta.id)}
                              >
                                <Check className="h-3 w-3" />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => resolverAlertaMutation.mutate(alerta.id)}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>

                        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                          {alerta.mensaje}
                        </p>

                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(alerta.created_at), {
                              addSuffix: true,
                              locale: es,
                            })}
                          </span>

                          {link && (
                            <Link
                              to={link}
                              onClick={() => {
                                if (!alerta.leida) {
                                  marcarLeidaMutation.mutate(alerta.id)
                                }
                                setOpen(false)
                              }}
                              className="text-xs text-primary hover:underline"
                            >
                              Ver detalle
                            </Link>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </ScrollArea>

        <div className="p-3 border-t">
          <Button
            variant="outline"
            className="w-full"
            asChild
            onClick={() => setOpen(false)}
          >
            <Link to="/alertas">Ver todas las alertas</Link>
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}

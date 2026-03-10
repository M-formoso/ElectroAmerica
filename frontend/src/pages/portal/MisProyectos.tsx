import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { MapPin, Calendar, Clock, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import api from '@/services/api'
import { formatDate } from '@/lib/utils'
import type { Proyecto, EstadoProyecto } from '@/types'

const estadoColors: Record<EstadoProyecto, string> = {
  planificacion: 'secondary',
  en_ejecucion: 'default',
  pausado: 'warning',
  finalizado: 'success',
}

const estadoLabels: Record<EstadoProyecto, string> = {
  planificacion: 'En Planificación',
  en_ejecucion: 'En Ejecución',
  pausado: 'Pausado',
  finalizado: 'Finalizado',
}

export function MisProyectosPage() {
  const { data: proyectos, isLoading } = useQuery({
    queryKey: ['mis-proyectos'],
    queryFn: async () => {
      const response = await api.get<Proyecto[]>('/portal/mis-proyectos')
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Mis Proyectos</h1>
        <div className="grid gap-4 md:grid-cols-2">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-5 bg-muted rounded w-3/4" />
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="h-2 bg-muted rounded" />
                <div className="h-4 bg-muted rounded w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Mis Proyectos</h1>
        <p className="text-muted-foreground">
          Seguimiento del avance de tus proyectos
        </p>
      </div>

      {proyectos?.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              No tienes proyectos asignados actualmente.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {proyectos?.map((proyecto) => {
            const hoy = new Date()
            const fechaFin = proyecto.fecha_fin_estimada
              ? new Date(proyecto.fecha_fin_estimada)
              : null
            const diasRestantes = fechaFin
              ? Math.ceil((fechaFin.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24))
              : null

            return (
              <Card key={proyecto.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-xl">{proyecto.nombre}</CardTitle>
                      {proyecto.ubicacion && (
                        <p className="text-sm text-muted-foreground flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {proyecto.ubicacion}
                        </p>
                      )}
                    </div>
                    <Badge variant={estadoColors[proyecto.estado] as any}>
                      {estadoLabels[proyecto.estado]}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {proyecto.descripcion && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {proyecto.descripcion}
                    </p>
                  )}

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Avance del proyecto</span>
                      <span className="font-medium">
                        {proyecto.porcentaje_avance.toFixed(0)}%
                      </span>
                    </div>
                    <Progress value={proyecto.porcentaje_avance} className="h-3" />
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    {proyecto.fecha_fin_estimada && (
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        <span>Fecha estimada: {formatDate(proyecto.fecha_fin_estimada)}</span>
                      </div>
                    )}
                    {diasRestantes !== null && diasRestantes > 0 && (
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        <span>{diasRestantes} días restantes</span>
                      </div>
                    )}
                  </div>

                  <Button asChild variant="outline" className="w-full">
                    <Link to={`/portal/proyecto/${proyecto.id}`}>
                      Ver detalles
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

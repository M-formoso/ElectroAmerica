import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  MapPin,
  Calendar,
  CheckCircle2,
  Clock,
  Image as ImageIcon,
  FileText,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import api from '@/services/api'
import { formatDate } from '@/lib/utils'
import type { Proyecto, Etapa, Foto, EstadoEtapa } from '@/types'

const estadoEtapaColors: Record<EstadoEtapa, string> = {
  pendiente: 'secondary',
  en_progreso: 'default',
  completada: 'success',
  pausada: 'warning',
}

export function DetalleProyectoPage() {
  const { proyectoId } = useParams<{ proyectoId: string }>()

  const { data: proyecto, isLoading: loadingProyecto } = useQuery({
    queryKey: ['portal-proyecto', proyectoId],
    queryFn: async () => {
      const response = await api.get<Proyecto>(`/portal/proyecto/${proyectoId}`)
      return response.data
    },
  })

  const { data: etapas } = useQuery({
    queryKey: ['portal-etapas', proyectoId],
    queryFn: async () => {
      const response = await api.get<Etapa[]>(`/portal/proyecto/${proyectoId}/etapas`)
      return response.data
    },
    enabled: !!proyectoId,
  })

  const { data: fotos } = useQuery({
    queryKey: ['portal-fotos', proyectoId],
    queryFn: async () => {
      const response = await api.get<Foto[]>(`/portal/proyecto/${proyectoId}/fotos`)
      return response.data
    },
    enabled: !!proyectoId,
  })

  const { data: reporte } = useQuery({
    queryKey: ['portal-reporte', proyectoId],
    queryFn: async () => {
      const response = await api.get(`/portal/proyecto/${proyectoId}/reporte`)
      return response.data
    },
    enabled: !!proyectoId,
  })

  if (loadingProyecto) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-muted rounded w-48 animate-pulse" />
        <Card className="animate-pulse">
          <CardHeader>
            <div className="h-6 bg-muted rounded w-3/4" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="h-4 bg-muted rounded" />
            <div className="h-4 bg-muted rounded w-1/2" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!proyecto) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Proyecto no encontrado</p>
        <Button asChild variant="link">
          <Link to="/portal">Volver a mis proyectos</Link>
        </Button>
      </div>
    )
  }

  const etapasCompletadas = etapas?.filter((e) => e.estado === 'completada').length || 0
  const totalEtapas = etapas?.length || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button asChild variant="ghost" size="icon">
          <Link to="/portal">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{proyecto.nombre}</h1>
          {proyecto.ubicacion && (
            <p className="text-muted-foreground flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              {proyecto.ubicacion}
            </p>
          )}
        </div>
      </div>

      {/* Progress card */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Avance General</p>
              <div className="flex items-end gap-2">
                <span className="text-4xl font-bold">
                  {proyecto.porcentaje_avance.toFixed(0)}%
                </span>
              </div>
              <Progress value={proyecto.porcentaje_avance} className="h-3" />
            </div>

            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Etapas Completadas</p>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-8 w-8 text-green-500" />
                <span className="text-2xl font-bold">
                  {etapasCompletadas} / {totalEtapas}
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Fecha Estimada</p>
              <div className="flex items-center gap-2">
                <Calendar className="h-8 w-8 text-muted-foreground" />
                <span className="text-xl font-medium">
                  {proyecto.fecha_fin_estimada
                    ? formatDate(proyecto.fecha_fin_estimada)
                    : 'Por definir'}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="etapas">
        <TabsList>
          <TabsTrigger value="etapas">Etapas</TabsTrigger>
          <TabsTrigger value="fotos">
            Fotos ({fotos?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="reportes">Reportes</TabsTrigger>
        </TabsList>

        <TabsContent value="etapas" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Etapas del Proyecto</CardTitle>
              <CardDescription>
                Seguimiento del avance por etapa
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {etapas?.map((etapa, index) => (
                  <div
                    key={etapa.id}
                    className="flex items-start gap-4 p-4 rounded-lg border"
                  >
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">{etapa.nombre}</h4>
                        <Badge variant={estadoEtapaColors[etapa.estado] as any}>
                          {etapa.estado.replace('_', ' ')}
                        </Badge>
                      </div>
                      {etapa.descripcion && (
                        <p className="text-sm text-muted-foreground">
                          {etapa.descripcion}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-sm">
                        <Progress
                          value={etapa.porcentaje_avance}
                          className="flex-1 h-2"
                        />
                        <span className="text-muted-foreground">
                          {etapa.porcentaje_avance.toFixed(0)}%
                        </span>
                      </div>
                      {(etapa.fecha_inicio_est || etapa.fecha_fin_est) && (
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {etapa.fecha_inicio_est && formatDate(etapa.fecha_inicio_est)}
                          {etapa.fecha_inicio_est && etapa.fecha_fin_est && ' - '}
                          {etapa.fecha_fin_est && formatDate(etapa.fecha_fin_est)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {(!etapas || etapas.length === 0) && (
                  <p className="text-center py-8 text-muted-foreground">
                    No hay etapas definidas
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fotos" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Galería de Fotos</CardTitle>
              <CardDescription>
                Registro fotográfico del avance
              </CardDescription>
            </CardHeader>
            <CardContent>
              {fotos && fotos.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {fotos.map((foto) => (
                    <a
                      key={foto.id}
                      href={foto.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group relative aspect-square rounded-lg overflow-hidden border hover:ring-2 ring-primary transition-all"
                    >
                      <img
                        src={foto.thumbnail_url || foto.url}
                        alt={foto.descripcion || 'Foto del proyecto'}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                        <div className="text-white text-xs">
                          <p className="font-medium truncate">
                            {foto.descripcion || 'Sin descripción'}
                          </p>
                          <p className="opacity-75">{formatDate(foto.fecha)}</p>
                        </div>
                      </div>
                    </a>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <ImageIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    No hay fotos disponibles
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reportes" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Reportes</CardTitle>
              <CardDescription>
                Reportes de avance compartidos
              </CardDescription>
            </CardHeader>
            <CardContent>
              {reporte ? (
                <div className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <p className="font-medium">Último Reporte</p>
                      <p className="text-sm text-muted-foreground">
                        Período: {formatDate(reporte.fecha_desde)} -{' '}
                        {formatDate(reporte.fecha_hasta)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Generado: {formatDate(reporte.created_at)}
                      </p>
                    </div>
                    {reporte.pdf_url && (
                      <Button asChild>
                        <a href={reporte.pdf_url} target="_blank" rel="noopener">
                          <FileText className="h-4 w-4 mr-2" />
                          Descargar PDF
                        </a>
                      </Button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    No hay reportes disponibles
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

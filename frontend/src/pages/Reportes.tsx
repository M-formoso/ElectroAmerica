import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileBarChart,
  Calendar,
  Download,
  FileSpreadsheet,
  FileText,
  Loader2,
  Building2,
  CheckCircle2,
  Package,
  Wrench,
  Receipt,
  Image as ImageIcon,
  Clock,
  DollarSign,
  TrendingUp,
  Share2,
  Printer,
  ChevronDown,
  ChevronUp,
  Eye,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
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
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { proyectosService } from '@/services/proyectos'
import { reportesService, type DatosReporte } from '@/services/reportes'
import { formatDate, formatCurrency } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { Timeline } from '@/components/ui/timeline'

const estadoColors: Record<string, string> = {
  planificacion: 'secondary',
  en_ejecucion: 'default',
  pausado: 'warning',
  finalizado: 'success',
  pendiente: 'secondary',
  en_progreso: 'default',
  completada: 'success',
  pausada: 'warning',
}

const estadoLabels: Record<string, string> = {
  planificacion: 'Planificacion',
  en_ejecucion: 'En Ejecucion',
  pausado: 'Pausado',
  finalizado: 'Finalizado',
  pendiente: 'Pendiente',
  en_progreso: 'En Progreso',
  completada: 'Completada',
  pausada: 'Pausada',
}

function getDateRange(range: string): { desde: string; hasta: string } {
  const today = new Date()
  const hasta = today.toISOString().split('T')[0]

  switch (range) {
    case 'semana': {
      const desde = new Date(today)
      desde.setDate(desde.getDate() - 7)
      return { desde: desde.toISOString().split('T')[0], hasta }
    }
    case 'mes': {
      const desde = new Date(today)
      desde.setMonth(desde.getMonth() - 1)
      return { desde: desde.toISOString().split('T')[0], hasta }
    }
    case 'trimestre': {
      const desde = new Date(today)
      desde.setMonth(desde.getMonth() - 3)
      return { desde: desde.toISOString().split('T')[0], hasta }
    }
    case 'anio': {
      const desde = new Date(today.getFullYear(), 0, 1)
      return { desde: desde.toISOString().split('T')[0], hasta }
    }
    default:
      return { desde: hasta, hasta }
  }
}

export function ReportesPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const printRef = useRef<HTMLDivElement>(null)

  const [selectedProyectoId, setSelectedProyectoId] = useState<string>('')
  const [rangoFecha, setRangoFecha] = useState<string>('mes')
  const [fechaDesde, setFechaDesde] = useState<string>(() => getDateRange('mes').desde)
  const [fechaHasta, setFechaHasta] = useState<string>(() => getDateRange('mes').hasta)
  const [expandedEtapas, setExpandedEtapas] = useState<Set<string>>(new Set())

  const { data: proyectos, isLoading: isLoadingProyectos } = useQuery({
    queryKey: ['proyectos-list'],
    queryFn: () => proyectosService.getProyectos(),
  })

  const {
    data: datosReporte,
    isLoading: isLoadingReporte,
    refetch: refetchReporte,
  } = useQuery({
    queryKey: ['reporte', selectedProyectoId, fechaDesde, fechaHasta],
    queryFn: () => reportesService.getDatosReporte(selectedProyectoId, fechaDesde, fechaHasta),
    enabled: !!selectedProyectoId && !!fechaDesde && !!fechaHasta,
  })

  const generarReporteMutation = useMutation({
    mutationFn: () => reportesService.generarReporte(selectedProyectoId, fechaDesde, fechaHasta),
    onSuccess: () => {
      toast({ title: 'Reporte generado exitosamente' })
      queryClient.invalidateQueries({ queryKey: ['reportes', selectedProyectoId] })
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al generar reporte' })
    },
  })

  const descargarPDFMutation = useMutation({
    mutationFn: () => reportesService.descargarPDF(selectedProyectoId, fechaDesde, fechaHasta),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `reporte_${datosReporte?.proyecto.nombre.replace(/\s+/g, '_')}_${fechaDesde}_${fechaHasta}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast({ title: 'PDF descargado exitosamente' })
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al descargar PDF. Verifique que WeasyPrint este instalado.' })
    },
  })

  const descargarExcelMutation = useMutation({
    mutationFn: () => reportesService.descargarExcel(selectedProyectoId, fechaDesde, fechaHasta),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `reporte_${datosReporte?.proyecto.nombre.replace(/\s+/g, '_')}_${fechaDesde}_${fechaHasta}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast({ title: 'Excel descargado exitosamente' })
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al descargar Excel. Verifique que openpyxl este instalado.' })
    },
  })

  const handleRangoChange = (range: string) => {
    setRangoFecha(range)
    if (range !== 'personalizado') {
      const { desde, hasta } = getDateRange(range)
      setFechaDesde(desde)
      setFechaHasta(hasta)
    }
  }

  const handlePrint = () => {
    window.print()
  }

  const toggleEtapa = (etapaId: string) => {
    setExpandedEtapas((prev) => {
      const next = new Set(prev)
      if (next.has(etapaId)) {
        next.delete(etapaId)
      } else {
        next.add(etapaId)
      }
      return next
    })
  }

  const expandAll = () => {
    if (datosReporte?.etapas) {
      setExpandedEtapas(new Set(datosReporte.etapas.map((e) => e.id)))
    }
  }

  const collapseAll = () => {
    setExpandedEtapas(new Set())
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileBarChart className="h-6 w-6" />
            Reportes de Proyecto
          </h1>
          <p className="text-muted-foreground">
            Genera reportes detallados de avance, costos y recursos
          </p>
        </div>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Configurar Reporte</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            <div className="space-y-2 lg:col-span-2">
              <label className="text-sm font-medium">Proyecto</label>
              <Select value={selectedProyectoId} onValueChange={setSelectedProyectoId}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar proyecto" />
                </SelectTrigger>
                <SelectContent>
                  {proyectos?.map((proyecto) => (
                    <SelectItem key={proyecto.id} value={proyecto.id}>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        {proyecto.nombre}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Periodo</label>
              <Select value={rangoFecha} onValueChange={handleRangoChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="semana">Ultima semana</SelectItem>
                  <SelectItem value="mes">Ultimo mes</SelectItem>
                  <SelectItem value="trimestre">Ultimo trimestre</SelectItem>
                  <SelectItem value="anio">Este ano</SelectItem>
                  <SelectItem value="personalizado">Personalizado</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Desde</label>
              <Input
                type="date"
                value={fechaDesde}
                onChange={(e) => {
                  setFechaDesde(e.target.value)
                  setRangoFecha('personalizado')
                }}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Hasta</label>
              <Input
                type="date"
                value={fechaHasta}
                onChange={(e) => {
                  setFechaHasta(e.target.value)
                  setRangoFecha('personalizado')
                }}
              />
            </div>
          </div>

          {selectedProyectoId && (
            <div className="flex flex-wrap gap-2 mt-4">
              <Button onClick={() => refetchReporte()}>
                <Eye className="h-4 w-4 mr-2" />
                Ver Reporte
              </Button>
              <Button variant="outline" onClick={handlePrint} disabled={!datosReporte}>
                <Printer className="h-4 w-4 mr-2" />
                Imprimir
              </Button>
              <Button
                variant="outline"
                onClick={() => descargarPDFMutation.mutate()}
                disabled={!datosReporte || descargarPDFMutation.isPending}
              >
                {descargarPDFMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4 mr-2" />
                )}
                Descargar PDF
              </Button>
              <Button
                variant="outline"
                onClick={() => descargarExcelMutation.mutate()}
                disabled={!datosReporte || descargarExcelMutation.isPending}
              >
                {descargarExcelMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <FileSpreadsheet className="h-4 w-4 mr-2" />
                )}
                Descargar Excel
              </Button>
              <Button
                variant="outline"
                onClick={() => generarReporteMutation.mutate()}
                disabled={!datosReporte || generarReporteMutation.isPending}
              >
                {generarReporteMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Guardar Reporte
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Contenido del Reporte */}
      {!selectedProyectoId ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileBarChart className="h-16 w-16 mx-auto text-muted-foreground mb-4 opacity-50" />
            <p className="text-muted-foreground">
              Selecciona un proyecto para generar el reporte
            </p>
          </CardContent>
        </Card>
      ) : isLoadingReporte ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : datosReporte ? (
        <div ref={printRef} className="space-y-6 print:space-y-4">
          {/* Cabecera del Reporte */}
          <Card className="print:shadow-none print:border-2">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-xl">{datosReporte.proyecto.nombre}</CardTitle>
                  <CardDescription className="mt-1">
                    {datosReporte.proyecto.ubicacion && (
                      <span className="block">{datosReporte.proyecto.ubicacion}</span>
                    )}
                    <span className="block mt-1">
                      Periodo: {formatDate(datosReporte.periodo.desde)} -{' '}
                      {formatDate(datosReporte.periodo.hasta)}
                    </span>
                  </CardDescription>
                </div>
                <Badge variant={estadoColors[datosReporte.proyecto.estado] as any}>
                  {estadoLabels[datosReporte.proyecto.estado]}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-sm text-muted-foreground">Avance General</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Progress value={datosReporte.proyecto.porcentaje_avance} className="flex-1" />
                    <span className="font-bold">
                      {datosReporte.proyecto.porcentaje_avance.toFixed(0)}%
                    </span>
                  </div>
                </div>
                {datosReporte.proyecto.cliente && (
                  <div>
                    <p className="text-sm text-muted-foreground">Cliente</p>
                    <p className="font-medium">{datosReporte.proyecto.cliente.nombre}</p>
                  </div>
                )}
                {datosReporte.proyecto.monto_contratado && (
                  <div>
                    <p className="text-sm text-muted-foreground">Monto Contratado</p>
                    <p className="font-bold text-lg">
                      {formatCurrency(datosReporte.proyecto.monto_contratado)}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Tarjetas de Resumen */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 print:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Etapas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {datosReporte.resumen.etapas_completadas}/{datosReporte.resumen.total_etapas}
                </div>
                <p className="text-xs text-muted-foreground">completadas</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Package className="h-4 w-4 text-blue-500" />
                  Materiales
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {datosReporte.resumen.total_materiales_asignados}
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatCurrency(datosReporte.resumen.costo_materiales)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Receipt className="h-4 w-4 text-orange-500" />
                  Gastos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(datosReporte.resumen.total_gastos)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {Object.keys(datosReporte.resumen.gastos_por_categoria).length} categorias
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-purple-500" />
                  Costo Total
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(
                    datosReporte.resumen.costo_materiales + datosReporte.resumen.total_gastos
                  )}
                </div>
                <p className="text-xs text-muted-foreground">materiales + gastos</p>
              </CardContent>
            </Card>
          </div>

          {/* Timeline Visual */}
          {datosReporte.etapas.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Cronograma de Etapas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Timeline
                  items={datosReporte.etapas.map((etapa) => ({
                    id: etapa.id,
                    nombre: etapa.nombre,
                    fecha_inicio_est: etapa.fecha_inicio_est,
                    fecha_fin_est: etapa.fecha_fin_est,
                    fecha_inicio_real: etapa.fecha_inicio_real,
                    fecha_fin_real: etapa.fecha_fin_real,
                    porcentaje_avance: etapa.porcentaje_avance,
                    estado: etapa.estado,
                  }))}
                  fechaInicio={datosReporte.proyecto.fecha_inicio}
                  fechaFin={datosReporte.proyecto.fecha_fin_estimada}
                />
              </CardContent>
            </Card>
          )}

          {/* Tabs de Detalle */}
          <Tabs defaultValue="etapas" className="print:hidden">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="etapas">
                <CheckCircle2 className="h-4 w-4 mr-1" />
                Etapas
              </TabsTrigger>
              <TabsTrigger value="materiales">
                <Package className="h-4 w-4 mr-1" />
                Materiales
              </TabsTrigger>
              <TabsTrigger value="equipos">
                <Wrench className="h-4 w-4 mr-1" />
                Equipos
              </TabsTrigger>
              <TabsTrigger value="gastos">
                <Receipt className="h-4 w-4 mr-1" />
                Gastos
              </TabsTrigger>
              <TabsTrigger value="fotos">
                <ImageIcon className="h-4 w-4 mr-1" />
                Fotos
              </TabsTrigger>
            </TabsList>

            <TabsContent value="etapas" className="space-y-4">
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={expandAll}>
                  Expandir todo
                </Button>
                <Button variant="outline" size="sm" onClick={collapseAll}>
                  Colapsar todo
                </Button>
              </div>

              {datosReporte.etapas.map((etapa) => (
                <Collapsible
                  key={etapa.id}
                  open={expandedEtapas.has(etapa.id)}
                  onOpenChange={() => toggleEtapa(etapa.id)}
                >
                  <Card>
                    <CollapsibleTrigger asChild>
                      <CardHeader className="cursor-pointer hover:bg-muted/50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {expandedEtapas.has(etapa.id) ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : (
                              <ChevronDown className="h-4 w-4" />
                            )}
                            <div>
                              <CardTitle className="text-base">{etapa.nombre}</CardTitle>
                              {etapa.descripcion && (
                                <CardDescription>{etapa.descripcion}</CardDescription>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <Badge variant={estadoColors[etapa.estado] as any}>
                              {estadoLabels[etapa.estado]}
                            </Badge>
                            <div className="text-right">
                              <span className="font-bold">{etapa.porcentaje_avance.toFixed(0)}%</span>
                              <Progress
                                value={etapa.porcentaje_avance}
                                className="w-24 h-2 mt-1"
                              />
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <CardContent>
                        <div className="grid gap-4 md:grid-cols-4 mb-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Inicio Est:</span>{' '}
                            {etapa.fecha_inicio_est ? formatDate(etapa.fecha_inicio_est) : '-'}
                          </div>
                          <div>
                            <span className="text-muted-foreground">Fin Est:</span>{' '}
                            {etapa.fecha_fin_est ? formatDate(etapa.fecha_fin_est) : '-'}
                          </div>
                          <div>
                            <span className="text-muted-foreground">Inicio Real:</span>{' '}
                            {etapa.fecha_inicio_real ? formatDate(etapa.fecha_inicio_real) : '-'}
                          </div>
                          <div>
                            <span className="text-muted-foreground">Fin Real:</span>{' '}
                            {etapa.fecha_fin_real ? formatDate(etapa.fecha_fin_real) : '-'}
                          </div>
                        </div>

                        {etapa.items.length > 0 && (
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Item</TableHead>
                                <TableHead>Unidad</TableHead>
                                <TableHead className="text-right">Estimado</TableHead>
                                <TableHead className="text-right">Ejecutado</TableHead>
                                <TableHead className="text-right">Avance</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {etapa.items.map((item) => (
                                <TableRow key={item.id}>
                                  <TableCell className="font-medium">{item.nombre}</TableCell>
                                  <TableCell>{item.unidad}</TableCell>
                                  <TableCell className="text-right">
                                    {item.cantidad_estimada}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    {item.cantidad_ejecutada}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    <div className="flex items-center justify-end gap-2">
                                      <Progress value={item.porcentaje} className="w-16 h-2" />
                                      <span className="text-sm">{item.porcentaje}%</span>
                                    </div>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        )}
                      </CardContent>
                    </CollapsibleContent>
                  </Card>
                </Collapsible>
              ))}
            </TabsContent>

            <TabsContent value="materiales">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Materiales Utilizados ({datosReporte.materiales.length})
                  </CardTitle>
                  <CardDescription>
                    Total: {formatCurrency(datosReporte.resumen.costo_materiales)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {datosReporte.materiales.length === 0 ? (
                    <p className="text-center text-muted-foreground py-8">
                      No hay materiales registrados en este periodo
                    </p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Material</TableHead>
                          <TableHead>Cantidad</TableHead>
                          <TableHead>Etapa</TableHead>
                          <TableHead>Fecha</TableHead>
                          <TableHead className="text-right">Costo Est.</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {datosReporte.materiales.map((material, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">{material.nombre}</TableCell>
                            <TableCell>
                              {material.cantidad} {material.unidad}
                            </TableCell>
                            <TableCell>{material.etapa}</TableCell>
                            <TableCell>{formatDate(material.fecha)}</TableCell>
                            <TableCell className="text-right">
                              {material.costo_estimado
                                ? formatCurrency(material.costo_estimado)
                                : '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="equipos">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Equipos Utilizados ({datosReporte.equipos.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {datosReporte.equipos.length === 0 ? (
                    <p className="text-center text-muted-foreground py-8">
                      No hay equipos registrados en este periodo
                    </p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Equipo</TableHead>
                          <TableHead>Tipo</TableHead>
                          <TableHead>Marca/Modelo</TableHead>
                          <TableHead>Asignado</TableHead>
                          <TableHead>Devuelto</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {datosReporte.equipos.map((equipo, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">{equipo.nombre}</TableCell>
                            <TableCell>{equipo.tipo}</TableCell>
                            <TableCell>
                              {equipo.marca} {equipo.modelo}
                            </TableCell>
                            <TableCell>{formatDate(equipo.fecha_asignacion)}</TableCell>
                            <TableCell>
                              {equipo.fecha_devolucion_real
                                ? formatDate(equipo.fecha_devolucion_real)
                                : '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="gastos">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Gastos del Periodo ({datosReporte.gastos.length})
                  </CardTitle>
                  <CardDescription>
                    Total: {formatCurrency(datosReporte.resumen.total_gastos)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Resumen por categoria */}
                  {Object.keys(datosReporte.resumen.gastos_por_categoria).length > 0 && (
                    <div className="mb-6">
                      <h4 className="font-medium mb-3">Resumen por Categoria</h4>
                      <div className="grid gap-2 md:grid-cols-3">
                        {Object.entries(datosReporte.resumen.gastos_por_categoria).map(
                          ([categoria, monto]) => (
                            <div
                              key={categoria}
                              className="flex justify-between p-3 bg-muted rounded-md"
                            >
                              <span>{categoria}</span>
                              <span className="font-medium">{formatCurrency(monto)}</span>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {datosReporte.gastos.length === 0 ? (
                    <p className="text-center text-muted-foreground py-8">
                      No hay gastos registrados en este periodo
                    </p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Fecha</TableHead>
                          <TableHead>Descripcion</TableHead>
                          <TableHead>Categoria</TableHead>
                          <TableHead className="text-right">Monto</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {datosReporte.gastos.map((gasto) => (
                          <TableRow key={gasto.id}>
                            <TableCell>{formatDate(gasto.fecha)}</TableCell>
                            <TableCell className="font-medium">{gasto.descripcion}</TableCell>
                            <TableCell>
                              <Badge variant="outline">{gasto.categoria}</Badge>
                            </TableCell>
                            <TableCell className="text-right font-medium">
                              {formatCurrency(gasto.monto)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="fotos">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Galeria de Fotos ({datosReporte.fotos.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {datosReporte.fotos.length === 0 ? (
                    <p className="text-center text-muted-foreground py-8">
                      No hay fotos registradas en este periodo
                    </p>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                      {datosReporte.fotos.map((foto) => (
                        <div
                          key={foto.id}
                          className="relative aspect-square rounded-lg overflow-hidden border"
                        >
                          <img
                            src={foto.thumbnail_url || foto.url}
                            alt={foto.descripcion || 'Foto'}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1">
                            <p className="truncate">{foto.etapa}</p>
                            <p className="opacity-75">{formatDate(foto.fecha)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Version para imprimir */}
          <div className="hidden print:block space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Detalle de Etapas</CardTitle>
              </CardHeader>
              <CardContent>
                {datosReporte.etapas.map((etapa) => (
                  <div key={etapa.id} className="mb-4 border-b pb-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">{etapa.nombre}</h4>
                      <span>{etapa.porcentaje_avance.toFixed(0)}%</span>
                    </div>
                    {etapa.items.length > 0 && (
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-1">Item</th>
                            <th className="text-right py-1">Est.</th>
                            <th className="text-right py-1">Ejec.</th>
                            <th className="text-right py-1">%</th>
                          </tr>
                        </thead>
                        <tbody>
                          {etapa.items.map((item) => (
                            <tr key={item.id}>
                              <td className="py-1">{item.nombre}</td>
                              <td className="text-right">{item.cantidad_estimada}</td>
                              <td className="text-right">{item.cantidad_ejecutada}</td>
                              <td className="text-right">{item.porcentaje}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  )
}

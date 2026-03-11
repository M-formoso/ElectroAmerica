import { useState, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  FileText,
  Download,
  Calendar,
  Search,
  Building2,
  Package,
  Wrench,
  DollarSign,
  Image as ImageIcon,
  CheckCircle,
  Clock,
  TrendingUp,
  Share2,
  Printer,
  ChevronDown,
  ChevronRight,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { proyectosService } from '@/services/proyectos'
import { reportesService, type DatosReporte } from '@/services/reportes'
import { formatDate, formatCurrency } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

const estadoColors: Record<string, string> = {
  pendiente: 'secondary',
  en_progreso: 'default',
  completada: 'success',
  pausada: 'warning',
  planificacion: 'secondary',
  en_ejecucion: 'default',
  pausado: 'warning',
  finalizado: 'success',
}

const estadoLabels: Record<string, string> = {
  pendiente: 'Pendiente',
  en_progreso: 'En Progreso',
  completada: 'Completada',
  pausada: 'Pausada',
  planificacion: 'Planificación',
  en_ejecucion: 'En Ejecución',
  pausado: 'Pausado',
  finalizado: 'Finalizado',
}

export function ReportesPage() {
  const { toast } = useToast()
  const printRef = useRef<HTMLDivElement>(null)

  // Estado para filtros
  const [selectedProyecto, setSelectedProyecto] = useState<string>('')
  const [fechaDesde, setFechaDesde] = useState<string>(() => {
    const date = new Date()
    date.setDate(date.getDate() - 7)
    return date.toISOString().split('T')[0]
  })
  const [fechaHasta, setFechaHasta] = useState<string>(() => {
    return new Date().toISOString().split('T')[0]
  })
  const [etapasAbiertas, setEtapasAbiertas] = useState<string[]>([])

  // Queries
  const { data: proyectos, isLoading: loadingProyectos } = useQuery({
    queryKey: ['proyectos'],
    queryFn: () => proyectosService.getProyectos(),
  })

  const { data: datosReporte, isLoading: loadingReporte, refetch: refetchReporte } = useQuery({
    queryKey: ['reporte', selectedProyecto, fechaDesde, fechaHasta],
    queryFn: () => reportesService.getDatosReporte(selectedProyecto, fechaDesde, fechaHasta),
    enabled: !!selectedProyecto && !!fechaDesde && !!fechaHasta,
  })

  const toggleEtapa = (etapaId: string) => {
    setEtapasAbiertas((prev) =>
      prev.includes(etapaId)
        ? prev.filter((id) => id !== etapaId)
        : [...prev, etapaId]
    )
  }

  const handlePrint = () => {
    window.print()
  }

  const handleExportPDF = () => {
    toast({ title: 'Generando PDF...', description: 'Esta función estará disponible próximamente' })
  }

  const handleExportExcel = () => {
    toast({ title: 'Generando Excel...', description: 'Esta función estará disponible próximamente' })
  }

  const setPresetDates = (preset: string) => {
    const today = new Date()
    let desde = new Date()

    switch (preset) {
      case 'semana':
        desde.setDate(today.getDate() - 7)
        break
      case 'quincena':
        desde.setDate(today.getDate() - 15)
        break
      case 'mes':
        desde.setMonth(today.getMonth() - 1)
        break
      case 'trimestre':
        desde.setMonth(today.getMonth() - 3)
        break
    }

    setFechaDesde(desde.toISOString().split('T')[0])
    setFechaHasta(today.toISOString().split('T')[0])
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="h-6 w-6" />
            Reportes
          </h1>
          <p className="text-muted-foreground">
            Genera reportes detallados de los proyectos
          </p>
        </div>
        {datosReporte && (
          <div className="flex gap-2 print:hidden">
            <Button variant="outline" onClick={handlePrint}>
              <Printer className="h-4 w-4 mr-2" />
              Imprimir
            </Button>
            <Button variant="outline" onClick={handleExportPDF}>
              <Download className="h-4 w-4 mr-2" />
              PDF
            </Button>
            <Button variant="outline" onClick={handleExportExcel}>
              <Download className="h-4 w-4 mr-2" />
              Excel
            </Button>
          </div>
        )}
      </div>

      {/* Filtros */}
      <Card className="print:hidden">
        <CardHeader>
          <CardTitle className="text-lg">Configurar Reporte</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <Label>Proyecto</Label>
              <Select value={selectedProyecto} onValueChange={setSelectedProyecto}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar proyecto" />
                </SelectTrigger>
                <SelectContent>
                  {proyectos?.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Desde</Label>
              <Input
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Hasta</Label>
              <Input
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Período predefinido</Label>
              <Select onValueChange={setPresetDates}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="semana">Última semana</SelectItem>
                  <SelectItem value="quincena">Últimos 15 días</SelectItem>
                  <SelectItem value="mes">Último mes</SelectItem>
                  <SelectItem value="trimestre">Último trimestre</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading */}
      {loadingReporte && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Sin selección */}
      {!selectedProyecto && !loadingReporte && (
        <Card>
          <CardContent className="py-12 text-center">
            <Building2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Selecciona un proyecto para generar el reporte
            </p>
          </CardContent>
        </Card>
      )}

      {/* Contenido del reporte */}
      {datosReporte && (
        <div ref={printRef} className="space-y-6 print:space-y-4">
          {/* Encabezado del reporte */}
          <Card className="border-2">
            <CardHeader className="bg-muted/50">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-2xl">{datosReporte.proyecto.nombre}</CardTitle>
                  <CardDescription className="text-base mt-1">
                    Reporte del {formatDate(datosReporte.periodo.desde)} al {formatDate(datosReporte.periodo.hasta)}
                  </CardDescription>
                </div>
                <Badge variant={estadoColors[datosReporte.proyecto.estado] as any} className="text-sm">
                  {estadoLabels[datosReporte.proyecto.estado]}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-3">
                  {datosReporte.proyecto.ubicacion && (
                    <p className="text-sm">
                      <span className="font-medium">Ubicación:</span> {datosReporte.proyecto.ubicacion}
                    </p>
                  )}
                  {datosReporte.proyecto.fecha_inicio && (
                    <p className="text-sm">
                      <span className="font-medium">Fecha inicio:</span> {formatDate(datosReporte.proyecto.fecha_inicio)}
                    </p>
                  )}
                  {datosReporte.proyecto.fecha_fin_estimada && (
                    <p className="text-sm">
                      <span className="font-medium">Fecha fin estimada:</span> {formatDate(datosReporte.proyecto.fecha_fin_estimada)}
                    </p>
                  )}
                  {datosReporte.proyecto.monto_contratado && (
                    <p className="text-sm">
                      <span className="font-medium">Monto contratado:</span> {formatCurrency(datosReporte.proyecto.monto_contratado)}
                    </p>
                  )}
                </div>
                <div className="space-y-3">
                  {datosReporte.proyecto.cliente && (
                    <div>
                      <p className="text-sm font-medium">Cliente:</p>
                      <p className="text-sm text-muted-foreground">{datosReporte.proyecto.cliente.nombre}</p>
                      <p className="text-sm text-muted-foreground">{datosReporte.proyecto.cliente.email}</p>
                    </div>
                  )}
                  {datosReporte.proyecto.supervisor && (
                    <div>
                      <p className="text-sm font-medium">Supervisor:</p>
                      <p className="text-sm text-muted-foreground">{datosReporte.proyecto.supervisor.nombre}</p>
                    </div>
                  )}
                </div>
              </div>

              <Separator className="my-6" />

              {/* Avance general */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Avance General del Proyecto</span>
                  <span className="text-2xl font-bold">
                    {datosReporte.proyecto.porcentaje_avance.toFixed(0)}%
                  </span>
                </div>
                <Progress value={datosReporte.proyecto.porcentaje_avance} className="h-3" />
              </div>
            </CardContent>
          </Card>

          {/* Resumen KPIs */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
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
                <div className="text-2xl font-bold">{datosReporte.resumen.total_materiales_asignados}</div>
                <p className="text-xs text-muted-foreground">
                  asignados • {formatCurrency(datosReporte.resumen.costo_materiales)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Wrench className="h-4 w-4 text-orange-500" />
                  Equipos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{datosReporte.resumen.total_equipos_usados}</div>
                <p className="text-xs text-muted-foreground">utilizados en el período</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-red-500" />
                  Gastos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(datosReporte.resumen.total_gastos)}</div>
                <p className="text-xs text-muted-foreground">en el período</p>
              </CardContent>
            </Card>
          </div>

          {/* Tabs de contenido */}
          <Tabs defaultValue="etapas" className="print:block">
            <TabsList className="print:hidden">
              <TabsTrigger value="etapas">Etapas e Ítems</TabsTrigger>
              <TabsTrigger value="materiales">Materiales</TabsTrigger>
              <TabsTrigger value="equipos">Equipos</TabsTrigger>
              <TabsTrigger value="gastos">Gastos</TabsTrigger>
              <TabsTrigger value="fotos">Fotos</TabsTrigger>
            </TabsList>

            {/* Etapas */}
            <TabsContent value="etapas" className="print:block print:mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Etapas del Proyecto</CardTitle>
                  <CardDescription>Estado y avance de cada etapa con sus ítems de trabajo</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {datosReporte.etapas.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">No hay etapas definidas</p>
                  ) : (
                    datosReporte.etapas.map((etapa) => (
                      <Collapsible
                        key={etapa.id}
                        open={etapasAbiertas.includes(etapa.id)}
                        onOpenChange={() => toggleEtapa(etapa.id)}
                      >
                        <div className="border rounded-lg">
                          <CollapsibleTrigger className="w-full">
                            <div className="p-4 flex items-center justify-between hover:bg-muted/50">
                              <div className="flex items-center gap-3">
                                {etapasAbiertas.includes(etapa.id) ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronRight className="h-4 w-4" />
                                )}
                                <div className="text-left">
                                  <p className="font-medium">{etapa.nombre}</p>
                                  {etapa.descripcion && (
                                    <p className="text-sm text-muted-foreground">{etapa.descripcion}</p>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-4">
                                <Badge variant={estadoColors[etapa.estado] as any}>
                                  {estadoLabels[etapa.estado]}
                                </Badge>
                                <div className="text-right">
                                  <p className="font-bold">{etapa.porcentaje_avance.toFixed(0)}%</p>
                                  <p className="text-xs text-muted-foreground">
                                    {etapa.items_total} ítems
                                  </p>
                                </div>
                              </div>
                            </div>
                          </CollapsibleTrigger>
                          <CollapsibleContent>
                            <div className="border-t p-4 bg-muted/20">
                              {etapa.items.length === 0 ? (
                                <p className="text-sm text-muted-foreground">Sin ítems de trabajo</p>
                              ) : (
                                <Table>
                                  <TableHeader>
                                    <TableRow>
                                      <TableHead>Ítem</TableHead>
                                      <TableHead className="text-right">Estimado</TableHead>
                                      <TableHead className="text-right">Ejecutado</TableHead>
                                      <TableHead className="text-right">Avance</TableHead>
                                    </TableRow>
                                  </TableHeader>
                                  <TableBody>
                                    {etapa.items.map((item) => (
                                      <TableRow key={item.id}>
                                        <TableCell>
                                          <p className="font-medium">{item.nombre}</p>
                                          {item.descripcion && (
                                            <p className="text-xs text-muted-foreground">{item.descripcion}</p>
                                          )}
                                        </TableCell>
                                        <TableCell className="text-right">
                                          {item.cantidad_estimada} {item.unidad}
                                        </TableCell>
                                        <TableCell className="text-right">
                                          {item.cantidad_ejecutada} {item.unidad}
                                        </TableCell>
                                        <TableCell className="text-right">
                                          <div className="flex items-center justify-end gap-2">
                                            <Progress value={item.porcentaje} className="w-16 h-2" />
                                            <span className="text-sm font-medium w-12">
                                              {item.porcentaje.toFixed(0)}%
                                            </span>
                                          </div>
                                        </TableCell>
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                              )}
                            </div>
                          </CollapsibleContent>
                        </div>
                      </Collapsible>
                    ))
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Materiales */}
            <TabsContent value="materiales" className="print:block print:mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Materiales Asignados</CardTitle>
                  <CardDescription>
                    Materiales utilizados en el período • Total: {formatCurrency(datosReporte.resumen.costo_materiales)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {datosReporte.materiales.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">
                      No se asignaron materiales en este período
                    </p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Material</TableHead>
                          <TableHead>Etapa</TableHead>
                          <TableHead className="text-right">Cantidad</TableHead>
                          <TableHead className="text-right">Costo Est.</TableHead>
                          <TableHead>Fecha</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {datosReporte.materiales.map((m, idx) => (
                          <TableRow key={idx}>
                            <TableCell>
                              <p className="font-medium">{m.nombre}</p>
                              <p className="text-xs text-muted-foreground">{m.codigo}</p>
                            </TableCell>
                            <TableCell>{m.etapa}</TableCell>
                            <TableCell className="text-right">
                              {m.cantidad} {m.unidad}
                            </TableCell>
                            <TableCell className="text-right">
                              {m.costo_estimado ? formatCurrency(m.costo_estimado) : '-'}
                            </TableCell>
                            <TableCell>{formatDate(m.fecha)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Equipos */}
            <TabsContent value="equipos" className="print:block print:mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Equipos Utilizados</CardTitle>
                  <CardDescription>
                    Equipos asignados al proyecto en el período
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {datosReporte.equipos.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">
                      No se utilizaron equipos en este período
                    </p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Equipo</TableHead>
                          <TableHead>Tipo</TableHead>
                          <TableHead>Asignación</TableHead>
                          <TableHead>Devolución</TableHead>
                          <TableHead>Notas</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {datosReporte.equipos.map((e, idx) => (
                          <TableRow key={idx}>
                            <TableCell>
                              <p className="font-medium">{e.nombre}</p>
                              <p className="text-xs text-muted-foreground">
                                {e.marca} {e.modelo} • {e.codigo}
                              </p>
                            </TableCell>
                            <TableCell className="capitalize">{e.tipo}</TableCell>
                            <TableCell>{formatDate(e.fecha_asignacion)}</TableCell>
                            <TableCell>
                              {e.fecha_devolucion_real
                                ? formatDate(e.fecha_devolucion_real)
                                : e.fecha_devolucion_est
                                ? `Est: ${formatDate(e.fecha_devolucion_est)}`
                                : 'En uso'}
                            </TableCell>
                            <TableCell className="max-w-[200px] truncate">
                              {e.notas || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Gastos */}
            <TabsContent value="gastos" className="print:block print:mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Gastos del Período</CardTitle>
                  <CardDescription>
                    Total: {formatCurrency(datosReporte.resumen.total_gastos)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Resumen por categoría */}
                  {Object.keys(datosReporte.resumen.gastos_por_categoria).length > 0 && (
                    <div className="grid gap-2 md:grid-cols-4">
                      {Object.entries(datosReporte.resumen.gastos_por_categoria).map(([cat, monto]) => (
                        <div key={cat} className="p-3 bg-muted rounded-lg">
                          <p className="text-sm font-medium">{cat}</p>
                          <p className="text-lg font-bold">{formatCurrency(monto)}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {datosReporte.gastos.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">
                      No se registraron gastos en este período
                    </p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Fecha</TableHead>
                          <TableHead>Categoría</TableHead>
                          <TableHead>Descripción</TableHead>
                          <TableHead className="text-right">Monto</TableHead>
                          <TableHead>Comprobante</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {datosReporte.gastos.map((g) => (
                          <TableRow key={g.id}>
                            <TableCell>{formatDate(g.fecha)}</TableCell>
                            <TableCell>
                              <Badge variant="outline">{g.categoria}</Badge>
                            </TableCell>
                            <TableCell>{g.descripcion}</TableCell>
                            <TableCell className="text-right font-medium">
                              {formatCurrency(g.monto)}
                            </TableCell>
                            <TableCell>
                              {g.numero_comprobante || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Fotos */}
            <TabsContent value="fotos" className="print:block print:mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ImageIcon className="h-5 w-5" />
                    Fotos del Período
                  </CardTitle>
                  <CardDescription>
                    {datosReporte.resumen.total_fotos} fotos tomadas
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {datosReporte.fotos.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">
                      No se subieron fotos en este período
                    </p>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {datosReporte.fotos.map((foto) => (
                        <div key={foto.id} className="space-y-2">
                          <div className="aspect-square rounded-lg overflow-hidden border">
                            <img
                              src={foto.thumbnail_url || foto.url}
                              alt={foto.descripcion || 'Foto'}
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <div className="text-xs">
                            <p className="font-medium truncate">{foto.etapa}</p>
                            <p className="text-muted-foreground">{formatDate(foto.fecha)}</p>
                            {foto.descripcion && (
                              <p className="text-muted-foreground truncate">{foto.descripcion}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      )}

      {/* Estilos de impresión */}
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          #print-area, #print-area * {
            visibility: visible;
          }
          #print-area {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
          .print\\:hidden {
            display: none !important;
          }
          .print\\:block {
            display: block !important;
          }
        }
      `}</style>
    </div>
  )
}

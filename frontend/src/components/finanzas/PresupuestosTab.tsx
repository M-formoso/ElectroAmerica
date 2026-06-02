import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, Search, BarChart3 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { listasPrecioService } from '@/services/listasPrecio'

const formatARS = (n: number) =>
  new Intl.NumberFormat('es-AR', {
    style: 'currency', currency: 'ARS', maximumFractionDigits: 2,
  }).format(Number(n || 0))

export function PresupuestosTab() {
  const [search, setSearch] = useState('')

  const { data: totales, isLoading } = useQuery({
    queryKey: ['totales-proyectos'],
    queryFn: () => listasPrecioService.getTotalesProyectos(),
  })

  const filtrados = useMemo(() => {
    if (!totales) return []
    const q = search.trim().toLowerCase()
    if (!q) return totales
    return totales.filter(
      (t) =>
        t.proyecto_nombre.toLowerCase().includes(q) ||
        t.cliente_nombre?.toLowerCase().includes(q) ||
        t.lista_precio_nombre?.toLowerCase().includes(q),
    )
  }, [totales, search])

  const totalGlobalPresup = useMemo(
    () => filtrados.reduce((acc, t) => acc + Number(t.total_presupuestado || 0), 0),
    [filtrados],
  )
  const totalGlobalEjec = useMemo(
    () => filtrados.reduce((acc, t) => acc + Number(t.total_ejecutado || 0), 0),
    [filtrados],
  )

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Presupuestos por proyecto</h2>
        <p className="text-sm text-muted-foreground">
          Total presupuestado y ejecutado en base a los precios congelados al cargar cada actividad.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Total presupuestado</p>
            <p className="text-2xl font-bold">{formatARS(totalGlobalPresup)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Total ejecutado</p>
            <p className="text-2xl font-bold text-primary">{formatARS(totalGlobalEjec)}</p>
          </CardContent>
        </Card>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar proyecto, cliente o lista..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : filtrados.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <BarChart3 className="h-10 w-10 mx-auto mb-3 opacity-50" />
            No hay proyectos para mostrar.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Proyecto</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Lista</TableHead>
                <TableHead className="text-center">Actividades</TableHead>
                <TableHead className="text-right">Presupuestado</TableHead>
                <TableHead className="text-right">Ejecutado</TableHead>
                <TableHead className="text-right">% ejec.</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtrados.map((t) => {
                const pct =
                  Number(t.total_presupuestado) > 0
                    ? (Number(t.total_ejecutado) / Number(t.total_presupuestado)) * 100
                    : 0
                return (
                  <TableRow key={t.proyecto_id}>
                    <TableCell>
                      <div className="font-medium text-sm">{t.proyecto_nombre}</div>
                      {t.estado && (
                        <div className="text-xs text-muted-foreground">{t.estado}</div>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">{t.cliente_nombre || '-'}</TableCell>
                    <TableCell>
                      {t.lista_precio_nombre ? (
                        <Badge variant="outline">{t.lista_precio_nombre}</Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">Sin lista</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="secondary">{t.cantidad_actividades}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {formatARS(Number(t.total_presupuestado))}
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm text-primary">
                      {formatARS(Number(t.total_ejecutado))}
                    </TableCell>
                    <TableCell className="text-right text-sm">{pct.toFixed(1)}%</TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Plus,
  Search,
  Filter,
  Receipt,
  Calendar,
  MoreVertical,
  Edit,
  Trash2,
  FileText,
  TrendingUp,
  Download,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Label } from '@/components/ui/label'
import { gastosService } from '@/services/gastos'
import { proyectosService } from '@/services/proyectos'
import { formatCurrency, formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin } from '@/store/auth'
import type { Gasto, CategoriaGasto } from '@/types'

const gastoSchema = z.object({
  descripcion: z.string().min(1, 'Descripción requerida'),
  monto: z.number().min(0.01, 'Monto debe ser mayor a 0'),
  fecha: z.string().min(1, 'Fecha requerida'),
  proyecto_id: z.string().optional(),
  categoria_id: z.string().optional(),
  numero_comprobante: z.string().optional(),
})

type GastoForm = z.infer<typeof gastoSchema>

export function GastosPage() {
  const [search, setSearch] = useState('')
  const [proyectoFilter, setProyectoFilter] = useState<string>('todos')
  const [categoriaFilter, setCategoriaFilter] = useState<string>('todos')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  const { data: gastos, isLoading } = useQuery({
    queryKey: ['gastos', proyectoFilter, categoriaFilter],
    queryFn: () => gastosService.getGastos({
      proyecto_id: proyectoFilter !== 'todos' ? proyectoFilter : undefined,
      categoria_id: categoriaFilter !== 'todos' ? categoriaFilter : undefined,
    }),
  })

  const { data: categorias } = useQuery({
    queryKey: ['categorias-gasto'],
    queryFn: gastosService.getCategorias,
  })

  const { data: proyectos } = useQuery({
    queryKey: ['proyectos'],
    queryFn: () => proyectosService.getProyectos(),
  })

  const createMutation = useMutation({
    mutationFn: gastosService.createGasto,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gastos'] })
      toast({ title: 'Gasto registrado correctamente' })
      setIsCreateOpen(false)
      reset()
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al registrar gasto' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: gastosService.deleteGasto,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gastos'] })
      toast({ title: 'Gasto eliminado' })
    },
  })

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<GastoForm>({
    resolver: zodResolver(gastoSchema),
    defaultValues: {
      fecha: new Date().toISOString().split('T')[0],
    },
  })

  const onSubmit = (data: GastoForm) => {
    createMutation.mutate({
      ...data,
      proyecto_id: data.proyecto_id || undefined,
      categoria_id: data.categoria_id || undefined,
    })
  }

  const filteredGastos = gastos?.filter((g) =>
    g.descripcion.toLowerCase().includes(search.toLowerCase())
  )

  const totalGastos = filteredGastos?.reduce((acc, g) => acc + g.monto, 0) || 0

  const gastosPorCategoria = categorias?.map((cat) => ({
    ...cat,
    total: gastos?.filter((g) => g.categoria_id === cat.id).reduce((acc, g) => acc + g.monto, 0) || 0,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Gastos</h1>
          <p className="text-muted-foreground">
            Registro y control de gastos operativos
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Gasto
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Registrado</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalGastos)}</div>
            <p className="text-xs text-muted-foreground">
              {filteredGastos?.length || 0} gastos
            </p>
          </CardContent>
        </Card>
        {gastosPorCategoria?.slice(0, 3).map((cat) => (
          <Card key={cat.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: cat.color || '#gray' }}
                />
                {cat.nombre}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(cat.total)}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar gastos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={proyectoFilter} onValueChange={setProyectoFilter}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Proyecto" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos los proyectos</SelectItem>
            {proyectos?.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={categoriaFilter} onValueChange={setCategoriaFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Categoría" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todas las categorías</SelectItem>
            {categorias?.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fecha</TableHead>
              <TableHead>Descripción</TableHead>
              <TableHead>Categoría</TableHead>
              <TableHead>Proyecto</TableHead>
              <TableHead className="text-right">Monto</TableHead>
              <TableHead className="w-[80px]">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <TableRow key={i}>
                  {[...Array(6)].map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 bg-muted rounded animate-pulse" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : filteredGastos?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  No se encontraron gastos
                </TableCell>
              </TableRow>
            ) : (
              filteredGastos?.map((gasto) => (
                <TableRow key={gasto.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      {formatDate(gasto.fecha)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{gasto.descripcion}</p>
                      {gasto.numero_comprobante && (
                        <p className="text-xs text-muted-foreground">
                          Comp: {gasto.numero_comprobante}
                        </p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {gasto.categoria ? (
                      <Badge
                        variant="outline"
                        style={{ borderColor: gasto.categoria.color }}
                      >
                        {gasto.categoria.nombre}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {gasto.proyecto?.nombre || (
                      <span className="text-muted-foreground">General</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(gasto.monto)}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {gasto.comprobante_url && (
                          <DropdownMenuItem asChild>
                            <a href={gasto.comprobante_url} target="_blank" rel="noopener">
                              <FileText className="h-4 w-4 mr-2" />
                              Ver comprobante
                            </a>
                          </DropdownMenuItem>
                        )}
                        {isAdmin && (
                          <>
                            <DropdownMenuItem>
                              <Edit className="h-4 w-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => deleteMutation.mutate(gasto.id)}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Eliminar
                            </DropdownMenuItem>
                          </>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Create dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar Gasto</DialogTitle>
            <DialogDescription>
              Ingresa los detalles del gasto
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label>Descripción *</Label>
              <Input
                {...register('descripcion')}
                placeholder="Ej: Compra de materiales"
              />
              {errors.descripcion && (
                <p className="text-sm text-destructive">{errors.descripcion.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Monto *</Label>
                <Input
                  type="number"
                  step="0.01"
                  {...register('monto', { valueAsNumber: true })}
                  placeholder="0.00"
                />
                {errors.monto && (
                  <p className="text-sm text-destructive">{errors.monto.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label>Fecha *</Label>
                <Input type="date" {...register('fecha')} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Categoría</Label>
              <Select onValueChange={(v) => setValue('categoria_id', v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar categoría" />
                </SelectTrigger>
                <SelectContent>
                  {categorias?.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      {cat.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Proyecto (opcional)</Label>
              <Select onValueChange={(v) => setValue('proyecto_id', v)}>
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
              <Label>Número de comprobante</Label>
              <Input
                {...register('numero_comprobante')}
                placeholder="Ej: FAC-001-00001234"
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreateOpen(false)}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                Registrar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Pencil, Trash2, Loader2, Search, Save, ListOrdered,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { useToast } from '@/hooks/use-toast'
import {
  listasPrecioService, type ListaPrecio, type PrecioActividadItem,
} from '@/services/listasPrecio'

const formatARS = (n: number) =>
  new Intl.NumberFormat('es-AR', {
    style: 'currency', currency: 'ARS', maximumFractionDigits: 2,
  }).format(Number(n || 0))

export function ListasPrecioTab() {
  const { toast } = useToast()
  const qc = useQueryClient()

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<ListaPrecio | null>(null)
  const [nombre, setNombre] = useState('')
  const [descripcion, setDescripcion] = useState('')

  const [deleting, setDeleting] = useState<ListaPrecio | null>(null)
  const [editingPrecios, setEditingPrecios] = useState<ListaPrecio | null>(null)

  const { data: listas, isLoading } = useQuery({
    queryKey: ['listas-precio'],
    queryFn: () => listasPrecioService.listar(),
  })

  const crearMutation = useMutation({
    mutationFn: () =>
      listasPrecioService.crear({ nombre: nombre.trim(), descripcion: descripcion.trim() || undefined }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['listas-precio'] })
      toast({ title: 'Lista creada' })
      closeForm()
    },
    onError: (e: any) => {
      toast({ variant: 'destructive', title: 'Error', description: e?.response?.data?.detail || '' })
    },
  })

  const actualizarMutation = useMutation({
    mutationFn: () =>
      listasPrecioService.actualizar(editing!.id, {
        nombre: nombre.trim(),
        descripcion: descripcion.trim() || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['listas-precio'] })
      toast({ title: 'Lista actualizada' })
      closeForm()
    },
    onError: (e: any) => {
      toast({ variant: 'destructive', title: 'Error', description: e?.response?.data?.detail || '' })
    },
  })

  const eliminarMutation = useMutation({
    mutationFn: () => listasPrecioService.eliminar(deleting!.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['listas-precio'] })
      toast({ title: 'Lista eliminada' })
      setDeleting(null)
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al eliminar' }),
  })

  const openCreate = () => {
    setEditing(null)
    setNombre('')
    setDescripcion('')
    setFormOpen(true)
  }
  const openEdit = (l: ListaPrecio) => {
    setEditing(l)
    setNombre(l.nombre)
    setDescripcion(l.descripcion || '')
    setFormOpen(true)
  }
  const closeForm = () => {
    setFormOpen(false)
    setEditing(null)
    setNombre('')
    setDescripcion('')
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Listas de precios</h2>
          <p className="text-sm text-muted-foreground">
            Cada proyecto usa una lista al crearse. El precio se congela en cada actividad cargada.
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Nueva lista
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : !listas || listas.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <ListOrdered className="h-10 w-10 mx-auto mb-3 opacity-50" />
            No hay listas de precios cargadas.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {listas.map((l) => (
            <Card key={l.id} className="hover:border-primary/50 transition">
              <CardContent className="p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold truncate">{l.nombre}</h3>
                    {l.descripcion && (
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                        {l.descripcion}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => openEdit(l)}
                      title="Editar nombre"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive"
                      onClick={() => setDeleting(l)}
                      title="Eliminar lista"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <Badge variant="secondary">
                    {l.cantidad_actividades_con_precio} actividades con precio
                  </Badge>
                  <Button size="sm" variant="outline" onClick={() => setEditingPrecios(l)}>
                    Editar precios
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Form crear/editar */}
      <Dialog open={formOpen} onOpenChange={(o) => !o && closeForm()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? 'Editar lista' : 'Nueva lista de precios'}</DialogTitle>
            <DialogDescription>
              {editing
                ? 'Cambia el nombre o descripcion. No afecta los precios cargados.'
                : 'Despues vas a poder cargar el precio de cada actividad de esta lista.'}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              if (nombre.trim().length === 0) {
                toast({ variant: 'destructive', title: 'El nombre es obligatorio' })
                return
              }
              if (editing) actualizarMutation.mutate()
              else crearMutation.mutate()
            }}
            className="space-y-3"
          >
            <div className="space-y-1">
              <Label>Nombre *</Label>
              <Input
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Ej: EMA, MANTELECTRIC, ELECTROAMERICA"
                required
              />
            </div>
            <div className="space-y-1">
              <Label>Descripcion (opcional)</Label>
              <Textarea
                rows={2}
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeForm}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={crearMutation.isPending || actualizarMutation.isPending}
              >
                {(crearMutation.isPending || actualizarMutation.isPending) && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                {editing ? 'Guardar' : 'Crear'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Confirmar eliminar */}
      <Dialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar lista de precios</DialogTitle>
            <DialogDescription>
              Vas a eliminar <strong>{deleting?.nombre}</strong>. Los proyectos que ya
              usan esta lista conservan sus precios congelados, no se ven afectados.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleting(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => eliminarMutation.mutate()}
              disabled={eliminarMutation.isPending}
            >
              {eliminarMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Editor de precios */}
      {editingPrecios && (
        <EditorPreciosDialog
          lista={editingPrecios}
          onClose={() => setEditingPrecios(null)}
        />
      )}
    </div>
  )
}


function EditorPreciosDialog({
  lista,
  onClose,
}: {
  lista: ListaPrecio
  onClose: () => void
}) {
  const { toast } = useToast()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  // map actividad_tipo_id -> precio (string para input)
  const [draft, setDraft] = useState<Record<string, string>>({})

  const { data: detail, isLoading } = useQuery({
    queryKey: ['lista-precio-detail', lista.id],
    queryFn: () => listasPrecioService.obtener(lista.id),
  })

  useEffect(() => {
    if (detail) {
      const initial: Record<string, string> = {}
      detail.items.forEach((it) => {
        initial[it.actividad_tipo_id] = it.precio_unitario
          ? String(Number(it.precio_unitario))
          : ''
      })
      setDraft(initial)
    }
  }, [detail])

  const itemsFiltrados = useMemo<PrecioActividadItem[]>(() => {
    if (!detail) return []
    const q = search.trim().toLowerCase()
    if (!q) return detail.items
    return detail.items.filter(
      (it) =>
        it.actividad_nombre.toLowerCase().includes(q) ||
        it.actividad_codigo?.toLowerCase().includes(q),
    )
  }, [detail, search])

  const guardarMutation = useMutation({
    mutationFn: () => {
      const items = Object.entries(draft)
        .map(([actividad_tipo_id, val]) => ({
          actividad_tipo_id,
          precio_unitario: parseFloat(val) || 0,
        }))
      return listasPrecioService.setearPrecios(lista.id, items)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lista-precio-detail', lista.id] })
      qc.invalidateQueries({ queryKey: ['listas-precio'] })
      toast({ title: 'Precios guardados' })
      onClose()
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al guardar' }),
  })

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Precios — {lista.nombre}</DialogTitle>
          <DialogDescription>
            Carga o actualiza el precio por unidad de cada actividad. Los proyectos ya creados
            mantienen sus precios congelados; los cambios se aplican a futuros proyectos.
          </DialogDescription>
        </DialogHeader>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar actividad..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex-1 overflow-y-auto border rounded-md">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : itemsFiltrados.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-12">
              No hay actividades que coincidan.
            </p>
          ) : (
            <Table>
              <TableHeader className="sticky top-0 bg-background z-10">
                <TableRow>
                  <TableHead>Codigo</TableHead>
                  <TableHead>Actividad</TableHead>
                  <TableHead className="text-right w-40">Precio unitario (ARS)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {itemsFiltrados.map((it) => (
                  <TableRow key={it.actividad_tipo_id}>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {it.actividad_codigo || '-'}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium text-sm">{it.actividad_nombre}</div>
                      {it.actividad_unidad && (
                        <div className="text-xs text-muted-foreground">por {it.actividad_unidad}</div>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={draft[it.actividad_tipo_id] ?? ''}
                        onChange={(e) =>
                          setDraft({ ...draft, [it.actividad_tipo_id]: e.target.value })
                        }
                        placeholder="0"
                        className="text-right"
                      />
                      {Number(draft[it.actividad_tipo_id]) > 0 && (
                        <div className="text-[10px] text-muted-foreground mt-1">
                          {formatARS(parseFloat(draft[it.actividad_tipo_id]) || 0)}
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={() => guardarMutation.mutate()} disabled={guardarMutation.isPending}>
            {guardarMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            Guardar precios
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

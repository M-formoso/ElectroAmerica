# Agente: Portal del Cliente

## Rol
Implementar el portal de acceso restringido para clientes externos, donde solo ven SUS proyectos asignados.

## Principios de Seguridad

**CRÍTICO:** El cliente NUNCA debe:
- Ver proyectos de otros clientes
- Ver costos, precios ni información financiera
- Acceder a endpoints que no sean `/portal/*`
- Modificar información del sistema

## Endpoints del Portal

### api/v1/endpoints/portal.py
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual
from app.models.usuario import Usuario, RolUsuario
from app.models.proyecto import Proyecto
from app.models.etapa import Etapa
from app.models.foto import Foto
from app.schemas.portal import (
    ProyectoClienteResponse,
    EtapaClienteResponse,
    FotoClienteResponse
)

router = APIRouter()

def verificar_cliente(usuario: Usuario):
    """Verifica que el usuario sea un cliente."""
    if usuario.rol != RolUsuario.cliente:
        raise HTTPException(status_code=403, detail="Acceso solo para clientes")
    return usuario

def verificar_proyecto_cliente(db: Session, proyecto_id: UUID, cliente_id: UUID) -> Proyecto:
    """Verifica que el proyecto pertenezca al cliente."""
    proyecto = db.query(Proyecto).filter(
        Proyecto.id == proyecto_id,
        Proyecto.cliente_id == cliente_id,
        Proyecto.activo == True
    ).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto

@router.get("/mis-proyectos", response_model=List[ProyectoClienteResponse])
def mis_proyectos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista los proyectos asignados al cliente autenticado."""
    verificar_cliente(usuario)

    proyectos = db.query(Proyecto).filter(
        Proyecto.cliente_id == usuario.id,
        Proyecto.activo == True
    ).order_by(Proyecto.fecha_inicio.desc()).all()

    return proyectos

@router.get("/proyecto/{proyecto_id}", response_model=ProyectoClienteResponse)
def detalle_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Detalle de un proyecto del cliente."""
    verificar_cliente(usuario)
    proyecto = verificar_proyecto_cliente(db, proyecto_id, usuario.id)
    return proyecto

@router.get("/proyecto/{proyecto_id}/etapas", response_model=List[EtapaClienteResponse])
def etapas_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista las etapas de un proyecto del cliente."""
    verificar_cliente(usuario)
    proyecto = verificar_proyecto_cliente(db, proyecto_id, usuario.id)

    etapas = db.query(Etapa).filter(
        Etapa.proyecto_id == proyecto_id,
        Etapa.activo == True
    ).order_by(Etapa.orden).all()

    return etapas

@router.get("/proyecto/{proyecto_id}/fotos", response_model=List[FotoClienteResponse])
def fotos_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista las fotos AUTORIZADAS de un proyecto del cliente."""
    verificar_cliente(usuario)
    proyecto = verificar_proyecto_cliente(db, proyecto_id, usuario.id)

    # IMPORTANTE: Solo fotos marcadas como visible_cliente=True
    fotos = db.query(Foto).filter(
        Foto.proyecto_id == proyecto_id,
        Foto.visible_cliente == True,
        Foto.activo == True
    ).order_by(Foto.fecha.desc()).all()

    return fotos

@router.get("/proyecto/{proyecto_id}/reporte")
def ultimo_reporte(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Obtiene el último reporte disponible para el cliente."""
    verificar_cliente(usuario)
    proyecto = verificar_proyecto_cliente(db, proyecto_id, usuario.id)

    # Buscar último reporte compartido con el cliente
    from app.models.reporte import Reporte
    reporte = db.query(Reporte).filter(
        Reporte.proyecto_id == proyecto_id,
        Reporte.compartido_cliente == True
    ).order_by(Reporte.created_at.desc()).first()

    if not reporte:
        raise HTTPException(status_code=404, detail="No hay reportes disponibles")

    return {
        "id": reporte.id,
        "fecha": reporte.created_at,
        "pdf_url": reporte.pdf_url
    }
```

## Schemas del Portal

### schemas/portal.py
```python
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from datetime import date, datetime

class ProyectoClienteResponse(BaseModel):
    """
    Respuesta de proyecto para cliente.
    EXCLUYE: monto_contratado y cualquier dato financiero.
    """
    id: UUID
    nombre: str
    descripcion: Optional[str]
    ubicacion: Optional[str]
    fecha_inicio: Optional[date]
    fecha_fin_estimada: Optional[date]
    estado: str
    porcentaje_avance: Decimal

    class Config:
        from_attributes = True

class EtapaClienteResponse(BaseModel):
    """
    Respuesta de etapa para cliente.
    EXCLUYE: costos de ítems de trabajo.
    """
    id: UUID
    nombre: str
    descripcion: Optional[str]
    orden: int
    fecha_inicio_est: Optional[date]
    fecha_fin_est: Optional[date]
    fecha_inicio_real: Optional[date]
    fecha_fin_real: Optional[date]
    estado: str
    porcentaje_avance: Decimal

    class Config:
        from_attributes = True

class FotoClienteResponse(BaseModel):
    """Foto autorizada para el cliente."""
    id: UUID
    url: str
    descripcion: Optional[str]
    fecha: date

    class Config:
        from_attributes = True
```

## Frontend: Layout del Cliente

### components/layout/ClientLayout.tsx
```typescript
import { Outlet, Navigate, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { Home, FolderKanban, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function ClientLayout() {
  const { usuario, logout, isAuthenticated } = useAuthStore();
  const location = useLocation();

  // Redirigir si no es cliente
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (usuario?.rol !== 'cliente') {
    return <Navigate to="/dashboard" replace />;
  }

  const navItems = [
    { href: '/portal', icon: Home, label: 'Inicio' },
    { href: '/portal/proyectos', icon: FolderKanban, label: 'Mis Proyectos' },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header simple */}
      <header className="bg-white border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.svg" alt="Electro América" className="h-8" />
            <span className="font-semibold text-lg hidden sm:block">Portal Cliente</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-muted hidden sm:block">
              {usuario?.nombre}
            </span>
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Nav móvil */}
      <nav className="bg-white border-b sm:hidden">
        <div className="flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              to={item.href}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm ${
                location.pathname === item.href
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-muted'
              }`}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="container mx-auto px-4 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t py-4 mt-auto">
        <div className="container mx-auto px-4 text-center text-sm text-muted">
          Electro América &copy; {new Date().getFullYear()}
        </div>
      </footer>
    </div>
  );
}
```

## Frontend: Páginas del Portal

### pages/portal-cliente/MisProyectos.tsx
```typescript
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { formatearFecha, formatearPorcentaje } from '@/utils/formatters';
import { MapPin, Calendar, ChevronRight } from 'lucide-react';
import api from '@/services/api';

const estadoLabels: Record<string, string> = {
  planificacion: 'Planificación',
  en_ejecucion: 'En Ejecución',
  pausado: 'Pausado',
  finalizado: 'Finalizado',
};

const estadoColors: Record<string, string> = {
  planificacion: 'bg-gray-500',
  en_ejecucion: 'bg-primary',
  pausado: 'bg-yellow-500',
  finalizado: 'bg-green-500',
};

export default function MisProyectos() {
  const { data: proyectos, isLoading } = useQuery({
    queryKey: ['portal', 'mis-proyectos'],
    queryFn: () => api.get('/portal/mis-proyectos').then(res => res.data),
  });

  if (isLoading) {
    return <div className="text-center py-8">Cargando proyectos...</div>;
  }

  if (!proyectos?.length) {
    return (
      <div className="text-center py-12">
        <p className="text-muted">No tiene proyectos asignados.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Mis Proyectos</h1>

      <div className="grid gap-4">
        {proyectos.map((proyecto: any) => (
          <Link key={proyecto.id} to={`/portal/proyecto/${proyecto.id}`}>
            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2">
                      <h2 className="font-semibold text-lg">{proyecto.nombre}</h2>
                      <Badge className={estadoColors[proyecto.estado]}>
                        {estadoLabels[proyecto.estado]}
                      </Badge>
                    </div>

                    {proyecto.ubicacion && (
                      <div className="flex items-center text-muted text-sm">
                        <MapPin className="h-4 w-4 mr-1" />
                        {proyecto.ubicacion}
                      </div>
                    )}

                    {proyecto.fechaFinEstimada && (
                      <div className="flex items-center text-muted text-sm">
                        <Calendar className="h-4 w-4 mr-1" />
                        Entrega estimada: {formatearFecha(proyecto.fechaFinEstimada)}
                      </div>
                    )}

                    <div className="pt-2">
                      <div className="flex justify-between text-sm mb-1">
                        <span>Avance del proyecto</span>
                        <span className="font-medium">
                          {formatearPorcentaje(proyecto.porcentajeAvance)}
                        </span>
                      </div>
                      <Progress value={proyecto.porcentajeAvance} className="h-2" />
                    </div>
                  </div>

                  <ChevronRight className="h-5 w-5 text-muted mt-2" />
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

### pages/portal-cliente/ProyectoDetalle.tsx
```typescript
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { formatearFecha, formatearPorcentaje } from '@/utils/formatters';
import { FileText, Image, ListChecks } from 'lucide-react';
import api from '@/services/api';

export default function ProyectoDetalle() {
  const { id } = useParams();

  const { data: proyecto, isLoading: loadingProyecto } = useQuery({
    queryKey: ['portal', 'proyecto', id],
    queryFn: () => api.get(`/portal/proyecto/${id}`).then(res => res.data),
  });

  const { data: etapas } = useQuery({
    queryKey: ['portal', 'proyecto', id, 'etapas'],
    queryFn: () => api.get(`/portal/proyecto/${id}/etapas`).then(res => res.data),
    enabled: !!id,
  });

  const { data: fotos } = useQuery({
    queryKey: ['portal', 'proyecto', id, 'fotos'],
    queryFn: () => api.get(`/portal/proyecto/${id}/fotos`).then(res => res.data),
    enabled: !!id,
  });

  if (loadingProyecto) {
    return <div className="text-center py-8">Cargando...</div>;
  }

  if (!proyecto) {
    return <div className="text-center py-8">Proyecto no encontrado</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">{proyecto.nombre}</h1>
        {proyecto.descripcion && (
          <p className="text-muted">{proyecto.descripcion}</p>
        )}
      </div>

      {/* Avance general */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex justify-between items-center mb-2">
            <span className="font-medium">Avance General</span>
            <span className="text-2xl font-bold text-primary">
              {formatearPorcentaje(proyecto.porcentajeAvance)}
            </span>
          </div>
          <Progress value={proyecto.porcentajeAvance} className="h-3" />
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="etapas">
        <TabsList className="w-full">
          <TabsTrigger value="etapas" className="flex-1">
            <ListChecks className="h-4 w-4 mr-2" />
            Etapas
          </TabsTrigger>
          <TabsTrigger value="fotos" className="flex-1">
            <Image className="h-4 w-4 mr-2" />
            Fotos
          </TabsTrigger>
          <TabsTrigger value="reporte" className="flex-1">
            <FileText className="h-4 w-4 mr-2" />
            Reporte
          </TabsTrigger>
        </TabsList>

        <TabsContent value="etapas" className="mt-4 space-y-3">
          {etapas?.map((etapa: any) => (
            <Card key={etapa.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-medium">{etapa.nombre}</h3>
                  <Badge variant={etapa.estado === 'completada' ? 'default' : 'secondary'}>
                    {etapa.estado}
                  </Badge>
                </div>
                <Progress value={etapa.porcentajeAvance} className="h-2" />
                <span className="text-sm text-muted">
                  {formatearPorcentaje(etapa.porcentajeAvance)}
                </span>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="fotos" className="mt-4">
          {fotos?.length ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {fotos.map((foto: any) => (
                <div key={foto.id} className="relative aspect-square">
                  <img
                    src={foto.url}
                    alt={foto.descripcion || 'Foto del proyecto'}
                    className="w-full h-full object-cover rounded-lg"
                  />
                  <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-2 rounded-b-lg">
                    {formatearFecha(foto.fecha)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted py-8">No hay fotos disponibles</p>
          )}
        </TabsContent>

        <TabsContent value="reporte" className="mt-4">
          <Card>
            <CardContent className="py-8 text-center">
              <FileText className="h-12 w-12 text-muted mx-auto mb-4" />
              <p className="mb-4">Descargue el último reporte del proyecto</p>
              <Button onClick={() => window.open(`/api/v1/portal/proyecto/${id}/reporte`)}>
                Descargar Reporte PDF
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

## Rutas del Portal

### App.tsx (fragmento)
```typescript
// Rutas del portal cliente
<Route path="/portal" element={<ClientLayout />}>
  <Route index element={<PortalHome />} />
  <Route path="proyectos" element={<MisProyectos />} />
  <Route path="proyecto/:id" element={<ProyectoDetalle />} />
</Route>
```

## Checklist de Completado
- [ ] Endpoints portal con verificación de cliente
- [ ] Schemas sin datos financieros
- [ ] ClientLayout responsive
- [ ] MisProyectos page
- [ ] ProyectoDetalle page
- [ ] EtapasList en portal
- [ ] GaleriaFotos (solo visible_cliente=true)
- [ ] Descarga de reporte
- [ ] Protección de rutas en frontend
- [ ] Tests de seguridad (cliente no accede a otros proyectos)

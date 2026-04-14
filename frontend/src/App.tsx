import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/toaster'
import { MainLayout } from '@/layouts/MainLayout'
import { ClientLayout } from '@/layouts/ClientLayout'
import { LoginPage } from '@/pages/Login'
import { DashboardPage } from '@/pages/Dashboard'
import { ProyectosPage } from '@/pages/Proyectos'
import { ProyectoDetallePage } from '@/pages/ProyectoDetalle'
import { ProyectoEditarPage } from '@/pages/ProyectoEditar'
import { MaterialesPage } from '@/pages/Materiales'
import { EquiposPage } from '@/pages/Equipos'
import { FinanzasPage } from '@/pages/Finanzas'
import { ClientesPage } from '@/pages/Clientes'
import { UsuariosPage } from '@/pages/Usuarios'
import { MisProyectosPage } from '@/pages/portal/MisProyectos'
import { DetalleProyectoPage } from '@/pages/portal/DetalleProyecto'
import { AlertasPage } from '@/pages/Alertas'
import { ReportesPage } from '@/pages/Reportes'
import { AuditoriaPage } from '@/pages/Auditoria'
// Operario pages
import IniciarJornadaPage from '@/pages/operario/IniciarJornada'
import JornadaActivaPage from '@/pages/operario/JornadaActiva'
import HistorialJornadasPage from '@/pages/operario/HistorialJornadas'
// Supervisor pages
import MonitorJornadasPage from '@/pages/admin/MonitorJornadas'
import PlanificacionDiariaPage from '@/pages/admin/PlanificacionDiaria'
import ActividadesTipoPage from '@/pages/admin/ActividadesTipo'
// Herramientas pages
import ControlPrestamosPage from '@/pages/herramientas/ControlPrestamos'
import InventarioHerramientasPage from '@/pages/herramientas/InventarioHerramientas'
import { useAuthStore, useIsAuthenticated, useIsCliente } from '@/store/auth'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useIsAuthenticated()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function StaffRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useIsAuthenticated()
  const isCliente = useIsCliente()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (isCliente) {
    return <Navigate to="/portal" replace />
  }

  return <>{children}</>
}

function ClientRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useIsAuthenticated()
  const isCliente = useIsCliente()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!isCliente) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  const fetchUser = useAuthStore((state) => state.fetchUser)
  const isAuthenticated = useIsAuthenticated()

  useEffect(() => {
    if (isAuthenticated) {
      fetchUser()
    }
  }, [isAuthenticated, fetchUser])

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Staff routes */}
      <Route
        path="/"
        element={
          <StaffRoute>
            <MainLayout />
          </StaffRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="proyectos" element={<ProyectosPage />} />
        <Route path="proyectos/:proyectoId" element={<ProyectoDetallePage />} />
        <Route path="proyectos/:proyectoId/editar" element={<ProyectoEditarPage />} />
        <Route path="materiales" element={<MaterialesPage />} />
        <Route path="equipos" element={<EquiposPage />} />
        <Route path="finanzas" element={<FinanzasPage />} />
        <Route path="clientes" element={<ClientesPage />} />
        <Route path="alertas" element={<AlertasPage />} />
        <Route path="reportes" element={<ReportesPage />} />
        <Route path="auditoria" element={<AuditoriaPage />} />
        <Route path="usuarios" element={<UsuariosPage />} />
        {/* Operario routes */}
        <Route path="operario/iniciar-jornada" element={<IniciarJornadaPage />} />
        <Route path="operario/jornada-activa" element={<JornadaActivaPage />} />
        <Route path="operario/historial" element={<HistorialJornadasPage />} />
        {/* Supervisor routes */}
        <Route path="jornadas/monitor" element={<MonitorJornadasPage />} />
        <Route path="jornadas/planificacion" element={<PlanificacionDiariaPage />} />
        <Route path="actividades-tipo" element={<ActividadesTipoPage />} />
        {/* Herramientas routes */}
        <Route path="herramientas/prestamos" element={<ControlPrestamosPage />} />
        <Route path="herramientas/inventario" element={<InventarioHerramientasPage />} />
      </Route>

      {/* Client portal routes */}
      <Route
        path="/portal"
        element={
          <ClientRoute>
            <ClientLayout />
          </ClientRoute>
        }
      >
        <Route index element={<MisProyectosPage />} />
        <Route path="proyecto/:proyectoId" element={<DetalleProyectoPage />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App

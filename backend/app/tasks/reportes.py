from celery import shared_task
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.proyecto import Proyecto, EstadoProyecto
from app.services import reporte_service


@shared_task(name="app.tasks.reportes.generar_reportes_semanales")
def generar_reportes_semanales():
    """
    Genera reportes semanales automáticos para todos los proyectos activos.
    Se ejecuta todos los lunes a las 8:00 AM.
    """
    db: Session = SessionLocal()
    try:
        # Obtener todos los proyectos en ejecución
        proyectos = db.query(Proyecto).filter(
            Proyecto.activo == True,
            Proyecto.estado == EstadoProyecto.en_ejecucion
        ).all()

        # Calcular rango de fechas (semana anterior)
        hoy = date.today()
        fecha_hasta = hoy - timedelta(days=1)  # Ayer
        fecha_desde = fecha_hasta - timedelta(days=6)  # Hace 7 días

        reportes_generados = []
        for proyecto in proyectos:
            try:
                reporte = reporte_service.guardar_reporte(
                    db=db,
                    proyecto_id=proyecto.id,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    pdf_url=None,  # Se generaría con WeasyPrint
                    excel_url=None,  # Se generaría con OpenPyXL
                    usuario_id=None,  # Sistema automático
                    tipo="semanal"
                )
                reportes_generados.append(str(proyecto.id))
            except Exception as e:
                print(f"Error generando reporte para proyecto {proyecto.id}: {e}")

        return {
            "status": "success",
            "proyectos_procesados": len(proyectos),
            "reportes_generados": len(reportes_generados),
            "fecha_desde": fecha_desde.isoformat(),
            "fecha_hasta": fecha_hasta.isoformat()
        }
    finally:
        db.close()


@shared_task(name="app.tasks.reportes.generar_reporte_proyecto")
def generar_reporte_proyecto(proyecto_id: str, fecha_desde: str, fecha_hasta: str):
    """
    Genera un reporte para un proyecto específico de forma asíncrona.
    """
    from uuid import UUID

    db: Session = SessionLocal()
    try:
        reporte = reporte_service.guardar_reporte(
            db=db,
            proyecto_id=UUID(proyecto_id),
            fecha_desde=date.fromisoformat(fecha_desde),
            fecha_hasta=date.fromisoformat(fecha_hasta),
            pdf_url=None,
            excel_url=None,
            usuario_id=None,
            tipo="personalizado"
        )

        return {
            "status": "success",
            "reporte_id": str(reporte.id),
            "proyecto_id": proyecto_id
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "proyecto_id": proyecto_id
        }
    finally:
        db.close()

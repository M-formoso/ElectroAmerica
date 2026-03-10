from celery import shared_task
from datetime import date
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.material import Material
from app.models.etapa import Etapa, EstadoEtapa


@shared_task(name="app.tasks.notificaciones.verificar_alertas_stock")
def verificar_alertas_stock():
    """
    Verifica materiales con stock bajo y genera alertas.
    Se ejecuta diariamente a las 9:00 AM.
    """
    db: Session = SessionLocal()
    try:
        materiales_bajo = db.query(Material).filter(
            Material.activo == True,
            Material.stock_actual <= Material.stock_minimo
        ).all()

        alertas = []
        for material in materiales_bajo:
            alertas.append({
                "material_id": str(material.id),
                "nombre": material.nombre,
                "stock_actual": float(material.stock_actual),
                "stock_minimo": float(material.stock_minimo),
                "deficit": float(material.stock_minimo - material.stock_actual)
            })

        # Aquí se enviarían notificaciones por email/push
        # Por ahora solo retornamos el resumen

        return {
            "status": "success",
            "materiales_con_stock_bajo": len(alertas),
            "alertas": alertas
        }
    finally:
        db.close()


@shared_task(name="app.tasks.notificaciones.verificar_etapas_demoradas")
def verificar_etapas_demoradas():
    """
    Verifica etapas con fecha de fin estimada vencida.
    Se ejecuta diariamente a las 9:30 AM.
    """
    db: Session = SessionLocal()
    try:
        hoy = date.today()

        etapas_demoradas = db.query(Etapa).filter(
            Etapa.activo == True,
            Etapa.fecha_fin_est < hoy,
            Etapa.estado.notin_([EstadoEtapa.completada])
        ).all()

        alertas = []
        for etapa in etapas_demoradas:
            dias_demora = (hoy - etapa.fecha_fin_est).days
            alertas.append({
                "etapa_id": str(etapa.id),
                "nombre": etapa.nombre,
                "proyecto_id": str(etapa.proyecto_id),
                "fecha_fin_estimada": etapa.fecha_fin_est.isoformat(),
                "dias_demora": dias_demora,
                "severidad": "critico" if dias_demora > 7 else "warning"
            })

        # Aquí se enviarían notificaciones
        # Por ahora solo retornamos el resumen

        return {
            "status": "success",
            "etapas_demoradas": len(alertas),
            "alertas": alertas
        }
    finally:
        db.close()


@shared_task(name="app.tasks.notificaciones.enviar_notificacion_email")
def enviar_notificacion_email(destinatario: str, asunto: str, contenido: str):
    """
    Envía una notificación por email.
    """
    # TODO: Implementar con SMTP cuando se configure
    # Por ahora solo logueamos
    print(f"Enviando email a {destinatario}: {asunto}")

    return {
        "status": "success",
        "destinatario": destinatario,
        "asunto": asunto
    }

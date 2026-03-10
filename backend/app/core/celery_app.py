from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "electroamerica",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.reportes", "app.tasks.notificaciones"]
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos máximo por tarea
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Tareas programadas
celery_app.conf.beat_schedule = {
    # Generar reportes semanales todos los lunes a las 8:00 AM
    "generar-reportes-semanales": {
        "task": "app.tasks.reportes.generar_reportes_semanales",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },
    # Verificar alertas de stock bajo diariamente a las 9:00 AM
    "verificar-stock-bajo": {
        "task": "app.tasks.notificaciones.verificar_alertas_stock",
        "schedule": crontab(hour=9, minute=0),
    },
    # Verificar etapas demoradas diariamente a las 9:30 AM
    "verificar-etapas-demoradas": {
        "task": "app.tasks.notificaciones.verificar_etapas_demoradas",
        "schedule": crontab(hour=9, minute=30),
    },
}

# Agente: Reportes de Proyecto

## Rol
Implementar el sistema de generación de reportes en PDF y Excel, incluyendo reportes semanales automáticos con Celery.

## Modelos

### models/reporte.py
```python
from sqlalchemy import Column, String, Date, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel

class Reporte(Base, BaseModel):
    __tablename__ = "reportes"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    fecha_desde = Column(Date, nullable=False)
    fecha_hasta = Column(Date, nullable=False)
    tipo = Column(String(50), default="personalizado")  # 'semanal', 'personalizado'
    pdf_url = Column(String(500), nullable=True)
    excel_url = Column(String(500), nullable=True)
    compartido_cliente = Column(Boolean, default=False)
    notas = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    # Relaciones
    proyecto = relationship("Proyecto")
    creador = relationship("Usuario")
```

## Services

### services/reporte_service.py
```python
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from weasyprint import HTML, CSS
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
import cloudinary.uploader

from app.models.proyecto import Proyecto
from app.models.etapa import Etapa
from app.models.item_trabajo import ItemTrabajo
from app.models.asignacion_material import AsignacionMaterial
from app.models.asignacion_equipo import AsignacionEquipo
from app.models.gasto import Gasto
from app.models.foto import Foto
from app.models.reporte import Reporte
from app.core.config import settings

def obtener_datos_reporte(
    db: Session,
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date
) -> dict:
    """
    Recopila todos los datos necesarios para generar el reporte.
    """
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        return None

    # Etapas con sus ítems
    etapas = db.query(Etapa).filter(
        Etapa.proyecto_id == proyecto_id,
        Etapa.activo == True
    ).order_by(Etapa.orden).all()

    etapas_data = []
    for etapa in etapas:
        items = db.query(ItemTrabajo).filter(
            ItemTrabajo.etapa_id == etapa.id,
            ItemTrabajo.activo == True
        ).all()

        items_completados = [i for i in items if i.estado.value == 'completado']

        etapas_data.append({
            "nombre": etapa.nombre,
            "estado": etapa.estado.value,
            "porcentaje_avance": float(etapa.porcentaje_avance),
            "items_total": len(items),
            "items_completados": len(items_completados),
        })

    # Materiales utilizados en el período
    materiales = db.query(AsignacionMaterial).filter(
        AsignacionMaterial.proyecto_id == proyecto_id,
        AsignacionMaterial.fecha >= fecha_desde,
        AsignacionMaterial.fecha <= fecha_hasta
    ).all()

    materiales_data = [
        {
            "nombre": m.material.nombre,
            "cantidad": float(m.cantidad),
            "unidad": m.material.unidad,
            "fecha": m.fecha.isoformat(),
        }
        for m in materiales
    ]

    # Equipos asignados en el período
    equipos = db.query(AsignacionEquipo).filter(
        AsignacionEquipo.proyecto_id == proyecto_id,
        AsignacionEquipo.fecha_desde <= fecha_hasta,
        (AsignacionEquipo.fecha_hasta >= fecha_desde) | (AsignacionEquipo.fecha_hasta.is_(None))
    ).all()

    equipos_data = [
        {
            "nombre": e.equipo.nombre,
            "tipo": e.equipo.tipo.value,
            "fecha_desde": e.fecha_desde.isoformat(),
            "fecha_hasta": e.fecha_hasta.isoformat() if e.fecha_hasta else "En uso",
        }
        for e in equipos
    ]

    # Gastos del período
    gastos = db.query(Gasto).filter(
        Gasto.proyecto_id == proyecto_id,
        Gasto.fecha >= fecha_desde,
        Gasto.fecha <= fecha_hasta,
        Gasto.activo == True
    ).all()

    total_gastos = sum(g.monto for g in gastos)

    gastos_data = [
        {
            "fecha": g.fecha.isoformat(),
            "categoria": g.categoria,
            "descripcion": g.descripcion,
            "monto": float(g.monto),
        }
        for g in gastos
    ]

    # Fotos del período
    fotos = db.query(Foto).filter(
        Foto.proyecto_id == proyecto_id,
        Foto.fecha >= fecha_desde,
        Foto.fecha <= fecha_hasta,
        Foto.activo == True
    ).order_by(Foto.fecha.desc()).limit(10).all()

    fotos_data = [
        {
            "url": f.url,
            "descripcion": f.descripcion,
            "fecha": f.fecha.isoformat(),
        }
        for f in fotos
    ]

    return {
        "proyecto": {
            "nombre": proyecto.nombre,
            "descripcion": proyecto.descripcion,
            "ubicacion": proyecto.ubicacion,
            "estado": proyecto.estado.value,
            "porcentaje_avance": float(proyecto.porcentaje_avance),
            "fecha_inicio": proyecto.fecha_inicio.isoformat() if proyecto.fecha_inicio else None,
            "fecha_fin_estimada": proyecto.fecha_fin_estimada.isoformat() if proyecto.fecha_fin_estimada else None,
        },
        "periodo": {
            "desde": fecha_desde.isoformat(),
            "hasta": fecha_hasta.isoformat(),
        },
        "etapas": etapas_data,
        "materiales": materiales_data,
        "equipos": equipos_data,
        "gastos": gastos_data,
        "total_gastos": float(total_gastos),
        "fotos": fotos_data,
    }

def generar_html_reporte(datos: dict) -> str:
    """Genera el HTML del reporte."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                margin: 40px;
                color: #1A1A1A;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 3px solid #E53935;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .logo {{
                height: 60px;
            }}
            h1 {{
                color: #E53935;
                margin: 0;
            }}
            h2 {{
                color: #424242;
                border-bottom: 1px solid #E0E0E0;
                padding-bottom: 10px;
            }}
            .info-box {{
                background: #FFEBEE;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .progress-bar {{
                background: #E0E0E0;
                border-radius: 10px;
                height: 20px;
                overflow: hidden;
            }}
            .progress-fill {{
                background: #E53935;
                height: 100%;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #E0E0E0;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background: #F5F5F5;
            }}
            .total {{
                font-weight: bold;
                background: #FFEBEE;
            }}
            .foto-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }}
            .foto-item img {{
                width: 100%;
                height: 150px;
                object-fit: cover;
                border-radius: 8px;
            }}
            .footer {{
                margin-top: 40px;
                text-align: center;
                color: #757575;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>Reporte de Proyecto</h1>
                <p>{datos['proyecto']['nombre']}</p>
            </div>
            <div style="text-align: right;">
                <strong>Electro América</strong><br>
                <small>Período: {datos['periodo']['desde']} al {datos['periodo']['hasta']}</small>
            </div>
        </div>

        <div class="info-box">
            <strong>Avance General: {datos['proyecto']['porcentaje_avance']:.1f}%</strong>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {datos['proyecto']['porcentaje_avance']}%"></div>
            </div>
        </div>

        <h2>Etapas del Proyecto</h2>
        <table>
            <tr>
                <th>Etapa</th>
                <th>Estado</th>
                <th>Avance</th>
                <th>Ítems</th>
            </tr>
            {''.join(f'''
            <tr>
                <td>{e['nombre']}</td>
                <td>{e['estado']}</td>
                <td>{e['porcentaje_avance']:.1f}%</td>
                <td>{e['items_completados']}/{e['items_total']}</td>
            </tr>
            ''' for e in datos['etapas'])}
        </table>

        <h2>Materiales Utilizados</h2>
        <table>
            <tr>
                <th>Material</th>
                <th>Cantidad</th>
                <th>Unidad</th>
                <th>Fecha</th>
            </tr>
            {''.join(f'''
            <tr>
                <td>{m['nombre']}</td>
                <td>{m['cantidad']}</td>
                <td>{m['unidad']}</td>
                <td>{m['fecha']}</td>
            </tr>
            ''' for m in datos['materiales']) if datos['materiales'] else '<tr><td colspan="4">Sin materiales en este período</td></tr>'}
        </table>

        <h2>Equipos Asignados</h2>
        <table>
            <tr>
                <th>Equipo</th>
                <th>Tipo</th>
                <th>Desde</th>
                <th>Hasta</th>
            </tr>
            {''.join(f'''
            <tr>
                <td>{e['nombre']}</td>
                <td>{e['tipo']}</td>
                <td>{e['fecha_desde']}</td>
                <td>{e['fecha_hasta']}</td>
            </tr>
            ''' for e in datos['equipos']) if datos['equipos'] else '<tr><td colspan="4">Sin equipos en este período</td></tr>'}
        </table>

        <h2>Gastos del Período</h2>
        <table>
            <tr>
                <th>Fecha</th>
                <th>Categoría</th>
                <th>Descripción</th>
                <th>Monto</th>
            </tr>
            {''.join(f'''
            <tr>
                <td>{g['fecha']}</td>
                <td>{g['categoria']}</td>
                <td>{g['descripcion']}</td>
                <td>${g['monto']:,.2f}</td>
            </tr>
            ''' for g in datos['gastos']) if datos['gastos'] else '<tr><td colspan="4">Sin gastos en este período</td></tr>'}
            <tr class="total">
                <td colspan="3">TOTAL</td>
                <td>${datos['total_gastos']:,.2f}</td>
            </tr>
        </table>

        <div class="footer">
            <p>Electro América - Reporte generado automáticamente</p>
            <p>Fecha de generación: {date.today().isoformat()}</p>
        </div>
    </body>
    </html>
    """
    return html

def generar_pdf(db: Session, proyecto_id: UUID, fecha_desde: date, fecha_hasta: date) -> bytes:
    """Genera el PDF del reporte."""
    datos = obtener_datos_reporte(db, proyecto_id, fecha_desde, fecha_hasta)
    if not datos:
        return None

    html_content = generar_html_reporte(datos)
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes

def generar_excel(db: Session, proyecto_id: UUID, fecha_desde: date, fecha_hasta: date) -> bytes:
    """Genera el archivo Excel del reporte."""
    datos = obtener_datos_reporte(db, proyecto_id, fecha_desde, fecha_hasta)
    if not datos:
        return None

    wb = Workbook()

    # Hoja de Resumen
    ws = wb.active
    ws.title = "Resumen"

    header_font = Font(bold=True, size=14, color="FFFFFF")
    header_fill = PatternFill(start_color="E53935", end_color="E53935", fill_type="solid")

    ws['A1'] = f"Reporte: {datos['proyecto']['nombre']}"
    ws['A1'].font = Font(bold=True, size=16)
    ws['A2'] = f"Período: {datos['periodo']['desde']} al {datos['periodo']['hasta']}"
    ws['A4'] = f"Avance General: {datos['proyecto']['porcentaje_avance']:.1f}%"

    # Hoja de Etapas
    ws_etapas = wb.create_sheet("Etapas")
    ws_etapas.append(["Etapa", "Estado", "Avance %", "Ítems Completados", "Ítems Total"])
    for cell in ws_etapas[1]:
        cell.font = header_font
        cell.fill = header_fill

    for e in datos['etapas']:
        ws_etapas.append([e['nombre'], e['estado'], e['porcentaje_avance'], e['items_completados'], e['items_total']])

    # Hoja de Materiales
    ws_mat = wb.create_sheet("Materiales")
    ws_mat.append(["Material", "Cantidad", "Unidad", "Fecha"])
    for cell in ws_mat[1]:
        cell.font = header_font
        cell.fill = header_fill

    for m in datos['materiales']:
        ws_mat.append([m['nombre'], m['cantidad'], m['unidad'], m['fecha']])

    # Hoja de Gastos
    ws_gastos = wb.create_sheet("Gastos")
    ws_gastos.append(["Fecha", "Categoría", "Descripción", "Monto"])
    for cell in ws_gastos[1]:
        cell.font = header_font
        cell.fill = header_fill

    for g in datos['gastos']:
        ws_gastos.append([g['fecha'], g['categoria'], g['descripcion'], g['monto']])

    ws_gastos.append(["", "", "TOTAL", datos['total_gastos']])

    # Guardar a bytes
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

def guardar_reporte(
    db: Session,
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date,
    pdf_bytes: bytes,
    excel_bytes: bytes,
    usuario_id: UUID,
    tipo: str = "personalizado"
) -> Reporte:
    """Guarda el reporte en la base de datos y sube archivos a Cloudinary."""

    # Subir PDF a Cloudinary
    pdf_result = cloudinary.uploader.upload(
        BytesIO(pdf_bytes),
        folder="reportes",
        resource_type="raw",
        format="pdf"
    )
    pdf_url = pdf_result['secure_url']

    # Subir Excel a Cloudinary
    excel_result = cloudinary.uploader.upload(
        BytesIO(excel_bytes),
        folder="reportes",
        resource_type="raw",
        format="xlsx"
    )
    excel_url = excel_result['secure_url']

    # Crear registro
    reporte = Reporte(
        proyecto_id=proyecto_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo=tipo,
        pdf_url=pdf_url,
        excel_url=excel_url,
        created_by=usuario_id
    )
    db.add(reporte)
    db.commit()
    db.refresh(reporte)

    return reporte
```

## Celery Tasks

### tasks/reportes.py
```python
from celery import shared_task
from datetime import date, timedelta
from app.db.session import SessionLocal
from app.models.proyecto import Proyecto, EstadoProyecto
from app.services import reporte_service

@shared_task
def generar_reporte_semanal():
    """
    Se ejecuta cada lunes. Genera reporte de la semana anterior
    para cada proyecto activo.
    """
    db = SessionLocal()
    try:
        # Calcular fechas de la semana anterior
        hoy = date.today()
        fecha_hasta = hoy - timedelta(days=1)  # Domingo
        fecha_desde = fecha_hasta - timedelta(days=6)  # Lunes anterior

        # Obtener proyectos en ejecución
        proyectos = db.query(Proyecto).filter(
            Proyecto.activo == True,
            Proyecto.estado == EstadoProyecto.en_ejecucion
        ).all()

        for proyecto in proyectos:
            try:
                # Generar PDF y Excel
                pdf_bytes = reporte_service.generar_pdf(db, proyecto.id, fecha_desde, fecha_hasta)
                excel_bytes = reporte_service.generar_excel(db, proyecto.id, fecha_desde, fecha_hasta)

                if pdf_bytes and excel_bytes:
                    # Guardar reporte (usando ID del sistema como creador)
                    reporte_service.guardar_reporte(
                        db,
                        proyecto.id,
                        fecha_desde,
                        fecha_hasta,
                        pdf_bytes,
                        excel_bytes,
                        None,  # Sistema
                        tipo="semanal"
                    )
                    print(f"Reporte semanal generado para: {proyecto.nombre}")

            except Exception as e:
                print(f"Error generando reporte para {proyecto.nombre}: {e}")

    finally:
        db.close()

# Configurar Celery Beat para ejecutar cada lunes a las 6:00 AM
# En celery_app.py agregar:
# app.conf.beat_schedule = {
#     'generar-reportes-semanales': {
#         'task': 'app.tasks.reportes.generar_reporte_semanal',
#         'schedule': crontab(hour=6, minute=0, day_of_week=1),
#     },
# }
```

## Endpoints

### api/v1/endpoints/reportes.py
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date
from io import BytesIO
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.services import reporte_service

router = APIRouter()

@router.get("/proyecto/{proyecto_id}")
def obtener_datos_reporte(
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene los datos del reporte sin generar archivos."""
    datos = reporte_service.obtener_datos_reporte(db, proyecto_id, fecha_desde, fecha_hasta)
    if not datos:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return datos

@router.post("/proyecto/{proyecto_id}/pdf")
def generar_pdf(
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Genera y descarga el reporte en PDF."""
    pdf_bytes = reporte_service.generar_pdf(db, proyecto_id, fecha_desde, fecha_hasta)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=reporte_{proyecto_id}.pdf"}
    )

@router.post("/proyecto/{proyecto_id}/excel")
def generar_excel(
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Genera y descarga el reporte en Excel."""
    excel_bytes = reporte_service.generar_excel(db, proyecto_id, fecha_desde, fecha_hasta)
    if not excel_bytes:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=reporte_{proyecto_id}.xlsx"}
    )

@router.post("/proyecto/{proyecto_id}/compartir")
def compartir_reporte(
    proyecto_id: UUID,
    reporte_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Marca un reporte como compartido con el cliente."""
    from app.models.reporte import Reporte

    reporte = db.query(Reporte).filter(
        Reporte.id == reporte_id,
        Reporte.proyecto_id == proyecto_id
    ).first()

    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    reporte.compartido_cliente = True
    db.commit()

    return {"message": "Reporte compartido con el cliente"}

@router.get("/semanal/{proyecto_id}")
def obtener_ultimo_reporte_semanal(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene el último reporte semanal de un proyecto."""
    from app.models.reporte import Reporte

    reporte = db.query(Reporte).filter(
        Reporte.proyecto_id == proyecto_id,
        Reporte.tipo == "semanal"
    ).order_by(Reporte.created_at.desc()).first()

    if not reporte:
        raise HTTPException(status_code=404, detail="No hay reportes semanales")

    return {
        "id": reporte.id,
        "fecha_desde": reporte.fecha_desde,
        "fecha_hasta": reporte.fecha_hasta,
        "pdf_url": reporte.pdf_url,
        "excel_url": reporte.excel_url,
        "compartido_cliente": reporte.compartido_cliente,
        "created_at": reporte.created_at
    }
```

## Checklist de Completado
- [ ] Modelo Reporte
- [ ] Service con obtención de datos
- [ ] Generación de HTML para PDF
- [ ] Generación de PDF con WeasyPrint
- [ ] Generación de Excel con OpenPyXL
- [ ] Subida a Cloudinary
- [ ] Celery task para reportes semanales
- [ ] Celery Beat configurado
- [ ] Endpoints de generación y descarga
- [ ] Endpoint compartir con cliente
- [ ] Frontend: GenerarReporte modal
- [ ] Frontend: ListaReportes component

"""
Servicio para generación de reportes en PDF.
Usa WeasyPrint para convertir HTML a PDF.
"""
import io
from datetime import date
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

# Intentar importar WeasyPrint, si no está disponible usar un fallback
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


def generar_pdf_reporte(datos: dict) -> Optional[bytes]:
    """
    Genera un PDF del reporte de proyecto.

    Args:
        datos: Diccionario con los datos del reporte (de reporte_service.obtener_datos_reporte)

    Returns:
        bytes del PDF generado, o None si WeasyPrint no está disponible
    """
    if not WEASYPRINT_AVAILABLE:
        return None

    # Configurar Jinja2
    templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')

    # Si no existe el directorio de templates, crear uno con template por defecto
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

    template_path = os.path.join(templates_dir, 'reporte_proyecto.html')

    # Si no existe el template, usar uno inline
    if not os.path.exists(template_path):
        html_content = _generar_html_inline(datos)
    else:
        env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('reporte_proyecto.html')
        html_content = template.render(datos=datos)

    # Generar PDF
    html = HTML(string=html_content)
    pdf_bytes = html.write_pdf()

    return pdf_bytes


def _generar_html_inline(datos: dict) -> str:
    """Genera HTML inline para el reporte cuando no hay template."""
    proyecto = datos.get('proyecto', {})
    periodo = datos.get('periodo', {})
    resumen = datos.get('resumen', {})
    etapas = datos.get('etapas', [])
    materiales = datos.get('materiales', [])
    gastos = datos.get('gastos', [])

    # Formatear moneda
    def fmt_currency(value):
        if value is None:
            return '-'
        return f"${value:,.2f}"

    # Formatear fecha
    def fmt_date(value):
        if value is None:
            return '-'
        if isinstance(value, str):
            return value
        return value.strftime('%d/%m/%Y')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Reporte - {proyecto.get('nombre', 'Proyecto')}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 10pt;
                line-height: 1.4;
                color: #333;
            }}
            .header {{
                border-bottom: 2px solid #1e40af;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .header h1 {{
                color: #1e40af;
                margin: 0;
                font-size: 18pt;
            }}
            .header .subtitle {{
                color: #666;
                font-size: 10pt;
            }}
            .section {{
                margin-bottom: 20px;
            }}
            .section h2 {{
                background: #f3f4f6;
                padding: 8px 12px;
                margin: 0 0 10px 0;
                font-size: 12pt;
                border-left: 4px solid #1e40af;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }}
            .info-box {{
                background: #f9fafb;
                padding: 10px;
                border-radius: 4px;
            }}
            .info-box .label {{
                color: #6b7280;
                font-size: 9pt;
            }}
            .info-box .value {{
                font-size: 14pt;
                font-weight: bold;
                color: #111;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 9pt;
            }}
            th {{
                background: #e5e7eb;
                padding: 8px;
                text-align: left;
                font-weight: 600;
            }}
            td {{
                padding: 6px 8px;
                border-bottom: 1px solid #e5e7eb;
            }}
            .text-right {{
                text-align: right;
            }}
            .progress-bar {{
                background: #e5e7eb;
                border-radius: 4px;
                height: 8px;
                overflow: hidden;
            }}
            .progress-fill {{
                background: #3b82f6;
                height: 100%;
            }}
            .badge {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 8pt;
                font-weight: 500;
            }}
            .badge-green {{ background: #dcfce7; color: #166534; }}
            .badge-blue {{ background: #dbeafe; color: #1e40af; }}
            .badge-yellow {{ background: #fef3c7; color: #92400e; }}
            .badge-gray {{ background: #f3f4f6; color: #374151; }}
            .footer {{
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                text-align: center;
                font-size: 8pt;
                color: #9ca3af;
                padding: 10px;
            }}
            .page-break {{
                page-break-before: always;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{proyecto.get('nombre', 'Proyecto')}</h1>
            <div class="subtitle">
                {proyecto.get('ubicacion', '')} |
                Periodo: {periodo.get('desde', '')} - {periodo.get('hasta', '')}
            </div>
        </div>

        <div class="section">
            <div class="info-grid">
                <div class="info-box">
                    <div class="label">Avance General</div>
                    <div class="value">{proyecto.get('porcentaje_avance', 0):.0f}%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {proyecto.get('porcentaje_avance', 0)}%"></div>
                    </div>
                </div>
                <div class="info-box">
                    <div class="label">Etapas Completadas</div>
                    <div class="value">{resumen.get('etapas_completadas', 0)}/{resumen.get('total_etapas', 0)}</div>
                </div>
                <div class="info-box">
                    <div class="label">Costo Total</div>
                    <div class="value">{fmt_currency(resumen.get('costo_materiales', 0) + resumen.get('total_gastos', 0))}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Etapas del Proyecto</h2>
            <table>
                <thead>
                    <tr>
                        <th>Etapa</th>
                        <th>Estado</th>
                        <th>Avance</th>
                        <th>Items</th>
                    </tr>
                </thead>
                <tbody>
    """

    estado_badges = {
        'pendiente': 'badge-gray',
        'en_progreso': 'badge-blue',
        'completada': 'badge-green',
        'pausada': 'badge-yellow',
    }

    estado_labels = {
        'pendiente': 'Pendiente',
        'en_progreso': 'En Progreso',
        'completada': 'Completada',
        'pausada': 'Pausada',
    }

    for etapa in etapas:
        estado = etapa.get('estado', 'pendiente')
        badge_class = estado_badges.get(estado, 'badge-gray')
        estado_label = estado_labels.get(estado, estado)

        html += f"""
                    <tr>
                        <td>
                            <strong>{etapa.get('nombre', '')}</strong>
                            {f"<br><small>{etapa.get('descripcion', '')}</small>" if etapa.get('descripcion') else ''}
                        </td>
                        <td><span class="badge {badge_class}">{estado_label}</span></td>
                        <td>
                            <div class="progress-bar" style="width: 80px;">
                                <div class="progress-fill" style="width: {etapa.get('porcentaje_avance', 0)}%"></div>
                            </div>
                            <small>{etapa.get('porcentaje_avance', 0):.0f}%</small>
                        </td>
                        <td>{etapa.get('items_total', 0)}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
        </div>
    """

    # Materiales
    if materiales:
        html += """
        <div class="section">
            <h2>Materiales Utilizados</h2>
            <table>
                <thead>
                    <tr>
                        <th>Material</th>
                        <th>Cantidad</th>
                        <th>Etapa</th>
                        <th class="text-right">Costo Est.</th>
                    </tr>
                </thead>
                <tbody>
        """

        for mat in materiales:
            html += f"""
                    <tr>
                        <td>{mat.get('nombre', '')}</td>
                        <td>{mat.get('cantidad', 0)} {mat.get('unidad', '')}</td>
                        <td>{mat.get('etapa', '')}</td>
                        <td class="text-right">{fmt_currency(mat.get('costo_estimado'))}</td>
                    </tr>
            """

        html += f"""
                    <tr>
                        <td colspan="3"><strong>Total</strong></td>
                        <td class="text-right"><strong>{fmt_currency(resumen.get('costo_materiales', 0))}</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    # Gastos
    if gastos:
        html += """
        <div class="section">
            <h2>Gastos del Periodo</h2>
            <table>
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Descripcion</th>
                        <th>Categoria</th>
                        <th class="text-right">Monto</th>
                    </tr>
                </thead>
                <tbody>
        """

        for gasto in gastos:
            html += f"""
                    <tr>
                        <td>{gasto.get('fecha', '')}</td>
                        <td>{gasto.get('descripcion', '')}</td>
                        <td>{gasto.get('categoria', '')}</td>
                        <td class="text-right">{fmt_currency(gasto.get('monto', 0))}</td>
                    </tr>
            """

        html += f"""
                    <tr>
                        <td colspan="3"><strong>Total</strong></td>
                        <td class="text-right"><strong>{fmt_currency(resumen.get('total_gastos', 0))}</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    # Footer
    html += """
        <div class="footer">
            Reporte generado por Sistema Electro America
        </div>
    </body>
    </html>
    """

    return html

"""
Servicio para generación de reportes en PDF.
Usa ReportLab para generar PDFs (no requiere dependencias del sistema).
"""
import io
from datetime import date, datetime
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generar_pdf_reporte(datos: dict) -> bytes:
    """
    Genera un PDF del reporte de proyecto.

    Args:
        datos: Diccionario con los datos del reporte

    Returns:
        bytes del PDF generado
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Title2',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1e40af'),
        spaceBefore=12,
        spaceAfter=8,
        borderPadding=4,
        backColor=colors.HexColor('#f3f4f6')
    ))
    styles.add(ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontSize=9
    ))
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER
    ))

    # Elementos del PDF
    elements = []

    proyecto = datos.get('proyecto', {})
    periodo = datos.get('periodo', {})
    resumen = datos.get('resumen', {})
    etapas = datos.get('etapas', [])
    materiales = datos.get('materiales', [])
    gastos = datos.get('gastos', [])

    # Funciones de formato
    def fmt_currency(value):
        if value is None:
            return '-'
        return f"${value:,.2f}"

    def fmt_date(value):
        if value is None:
            return '-'
        if isinstance(value, str):
            return value
        return value.strftime('%d/%m/%Y')

    # Header
    elements.append(Paragraph(proyecto.get('nombre', 'Proyecto'), styles['Title2']))
    subtitle = f"{proyecto.get('ubicacion', '')} | Periodo: {periodo.get('desde', '')} - {periodo.get('hasta', '')}"
    elements.append(Paragraph(subtitle, styles['Subtitle']))
    elements.append(Spacer(1, 12))

    # Resumen en tabla
    avance = proyecto.get('porcentaje_avance', 0)
    etapas_completadas = resumen.get('etapas_completadas', 0)
    total_etapas = resumen.get('total_etapas', 0)
    costo_total = (resumen.get('costo_materiales', 0) or 0) + (resumen.get('total_gastos', 0) or 0)

    resumen_data = [
        ['Avance General', 'Etapas Completadas', 'Costo Total'],
        [f'{avance:.0f}%', f'{etapas_completadas}/{total_etapas}', fmt_currency(costo_total)]
    ]

    resumen_table = Table(resumen_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#6b7280')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    elements.append(resumen_table)
    elements.append(Spacer(1, 20))

    # Etapas
    elements.append(Paragraph('Etapas del Proyecto', styles['SectionHeader']))

    estado_labels = {
        'pendiente': 'Pendiente',
        'en_progreso': 'En Progreso',
        'completada': 'Completada',
        'pausada': 'Pausada',
    }

    etapas_data = [['Etapa', 'Estado', 'Avance', 'Items']]
    for etapa in etapas:
        estado = etapa.get('estado', 'pendiente')
        estado_label = estado_labels.get(estado, estado)
        avance_etapa = etapa.get('porcentaje_avance', 0)
        etapas_data.append([
            etapa.get('nombre', ''),
            estado_label,
            f'{avance_etapa:.0f}%',
            str(etapa.get('items_total', 0))
        ])

    if len(etapas_data) > 1:
        etapas_table = Table(etapas_data, colWidths=[7*cm, 3*cm, 3*cm, 2*cm])
        etapas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(etapas_table)
    elements.append(Spacer(1, 16))

    # Materiales
    if materiales:
        elements.append(Paragraph('Materiales Utilizados', styles['SectionHeader']))

        mat_data = [['Material', 'Cantidad', 'Etapa', 'Costo Est.']]
        for mat in materiales:
            mat_data.append([
                mat.get('nombre', ''),
                f"{mat.get('cantidad', 0)} {mat.get('unidad', '')}",
                mat.get('etapa', ''),
                fmt_currency(mat.get('costo_estimado'))
            ])
        # Total
        mat_data.append(['Total', '', '', fmt_currency(resumen.get('costo_materiales', 0))])

        mat_table = Table(mat_data, colWidths=[6*cm, 3*cm, 4*cm, 3*cm])
        mat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f9fafb')),
        ]))
        elements.append(mat_table)
        elements.append(Spacer(1, 16))

    # Gastos
    if gastos:
        elements.append(Paragraph('Gastos del Periodo', styles['SectionHeader']))

        gastos_data = [['Fecha', 'Descripcion', 'Categoria', 'Monto']]
        for gasto in gastos:
            gastos_data.append([
                gasto.get('fecha', ''),
                gasto.get('descripcion', ''),
                gasto.get('categoria', ''),
                fmt_currency(gasto.get('monto', 0))
            ])
        # Total
        gastos_data.append(['Total', '', '', fmt_currency(resumen.get('total_gastos', 0))])

        gastos_table = Table(gastos_data, colWidths=[3*cm, 6*cm, 4*cm, 3*cm])
        gastos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f9fafb')),
        ]))
        elements.append(gastos_table)

    # Footer
    elements.append(Spacer(1, 30))
    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(
        f'Reporte generado por Sistema Electro America - {fecha_generacion}',
        styles['Footer']
    ))

    # Generar PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes

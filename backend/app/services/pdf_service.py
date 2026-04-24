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


def generar_pdf_resumen_actividades(datos: dict) -> bytes:
    """
    Genera un PDF con el resumen de actividades y materiales del proyecto.

    Args:
        datos: Diccionario con proyecto, actividades, resumen y materiales_totales

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
        name='TitleRed',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#E53935'),
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='SubtitleGray',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#424242'),
        spaceAfter=16
    ))
    styles.add(ParagraphStyle(
        name='SectionRed',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#C62828'),
        spaceBefore=16,
        spaceAfter=10,
        borderPadding=6,
        backColor=colors.HexColor('#FFEBEE')
    ))
    styles.add(ParagraphStyle(
        name='FooterCenter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER
    ))

    elements = []

    proyecto = datos.get('proyecto', {})
    actividades = datos.get('actividades', [])
    resumen = datos.get('resumen', {})
    materiales_totales = datos.get('materiales_totales', [])

    # Header con nombre del proyecto
    elements.append(Paragraph(f"Resumen de Actividades", styles['TitleRed']))
    elements.append(Paragraph(proyecto.get('nombre', 'Proyecto'), styles['Heading1']))

    info_proyecto = []
    if proyecto.get('ubicacion'):
        info_proyecto.append(f"Ubicación: {proyecto.get('ubicacion')}")
    if proyecto.get('fecha_inicio'):
        info_proyecto.append(f"Inicio: {proyecto.get('fecha_inicio')}")
    if proyecto.get('cliente_nombre'):
        info_proyecto.append(f"Cliente: {proyecto.get('cliente_nombre')}")

    if info_proyecto:
        elements.append(Paragraph(' | '.join(info_proyecto), styles['SubtitleGray']))

    elements.append(Spacer(1, 12))

    # Resumen general en cards
    total_act = resumen.get('total_actividades', 0)
    completadas = resumen.get('actividades_completadas', 0)
    en_progreso = resumen.get('actividades_en_progreso', 0)
    pendientes = resumen.get('actividades_pendientes', 0)
    avance_global = resumen.get('porcentaje_avance_global', 0)

    resumen_data = [
        ['Total Actividades', 'Completadas', 'En Progreso', 'Pendientes', 'Avance Global'],
        [str(total_act), str(completadas), str(en_progreso), str(pendientes), f'{avance_global:.1f}%']
    ]

    resumen_table = Table(resumen_data, colWidths=[3.2*cm, 3.2*cm, 3.2*cm, 3.2*cm, 3.2*cm])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFEBEE')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#C62828')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#2e7d32')),  # Completadas verde
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#1565c0')),  # En progreso azul
        ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor('#757575')),  # Pendientes gris
        ('TEXTCOLOR', (4, 1), (4, 1), colors.HexColor('#E53935')),  # Avance rojo
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FFCDD2')),
    ]))
    elements.append(resumen_table)
    elements.append(Spacer(1, 20))

    # Lista de Actividades
    elements.append(Paragraph('Detalle de Actividades', styles['SectionRed']))

    if actividades:
        act_data = [['Código', 'Actividad', 'Categoría', 'Planif.', 'Ejecut.', 'Avance']]
        for act in actividades:
            porcentaje = act.get('porcentaje_avance', 0)
            estado_str = f'{porcentaje:.0f}%'
            if porcentaje >= 100:
                estado_str = '✓ 100%'

            act_data.append([
                act.get('actividad_codigo', ''),
                act.get('actividad_nombre', '')[:35],
                act.get('actividad_categoria', '')[:15],
                f"{act.get('cantidad_planificada', 0)} {act.get('unidad_trabajo', '')}",
                f"{act.get('cantidad_ejecutada', 0)} {act.get('unidad_trabajo', '')}",
                estado_str
            ])

        act_table = Table(act_data, colWidths=[2*cm, 5.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm])
        act_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C62828')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FFCDD2')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF8F8')]),
        ]))
        elements.append(act_table)
    else:
        elements.append(Paragraph('No hay actividades asignadas al proyecto.', styles['Normal']))

    elements.append(Spacer(1, 24))

    # Materiales Totales
    elements.append(Paragraph('Materiales Totales Requeridos', styles['SectionRed']))

    if materiales_totales:
        mat_data = [['Material', 'Cantidad Total', 'Unidad']]
        for mat in materiales_totales:
            cantidad = mat.get('cantidad_total', 0)
            if isinstance(cantidad, (int, float)):
                cantidad_str = f"{cantidad:.2f}"
            else:
                cantidad_str = str(cantidad)

            mat_data.append([
                mat.get('material_nombre', ''),
                cantidad_str,
                mat.get('unidad', '')
            ])

        mat_table = Table(mat_data, colWidths=[9*cm, 4*cm, 3*cm])
        mat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C62828')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FFCDD2')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF8F8')]),
        ]))
        elements.append(mat_table)
    else:
        elements.append(Paragraph('No hay materiales calculados para este proyecto.', styles['Normal']))

    # Footer
    elements.append(Spacer(1, 40))
    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(
        f'Electro América - Reporte generado el {fecha_generacion}',
        styles['FooterCenter']
    ))

    # Generar PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes

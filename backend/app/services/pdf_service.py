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


def generar_pdf_facturacion_proyecto(datos: dict) -> bytes:
    """Genera el "super remito" / detalle del proyecto finalizado para
    facturación. Incluye datos de la empresa, cliente, proyecto, lista
    de actividades ejecutadas con precios y subtotales, total y estado
    de facturación / cobro.
    """
    ROJO = colors.HexColor('#E53935')
    ROJO_OSCURO = colors.HexColor('#C62828')
    GRIS_FONDO = colors.HexColor('#F5F5F5')
    GRIS_BORDE = colors.HexColor('#E0E0E0')
    NEGRO = colors.HexColor('#1A1A1A')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"Detalle proyecto {datos.get('proyecto_nombre', '')}",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='HeaderTitle',
        parent=styles['Title'],
        fontSize=20,
        textColor=ROJO,
        alignment=TA_LEFT,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name='HeaderSub',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name='Section',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.white,
        backColor=ROJO,
        borderPadding=6,
        spaceBefore=14,
        spaceAfter=10,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name='Body',
        parent=styles['Normal'],
        fontSize=9,
        textColor=NEGRO,
        leading=12,
    ))
    styles.add(ParagraphStyle(
        name='SmallCenter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER,
    ))

    def fmt_money(v):
        try:
            return f"$ {float(v or 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except Exception:
            return "$ 0,00"

    def fmt_qty(v):
        try:
            return f"{float(v or 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except Exception:
            return "0,00"

    def fmt_date(v):
        if not v:
            return '-'
        if hasattr(v, 'strftime'):
            return v.strftime('%d/%m/%Y')
        s = str(v)
        if len(s) >= 10 and s[4] == '-':
            return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
        return s

    estado_label = {
        'pendiente': 'PENDIENTE DE FACTURAR',
        'facturado': 'FACTURADO',
        'cobrado': 'COBRADO',
    }.get(datos.get('estado_facturacion', 'pendiente'), 'PENDIENTE')
    estado_color = {
        'pendiente': colors.HexColor('#F59E0B'),
        'facturado': colors.HexColor('#3B82F6'),
        'cobrado': colors.HexColor('#10B981'),
    }.get(datos.get('estado_facturacion', 'pendiente'), colors.HexColor('#9CA3AF'))

    elements = []

    # ============ Header ============
    header_left = [
        Paragraph('ELECTRO AMERICA', styles['HeaderTitle']),
        Paragraph('Servicios de Ingeniería y Construcción', styles['HeaderSub']),
    ]
    header_right_text = (
        f"<b>DETALLE DE PROYECTO</b><br/>"
        f"Fecha de emisión: {fmt_date(datos.get('fecha_emision'))}"
    )
    header_right = [Paragraph(header_right_text, ParagraphStyle(
        name='HeaderRightDoc',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_RIGHT,
        leading=12,
    ))]
    header_table = Table(
        [[header_left, header_right]],
        colWidths=[10 * cm, 7.4 * cm],
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, ROJO),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 6))

    # ============ Estado ============
    estado_table = Table(
        [[Paragraph(f"<b>ESTADO:</b> {estado_label}", ParagraphStyle(
            name='Estado', parent=styles['Normal'], fontSize=11,
            textColor=colors.white, alignment=TA_CENTER,
        ))]],
        colWidths=[17.4 * cm],
    )
    estado_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), estado_color),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(estado_table)

    # ============ Cliente / Proyecto ============
    elements.append(Paragraph('CLIENTE Y PROYECTO', styles['Section']))
    info_data = [
        ['Proyecto', datos.get('proyecto_nombre', '-')],
        ['Cliente', datos.get('cliente_nombre') or '-'],
        ['Ubicación', datos.get('ubicacion') or '-'],
        ['Lista de precios', datos.get('lista_precio_nombre') or '-'],
        ['Fecha inicio', fmt_date(datos.get('fecha_inicio'))],
        ['Fecha finalización', fmt_date(datos.get('fecha_fin_real'))],
    ]
    info_table = Table(info_data, colWidths=[4.5 * cm, 12.9 * cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
        ('BACKGROUND', (0, 0), (0, -1), GRIS_FONDO),
        ('GRID', (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)

    # ============ Facturación ============
    if datos.get('estado_facturacion') != 'pendiente':
        elements.append(Paragraph('FACTURACIÓN', styles['Section']))
        fact_data = [
            ['Nº de factura', datos.get('numero_factura') or '-'],
            ['Fecha de facturación', fmt_date(datos.get('fecha_facturacion'))],
            ['Monto facturado', fmt_money(datos.get('monto_facturado'))],
        ]
        if datos.get('estado_facturacion') == 'cobrado':
            fact_data.append(['Fecha de cobro', fmt_date(datos.get('fecha_cobro'))])
        fact_table = Table(fact_data, colWidths=[4.5 * cm, 12.9 * cm])
        fact_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
            ('BACKGROUND', (0, 0), (0, -1), GRIS_FONDO),
            ('GRID', (0, 0), (-1, -1), 0.4, GRIS_BORDE),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(fact_table)

    # ============ Detalle de actividades ============
    elements.append(Paragraph('DETALLE DE ACTIVIDADES EJECUTADAS', styles['Section']))
    items = datos.get('items', [])

    detalle_data = [[
        Paragraph('<b>Actividad</b>', styles['Body']),
        Paragraph('<b>Unidad</b>', styles['Body']),
        Paragraph('<b>Planif.</b>', styles['Body']),
        Paragraph('<b>Ejec.</b>', styles['Body']),
        Paragraph('<b>P. unit.</b>', styles['Body']),
        Paragraph('<b>Subtotal</b>', styles['Body']),
    ]]
    for it in items:
        nombre = it.get('actividad_nombre') or '-'
        if it.get('actividad_codigo'):
            nombre = f"{it['actividad_codigo']} · {nombre}"
        detalle_data.append([
            Paragraph(nombre, styles['Body']),
            Paragraph(it.get('unidad') or '-', styles['Body']),
            Paragraph(fmt_qty(it.get('cantidad_planificada')), styles['Body']),
            Paragraph(fmt_qty(it.get('cantidad_ejecutada')), styles['Body']),
            Paragraph(fmt_money(it.get('precio_unitario_snapshot')), styles['Body']),
            Paragraph(fmt_money(it.get('subtotal_ejecutado')), styles['Body']),
        ])

    if len(detalle_data) == 1:
        detalle_data.append([
            Paragraph('<i>El proyecto no tiene actividades cargadas.</i>', styles['Body']),
            '', '', '', '', '',
        ])

    detalle_table = Table(
        detalle_data,
        colWidths=[6.0 * cm, 1.8 * cm, 1.8 * cm, 1.8 * cm, 2.8 * cm, 3.2 * cm],
        repeatRows=1,
    )
    detalle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ROJO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRIS_FONDO]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(detalle_table)

    # ============ Totales ============
    elements.append(Spacer(1, 8))
    totales_data = [
        ['Total presupuestado', fmt_money(datos.get('total_presupuestado'))],
        ['Total ejecutado', fmt_money(datos.get('total_ejecutado'))],
    ]
    totales_table = Table(totales_data, colWidths=[12.4 * cm, 5.0 * cm])
    totales_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, 1), 12),
        ('TEXTCOLOR', (0, 1), (-1, 1), ROJO_OSCURO),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 1), (-1, 1), GRIS_FONDO),
        ('LINEABOVE', (0, 1), (-1, 1), 1.5, ROJO),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(totales_table)

    # ============ Footer ============
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(
        f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} — Electro América",
        styles['SmallCenter'],
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

"""Generador de PDF para el stock consolidado de un deposito."""
import io
import os
from datetime import datetime
from typing import List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "logo.jpg",
)

ROJO = colors.HexColor("#E53935")
NEGRO = colors.HexColor("#1A1A1A")
GRIS = colors.HexColor("#666666")
GRIS_CLARO = colors.HexColor("#F5F5F5")


def generar_pdf_stock_deposito(data: dict) -> bytes:
    """Genera el PDF del stock consolidado de un deposito.

    `data` debe tener:
      - deposito_nombre, cliente_nombre, fecha (datetime), usuario_nombre
      - subdepositos: list[str] (nombres) — opcional, para listar contexto
      - items: list[dict] {material_codigo, material_nombre, material_unidad, stock_total}
    """
    buffer = io.BytesIO()
    # Landscape A4 (29.7cm x 21cm) para dar mas ancho a las celdas y
    # evitar que codigos/nombres largos se superpongan.
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    h_subtitle = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=NEGRO, alignment=TA_CENTER, spaceAfter=6,
    )
    h_info = ParagraphStyle(
        "Info", parent=styles["Normal"],
        fontSize=9, textColor=GRIS, alignment=TA_CENTER, spaceAfter=2,
    )
    h_seccion = ParagraphStyle(
        "Seccion", parent=styles["Heading3"],
        fontSize=11, textColor=ROJO, spaceBefore=8, spaceAfter=4,
    )
    p_footer = ParagraphStyle(
        "PFooter", parent=styles["Normal"],
        fontSize=8, textColor=GRIS, alignment=TA_CENTER,
    )

    elements = []

    # Logo
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=5 * cm, height=1.32 * cm)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 2))

    elements.append(Paragraph("CONTROL DE STOCK", h_subtitle))

    titulo_dep = data.get("deposito_nombre") or "-"
    cliente = data.get("cliente_nombre")
    if cliente:
        elements.append(Paragraph(
            f"<b>{titulo_dep}</b> &mdash; {cliente}",
            ParagraphStyle("DepInfo", parent=styles["Normal"],
                           fontSize=11, textColor=NEGRO, alignment=TA_CENTER,
                           spaceAfter=2),
        ))
    else:
        elements.append(Paragraph(
            f"<b>{titulo_dep}</b>",
            ParagraphStyle("DepInfo", parent=styles["Normal"],
                           fontSize=11, textColor=NEGRO, alignment=TA_CENTER,
                           spaceAfter=2),
        ))

    fecha_str = (data.get("fecha") or datetime.now()).strftime("%d/%m/%Y %H:%M")
    subdeps: List[str] = data.get("subdepositos") or []
    if subdeps:
        elements.append(Paragraph(
            f"Incluye subdepositos: {', '.join(subdeps)}",
            h_info,
        ))
    elements.append(Paragraph(f"Generado: {fecha_str}", h_info))
    elements.append(Spacer(1, 8))

    items = data.get("items", [])
    elements.append(Paragraph(
        f"Materiales: {len(items)}", h_seccion,
    ))

    if not items:
        elements.append(Paragraph(
            "Este deposito no tiene materiales cargados.",
            ParagraphStyle("Empty", parent=styles["Normal"],
                           fontSize=10, textColor=GRIS, alignment=TA_CENTER,
                           spaceAfter=10),
        ))
    else:
        # Estilos para celdas con wrap automatico. wordWrap='CJK' fuerza
        # a partir palabras aunque no haya espacio, asi codigos largos
        # como 'PRENSACABLE C/TUERCA' nunca se desbordan.
        cell_left = ParagraphStyle(
            "CellLeft", parent=styles["Normal"],
            fontSize=9, textColor=NEGRO, leading=11, alignment=TA_LEFT,
            wordWrap="CJK",
        )
        cell_code = ParagraphStyle(
            "CellCode", parent=cell_left,
            fontName="Helvetica-Bold",
        )

        def _escape(s):
            return (str(s or "-")
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;"))

        header = [
            Paragraph("<b>Codigo</b>", ParagraphStyle("H", parent=cell_left, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Material</b>", ParagraphStyle("H", parent=cell_left, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Unidad</b>", ParagraphStyle("H", parent=cell_left, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Stock sistema</b>", ParagraphStyle("H", parent=cell_left, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Conteo fisico</b>", ParagraphStyle("H", parent=cell_left, textColor=colors.white, alignment=TA_CENTER)),
        ]
        data_tbl = [header]
        for it in items:
            data_tbl.append([
                Paragraph(_escape(it.get("material_codigo")), cell_code),
                Paragraph(_escape(it.get("material_nombre")), cell_left),
                it.get("material_unidad") or "-",
                f"{float(it.get('stock_total', 0)):.2f}",
                "",
            ])

        # Landscape A4 util ~26.7cm: codigo + nombre + unidad + stock + conteo
        tbl = Table(
            data_tbl,
            colWidths=[5 * cm, 10 * cm, 2 * cm, 3.4 * cm, 4 * cm],
            repeatRows=1,
        )
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ROJO),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTSIZE", (2, 1), (-1, -1), 9),
            ("ALIGN", (2, 1), (4, -1), "CENTER"),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.4, GRIS),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            # Asegura espacio minimo para escribir a mano en 'Conteo fisico'
            ("MINROWHEIGHT", (0, 1), (-1, -1), 22),
        ]))
        elements.append(tbl)

    elements.append(Spacer(1, 10))
    usuario = data.get("usuario_nombre") or "-"
    elements.append(Paragraph(
        f"Generado por: {usuario}", p_footer,
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_detalle_movimientos_deposito(data: dict) -> bytes:
    """PDF con el detalle de movimientos del deposito en un periodo.

    Muestra en una sola pieza:
      - Ingresos al deposito (padre + subdepositos), agregado por material.
      - Egresos por cada subdeposito (y el deposito principal si tuvo
        salidas directas), agregado por material.
      - Stock actual por subdeposito.

    `data` debe tener:
      - deposito_nombre, cliente_nombre, fecha (datetime), usuario_nombre
      - fecha_desde, fecha_hasta (date | None)
      - ingresos_por_material: list[dict] {material_codigo, material_nombre,
                                           material_unidad, cantidad_total,
                                           remitos_count}
      - egresos_por_subdeposito: list[dict] {
            subdeposito_nombre,
            es_principal (bool),
            items: list[dict] {material_codigo, material_nombre,
                               material_unidad, cantidad_total},
            cantidad_remitos (int),
          }
      - stock_por_subdeposito: list[dict] {
            subdeposito_nombre,
            es_principal (bool),
            items: list[dict] {material_codigo, material_nombre,
                               material_unidad, stock_actual},
          }
      - totales: dict {ingresos_total_items, egresos_total_items,
                        remitos_ingreso, remitos_egreso}
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = getSampleStyleSheet()
    h_subtitle = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=12, textColor=NEGRO, alignment=TA_CENTER, spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    h_info = ParagraphStyle(
        "Info", parent=styles["Normal"],
        fontSize=9, textColor=GRIS, alignment=TA_CENTER, spaceAfter=1,
    )
    h_seccion = ParagraphStyle(
        "Seccion", parent=styles["Heading3"],
        fontSize=11, textColor=colors.white, spaceBefore=6, spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    h_sub_seccion = ParagraphStyle(
        "SubSeccion", parent=styles["Normal"],
        fontSize=10, textColor=NEGRO, spaceBefore=4, spaceAfter=2,
        fontName="Helvetica-Bold",
    )
    p_footer = ParagraphStyle(
        "PFooter", parent=styles["Normal"],
        fontSize=8, textColor=GRIS, alignment=TA_CENTER,
    )
    cell_left = ParagraphStyle(
        "CellLeft", parent=styles["Normal"],
        fontSize=8.5, textColor=NEGRO, leading=10, alignment=TA_LEFT,
        wordWrap="CJK",
    )
    cell_code = ParagraphStyle(
        "CellCode", parent=cell_left, fontName="Helvetica-Bold",
    )
    header_style = ParagraphStyle(
        "H", parent=cell_left, textColor=colors.white,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    empty_style = ParagraphStyle(
        "Empty", parent=styles["Normal"],
        fontSize=9, textColor=GRIS, alignment=TA_CENTER,
        spaceBefore=4, spaceAfter=6,
    )

    def _escape(s):
        return (str(s or "-")
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

    def _banda_titulo(texto: str) -> Table:
        """Banda roja con titulo de seccion."""
        t = Table(
            [[Paragraph(texto, h_seccion)]],
            colWidths=[27.3 * cm],
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ROJO),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    def _tabla_materiales_con_cantidad(items: List[dict], col_cantidad_titulo: str) -> Table:
        """Tabla estandar: codigo | material | unidad | cantidad."""
        header = [
            Paragraph("Codigo", header_style),
            Paragraph("Material", header_style),
            Paragraph("Unidad", header_style),
            Paragraph(col_cantidad_titulo, header_style),
        ]
        rows = [header]
        for it in items:
            rows.append([
                Paragraph(_escape(it.get("material_codigo")), cell_code),
                Paragraph(_escape(it.get("material_nombre")), cell_left),
                Paragraph(_escape(it.get("material_unidad")), cell_left),
                f"{float(it.get('cantidad_total', it.get('stock_actual', 0)) or 0):.2f}",
            ])
        tbl = Table(
            rows,
            colWidths=[4.5 * cm, 15.3 * cm, 3.5 * cm, 4 * cm],
            repeatRows=1,
        )
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NEGRO),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTSIZE", (2, 1), (-1, -1), 8.5),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.3, GRIS),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return tbl

    elements = []

    # ============ Encabezado ============
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=4.5 * cm, height=1.19 * cm)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 2))

    elements.append(Paragraph("DETALLE DE MOVIMIENTOS", h_subtitle))

    titulo_dep = data.get("deposito_nombre") or "-"
    cliente = data.get("cliente_nombre")
    if cliente:
        elements.append(Paragraph(
            f"<b>{_escape(titulo_dep)}</b> &mdash; {_escape(cliente)}",
            ParagraphStyle("DepInfo", parent=styles["Normal"],
                           fontSize=11, textColor=NEGRO, alignment=TA_CENTER,
                           spaceAfter=2),
        ))
    else:
        elements.append(Paragraph(
            f"<b>{_escape(titulo_dep)}</b>",
            ParagraphStyle("DepInfo", parent=styles["Normal"],
                           fontSize=11, textColor=NEGRO, alignment=TA_CENTER,
                           spaceAfter=2),
        ))

    fecha_desde = data.get("fecha_desde")
    fecha_hasta = data.get("fecha_hasta")
    if fecha_desde and fecha_hasta:
        periodo_txt = f"Periodo: {fecha_desde.strftime('%d/%m/%Y')} al {fecha_hasta.strftime('%d/%m/%Y')}"
    elif fecha_desde:
        periodo_txt = f"Desde: {fecha_desde.strftime('%d/%m/%Y')}"
    elif fecha_hasta:
        periodo_txt = f"Hasta: {fecha_hasta.strftime('%d/%m/%Y')}"
    else:
        periodo_txt = "Periodo: historico completo"
    elements.append(Paragraph(periodo_txt, h_info))

    fecha_str = (data.get("fecha") or datetime.now()).strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Generado: {fecha_str}", h_info))

    # Resumen KPI
    totales = data.get("totales") or {}
    kpi_row = (
        f"Ingresos: <b>{totales.get('remitos_ingreso', 0)}</b> remitos, "
        f"<b>{totales.get('ingresos_total_items', 0)}</b> lineas &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Egresos: <b>{totales.get('remitos_egreso', 0)}</b> remitos, "
        f"<b>{totales.get('egresos_total_items', 0)}</b> lineas"
    )
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        kpi_row,
        ParagraphStyle("KPI", parent=styles["Normal"],
                       fontSize=9.5, textColor=NEGRO, alignment=TA_CENTER,
                       spaceAfter=6),
    ))

    # ============ INGRESOS ============
    ingresos = data.get("ingresos_por_material") or []
    elements.append(_banda_titulo(
        f"1. INGRESOS AL DEPOSITO ({len(ingresos)} materiales)"
    ))
    if not ingresos:
        elements.append(Paragraph(
            "Sin ingresos registrados en el periodo.", empty_style,
        ))
    else:
        elements.append(_tabla_materiales_con_cantidad(
            ingresos, "Cant. ingresada",
        ))
    elements.append(Spacer(1, 8))

    # ============ EGRESOS POR SUBDEPOSITO ============
    egresos = data.get("egresos_por_subdeposito") or []
    total_grupos_egreso = sum(1 for g in egresos if (g.get("items") or []))
    elements.append(_banda_titulo(
        f"2. EGRESOS POR SUBDEPOSITO ({total_grupos_egreso} destinos)"
    ))
    if not any((g.get("items") or []) for g in egresos):
        elements.append(Paragraph(
            "Sin egresos registrados en el periodo.", empty_style,
        ))
    else:
        for grupo in egresos:
            items = grupo.get("items") or []
            if not items:
                continue
            label = grupo.get("subdeposito_nombre") or "-"
            if grupo.get("es_principal"):
                label = f"{label} (deposito principal)"
            cant_remitos = grupo.get("cantidad_remitos", 0)
            titulo = (
                f"&#9656; <b>{_escape(label)}</b> &mdash; "
                f"{len(items)} materiales &middot; {cant_remitos} remitos"
            )
            elements.append(KeepTogether([
                Paragraph(titulo, h_sub_seccion),
                _tabla_materiales_con_cantidad(items, "Cant. consumida"),
                Spacer(1, 6),
            ]))

    elements.append(Spacer(1, 6))

    # ============ STOCK ACTUAL ============
    stock = data.get("stock_por_subdeposito") or []
    total_grupos_stock = sum(1 for g in stock if (g.get("items") or []))
    elements.append(_banda_titulo(
        f"3. STOCK ACTUAL POR SUBDEPOSITO ({total_grupos_stock} depositos)"
    ))
    if not any((g.get("items") or []) for g in stock):
        elements.append(Paragraph(
            "Sin stock cargado.", empty_style,
        ))
    else:
        for grupo in stock:
            items = grupo.get("items") or []
            if not items:
                continue
            label = grupo.get("subdeposito_nombre") or "-"
            if grupo.get("es_principal"):
                label = f"{label} (deposito principal)"
            titulo = (
                f"&#9656; <b>{_escape(label)}</b> &mdash; "
                f"{len(items)} materiales"
            )
            elements.append(KeepTogether([
                Paragraph(titulo, h_sub_seccion),
                _tabla_materiales_con_cantidad(items, "Stock actual"),
                Spacer(1, 6),
            ]))

    elements.append(Spacer(1, 8))
    usuario = data.get("usuario_nombre") or "-"
    elements.append(Paragraph(
        f"Generado por: {usuario}", p_footer,
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

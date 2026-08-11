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

    Estructura (tabla cruzada material x subdeposito):
      1. INGRESOS: filas=materiales, columnas=subdeps con movimiento + Total.
      2. EGRESOS: idem. Atribuido al subdep del remito (no la cascada).
      3. STOCK CALCULADO: total ingresado - total egresado por material.

    `data` debe tener:
      - deposito_nombre, cliente_nombre, fecha (datetime), usuario_nombre
      - fecha_desde, fecha_hasta (date | None)
      - ingresos_columnas: list[{deposito_id, nombre, es_principal}]
      - ingresos_filas: list[{material_codigo, material_nombre, material_unidad,
                              por_deposito: list[float], total: float}]
      - egresos_columnas, egresos_filas: idem estructura
      - stock_filas: list[{material_codigo, material_nombre, material_unidad,
                           total_ingresado, total_egresado, stock_calculado}]
      - totales: {ingresos_materiales, egresos_materiales,
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

    # Ancho util de la pagina (landscape A4 - margenes)
    ancho_util_cm = 27.3

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
        alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=9,
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

    def _num(v: float) -> str:
        """Formatea numero: sin decimales si es entero, si no con 2."""
        f = float(v or 0)
        if f == int(f):
            return f"{int(f)}"
        return f"{f:.2f}"

    def _banda_titulo(texto: str) -> Table:
        t = Table(
            [[Paragraph(texto, h_seccion)]],
            colWidths=[ancho_util_cm * cm],
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ROJO),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    def _tabla_cruzada(columnas: list, filas: list, titulo_total: str) -> Table:
        """Tabla cruzada: Codigo | Material | Unidad | <subdep_1> | ... | Total.

        Ajusta anchos dinamicamente segun cantidad de subdeps.
        """
        n_subdeps = max(1, len(columnas))
        # Anchos fijos
        w_codigo = 3.0
        w_unidad = 1.6
        w_total = 2.3
        # Ancho por columna de subdep (min 1.5cm, max 3cm)
        w_sub_disponible = ancho_util_cm - w_codigo - w_unidad - w_total - 5.0
        w_sub = max(1.5, min(3.0, w_sub_disponible / n_subdeps))
        w_material = ancho_util_cm - w_codigo - w_unidad - w_total - (w_sub * n_subdeps)
        if w_material < 4.0:
            w_material = 4.0

        col_widths = [
            w_codigo * cm,
            w_material * cm,
            w_unidad * cm,
        ] + [w_sub * cm] * n_subdeps + [w_total * cm]

        # Header
        header = [
            Paragraph("Codigo", header_style),
            Paragraph("Material", header_style),
            Paragraph("Unidad", header_style),
        ]
        for c in columnas:
            label = c.get("nombre") or "-"
            if c.get("es_principal"):
                label = f"{label} (principal)"
            header.append(Paragraph(_escape(label), header_style))
        header.append(Paragraph(_escape(titulo_total), header_style))

        rows = [header]
        for f in filas:
            fila = [
                Paragraph(_escape(f.get("material_codigo")), cell_code),
                Paragraph(_escape(f.get("material_nombre")), cell_left),
                Paragraph(_escape(f.get("material_unidad")), cell_left),
            ]
            por_dep = f.get("por_deposito") or []
            for v in por_dep:
                fila.append(_num(v))
            fila.append(f"<b>{_num(f.get('total', 0))}</b>")
            # El total en negrita: envuelvo en Paragraph
            fila[-1] = Paragraph(fila[-1], ParagraphStyle(
                "TotalCell", parent=cell_left,
                fontName="Helvetica-Bold", alignment=TA_RIGHT,
            ))
            rows.append(fila)

        tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        # Estilos base
        estilo = [
            ("BACKGROUND", (0, 0), (-1, 0), NEGRO),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTSIZE", (2, 1), (-1, -1), 8.5),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            # Columnas de cantidades (subdeps + total): alineadas a la derecha
            ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.3, GRIS),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            # Resalta columna Total con fondo suave
            ("BACKGROUND", (-1, 1), (-1, -1), colors.HexColor("#FFF4E5")),
        ]
        tbl.setStyle(TableStyle(estilo))
        return tbl

    def _tabla_stock_calculado(filas: list) -> Table:
        """Tabla: Codigo | Material | Unidad | Total ingresado | Total egresado | Stock."""
        col_widths = [
            3.0 * cm,   # Codigo
            (ancho_util_cm - 3.0 - 1.8 - 3.0 - 3.0 - 3.0) * cm,  # Material
            1.8 * cm,   # Unidad
            3.0 * cm,   # Total ingresado
            3.0 * cm,   # Total egresado
            3.0 * cm,   # Stock calculado
        ]
        header = [
            Paragraph("Codigo", header_style),
            Paragraph("Material", header_style),
            Paragraph("Unidad", header_style),
            Paragraph("Total ingresado", header_style),
            Paragraph("Total egresado", header_style),
            Paragraph("Stock (ingresos - egresos)", header_style),
        ]
        rows = [header]
        stock_bold = ParagraphStyle(
            "StockCell", parent=cell_left,
            fontName="Helvetica-Bold", alignment=TA_RIGHT,
        )
        for f in filas:
            stock = f.get("stock_calculado", 0)
            rows.append([
                Paragraph(_escape(f.get("material_codigo")), cell_code),
                Paragraph(_escape(f.get("material_nombre")), cell_left),
                Paragraph(_escape(f.get("material_unidad")), cell_left),
                _num(f.get("total_ingresado", 0)),
                _num(f.get("total_egresado", 0)),
                Paragraph(_num(stock), stock_bold),
            ])
        tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        estilo = [
            ("BACKGROUND", (0, 0), (-1, 0), NEGRO),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTSIZE", (2, 1), (-1, -1), 8.5),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.3, GRIS),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BACKGROUND", (-1, 1), (-1, -1), colors.HexColor("#FFF4E5")),
        ]
        # Colorea rojo suave las filas con stock negativo (mas egresos que ingresos)
        for i, f in enumerate(filas, start=1):
            if f.get("stock_calculado", 0) < 0:
                estilo.append(("BACKGROUND", (-1, i), (-1, i), colors.HexColor("#FFD6D6")))
        tbl.setStyle(TableStyle(estilo))
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

    totales = data.get("totales") or {}
    kpi_row = (
        f"Ingresos: <b>{totales.get('remitos_ingreso', 0)}</b> remitos, "
        f"<b>{totales.get('ingresos_materiales', 0)}</b> materiales &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Egresos: <b>{totales.get('remitos_egreso', 0)}</b> remitos, "
        f"<b>{totales.get('egresos_materiales', 0)}</b> materiales"
    )
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        kpi_row,
        ParagraphStyle("KPI", parent=styles["Normal"],
                       fontSize=9.5, textColor=NEGRO, alignment=TA_CENTER,
                       spaceAfter=6),
    ))

    # ============ 1. INGRESOS ============
    ingresos_columnas = data.get("ingresos_columnas") or []
    ingresos_filas = data.get("ingresos_filas") or []
    elements.append(_banda_titulo(
        f"1. INGRESOS POR SUBDEPOSITO ({len(ingresos_filas)} materiales)"
    ))
    if not ingresos_filas:
        elements.append(Paragraph(
            "Sin ingresos registrados en el periodo.", empty_style,
        ))
    else:
        elements.append(_tabla_cruzada(
            ingresos_columnas, ingresos_filas, "Total ingresado",
        ))
    elements.append(Spacer(1, 10))

    # ============ 2. EGRESOS ============
    egresos_columnas = data.get("egresos_columnas") or []
    egresos_filas = data.get("egresos_filas") or []
    elements.append(_banda_titulo(
        f"2. EGRESOS POR SUBDEPOSITO ({len(egresos_filas)} materiales)"
    ))
    if not egresos_filas:
        elements.append(Paragraph(
            "Sin egresos registrados en el periodo.", empty_style,
        ))
    else:
        elements.append(_tabla_cruzada(
            egresos_columnas, egresos_filas, "Total egresado",
        ))
    elements.append(Spacer(1, 10))

    # ============ 3. STOCK CALCULADO ============
    stock_filas = data.get("stock_filas") or []
    elements.append(_banda_titulo(
        f"3. STOCK CALCULADO (INGRESOS - EGRESOS) — {len(stock_filas)} materiales"
    ))
    if not stock_filas:
        elements.append(Paragraph(
            "Sin movimientos en el periodo.", empty_style,
        ))
    else:
        elements.append(_tabla_stock_calculado(stock_filas))

    elements.append(Spacer(1, 8))
    usuario = data.get("usuario_nombre") or "-"
    elements.append(Paragraph(
        f"Generado por: {usuario}", p_footer,
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

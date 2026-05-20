"""Generador de PDF para el stock consolidado de un deposito."""
import io
import os
from datetime import datetime
from typing import List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


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
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.8 * cm,
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
        # Tabla con columna 'Conteo fisico' a la derecha para llenar a mano
        data_tbl = [["Codigo", "Material", "Unidad", "Stock sistema", "Conteo fisico"]]
        for it in items:
            data_tbl.append([
                it.get("material_codigo") or "-",
                it.get("material_nombre") or "-",
                it.get("material_unidad") or "-",
                f"{float(it.get('stock_total', 0)):.2f}",
                "",
            ])

        tbl = Table(
            data_tbl,
            colWidths=[3 * cm, 7.5 * cm, 1.8 * cm, 2.6 * cm, 2.6 * cm],
            repeatRows=1,
        )
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ROJO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (2, 1), (4, -1), "CENTER"),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.4, GRIS),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            # La ultima columna queda vacia (alta) para escribir a mano
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

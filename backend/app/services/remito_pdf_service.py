"""Generador de PDF para remitos de salida de materiales."""
import io
import os
from datetime import datetime
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


# Identidad visual Electro America
ROJO = colors.HexColor("#E53935")
NEGRO = colors.HexColor("#1A1A1A")
GRIS = colors.HexColor("#666666")
GRIS_CLARO = colors.HexColor("#F5F5F5")


def generar_pdf_remito(remito_data: dict) -> bytes:
    """Genera el PDF de un remito.

    `remito_data` debe ser el dict producido por `remito_service.to_response_dict`.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    h_titulo = ParagraphStyle(
        "RemitoTitulo", parent=styles["Title"],
        fontSize=22, textColor=ROJO, alignment=TA_CENTER, spaceAfter=2,
    )
    h_numero = ParagraphStyle(
        "RemitoNumero", parent=styles["Normal"],
        fontSize=14, textColor=NEGRO, alignment=TA_CENTER, spaceAfter=10,
    )
    h_seccion = ParagraphStyle(
        "Seccion", parent=styles["Heading3"],
        fontSize=11, textColor=ROJO, spaceBefore=10, spaceAfter=6,
    )
    p_normal = ParagraphStyle(
        "PNormal", parent=styles["Normal"],
        fontSize=10, textColor=NEGRO, spaceAfter=2,
    )
    p_label = ParagraphStyle(
        "PLabel", parent=styles["Normal"],
        fontSize=9, textColor=GRIS, spaceAfter=0,
    )
    p_footer = ParagraphStyle(
        "PFooter", parent=styles["Normal"],
        fontSize=8, textColor=GRIS, alignment=TA_CENTER,
    )

    elements = []

    # Cabecera con logo (proporcion 648:171, ancho 6cm => alto ~1.58cm)
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=6 * cm, height=1.58 * cm)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 4))
    else:
        # Fallback si por algun motivo no esta el logo
        elements.append(Paragraph("ELECTRO AMERICA", h_titulo))

    es_ingreso = (remito_data.get("tipo") or "egreso") == "ingreso"
    subtitulo = "REMITO DE INGRESO" if es_ingreso else "REMITO DE SALIDA"
    elements.append(Paragraph(subtitulo, ParagraphStyle(
        "Subtitle", parent=styles["Normal"], fontSize=11, textColor=NEGRO,
        alignment=TA_CENTER, spaceAfter=4,
    )))
    elements.append(Paragraph(
        f"<b>N° {remito_data.get('numero_formateado', '')}</b>", h_numero
    ))

    # Datos generales en tabla 2 columnas
    fecha = remito_data.get("fecha")
    fecha_str = fecha.strftime("%d/%m/%Y") if fecha else "-"
    creado = remito_data.get("created_at")
    creado_str = creado.strftime("%d/%m/%Y %H:%M") if creado else "-"

    deposito_label = remito_data.get("deposito_nombre") or (
        "Stock global / Catálogo" if es_ingreso else "-"
    )
    if remito_data.get("deposito_padre_nombre"):
        deposito_label = f"{remito_data['deposito_padre_nombre']} → {deposito_label}"

    label_destinatario = "Proveedor:" if es_ingreso else "Destinatario:"
    label_responsable = "Responsable recibe:" if es_ingreso else "Responsable retira:"

    info_rows = [
        ["Fecha:", fecha_str, "Depósito:", deposito_label],
        ["Proyecto:", remito_data.get("proyecto_nombre") or "-",
         label_destinatario, remito_data.get("destinatario_texto") or "-"],
        [label_responsable, remito_data.get("responsable_retira") or "-",
         "Transportista:", remito_data.get("transportista") or "-"],
    ]
    direccion = remito_data.get("direccion_entrega")
    if direccion:
        info_rows.append(["Dirección entrega:", direccion, "", ""])

    tbl_info = Table(info_rows, colWidths=[3.2 * cm, 5.3 * cm, 3.2 * cm, 5.3 * cm])
    tbl_info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), GRIS),
        ("TEXTCOLOR", (2, 0), (2, -1), GRIS),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(tbl_info)
    elements.append(Spacer(1, 8))

    # Tabla de items
    titulo_items = "Materiales recibidos" if es_ingreso else "Materiales entregados"
    elements.append(Paragraph(titulo_items, h_seccion))

    items = remito_data.get("items", [])
    data_tbl = [["Código", "Material", "Cantidad", "Unidad"]]
    for it in items:
        data_tbl.append([
            it.get("material_codigo") or "-",
            it.get("material_nombre") or "-",
            f"{float(it.get('cantidad', 0)):.2f}",
            it.get("material_unidad") or "-",
        ])

    tbl_items = Table(data_tbl, colWidths=[3.5 * cm, 8.5 * cm, 2.5 * cm, 2.5 * cm])
    tbl_items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ROJO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("ALIGN", (3, 1), (3, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.4, GRIS),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(tbl_items)

    # Observaciones
    obs = remito_data.get("observaciones")
    if obs:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Observaciones", h_seccion))
        elements.append(Paragraph(obs.replace("\n", "<br/>"), p_normal))

    # Firmas
    elements.append(Spacer(1, 30))
    firma_rows = [["", ""], ["Firma quien entrega", "Firma quien recibe"]]
    # Para ingresos invierto los roles solo visualmente
    if es_ingreso:
        firma_rows = [["", ""], ["Firma del proveedor", "Firma quien recibe"]]
    tbl_firmas = Table(firma_rows, colWidths=[8 * cm, 8 * cm])
    tbl_firmas.setStyle(TableStyle([
        ("LINEABOVE", (0, 1), (-1, 1), 0.5, NEGRO),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("TEXTCOLOR", (0, 1), (-1, 1), GRIS),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 30),
    ]))
    elements.append(tbl_firmas)

    # Footer
    elements.append(Spacer(1, 12))
    usuario = remito_data.get("usuario_nombre") or "-"
    elements.append(Paragraph(
        f"Generado por: {usuario} | {creado_str}", p_footer
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

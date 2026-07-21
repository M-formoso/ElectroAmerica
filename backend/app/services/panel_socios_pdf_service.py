"""Generador de PDF del Panel de Socios."""
import io
import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.schemas.socio import ResumenPanelSocios


LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "logo.jpg",
)

ROJO = colors.HexColor("#E53935")
NEGRO = colors.HexColor("#1A1A1A")
GRIS = colors.HexColor("#666666")
GRIS_CLARO = colors.HexColor("#F5F5F5")
VERDE = colors.HexColor("#059669")
ROJO_ERROR = colors.HexColor("#DC2626")
AZUL = colors.HexColor("#2563EB")


def _fmt_moneda(monto: float) -> str:
    return f"$ {monto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_fecha(f: date) -> str:
    return f.strftime("%d/%m/%Y") if f else "-"


def generar_pdf_panel_socios(resumen: ResumenPanelSocios) -> bytes:
    """Genera el PDF del panel de socios con ingresos, gastos, ganancia y retiros."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    h_titulo = ParagraphStyle(
        "Titulo", parent=styles["Title"],
        fontSize=20, textColor=ROJO, alignment=TA_CENTER, spaceAfter=4,
    )
    h_subtitulo = ParagraphStyle(
        "Subtitulo", parent=styles["Normal"],
        fontSize=12, textColor=NEGRO, alignment=TA_CENTER, spaceAfter=12,
    )
    h_seccion = ParagraphStyle(
        "Seccion", parent=styles["Heading2"],
        fontSize=13, textColor=ROJO, spaceBefore=12, spaceAfter=6,
    )
    h_sub_seccion = ParagraphStyle(
        "SubSeccion", parent=styles["Heading3"],
        fontSize=11, textColor=NEGRO, spaceBefore=8, spaceAfter=4,
    )
    p_normal = ParagraphStyle(
        "PNormal", parent=styles["Normal"],
        fontSize=10, textColor=NEGRO, spaceAfter=2,
    )
    p_pequeno = ParagraphStyle(
        "PPequeno", parent=styles["Normal"],
        fontSize=8, textColor=GRIS, alignment=TA_CENTER,
    )

    elements = []

    # Cabecera con logo
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=5 * cm, height=1.3 * cm)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 4))
    else:
        elements.append(Paragraph("ELECTRO AMERICA", h_titulo))

    elements.append(Paragraph("PANEL DE SOCIOS", h_titulo))
    elements.append(Paragraph(
        f"Periodo: {_fmt_fecha(resumen.fecha_desde)} — {_fmt_fecha(resumen.fecha_hasta)}",
        h_subtitulo,
    ))

    # Totales
    totales_data = [
        [
            Paragraph("<b>Total Ingresos</b>", p_normal),
            Paragraph("<b>Total Gastos</b>", p_normal),
            Paragraph("<b>Ganancia</b>", p_normal),
        ],
        [
            Paragraph(f"<font color='#059669'><b>{_fmt_moneda(resumen.total_ingresos)}</b></font>",
                      ParagraphStyle("T1", parent=p_normal, fontSize=14, alignment=TA_CENTER)),
            Paragraph(f"<font color='#DC2626'><b>{_fmt_moneda(resumen.total_gastos)}</b></font>",
                      ParagraphStyle("T2", parent=p_normal, fontSize=14, alignment=TA_CENTER)),
            Paragraph(
                f"<font color='{'#059669' if resumen.ganancia >= 0 else '#DC2626'}'><b>{_fmt_moneda(resumen.ganancia)}</b></font>",
                ParagraphStyle("T3", parent=p_normal, fontSize=14, alignment=TA_CENTER),
            ),
        ],
    ]
    tbl_tot = Table(totales_data, colWidths=[6 * cm, 6 * cm, 6 * cm])
    tbl_tot.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, GRIS),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, GRIS_CLARO),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(tbl_tot)
    elements.append(Spacer(1, 14))

    # ============ INGRESOS ============
    elements.append(Paragraph("PLANILLAS DE INGRESOS", h_seccion))

    if not resumen.planillas_ingresos or all(p.cantidad == 0 for p in resumen.planillas_ingresos):
        elements.append(Paragraph("No hay ingresos registrados en el periodo.", p_normal))
    else:
        for planilla in resumen.planillas_ingresos:
            if planilla.cantidad == 0:
                continue
            elements.append(Paragraph(
                f"{planilla.nombre} — <b>{_fmt_moneda(planilla.total)}</b> ({planilla.cantidad} mov.)",
                h_sub_seccion,
            ))

            rows = [["Fecha", "Concepto", "Referencia", "Monto"]]
            for i in planilla.items:
                rows.append([
                    _fmt_fecha(i.fecha),
                    i.concepto[:50],
                    (i.referencia or "-")[:35],
                    _fmt_moneda(i.monto),
                ])
            tbl = Table(rows, colWidths=[2.2 * cm, 8 * cm, 4.5 * cm, 3.3 * cm])
            tbl.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
                ("GRID", (0, 0), (-1, -1), 0.3, GRIS),
                ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                ("TEXTCOLOR", (3, 1), (3, -1), VERDE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(tbl)
            elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 10))

    # ============ GASTOS ============
    elements.append(Paragraph("PLANILLAS DE GASTOS", h_seccion))

    if not resumen.planillas_gastos:
        elements.append(Paragraph("No hay gastos registrados en el periodo.", p_normal))
    else:
        for planilla in resumen.planillas_gastos:
            elements.append(Paragraph(
                f"{planilla.categoria} — <b>{_fmt_moneda(planilla.total)}</b> ({planilla.cantidad} gasto/s)",
                h_sub_seccion,
            ))

            rows = [["Fecha", "Concepto", "Referencia", "Monto"]]
            for i in planilla.items:
                rows.append([
                    _fmt_fecha(i.fecha),
                    i.concepto[:50],
                    (i.referencia or "-")[:35],
                    _fmt_moneda(i.monto),
                ])
            tbl = Table(rows, colWidths=[2.2 * cm, 8 * cm, 4.5 * cm, 3.3 * cm])
            tbl.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
                ("GRID", (0, 0), (-1, -1), 0.3, GRIS),
                ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                ("TEXTCOLOR", (3, 1), (3, -1), ROJO_ERROR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(tbl)
            elements.append(Spacer(1, 4))

    elements.append(PageBreak())

    # ============ SOCIOS ============
    elements.append(Paragraph("DISTRIBUCION DE GANANCIA Y RETIROS", h_seccion))

    if not resumen.socios:
        elements.append(Paragraph("No hay socios cargados.", p_normal))
    else:
        # Resumen general
        socios_data = [["Socio", "Participacion", "Ganancia", "Retiros", "Saldo"]]
        for s in resumen.socios:
            socios_data.append([
                s.nombre,
                f"{s.porcentaje_participacion:.2f}%",
                _fmt_moneda(s.ganancia_asignada),
                _fmt_moneda(s.total_retiros),
                _fmt_moneda(s.saldo_disponible),
            ])
        tbl_socios = Table(socios_data, colWidths=[4.5 * cm, 2.8 * cm, 3.5 * cm, 3.5 * cm, 3.7 * cm])
        tbl_socios.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), ROJO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, GRIS),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("BACKGROUND", (0, 1), (-1, -1), GRIS_CLARO),
        ]))
        elements.append(tbl_socios)
        elements.append(Spacer(1, 14))

        # Detalle de retiros por socio
        for s in resumen.socios:
            elements.append(Paragraph(
                f"Retiros de {s.nombre} — <b>{_fmt_moneda(s.total_retiros)}</b>",
                h_sub_seccion,
            ))
            if not s.retiros:
                elements.append(Paragraph("Sin retiros en el periodo.", p_normal))
                elements.append(Spacer(1, 6))
                continue

            rows = [["Fecha", "Concepto", "Cuenta", "Monto"]]
            for r in s.retiros:
                rows.append([
                    _fmt_fecha(r.fecha),
                    (r.concepto or "-")[:50],
                    (r.referencia or "-")[:35],
                    _fmt_moneda(r.monto),
                ])
            tbl_r = Table(rows, colWidths=[2.2 * cm, 8 * cm, 4.5 * cm, 3.3 * cm])
            tbl_r.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
                ("GRID", (0, 0), (-1, -1), 0.3, GRIS),
                ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                ("TEXTCOLOR", (3, 1), (3, -1), ROJO_ERROR),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(tbl_r)
            elements.append(Spacer(1, 8))

    # Footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "Generado desde el Sistema Electro America",
        p_pequeno,
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

"""Generador de PDF de fichajes con horas normales y extras."""
import io
import os
from datetime import date
from decimal import Decimal
from typing import List, Optional
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.models.fichaje import FichajeJornada, EstadoFichaje

LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "logo.jpg",
)

ROJO = colors.HexColor("#E53935")
NEGRO = colors.HexColor("#1A1A1A")
GRIS = colors.HexColor("#666666")
GRIS_CLARO = colors.HexColor("#F2F2F2")
NARANJA = colors.HexColor("#EA580C")
VERDE = colors.HexColor("#059669")
AZUL = colors.HexColor("#2563EB")

HORAS_NORMALES = Decimal("9")


def _fmt_hora(dt) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%H:%M")


def _fmt_fecha(d) -> str:
    if d is None:
        return "—"
    if isinstance(d, str):
        return d
    return d.strftime("%d/%m/%Y")


def _horas_str(h: Optional[Decimal]) -> str:
    if h is None:
        return "—"
    return f"{h:.2f}h"


def generar_pdf_fichajes(
    fichajes: List[FichajeJornada],
    fecha_desde: Optional[date],
    fecha_hasta: Optional[date],
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "Titulo", parent=styles["Title"],
        fontSize=18, textColor=ROJO, alignment=TA_CENTER, spaceAfter=4,
    )
    estilo_subtitulo = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=10, textColor=GRIS, alignment=TA_CENTER, spaceAfter=2,
    )
    estilo_seccion = ParagraphStyle(
        "Seccion", parent=styles["Normal"],
        fontSize=11, textColor=NEGRO, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=10,
    )
    estilo_nota = ParagraphStyle(
        "Nota", parent=styles["Normal"],
        fontSize=8, textColor=GRIS, alignment=TA_RIGHT,
    )

    story = []

    # Encabezado
    story.append(Paragraph("Electro América", estilo_titulo))
    story.append(Paragraph("Reporte de Fichajes — Horas Trabajadas", estilo_subtitulo))
    periodo = ""
    if fecha_desde and fecha_hasta:
        periodo = f"Período: {_fmt_fecha(fecha_desde)} — {_fmt_fecha(fecha_hasta)}"
    elif fecha_desde:
        periodo = f"Desde: {_fmt_fecha(fecha_desde)}"
    elif fecha_hasta:
        periodo = f"Hasta: {_fmt_fecha(fecha_hasta)}"
    if periodo:
        story.append(Paragraph(periodo, estilo_subtitulo))
    story.append(Spacer(1, 0.4 * cm))

    # Agrupar por operario
    por_operario: dict = defaultdict(list)
    for f in fichajes:
        if f.estado == EstadoFichaje.completado:
            nombre = f"{f.operario.nombre} {f.operario.apellido}" if f.operario else str(f.operario_id)
            por_operario[nombre].append(f)

    if not por_operario:
        story.append(Paragraph("No hay fichajes completados en el período seleccionado.", styles["Normal"]))
        doc.build(story)
        return buffer.getvalue()

    # Resumen global primero
    resumen_rows = [["Operario", "Días", "Horas totales", "Horas normales", "Horas extras"]]
    total_global_normales = Decimal("0")
    total_global_extras = Decimal("0")

    for nombre, flist in sorted(por_operario.items()):
        horas_total = sum((f.horas_trabajadas or Decimal("0")) for f in flist)
        dias = len(flist)
        normales = min(horas_total, HORAS_NORMALES * dias)
        extras = max(Decimal("0"), horas_total - HORAS_NORMALES * dias)
        total_global_normales += normales
        total_global_extras += extras
        resumen_rows.append([
            nombre,
            str(dias),
            _horas_str(horas_total),
            _horas_str(normales),
            _horas_str(extras) if extras > 0 else "—",
        ])

    resumen_rows.append([
        "TOTAL",
        "",
        _horas_str(total_global_normales + total_global_extras),
        _horas_str(total_global_normales),
        _horas_str(total_global_extras) if total_global_extras > 0 else "—",
    ])

    story.append(Paragraph("Resumen por operario", estilo_seccion))
    t_resumen = Table(resumen_rows, colWidths=[6 * cm, 2 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
    t_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ROJO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, GRIS_CLARO]),
        ("BACKGROUND", (0, -1), (-1, -1), NEGRO),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_resumen)
    story.append(Spacer(1, 0.6 * cm))

    # Detalle por operario
    story.append(Paragraph("Detalle de fichajes", estilo_seccion))

    for nombre, flist in sorted(por_operario.items()):
        horas_op = sum((f.horas_trabajadas or Decimal("0")) for f in flist)
        normales_op = min(horas_op, HORAS_NORMALES * len(flist))
        extras_op = max(Decimal("0"), horas_op - HORAS_NORMALES * len(flist))

        story.append(Paragraph(f"▶  {nombre}", ParagraphStyle(
            "Op", parent=styles["Normal"],
            fontSize=10, textColor=ROJO, fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=3,
        )))

        header = ["Fecha", "Entrada", "Salida", "Horas trabajadas", "Horas normales", "Horas extras", "Notas"]
        rows = [header]
        for f in sorted(flist, key=lambda x: x.fecha):
            h = f.horas_trabajadas or Decimal("0")
            norm = min(h, HORAS_NORMALES)
            ext = max(Decimal("0"), h - HORAS_NORMALES)
            rows.append([
                _fmt_fecha(f.fecha),
                _fmt_hora(f.hora_inicio),
                _fmt_hora(f.hora_fin),
                _horas_str(h),
                _horas_str(norm),
                _horas_str(ext) if ext > 0 else "—",
                (f.notas_fin or f.notas_inicio or "")[:40],
            ])
        # Fila totales del operario
        rows.append([
            "TOTAL",
            "",
            "",
            _horas_str(horas_op),
            _horas_str(normales_op),
            _horas_str(extras_op) if extras_op > 0 else "—",
            "",
        ])

        col_w = [3 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm, 3.5 * cm, 3 * cm, 5 * cm]
        t = Table(rows, colWidths=col_w)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#424242")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-2, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (-1, 0), (-1, -1), "LEFT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, GRIS_CLARO]),
            # Highlight extras > 0
            *[
                ("TEXTCOLOR", (5, i + 1), (5, i + 1), NARANJA)
                for i, row in enumerate(rows[1:-1])
                if row[5] != "—"
            ],
            # Totals row
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EEEEEE")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"* Jornada normal: {HORAS_NORMALES}h. Todo lo que supere ese valor por día se considera hora extra.", estilo_nota))

    doc.build(story)
    return buffer.getvalue()

"""
Exportadores a Excel (.xlsx) y PDF para los horarios del GA.

Ambos exportan UN archivo con LOS K horarios:
- Excel: 1 hoja por horario.
- PDF: 1 página por horario.

Cada horario se renderiza como una grilla LUN-SAB × horas + metadatos
(fitness, scores, créditos, asignaturas omitidas).
"""
from pathlib import Path
from typing import List, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models import Cromosoma
from fitness import ContextoAlumno, evaluar_fitness, preferencia_horarios, preferencia_docentes, preferencia_cupos
from .visualizer import (
    DIAS,
    DIAS_ABREV,
    HORA_FIN,
    HORA_INICIO,
    _abreviar_asignatura,
)


# Paleta para colorear asignaturas (clara, legible)
PALETA_COLORES = [
    "FFE5CC", "CCE5FF", "CCFFCC", "FFFFCC", "FFCCE5",
    "E5CCFF", "CCFFFF", "FFD9B3", "B3D9FF", "D4FFD4",
]


def _construir_celdas_grilla(cromosoma: Cromosoma):
    """
    Devuelve dict[(hora, dia)] → (etiqueta, asignatura_cod) y un mapeo
    codAsignatura → índice de color.
    """
    celdas = {}
    asignaturas_orden = []
    for s in cromosoma.secciones:
        if s.codAsignatura not in asignaturas_orden:
            asignaturas_orden.append(s.codAsignatura)
        abrev = _abreviar_asignatura(s.desAsignatura)
        etiqueta = f"{abrev}-S{s.codSeccion}"
        for b in s.bloques:
            if b.dia not in DIAS or b.horaInicio is None or b.horaFin is None:
                continue
            h_ini = int(b.horaInicio.split(":")[0])
            h_fin = int(b.horaFin.split(":")[0])
            for h in range(max(h_ini, HORA_INICIO), min(h_fin, HORA_FIN)):
                celdas[(h, b.dia)] = (etiqueta, s.codAsignatura)

    color_de = {
        cod: PALETA_COLORES[i % len(PALETA_COLORES)]
        for i, cod in enumerate(asignaturas_orden)
    }
    return celdas, color_de


def _horas_relevantes(celdas) -> List[int]:
    """Horas (filas) que tienen al menos una celda ocupada."""
    if not celdas:
        return list(range(HORA_INICIO, HORA_FIN))
    horas = sorted({h for (h, _) in celdas.keys()})
    if not horas:
        return list(range(HORA_INICIO, HORA_FIN))
    # rango contiguo entre la primera y última hora ocupada
    return list(range(min(horas), max(horas) + 1))


# ─────────────────────────────────────────────────────────────────────
# EXCEL
# ─────────────────────────────────────────────────────────────────────

def _escribir_hoja_excel(ws, rank: int, cromosoma: Cromosoma, ctx: ContextoAlumno):
    """Llena una hoja con un horario."""
    fit = evaluar_fitness(cromosoma, ctx)
    p_hor = preferencia_horarios(cromosoma, ctx)
    p_doc = preferencia_docentes(cromosoma, ctx)
    p_cup = preferencia_cupos(cromosoma, ctx)
    creditos = sum(s.creditos for s in cromosoma.secciones)

    ws.title = f"Horario {rank}"

    # ── Header con metadata ──
    bold = Font(bold=True, size=12)
    titulo = Font(bold=True, size=14)
    ws["A1"] = f"HORARIO #{rank}"
    ws["A1"].font = titulo
    ws.merge_cells("A1:G1")
    ws["A1"].alignment = Alignment(horizontal="center")

    ws["A3"] = "Fitness"
    ws["B3"] = round(fit, 4)
    ws["C3"] = "Horarios"
    ws["D3"] = round(p_hor, 2)
    ws["E3"] = "Docentes"
    ws["F3"] = round(p_doc, 2)
    ws["A4"] = "Cupos"
    ws["B4"] = round(p_cup, 2)
    ws["C4"] = "Créditos"
    ws["D4"] = creditos
    for cell in ["A3", "C3", "E3", "A4", "C4"]:
        ws[cell].font = bold

    # ── Grilla ──
    celdas, color_de = _construir_celdas_grilla(cromosoma)
    horas = _horas_relevantes(celdas)
    fila_inicial = 6

    thin = Side(border_style="thin", color="888888")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Cabecera días
    ws.cell(row=fila_inicial, column=1, value="HORA").font = bold
    ws.cell(row=fila_inicial, column=1).fill = PatternFill("solid", fgColor="DDDDDD")
    ws.cell(row=fila_inicial, column=1).alignment = center
    ws.cell(row=fila_inicial, column=1).border = border
    for i, d in enumerate(DIAS_ABREV, start=2):
        c = ws.cell(row=fila_inicial, column=i, value=d)
        c.font = bold
        c.fill = PatternFill("solid", fgColor="DDDDDD")
        c.alignment = center
        c.border = border

    # Filas de horas
    for j, h in enumerate(horas, start=fila_inicial + 1):
        c = ws.cell(row=j, column=1, value=f"{h:02d}:00")
        c.font = bold
        c.alignment = center
        c.border = border
        for i, d in enumerate(DIAS, start=2):
            etiq_color = celdas.get((h, d))
            celda = ws.cell(row=j, column=i)
            celda.border = border
            celda.alignment = center
            if etiq_color:
                etiqueta, cod_asig = etiq_color
                celda.value = etiqueta
                celda.fill = PatternFill("solid", fgColor=color_de[cod_asig])

    # Anchos de columna
    ws.column_dimensions["A"].width = 8
    for i in range(2, 8):
        ws.column_dimensions[get_column_letter(i)].width = 14

    # ── Leyenda ──
    fila_leyenda = fila_inicial + len(horas) + 3
    ws.cell(row=fila_leyenda, column=1, value="LEYENDA").font = titulo
    ws.cell(row=fila_leyenda + 1, column=1, value="Código").font = bold
    ws.cell(row=fila_leyenda + 1, column=2, value="Asignatura").font = bold
    ws.cell(row=fila_leyenda + 1, column=4, value="Docente").font = bold
    ws.cell(row=fila_leyenda + 1, column=6, value="Cupo").font = bold
    ws.cell(row=fila_leyenda + 1, column=7, value="Cr").font = bold

    visto = set()
    fila_actual = fila_leyenda + 2
    for s in cromosoma.secciones:
        key = (s.codAsignatura, s.codSeccion)
        if key in visto:
            continue
        visto.add(key)
        abrev = _abreviar_asignatura(s.desAsignatura)
        etiqueta = f"{abrev}-S{s.codSeccion}"
        ws.cell(row=fila_actual, column=1, value=etiqueta).fill = PatternFill(
            "solid", fgColor=color_de[s.codAsignatura]
        )
        ws.cell(row=fila_actual, column=2, value=s.desAsignatura.strip())
        ws.merge_cells(start_row=fila_actual, start_column=2, end_row=fila_actual, end_column=3)
        ws.cell(row=fila_actual, column=4, value=s.docente_completo)
        ws.merge_cells(start_row=fila_actual, start_column=4, end_row=fila_actual, end_column=5)
        ws.cell(row=fila_actual, column=6, value=f"{s.matriculados}/{s.topeAlumnos}")
        ws.cell(row=fila_actual, column=7, value=int(s.creditos))
        fila_actual += 1


def exportar_excel(
    cromosomas: List[Cromosoma],
    contexto: ContextoAlumno,
    filename: str = "output/horarios.xlsx",
    asignaturas_omitidas: Optional[List[str]] = None,
) -> Path:
    """
    Exporta los K horarios a un archivo Excel con una hoja por horario.

    Devuelve el Path del archivo creado.
    """
    wb = Workbook()
    # Quitar la hoja por defecto
    wb.remove(wb.active)

    for rank, c in enumerate(cromosomas, start=1):
        ws = wb.create_sheet(title=f"Horario {rank}")
        _escribir_hoja_excel(ws, rank, c, contexto)

    if asignaturas_omitidas:
        ws = wb.create_sheet(title="Omitidas", index=0)
        ws["A1"] = "Asignaturas sin sección disponible (omitidas del horario)"
        ws["A1"].font = Font(bold=True, size=12)
        for i, cod in enumerate(asignaturas_omitidas, start=3):
            ws.cell(row=i, column=1, value=cod)

    out = Path(filename)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


# ─────────────────────────────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────────────────────────────

def _color_hex_a_rgb(hex_str: str):
    """'FFE5CC' → colors.Color(255/255, 229/255, 204/255)."""
    r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    return colors.Color(r / 255, g / 255, b / 255)


def _construir_tabla_grilla_pdf(cromosoma: Cromosoma) -> Table:
    """Construye un objeto Table de reportlab con la grilla del horario."""
    celdas, color_de = _construir_celdas_grilla(cromosoma)
    horas = _horas_relevantes(celdas)

    # Data: primera fila = cabecera, primera columna = horas
    data = [["HORA"] + DIAS_ABREV]
    estilos_celda = []  # (col, fila) → color

    for j, h in enumerate(horas, start=1):
        fila = [f"{h:02d}:00"]
        for i, d in enumerate(DIAS, start=1):
            etiq_color = celdas.get((h, d))
            if etiq_color:
                etiqueta, cod_asig = etiq_color
                fila.append(etiqueta)
                estilos_celda.append((i, j, color_de[cod_asig]))
            else:
                fila.append("")
        data.append(fila)

    # Anchos de columna
    col_widths = [1.4 * cm] + [2.7 * cm] * len(DIAS)

    tabla = Table(data, colWidths=col_widths, rowHeights=0.55 * cm)
    style = TableStyle([
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0),  colors.HexColor("#DDDDDD")),
        ("BACKGROUND", (0, 1), (0, -1),  colors.HexColor("#EEEEEE")),
        ("FONTNAME",   (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTNAME",   (0, 1), (0, -1),  "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 7),
    ])
    for col, fila, hexc in estilos_celda:
        style.add("BACKGROUND", (col, fila), (col, fila), _color_hex_a_rgb(hexc))
    tabla.setStyle(style)
    return tabla


def _construir_pagina_pdf(rank: int, cromosoma: Cromosoma, ctx: ContextoAlumno, styles):
    """Devuelve la lista de elementos (flowables) de la página de UN horario."""
    fit = evaluar_fitness(cromosoma, ctx)
    p_hor = preferencia_horarios(cromosoma, ctx)
    p_doc = preferencia_docentes(cromosoma, ctx)
    p_cup = preferencia_cupos(cromosoma, ctx)
    creditos = sum(s.creditos for s in cromosoma.secciones)

    elementos = []
    elementos.append(Paragraph(f"<b>HORARIO #{rank}</b>", styles["Heading1"]))
    meta = (
        f"<b>Fitness:</b> {fit:.4f} &nbsp;&nbsp; "
        f"<b>Horarios:</b> {p_hor:.2f} &nbsp;&nbsp; "
        f"<b>Docentes:</b> {p_doc:.2f} &nbsp;&nbsp; "
        f"<b>Cupos:</b> {p_cup:.2f} &nbsp;&nbsp; "
        f"<b>Créditos:</b> {creditos:.0f}"
    )
    elementos.append(Paragraph(meta, styles["Normal"]))
    elementos.append(Spacer(1, 0.2 * cm))

    elementos.append(_construir_tabla_grilla_pdf(cromosoma))
    elementos.append(Spacer(1, 0.25 * cm))

    # Leyenda
    elementos.append(Paragraph("<b>Leyenda</b>", styles["Heading4"]))
    visto = set()
    leyenda_data = [["Código", "Asignatura", "Docente", "Cupo", "Cr"]]
    for s in cromosoma.secciones:
        key = (s.codAsignatura, s.codSeccion)
        if key in visto:
            continue
        visto.add(key)
        abrev = _abreviar_asignatura(s.desAsignatura)
        etiqueta = f"{abrev}-S{s.codSeccion}"
        leyenda_data.append([
            etiqueta,
            s.desAsignatura.strip()[:40],
            s.docente_completo[:32],
            f"{s.matriculados}/{s.topeAlumnos}",
            f"{int(s.creditos)}",
        ])
    leyenda = Table(leyenda_data, colWidths=[2.5 * cm, 7 * cm, 6 * cm, 2 * cm, 1.2 * cm])
    leyenda.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDDDDD")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))
    elementos.append(leyenda)

    return elementos


def exportar_pdf(
    cromosomas: List[Cromosoma],
    contexto: ContextoAlumno,
    filename: str = "output/horarios.pdf",
    asignaturas_omitidas: Optional[List[str]] = None,
) -> Path:
    """
    Exporta los K horarios a un PDF con una página por horario.

    Devuelve el Path del archivo creado.
    """
    out = Path(filename)
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out),
        pagesize=landscape(A4),
        leftMargin=1.0 * cm,
        rightMargin=1.0 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        title="Horarios optimizados — Tesis UNMSM",
    )

    styles = getSampleStyleSheet()
    elementos = []
    for rank, c in enumerate(cromosomas, start=1):
        elementos.extend(_construir_pagina_pdf(rank, c, contexto, styles))
        if rank < len(cromosomas):
            elementos.append(PageBreak())

    if asignaturas_omitidas:
        elementos.append(PageBreak())
        elementos.append(Paragraph("<b>Asignaturas sin sección disponible</b>", styles["Title"]))
        elementos.append(Spacer(1, 0.3 * cm))
        for cod in asignaturas_omitidas:
            elementos.append(Paragraph(f"• {cod}", styles["Normal"]))

    doc.build(elementos)
    return out

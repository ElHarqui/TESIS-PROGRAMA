"""
Visualización de un horario como grilla semanal LUN-SAB × horas.

Reemplaza el listado lineal por una grilla tipo planner que muestra a primera
vista qué días están ocupados, los huecos, y el balance de carga.
"""
from models import Cromosoma


HORA_INICIO = 7   # 07:00
HORA_FIN    = 23  # 22:00 inclusive como bloque que termina a 22

DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO"]
DIAS_ABREV = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB"]

ANCHO_CELDA = 9
# Palabras de relleno que ignoramos al abreviar el nombre de la asignatura
PALABRAS_VACIAS = {"DE", "DEL", "LA", "EL", "LOS", "LAS", "Y", "EN", "A"}


def _abreviar_asignatura(desAsignatura: str, max_chars: int = 4) -> str:
    """
    Abreviatura compacta del nombre de la asignatura.

    Si tiene varias palabras significativas, devuelve las iniciales (ej.
    "DESARROLLO DE SISTEMAS MÓVILES" → "DSM"). Si tiene una sola palabra,
    devuelve sus primeras `max_chars` letras.
    """
    palabras = [
        p for p in desAsignatura.strip().split()
        if p.upper() not in PALABRAS_VACIAS and len(p) > 1
    ]
    if not palabras:
        return desAsignatura[:max_chars].upper()
    if len(palabras) == 1:
        return palabras[0][:max_chars].upper()
    return "".join(p[0] for p in palabras[:max_chars]).upper()


def visualizar_grilla(cromosoma: Cromosoma) -> str:
    """
    Devuelve un string con la grilla semanal del cromosoma.

    Filas: horas (07:00 a 22:00). Columnas: LUN-SAB.
    Cada celda muestra la abreviatura de la asignatura + número de sección
    si hay clase en ese día/hora. Bloques largos rellenan varias filas.
    """
    # Tabla (hora_inicio_int, dia) → contenido. Usamos minutos desde medianoche.
    celdas = {(h, d): "" for h in range(HORA_INICIO, HORA_FIN) for d in DIAS}

    for s in cromosoma.secciones:
        abrev = _abreviar_asignatura(s.desAsignatura)
        etiqueta = f"{abrev}-S{s.codSeccion}"
        for b in s.bloques:
            if b.dia not in DIAS or b.horaInicio is None or b.horaFin is None:
                continue
            h_ini = int(b.horaInicio.split(":")[0])
            h_fin = int(b.horaFin.split(":")[0])
            for h in range(max(h_ini, HORA_INICIO), min(h_fin, HORA_FIN)):
                celdas[(h, b.dia)] = etiqueta

    # Render
    lineas = []
    # Cabecera con días
    cab = "       │" + "│".join(f"{d:^{ANCHO_CELDA}}" for d in DIAS_ABREV) + "│"
    lineas.append(cab)
    sep = "       ├" + "┼".join("─" * ANCHO_CELDA for _ in DIAS) + "┤"
    lineas.append(sep)

    for h in range(HORA_INICIO, HORA_FIN):
        contenidos = [celdas[(h, d)] or "" for d in DIAS]
        if not any(contenidos):
            # fila completamente vacía: omitir si ya hubo alguna ocupada antes
            # (para no inundar de líneas vacías; mostramos al menos las que tienen clase)
            continue
        fila = f" {h:02d}:00 │" + "│".join(f"{c:^{ANCHO_CELDA}}" for c in contenidos) + "│"
        lineas.append(fila)

    # Pie con horas: agregar una marca final si la última hora fue ocupada
    return "\n".join(lineas)


def leyenda_asignaturas(cromosoma: Cromosoma) -> str:
    """
    Devuelve un string con la leyenda: cada abreviatura → asignatura completa + docente.
    Útil para complementar la grilla compacta.
    """
    vistas = {}
    for s in cromosoma.secciones:
        abrev = _abreviar_asignatura(s.desAsignatura)
        key = f"{abrev}-S{s.codSeccion}"
        if key not in vistas:
            vistas[key] = (s.desAsignatura.strip(), s.docente_completo, s.matriculados, s.topeAlumnos, s.creditos)

    lineas = []
    for key, (desc, docente, mat, tope, cr) in vistas.items():
        lineas.append(f"  {key:10}  {desc[:42]:42}  Doc: {docente[:30]:30}  cupo={mat}/{tope}  cr={cr:.0f}")
    return "\n".join(lineas)

"""
Interfaz web (Streamlit) del optimizador de horarios UNMSM.

Ejecutar:
    streamlit run app.py

Estructura:
- Sidebar: login + datos del alumno + control de caché
- Pestaña "Mis horarios": generar y visualizar los K horarios + descargas
- Pestaña "Preferencias": editar docentes y horarios (se guardan a JSON)
- Pestaña "Datos académicos": perfil + plan + prematrícula + historial
"""
import asyncio
import json
import os
import time
from datetime import time as dt_time
from pathlib import Path
from typing import List

import nest_asyncio
import streamlit as st
from dotenv import load_dotenv

from data import (
    Cache,
    extraer_aprobados,
    extraer_prerequisitos,
    obtener_datos_sum,
    parsear_alumno,
    parsear_historial,
    parsear_plan_estudios,
    parsear_prematricula,
    parsear_respuesta,
)
from fitness import (
    ContextoAlumno,
    PreferenciasHorario,
    cargar_preferencias_horarios,
    cargar_scores_docentes,
    evaluar_fitness,
    preferencia_cupos,
    preferencia_docentes,
    preferencia_horarios,
)
from fitness.contexto import (
    DENSIDAD_COMPACTO,
    DENSIDAD_DISTRIBUIDO,
    DENSIDAD_INDIFERENTE,
    TURNO_INDIFERENTE,
    TURNO_MANANA,
    TURNO_NOCHE,
    TURNO_TARDE,
)
from genetic import ejecutar_ga, generar_poblacion_inicial, top_k_diversos
from genetic.population import _es_seccion_valida
from output import exportar_excel, exportar_pdf
from output.visualizer import (
    DIAS,
    DIAS_ABREV,
    HORA_FIN,
    HORA_INICIO,
    _abreviar_asignatura,
)
from config import cargar_config


# Playwright es async; Streamlit corre en su propio loop. Permitir loops anidados.
nest_asyncio.apply()

# .env como FALLBACK: si no se hace login en la UI, se intentan estas credenciales.
load_dotenv()

CACHE_KEY = "datos_sum"

PALETA = [
    "#FFE5CC", "#CCE5FF", "#CCFFCC", "#FFFFCC", "#FFCCE5",
    "#E5CCFF", "#CCFFFF", "#FFD9B3", "#B3D9FF", "#D4FFD4",
]


# ─────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LA PÁGINA
# ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Optimizador de horarios UNMSM",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "Sistema de optimización de horarios de matrícula UNMSM "
            "mediante algoritmos genéticos. Tesis de Ingeniería de Sistemas."
        ),
    },
)


# ─────────────────────────────────────────────────────────────────────
# CSS PERSONALIZADO (estilo profesional)
# ─────────────────────────────────────────────────────────────────────

_CUSTOM_CSS = """
<style>
  /* Ocultar chrome innecesario de Streamlit para un aspecto pulido */
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  [data-testid="stStatusWidget"] {display: none;}

  /* Contenedor principal con menos padding vertical y un ancho contenido */
  .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
  }

  /* Header institucional */
  .app-header {
    background: linear-gradient(135deg, #8B1A1A 0%, #6B1414 100%);
    color: #FFFFFF;
    padding: 1.25rem 1.75rem;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }
  .app-header h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.01em;
  }
  .app-header .subtitulo {
    opacity: 0.85;
    font-size: 0.9rem;
    margin-top: 0.2rem;
  }
  .app-header .alumno-info {
    text-align: right;
    font-size: 0.85rem;
    line-height: 1.4;
  }
  .app-header .alumno-info strong {
    font-size: 0.95rem;
  }

  /* Cards de métricas coloreadas por concepto */
  .metrica-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-left: 4px solid #8B1A1A;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  }
  .metrica-card .label {
    font-size: 0.75rem;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin-bottom: 0.2rem;
  }
  .metrica-card .valor {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.2;
  }
  .metrica-card.fitness   {border-left-color: #8B1A1A;}
  .metrica-card.horarios  {border-left-color: #1D4ED8;}
  .metrica-card.docentes  {border-left-color: #059669;}
  .metrica-card.cupos     {border-left-color: #D97706;}
  .metrica-card.creditos  {border-left-color: #7C3AED;}

  /* Sidebar limpio */
  section[data-testid="stSidebar"] {
    background-color: #FAFAF7;
    border-right: 1px solid #E5E7EB;
  }
  section[data-testid="stSidebar"] h1,
  section[data-testid="stSidebar"] h2,
  section[data-testid="stSidebar"] h3 {
    color: #1F2937;
  }
  .sidebar-caja {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
  }
  .sidebar-caja .nombre {
    font-weight: 600;
    font-size: 0.95rem;
    color: #111827;
  }
  .sidebar-caja .detalle {
    font-size: 0.8rem;
    color: #6B7280;
    margin-top: 0.15rem;
  }

  /* Tablas de leyenda y datos */
  .stDataFrame {border-radius: 8px; overflow: hidden;}

  /* Botones */
  .stButton > button {
    border-radius: 6px;
    font-weight: 500;
  }
  .stDownloadButton > button {
    border-radius: 6px;
    font-weight: 500;
  }

  /* Tabs con más aire y color activo institucional */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
  }
  .stTabs [data-baseweb="tab"] {
    padding: 0.6rem 1.1rem;
    font-weight: 500;
  }
</style>
"""
st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "datos_raw": None,
        "alumno": None,
        "plan": None,
        "secciones": None,
        "prematricula": None,
        "historial": None,
        "horarios": None,
        "omitidas": [],
        "fitness_fin": None,
        "duracion_ga": None,
        "gen_validos_ini": 0,
        "gen_validos_fin": 0,
        "credenciales_usuario": "",
        "credenciales_password": "",
        # Fallback state cuando las HARD del alumno dejan sin horarios
        "ga_ya_corrio": False,
        "modo_fallback": False,
        "hard_relajadas": [],
        "contexto_original": None,   # se guarda para poder marcar violaciones en la grilla del fallback
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ─────────────────────────────────────────────────────────────────────
# HELPERS DE BACKEND (envuelven el async)
# ─────────────────────────────────────────────────────────────────────

def _scrape_o_cargar_cache(login: str, password: str, forzar_scrape: bool):
    cache = Cache(ttl=3600)
    cache.limpiar_expirados()

    datos = cache.get(CACHE_KEY)
    if datos and not forzar_scrape:
        return datos, "cache"

    # Scrape — bloquea Streamlit unos ~30s. Mostrar spinner desde el caller.
    datos = asyncio.run(obtener_datos_sum(login, password))
    cache.set(CACHE_KEY, datos)
    return datos, "scrape"


def _parsear_y_guardar(datos_raw: dict):
    """Parsea el scrape y guarda todo en session_state."""
    st.session_state.datos_raw = datos_raw
    st.session_state.secciones = parsear_respuesta(datos_raw["programacion"])
    st.session_state.alumno = parsear_alumno(datos_raw["alumno"])
    st.session_state.plan = parsear_plan_estudios(datos_raw["plan_estudios"])
    st.session_state.prematricula = parsear_prematricula(datos_raw["prematricula"])
    st.session_state.historial = parsear_historial(datos_raw["historial"])

    # El codAlumno y otros datos de identificacion NO estan en el endpoint
    # /informacion/perfil (que solo trae DNI, correos, ciclo, ponderado).
    # Viven en programacion.data.alumno junto con nomAlumno, apePaterno,
    # desEscuela y desFacultad. Los cross-referenciamos al raw del alumno
    # para que la UI (header y sidebar) los pueda mostrar.
    prog_data = datos_raw.get("programacion", {}).get("data", {})
    prog_alumno = prog_data.get("alumno", {}) if isinstance(prog_data, dict) else {}
    if isinstance(prog_alumno, dict) and st.session_state.alumno is not None:
        for k in ("codAlumno", "nomAlumno", "apePaterno", "apeMaterno",
                  "desEscuela", "desFacultad"):
            if prog_alumno.get(k):
                st.session_state.alumno.raw[k] = prog_alumno[k]


def _construir_contexto(scores_docentes: dict, prefs_horario: PreferenciasHorario) -> ContextoAlumno:
    config = cargar_config()
    return ContextoAlumno(
        prerequisitos=extraer_prerequisitos(st.session_state.plan),
        aprobados=extraer_aprobados(st.session_state.historial),
        max_creditos=config.max_creditos,
        scores_docentes=scores_docentes,
        prefs_horario=prefs_horario,
        pesos=config.pesos,
    )


def _hard_configurables_activas(prefs: PreferenciasHorario) -> List[str]:
    """
    Devuelve los nombres de las HARD configurables por el alumno que están activas.
    Vacío si el alumno no configuró ninguna (defaults: [], None, None).
    Se usa para decidir si vale la pena disparar el fallback y para el banner.
    """
    activas = []
    if prefs.dias_libres_obligatorios:
        activas.append("dias_libres_obligatorios")
    if prefs.hora_min:
        activas.append("hora_min")
    if prefs.hora_max:
        activas.append("hora_max")
    return activas


def _relajar_prefs(prefs: PreferenciasHorario) -> PreferenciasHorario:
    """
    Devuelve una copia de `prefs` con las 3 HARD configurables desactivadas
    (`[]`, `None`, `None`). Preserva las SOFT (turno, dias deseados, densidad).
    """
    import dataclasses
    return dataclasses.replace(
        prefs,
        dias_libres_obligatorios=[],
        hora_min=None,
        hora_max=None,
    )


def _violaciones_bloque(bloque, prefs: PreferenciasHorario) -> List[str]:
    """
    Devuelve la lista de motivos por los que este bloque viola las HARD
    configurables. Cada motivo es uno de: "dia_libre", "hora_min", "hora_max".
    Vacía si el bloque no viola ninguna.

    Reutiliza la lógica de verificar_dias_libres_obligatorios y verificar_rango_horario
    (fitness/hard_constraints.py) pero a nivel de un solo bloque para poder
    marcar celdas específicas en la grilla.
    """
    from fitness.hard_constraints import _hhmm_a_minutos

    motivos = []
    if bloque.dia and bloque.dia in prefs.dias_libres_obligatorios:
        motivos.append("dia_libre")
    if bloque.horaInicio is not None and bloque.horaFin is not None:
        if prefs.hora_min:
            min_int = _hhmm_a_minutos(prefs.hora_min)
            if bloque.hora_inicio_int < min_int:
                motivos.append("hora_min")
        if prefs.hora_max:
            max_int = _hhmm_a_minutos(prefs.hora_max)
            if bloque.hora_fin_int > max_int:
                motivos.append("hora_max")
    return motivos


# Texto amigable por motivo per-bloque (usado en tooltips y expanders)
_MOTIVO_DESC = {
    "dia_libre": "cae en un día que marcaste como obligatoriamente libre",
    "hora_min":  "empieza antes de tu hora mínima obligatoria",
    "hora_max":  "termina después de tu hora máxima obligatoria",
}

# Texto amigable por nombre de HARD (usado en el banner "se relajaron X e Y")
_HARD_DESC = {
    "dias_libres_obligatorios": "días obligatoriamente libres",
    "hora_min": "hora mínima obligatoria",
    "hora_max": "hora máxima obligatoria",
}


def _recomendaciones_por_horario(cromosoma, prefs: PreferenciasHorario) -> List[dict]:
    """
    Recorre las secciones del cromosoma y devuelve una lista con las secciones
    que tienen al menos un bloque que viola alguna HARD configurable. Cada item:
        {
          "asignatura": "MINERIA DE DATOS",
          "seccion": 2,
          "docente": "COSME FELIX",
          "bloques_violadores": [
              {"dia": "SABADO", "hora": "08:00-10:00", "motivos": ["dia_libre"]},
              ...
          ]
        }
    Solo se usa cuando modo_fallback está activo.
    """
    items = []
    for s in cromosoma.secciones:
        bloques_violadores = []
        for b in s.bloques:
            motivos = _violaciones_bloque(b, prefs)
            if motivos:
                bloques_violadores.append({
                    "dia": b.dia,
                    "hora": f"{b.horaInicio}-{b.horaFin}",
                    "motivos": motivos,
                })
        if bloques_violadores:
            items.append({
                "asignatura": s.desAsignatura.strip(),
                "seccion": s.codSeccion,
                "docente": s.docente_completo,
                "bloques_violadores": bloques_violadores,
            })
    return items


def _ejecutar_pase_ga(contexto: ContextoAlumno):
    """
    Un pase del GA con el contexto dado. Devuelve dict con top, fitness_fin,
    omitidas, duracion, gen_validos_ini, gen_validos_fin.
    """
    config = cargar_config().ga

    asignaturas = [p["codAsignatura"] for p in st.session_state.prematricula]
    sec_por_asig = {}
    for s in st.session_state.secciones:
        if _es_seccion_valida(s):
            sec_por_asig.setdefault(s.codAsignatura, []).append(s)

    poblacion, omitidas = generar_poblacion_inicial(
        asignaturas,
        st.session_state.secciones,
        tamano_poblacion=config.tamano_poblacion,
        seed=config.seed,
    )
    fitness_ini = [evaluar_fitness(c, contexto) for c in poblacion]

    t0 = time.time()
    poblacion_final = ejecutar_ga(
        poblacion,
        evaluador=lambda c: evaluar_fitness(c, contexto),
        secciones_por_asig=sec_por_asig,
        max_generaciones=config.generaciones,
        tasa_mutacion=config.tasa_mutacion,
        tamano_torneo=config.tamano_torneo,
        elitismo=config.elitismo,
    )
    duracion = time.time() - t0

    fitness_fin = [evaluar_fitness(c, contexto) for c in poblacion_final]
    top = top_k_diversos(poblacion_final, fitness_fin, k=config.top_k, distancia_minima=config.distancia_minima)

    return {
        "top": top,
        "fitness_fin": fitness_fin,
        "omitidas": omitidas,
        "duracion": duracion,
        "gen_validos_ini": sum(1 for f in fitness_ini if f > 0),
        "gen_validos_fin": sum(1 for f in fitness_fin if f > 0),
    }


def _correr_ga(contexto: ContextoAlumno):
    """
    Ejecuta el GA con fallback:
    1. Primer pase con el contexto original (respetando TODAS las HARD del alumno).
    2. Si el top queda vacío Y el alumno tiene HARD configurables activas, corre
       un segundo pase con esas HARD relajadas. Marca modo_fallback=True y guarda
       los horarios relajados junto con la lista de HARD relajadas.
    3. Si tampoco hay hard configurables o el segundo pase también queda vacío,
       deja horarios=[] y modo_fallback=False. La UI mostrará mensaje de problema
       estructural.

    Guarda todo en session_state y marca ga_ya_corrio=True.
    """
    resultado = _ejecutar_pase_ga(contexto)
    st.session_state.contexto_original = contexto

    hard_activas = _hard_configurables_activas(contexto.prefs_horario)

    if resultado["top"] or not hard_activas:
        # Camino normal: hay horarios, o no hay hard configurables para relajar
        st.session_state.horarios = resultado["top"]
        st.session_state.fitness_fin = resultado["fitness_fin"]
        st.session_state.omitidas = resultado["omitidas"]
        st.session_state.duracion_ga = resultado["duracion"]
        st.session_state.gen_validos_ini = resultado["gen_validos_ini"]
        st.session_state.gen_validos_fin = resultado["gen_validos_fin"]
        st.session_state.modo_fallback = False
        st.session_state.hard_relajadas = []
    else:
        # Primer pase vacío + hay hard configurables → relajarlas y reintentar
        contexto_relajado = ContextoAlumno(
            prerequisitos=contexto.prerequisitos,
            aprobados=contexto.aprobados,
            max_creditos=contexto.max_creditos,
            scores_docentes=contexto.scores_docentes,
            prefs_horario=_relajar_prefs(contexto.prefs_horario),
            pesos=contexto.pesos,
        )
        r2 = _ejecutar_pase_ga(contexto_relajado)
        st.session_state.horarios = r2["top"]
        st.session_state.fitness_fin = r2["fitness_fin"]
        st.session_state.omitidas = r2["omitidas"]
        st.session_state.duracion_ga = resultado["duracion"] + r2["duracion"]
        st.session_state.gen_validos_ini = r2["gen_validos_ini"]
        st.session_state.gen_validos_fin = r2["gen_validos_fin"]
        st.session_state.modo_fallback = bool(r2["top"])
        st.session_state.hard_relajadas = hard_activas if r2["top"] else []

    st.session_state.ga_ya_corrio = True


# ─────────────────────────────────────────────────────────────────────
# COMPONENTES DE UI
# ─────────────────────────────────────────────────────────────────────

def _parsear_hhmm(hhmm):
    """Convierte 'HH:MM' → datetime.time. Devuelve None si el input es falsy o inválido."""
    if not hhmm:
        return None
    try:
        h, m = map(int, str(hhmm).split(":"))
        return dt_time(h, m)
    except (ValueError, AttributeError):
        return None


def _apellido_corto(apePaterno: str, max_chars: int = 14) -> str:
    """Trunca el apellido paterno para caber en una celda de grilla."""
    if not apePaterno:
        return "—"
    ap = apePaterno.strip().upper()
    if len(ap) <= max_chars:
        return ap
    return ap[: max_chars - 1] + "…"


def _render_grilla_html(cromosoma, contexto_original: ContextoAlumno = None) -> str:
    """
    Renderiza la grilla del horario como tabla HTML coloreada.

    Cada celda con clase muestra 3 líneas:
      1. Código abreviado de la asignatura (ej. DSM).
      2. Sección (ej. Sec 2).
      3. Apellido paterno del docente (truncado).

    Datos completos (nombre completo del docente, cupo, créditos) están en
    la tabla-leyenda debajo de la grilla.

    Si `contexto_original` se pasa (modo fallback), las celdas cuyos bloques
    violan alguna HARD configurable del alumno se marcan con borde rojo y un
    icono de advertencia. Se usa cuando el fallback está activo para señalar
    exactamente qué bloques rompen las reglas estrictas.
    """
    prefs_para_violar = None
    if contexto_original is not None and _hard_configurables_activas(contexto_original.prefs_horario):
        prefs_para_violar = contexto_original.prefs_horario

    # Mapear celdas (hora, día) → info completa para el render
    celdas = {}
    asignaturas_orden = []
    for s in cromosoma.secciones:
        if s.codAsignatura not in asignaturas_orden:
            asignaturas_orden.append(s.codAsignatura)
        abrev = _abreviar_asignatura(s.desAsignatura)
        for b in s.bloques:
            if b.dia not in DIAS or b.horaInicio is None or b.horaFin is None:
                continue
            violaciones = _violaciones_bloque(b, prefs_para_violar) if prefs_para_violar else []
            info_celda = {
                "abrev": abrev,
                "seccion": s.codSeccion,
                "docente": _apellido_corto(s.apePatDocente),
                "cod_asig": s.codAsignatura,
                "violaciones": violaciones,
            }
            h_ini = int(b.horaInicio.split(":")[0])
            h_fin = int(b.horaFin.split(":")[0])
            for h in range(max(h_ini, HORA_INICIO), min(h_fin, HORA_FIN)):
                celdas[(h, b.dia)] = info_celda

    color_de = {cod: PALETA[i % len(PALETA)] for i, cod in enumerate(asignaturas_orden)}

    # Solo horas con clase
    if celdas:
        horas = sorted({h for (h, _) in celdas.keys()})
        horas = list(range(min(horas), max(horas) + 1))
    else:
        horas = list(range(HORA_INICIO, HORA_FIN))

    # HTML — color de texto FIJO en oscuro para celdas pintadas y cabeceras,
    # asi la grilla es legible tanto en modo claro como oscuro de Streamlit.
    # Las celdas vacias heredan el color del tema (no se fija).
    html = [
        "<style>",
        ".horario-wrap {",
        "  border-radius: 10px; overflow: hidden;",
        "  box-shadow: 0 1px 3px rgba(0,0,0,0.08);",
        "  border: 1px solid #E5E7EB;",
        "  margin: 0.5rem 0 1rem 0;",
        "}",
        ".horario {",
        "  border-collapse: collapse; width: 100%; font-size: 0.85em;",
        "  background: #FFFFFF; table-layout: fixed;",
        "}",
        ".horario th, .horario td {",
        "  border: 1px solid #E5E7EB; padding: 6px 4px; text-align: center;",
        "  vertical-align: middle; overflow: hidden; text-overflow: ellipsis;",
        "}",
        ".horario th {background: #F5F5F0; color: #1F2937; font-weight: 600;}",
        ".horario td.hora {background: #FAFAF7; color: #6B7280; font-weight: 600; width: 62px;}",
        ".horario td.clase {color: #1F2937; padding: 6px 3px; line-height: 1.2;}",
        ".horario td.clase .asig {font-weight: 700; font-size: 0.95em;}",
        ".horario td.clase .sec {font-size: 0.75em; color: #4B5563; margin-top: 1px;}",
        ".horario td.clase .prof {",
        "  font-size: 0.72em; color: #374151; margin-top: 3px;",
        "  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;",
        "}",
        # Celda violada: mantiene el color pastel de la asignatura pero suma un
        # borde rojo grueso via box-shadow inset (no altera el layout de la tabla)
        # y un icono ⚠ en la esquina superior derecha.
        ".horario td.clase.violada {",
        "  box-shadow: inset 0 0 0 3px #DC2626; position: relative;",
        "}",
        ".horario td.clase.violada::after {",
        "  content: '⚠'; position: absolute; top: 1px; right: 3px;",
        "  color: #DC2626; font-size: 0.85em; font-weight: 700;",
        "}",
        "</style>",
        "<div class='horario-wrap'>",
        "<table class='horario'>",
        "<tr><th style='width:62px;'>HORA</th>" + "".join(f"<th>{d}</th>" for d in DIAS_ABREV) + "</tr>",
    ]
    for h in horas:
        fila = [f"<td class='hora'>{h:02d}:00</td>"]
        for d in DIAS:
            celda = celdas.get((h, d))
            if celda:
                bg = color_de[celda["cod_asig"]]
                clases = "clase"
                # Tooltip con datos completos al pasar el mouse
                tooltip = f"{celda['abrev']} · Sección {celda['seccion']} · Prof. {celda['docente']}"
                if celda.get("violaciones"):
                    clases += " violada"
                    motivos_txt = ", ".join(_MOTIVO_DESC.get(m, m) for m in celda["violaciones"])
                    tooltip += f" | ⚠ Viola: {motivos_txt}"
                fila.append(
                    f"<td class='{clases}' style='background:{bg};' title='{tooltip}'>"
                    f"<div class='asig'>{celda['abrev']}</div>"
                    f"<div class='sec'>Sec {celda['seccion']}</div>"
                    f"<div class='prof'>{celda['docente']}</div>"
                    f"</td>"
                )
            else:
                fila.append("<td></td>")
        html.append("<tr>" + "".join(fila) + "</tr>")
    html.append("</table>")
    html.append("</div>")
    return "\n".join(html)


def _render_leyenda(cromosoma):
    """Tabla con asignatura, docente, cupo, créditos."""
    filas = []
    visto = set()
    for s in cromosoma.secciones:
        key = (s.codAsignatura, s.codSeccion)
        if key in visto:
            continue
        visto.add(key)
        abrev = _abreviar_asignatura(s.desAsignatura)
        filas.append({
            "Código": f"{abrev}-S{s.codSeccion}",
            "Asignatura": s.desAsignatura.strip(),
            "Docente": s.docente_completo,
            "Cupo": f"{s.matriculados}/{s.topeAlumnos}",
            "Cr": int(s.creditos),
        })
    st.dataframe(filas, hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────
# SIDEBAR: login + control de caché
# ─────────────────────────────────────────────────────────────────────

def _sidebar():
    with st.sidebar:
        # Título institucional
        st.markdown(
            "<h2 style='margin:0 0 0.25rem 0; color:#8B1A1A;'>🎓 Horarios UNMSM</h2>"
            "<div style='color:#6B7280; font-size:0.85rem; margin-bottom:1rem;'>"
            "Optimizador con algoritmos genéticos</div>",
            unsafe_allow_html=True,
        )

        if st.session_state.alumno is None:
            st.markdown("#### 🔐 Iniciar sesión")
            st.caption("Ingresá tus credenciales del Sistema Único de Matrícula.")
            usuario = st.text_input(
                "Usuario / código", value=os.getenv("LOGIN", ""),
                placeholder="Ej: 22200033",
            )
            password = st.text_input(
                "Contraseña", type="password", value=os.getenv("PASSWORD", ""),
                placeholder="••••••••",
            )
            forzar = st.checkbox(
                "Forzar re-scraping (ignorar caché)", value=False,
                help="Marcar solo si los datos del caché están desactualizados.",
            )

            if st.button("Conectar al SUM", type="primary", use_container_width=True):
                if not usuario or not password:
                    st.error("Faltan credenciales.")
                    return
                with st.spinner("Conectando al SUM..."):
                    try:
                        datos, origen = _scrape_o_cargar_cache(usuario, password, forzar)
                        _parsear_y_guardar(datos)
                        st.session_state.credenciales_usuario = usuario
                        st.session_state.credenciales_password = password
                        st.success(
                            f"Datos cargados desde {'caché local' if origen == 'cache' else 'SUM'}"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo conectar: {e}")
        else:
            alumno = st.session_state.alumno
            raw = alumno.raw
            nombre_completo = f"{raw.get('nomAlumno', '').strip()} {raw.get('apePaterno', '').strip()} {raw.get('apeMaterno', '').strip()}"

            # Card del alumno
            st.markdown("#### 👤 Sesión activa")
            st.markdown(
                f"""
                <div class="sidebar-caja">
                    <div class="nombre">{nombre_completo}</div>
                    <div class="detalle">Código {raw.get('codAlumno', '?')}</div>
                    <div class="detalle">Ciclo {alumno.cicloActual} · Ponderado {alumno.promedioPonderado}</div>
                    <div class="detalle">{raw.get('desEscuela', '').strip()}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Acciones
            st.markdown("#### ⚙️ Acciones")
            if st.button("🔄 Re-scrapear datos", use_container_width=True, help="Ignora el caché y consulta el SUM"):
                with st.spinner("Re-scrapeando..."):
                    try:
                        usuario = st.session_state.credenciales_usuario or os.getenv("LOGIN", "")
                        password = st.session_state.credenciales_password or os.getenv("PASSWORD", "")
                        if not usuario or not password:
                            st.error("Cerrá sesión y volvé a loguearte para forzar scrape.")
                        else:
                            datos, _ = _scrape_o_cargar_cache(usuario, password, forzar_scrape=True)
                            _parsear_y_guardar(datos)
                            st.success("Re-scrape completo")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Fallo: {e}")

            if st.button("🚪 Cerrar sesión", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                _init_state()
                st.rerun()

            # Footer informativo
            st.markdown("---")
            st.caption(
                "Sistema desarrollado como tesis de la Escuela Profesional de "
                "Ingeniería de Sistemas · UNMSM"
            )


# ─────────────────────────────────────────────────────────────────────
# TAB 1: MIS HORARIOS
# ─────────────────────────────────────────────────────────────────────

def _tab_horarios():
    st.markdown("### 📅 Mis horarios")
    st.markdown(
        "<div style='color:#6B7280; margin-bottom:1rem;'>"
        "Optimización con algoritmo genético · Genera 5 horarios diversos ajustados a "
        "tus preferencias y la realidad del semestre."
        "</div>",
        unsafe_allow_html=True,
    )

    if not st.session_state.prematricula:
        st.warning("Tu prematrícula está vacía. No hay asignaturas para optimizar.")
        return

    col1, col2 = st.columns([1, 3])
    with col1:
        k = cargar_config().ga.top_k
        if st.button(f"🧬 Generar {k} horarios", type="primary", use_container_width=True):
            with st.spinner("Ejecutando algoritmo genético..."):
                scores = cargar_scores_docentes()
                prefs = cargar_preferencias_horarios()
                contexto = _construir_contexto(scores, prefs)
                _correr_ga(contexto)
                st.rerun()
    with col2:
        if st.session_state.horarios:
            st.success(
                f"✅ **{len(st.session_state.horarios)} horarios** generados en "
                f"**{st.session_state.duracion_ga:.2f}s** · "
                f"Cromosomas válidos: {st.session_state.gen_validos_ini} → {st.session_state.gen_validos_fin}"
            )

    # ── Distinguir "aún no clickeó" vs "clickeó y no hay resultados" ──
    if not st.session_state.horarios:
        if not st.session_state.ga_ya_corrio:
            st.info("Aún no se generaron horarios. Apretá el botón de arriba.")
        else:
            # El GA corrió pero devolvió vacío incluso relajando las HARD configurables
            # (o no había hard configurables para relajar). Es un problema estructural.
            st.error(
                "❌ **No se pudo generar ningún horario válido para tu prematrícula.** "
                "El problema es estructural, no se resuelve relajando tus preferencias:"
            )
            st.markdown(
                "- Puede haber **choques horarios inevitables** entre las secciones disponibles.\n"
                "- Alguna asignatura puede tener **prerequisitos no aprobados** en tu historial.\n"
                "- La suma de créditos de tu prematrícula puede **exceder el máximo** del plan.\n"
                "- Puede haber **asignaturas sin secciones disponibles** este semestre."
            )
            if st.session_state.omitidas:
                st.info(
                    f"ℹ️ Detectamos {len(st.session_state.omitidas)} asignatura(s) sin sección "
                    "disponible este semestre. Reducí tu prematrícula en el SUM para excluirlas."
                )
        return

    if st.session_state.omitidas:
        with st.expander(f"⚠️ {len(st.session_state.omitidas)} asignatura(s) sin sección disponible"):
            for cod in st.session_state.omitidas:
                desc = next(
                    (p["desAsignatura"].strip() for p in st.session_state.prematricula
                     if p["codAsignatura"] == cod), "?"
                )
                st.write(f"- **{cod}** — {desc}")

    # Render por horario
    horarios = st.session_state.horarios
    k_pedido = cargar_config().ga.top_k
    scores = cargar_scores_docentes()
    prefs = cargar_preferencias_horarios()
    contexto = _construir_contexto(scores, prefs)
    modo_fallback = st.session_state.modo_fallback

    # ── Banner de fallback (arriba de todos los horarios) ──
    if modo_fallback:
        hard_txt = ", ".join(f"**{_HARD_DESC.get(h, h)}**" for h in st.session_state.hard_relajadas)
        st.warning(
            f"⚠️ **No se encontraron horarios cumpliendo TODAS tus restricciones estrictas.** "
            f"Se muestran alternativas ignorando temporalmente: {hard_txt}. "
            f"Los bloques con **borde rojo y ⚠** son los que violan esas restricciones. "
            f"Considerá relajar alguna de esas reglas en la pestaña **Preferencias** para "
            f"que el sistema pueda encontrar horarios válidos."
        )

    def _render_uno(c):
        fit = evaluar_fitness(c, contexto)
        p_hor = preferencia_horarios(c, contexto)
        p_doc = preferencia_docentes(c, contexto)
        p_cup = preferencia_cupos(c, contexto)
        creditos = sum(s.creditos for s in c.secciones)

        # Métricas como cards coloreadas por concepto
        m1, m2, m3, m4, m5 = st.columns(5)
        for col, cls, label, valor in [
            (m1, "fitness",  "Fitness",  f"{fit:.4f}"),
            (m2, "horarios", "Horarios", f"{p_hor:.2f}"),
            (m3, "docentes", "Docentes", f"{p_doc:.2f}"),
            (m4, "cupos",    "Cupos",    f"{p_cup:.2f}"),
            (m5, "creditos", "Créditos", f"{creditos:.0f}"),
        ]:
            col.markdown(
                f"<div class='metrica-card {cls}'>"
                f"<div class='label'>{label}</div>"
                f"<div class='valor'>{valor}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.write("")  # aire

        # En modo fallback, pasamos el contexto original a la grilla para que
        # marque las celdas violadoras con borde rojo.
        ctx_para_grilla = contexto if modo_fallback else None
        st.markdown(_render_grilla_html(c, ctx_para_grilla), unsafe_allow_html=True)

        # Expander con recomendaciones (solo en modo fallback)
        if modo_fallback:
            recs = _recomendaciones_por_horario(c, contexto.prefs_horario)
            if recs:
                with st.expander(f"💡 Recomendaciones para este horario ({len(recs)} sección(es) en conflicto)"):
                    for r in recs:
                        motivos_lista = []
                        for bv in r["bloques_violadores"]:
                            motivo_txt = ", ".join(_MOTIVO_DESC.get(m, m) for m in bv["motivos"])
                            motivos_lista.append(f"{bv['dia']} {bv['hora']} — {motivo_txt}")
                        st.markdown(
                            f"- **{r['asignatura']}** (Sección {r['seccion']}, docente {r['docente']}):"
                        )
                        for line in motivos_lista:
                            st.markdown(f"    - {line}")
                        st.caption(
                            "Para tomar esta sección: quitá la restricción correspondiente en "
                            "**Preferencias → Horarios**."
                        )

        st.markdown("##### Detalle de secciones")
        _render_leyenda(c)

    if len(horarios) == 1:
        if not modo_fallback:
            st.warning(
                f"ℹ️ **Solo hay UN horario posible** que cumple todas las restricciones de tu "
                f"prematrícula. No existen más combinaciones distintas (se pidieron {k_pedido}, "
                f"pero el espacio de búsqueda no permite más variantes)."
            )
        st.subheader("Horario óptimo único")
        _render_uno(horarios[0])
    else:
        if len(horarios) < k_pedido and not modo_fallback:
            st.info(
                f"ℹ️ Solo se encontraron **{len(horarios)} horarios suficientemente distintos** "
                f"(se pidieron {k_pedido}). El espacio de búsqueda de tu prematrícula no permite más variantes."
            )
        tabs = st.tabs([f"Horario #{i+1}" for i in range(len(horarios))])
        for tab, c in zip(tabs, horarios):
            with tab:
                _render_uno(c)

    # Descargas
    st.divider()
    st.markdown("#### 📥 Exportar horarios")
    st.caption("Descargá los 5 horarios en formato Excel (una hoja por horario) o PDF (una página por horario).")
    col_x, col_p = st.columns(2)
    try:
        path_x = exportar_excel(horarios, contexto, "output/horarios.xlsx", asignaturas_omitidas=st.session_state.omitidas)
        with open(path_x, "rb") as f:
            col_x.download_button(
                "⬇️ Descargar Excel (.xlsx)",
                data=f.read(),
                file_name="horarios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    except Exception as e:
        col_x.error(f"Excel falló: {e}")

    try:
        path_p = exportar_pdf(horarios, contexto, "output/horarios.pdf", asignaturas_omitidas=st.session_state.omitidas)
        with open(path_p, "rb") as f:
            col_p.download_button(
                "⬇️ Descargar PDF",
                data=f.read(),
                file_name="horarios.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    except Exception as e:
        col_p.error(f"PDF falló: {e}")


# ─────────────────────────────────────────────────────────────────────
# TAB 2: PREFERENCIAS
# ─────────────────────────────────────────────────────────────────────

def _docentes_unicos_en_prematricula() -> List[dict]:
    """Lista única de docentes presentes en las secciones de la prematrícula."""
    if not st.session_state.prematricula or not st.session_state.secciones:
        return []
    cods_pre = {p["codAsignatura"] for p in st.session_state.prematricula}
    visto = {}
    for s in st.session_state.secciones:
        if s.codAsignatura not in cods_pre or s.codDocente in visto:
            continue
        visto[s.codDocente] = {
            "codDocente": s.codDocente,
            "nombre": s.docente_completo,
            "asignatura_ejemplo": s.desAsignatura.strip(),
        }
    return list(visto.values())


def _tab_preferencias():
    st.header("Preferencias")
    st.caption(
        "Ajustá tus preferencias. El GA usa estos valores para puntuar cada horario. "
        "Los cambios se guardan en `data/preferencias_*.json` (ignorados por git)."
    )

    sub_doc, sub_hor = st.tabs(["🎓 Docentes", "🕒 Horarios"])

    # ───── Docentes ─────
    with sub_doc:
        st.write("**Slider 0 = evitar, 0.5 = neutral, 1 = preferido.**")
        scores_actuales = cargar_scores_docentes()
        docentes = _docentes_unicos_en_prematricula()
        if not docentes:
            st.info("Conectate al SUM primero para ver los docentes de tu prematrícula.")
        else:
            nuevos_scores = dict(scores_actuales)
            for doc in docentes:
                cod = doc["codDocente"]
                actual = scores_actuales.get(cod, 0.5)
                nuevos_scores[cod] = st.slider(
                    f"{doc['nombre']} _(ej: {doc['asignatura_ejemplo'][:32]})_",
                    min_value=0.0, max_value=1.0, value=float(actual), step=0.05,
                    key=f"score_doc_{cod}",
                )
            if st.button("💾 Guardar scores de docentes", type="primary"):
                Path("data/preferencias_docentes.json").write_text(
                    json.dumps({"scores": nuevos_scores}, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                st.success("Guardado. Regenerá los horarios para que apliquen.")

    # ───── Horarios ─────
    with sub_hor:
        prefs_actual = cargar_preferencias_horarios()

        # ── Preferencias SOFT (penalizan el fitness) ──
        st.markdown("##### Preferencias (afectan el puntaje del horario)")
        turnos = [TURNO_INDIFERENTE, TURNO_MANANA, TURNO_TARDE, TURNO_NOCHE]
        turno_idx = turnos.index(prefs_actual.turno_preferido) if prefs_actual.turno_preferido in turnos else 0
        nuevo_turno = st.selectbox(
            "Turno preferido",
            options=turnos,
            index=turno_idx,
            help="Mañana 7-13, Tarde 13-18, Noche 18-22",
        )

        nuevos_dias = st.multiselect(
            "Días libres deseados (sin clase)",
            options=DIAS,
            default=prefs_actual.dias_libres_deseados,
            help="Preferís que estos días queden libres, pero el sistema puede "
                 "elegir asignarlos si mejora el balance general.",
        )

        densidades = [DENSIDAD_INDIFERENTE, DENSIDAD_COMPACTO, DENSIDAD_DISTRIBUIDO]
        dens_idx = densidades.index(prefs_actual.densidad) if prefs_actual.densidad in densidades else 0
        nueva_dens = st.selectbox(
            "Densidad",
            options=densidades,
            index=dens_idx,
            help="Compacto = clases en pocos días; Distribuido = repartidas",
        )

        # ── Restricciones HARD (descalifican horarios que las violen) ──
        st.markdown("---")
        st.markdown("##### 🔒 Restricciones estrictas (descartan horarios que las violen)")
        st.caption(
            "⚠️ Cuidado: si marcás muchas restricciones estrictas puede que no "
            "existan horarios posibles con tu prematrícula. En ese caso el "
            "sistema te va a avisar."
        )

        nuevos_dias_hard = st.multiselect(
            "🔒 Días obligatoriamente libres",
            options=DIAS,
            default=prefs_actual.dias_libres_obligatorios,
            help="Ningún horario generado tendrá clase en estos días. Se aplica "
                 "como regla dura (no como preferencia).",
        )

        col_min, col_max = st.columns(2)
        with col_min:
            usa_min = st.checkbox(
                "Aplicar hora mínima",
                value=prefs_actual.hora_min is not None,
                help="Si está activo, no se aceptarán bloques que empiecen antes de la hora indicada.",
            )
            if usa_min:
                default_min = _parsear_hhmm(prefs_actual.hora_min) or dt_time(8, 0)
                nueva_hmin_t = st.time_input("🔒 Hora mínima obligatoria", value=default_min, step=1800)
                nueva_hora_min = f"{nueva_hmin_t.hour:02d}:{nueva_hmin_t.minute:02d}"
            else:
                nueva_hora_min = None
        with col_max:
            usa_max = st.checkbox(
                "Aplicar hora máxima",
                value=prefs_actual.hora_max is not None,
                help="Si está activo, no se aceptarán bloques que terminen después de la hora indicada.",
            )
            if usa_max:
                default_max = _parsear_hhmm(prefs_actual.hora_max) or dt_time(22, 0)
                nueva_hmax_t = st.time_input("🔒 Hora máxima obligatoria", value=default_max, step=1800)
                nueva_hora_max = f"{nueva_hmax_t.hour:02d}:{nueva_hmax_t.minute:02d}"
            else:
                nueva_hora_max = None

        st.markdown("---")
        if st.button("💾 Guardar preferencias de horario", type="primary", key="save_hor"):
            Path("data/preferencias_horarios.json").write_text(
                json.dumps({
                    "turno_preferido": nuevo_turno,
                    "dias_libres_deseados": nuevos_dias,
                    "densidad": nueva_dens,
                    "dias_libres_obligatorios": nuevos_dias_hard,
                    "hora_min": nueva_hora_min,
                    "hora_max": nueva_hora_max,
                }, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            st.success("Guardado. Regenerá los horarios para que apliquen.")


# ─────────────────────────────────────────────────────────────────────
# TAB 3: DATOS ACADÉMICOS
# ─────────────────────────────────────────────────────────────────────

def _tab_datos():
    st.header("Datos académicos")
    alumno = st.session_state.alumno
    raw = alumno.raw

    col1, col2, col3 = st.columns(3)
    col1.metric("Ciclo actual", alumno.cicloActual)
    col2.metric("Ponderado", alumno.promedioPonderado)
    col3.metric("Plan", st.session_state.plan[0].codPlan if st.session_state.plan else "?")

    st.write("**Escuela**:", raw.get("desEscuela", "?"))
    st.write("**Facultad**:", raw.get("desFacultad", "?"))
    st.write("**Situación**:", raw.get("desSituacion", "?"))

    st.divider()

    # Prematrícula
    st.subheader(f"📝 Prematrícula ({len(st.session_state.prematricula)} asignaturas)")
    pre_rows = [
        {
            "Código": p["codAsignatura"],
            "Asignatura": p["desAsignatura"].strip(),
            "Créditos": p.get("num_creditaje", 0),
            "Ciclo plan": p.get("num_ciclo_ano_asig", "?"),
        }
        for p in st.session_state.prematricula
    ]
    st.dataframe(pre_rows, hide_index=True, use_container_width=True)

    # Plan
    with st.expander(f"📖 Plan de estudios ({len(st.session_state.plan)} asignaturas)"):
        plan_rows = [
            {
                "Ciclo": a.ciclo,
                "Código": a.codAsignatura,
                "Asignatura": a.desAsignatura,
                "Créditos": a.creditos,
                "Tipo": a.tipoAsignatura,
                "Prerequisito": a.codAsignaturaPre if a.codAsignaturaPre != "NR" else "—",
            }
            for a in st.session_state.plan
        ]
        st.dataframe(plan_rows, hide_index=True, use_container_width=True)

    # Historial
    aprobadas = extraer_aprobados(st.session_state.historial)
    with st.expander(f"📜 Historial ({len(st.session_state.historial)} registros · {len(aprobadas)} aprobadas)"):
        hist_rows = [
            {
                "Semestre": r.codSemestre,
                "Código": r.codAsignatura,
                "Asignatura": r.desAsignatura,
                "Nota": r.calificacion,
                "Créditos": r.creditos,
            }
            for r in st.session_state.historial
        ]
        st.dataframe(hist_rows, hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

def _render_header():
    """Header institucional visible cuando hay una sesión activa."""
    alumno = st.session_state.alumno
    raw = alumno.raw
    nombre = f"{raw.get('nomAlumno', '').strip()} {raw.get('apePaterno', '').strip()}"
    escuela = raw.get("desEscuela", "").strip()
    codigo = raw.get("codAlumno", "?")
    st.markdown(
        f"""
        <div class="app-header">
            <div>
                <h1>🎓 Optimizador de horarios UNMSM</h1>
                <div class="subtitulo">
                    Generación de horarios óptimos mediante algoritmos genéticos
                </div>
            </div>
            <div class="alumno-info">
                <strong>{nombre}</strong><br/>
                {escuela}<br/>
                Código {codigo} · Ciclo {alumno.cicloActual} · Ponderado {alumno.promedioPonderado}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_bienvenida():
    """Pantalla de bienvenida cuando no hay sesión."""
    st.markdown(
        """
        <div class="app-header">
            <div>
                <h1>🎓 Optimizador de horarios UNMSM</h1>
                <div class="subtitulo">
                    Generación de horarios óptimos mediante algoritmos genéticos
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown(
            """
            ### Cómo funciona

            1. **Iniciá sesión** con tus credenciales del SUM desde la barra lateral.
            2. **Ajustá tus preferencias** de docentes y horarios.
            3. **Generá 5 horarios óptimos** diferentes entre sí, listos para revisar y descargar.

            El sistema evalúa cada horario contra restricciones duras (choques, prerequisitos,
            créditos) y suaves (turno preferido, docentes, disponibilidad de cupos) para
            entregarte alternativas realistas que respetan tu situación académica.
            """
        )
    with col_right:
        st.info(
            "💡 Si tenés configurado `LOGIN` y `PASSWORD` en un archivo `.env`, "
            "las credenciales se cargan como valores por defecto."
        )


def main():
    _sidebar()

    if st.session_state.alumno is None:
        _render_bienvenida()
        return

    _render_header()

    tab_h, tab_p, tab_d = st.tabs(["📅 Mis horarios", "⚙️ Preferencias", "🎓 Datos académicos"])
    with tab_h:
        _tab_horarios()
    with tab_p:
        _tab_preferencias()
    with tab_d:
        _tab_datos()


if __name__ == "__main__":
    main()

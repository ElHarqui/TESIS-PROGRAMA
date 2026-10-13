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
import sys
import time
from datetime import time as dt_time
from pathlib import Path
from typing import List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
    SumCredencialesInvalidasError,
    SumDatosIncompletosError,
    SumError,
    SumMantenimientoError,
    SumTimeoutError,
)
from fitness import (
    ContextoAlumno,
    PreferenciasHorario,
    evaluar_fitness,
    preferencia_cupos,
    preferencia_docentes,
    preferencia_horarios,
)
from fitness.preferencias import (
    cargar_preferencias_horarios,
    guardar_preferencias_horarios,
    cargar_scores_docentes,
    guardar_scores_docentes,
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
from services import (
    ejecutar_optimizacion,
    detectar_hard_activas,
    detectar_violaciones_bloque,
    generar_recomendaciones_horario,
)
from models import Cromosoma, HorarioResultado
from output import exportar_excel, exportar_pdf
from output.visualizer import (
    DIAS,
    DIAS_ABREV,
    HORA_FIN,
    HORA_INICIO,
    _abreviar_asignatura,
)
from config import cargar_config, ParametrosGA


# Playwright es async; Streamlit corre en su propio loop. Permitir loops anidados.
nest_asyncio.apply()

# .env como FALLBACK: si no se hace login en la UI, se intentan estas credenciales.
load_dotenv()

CACHE_KEY = "datos_sum"

PALETA_CURSOS = [
    {"bg": "#EEF2FF", "border": "#4F46E5", "text": "#1E1B4B", "badge_bg": "#E0E7FF", "badge_text": "#3730A3"},  # Indigo
    {"bg": "#ECFDF5", "border": "#059669", "text": "#064E3B", "badge_bg": "#D1FAE5", "badge_text": "#047857"},  # Esmeralda
    {"bg": "#FFFBEB", "border": "#D97706", "text": "#78350F", "badge_bg": "#FEF3C7", "badge_text": "#B45309"},  # Ámbar
    {"bg": "#F5F3FF", "border": "#7C3AED", "text": "#4C1D95", "badge_bg": "#EDE9FE", "badge_text": "#6D28D9"},  # Violeta
    {"bg": "#EFF6FF", "border": "#2563EB", "text": "#1E3A8A", "badge_bg": "#DBEAFE", "badge_text": "#1D4ED8"},  # Azul
    {"bg": "#FDF2F8", "border": "#DB2777", "text": "#831843", "badge_bg": "#FCE7F3", "badge_text": "#BE185D"},  # Rosa
    {"bg": "#F0FDFA", "border": "#0D9488", "text": "#134E4A", "badge_bg": "#CCFBF1", "badge_text": "#0F766E"},  # Teal
    {"bg": "#FFF7ED", "border": "#EA580C", "text": "#7C2D12", "badge_bg": "#FFEDD5", "badge_text": "#C2410C"},  # Naranja
    {"bg": "#F8FAFC", "border": "#475569", "text": "#0F172A", "badge_bg": "#E2E8F0", "badge_text": "#334155"},  # Pizarra
    {"bg": "#FAF5FF", "border": "#9333EA", "text": "#581C87", "badge_bg": "#F3E8FF", "badge_text": "#7E22CE"},  # Púrpura
]


# ─────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LA PÁGINA
# ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Optimizador de Horarios UNMSM",
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
# CSS PERSONALIZADO (Diseño Institucional Premium)
# ─────────────────────────────────────────────────────────────────────

_CUSTOM_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  /* Tipografía general para elementos de texto sin pisar los iconos de Streamlit */
  html, body, p, h1, h2, h3, h4, h5, h6, label, input, textarea {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  /* PROTECCIÓN ESTRICTA de las fuentes de iconos de Streamlit (Material Symbols / Icons) */
  [data-testid*="stIcon"],
  [data-testid*="Icon"],
  .material-symbols-rounded,
  .material-symbols-outlined,
  .material-icons,
  [class*="material-symbols"],
  [class*="material-icons"],
  button[data-testid="stSidebarCollapseButton"] *,
  button[data-testid="collapsedControl"] *,
  details summary [class*="st-"],
  [data-baseweb="tab"] [class*="st-"] {
    font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons", sans-serif !important;
    font-style: normal !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    word-wrap: normal !important;
    white-space: nowrap !important;
    direction: ltr !important;
  }

  /* Ocultar decoraciones por defecto de Streamlit y barra superior vacía */
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  [data-testid="stStatusWidget"] {display: none;}
  header[data-testid="stHeader"],
  [data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  /* Contenedor principal: pegado al tope superior y con ancho completo responsivo */
  .main .block-container,
  div[data-testid="stAppViewContainer"] .block-container,
  .block-container {
    padding-top: 0.75rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
  }

  /* Contenedor de la barra lateral ajustado al tope */
  section[data-testid="stSidebar"] div.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
  }

  /* Header institucional con degradado Granate UNMSM */
  .app-header {
    background: linear-gradient(135deg, #7C1010 0%, #580B0B 60%, #3D0707 100%);
    color: #FFFFFF;
    padding: 1.35rem 1.85rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 15px rgba(124, 16, 16, 0.22);
    border-bottom: 3px solid #D97706;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1.5rem;
    flex-wrap: wrap;
  }
  .app-header h1 {
    margin: 0;
    font-size: 1.55rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF;
  }
  .app-header .subtitulo {
    opacity: 0.9;
    font-size: 0.88rem;
    margin-top: 0.25rem;
    font-weight: 400;
    color: #FEE2E2;
  }

  /* Chips del alumno */
  .alumno-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    justify-content: flex-end;
  }
  .badge-chip {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 9999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 500;
    color: #FFFFFF;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
  }
  .badge-chip.destacado {
    background: #D97706;
    border-color: #F59E0B;
    color: #FFFFFF;
    font-weight: 700;
  }

  /* Tarjetas KPI de Métricas */
  .kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    position: relative;
    overflow: hidden;
  }
  .kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(0, 0, 0, 0.06);
  }
  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
  }
  .kpi-card.fitness::before   { background: #7C1010; }
  .kpi-card.horarios::before  { background: #2563EB; }
  .kpi-card.docentes::before  { background: #059669; }
  .kpi-card.cupos::before     { background: #D97706; }
  .kpi-card.creditos::before  { background: #7C3AED; }

  .kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.35rem;
  }
  .kpi-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748B;
  }
  .kpi-icon {
    font-size: 1.1rem;
  }
  .kpi-value {
    font-size: 1.55rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.1;
    font-family: 'JetBrains Mono', monospace;
  }
  .kpi-desc {
    font-size: 0.75rem;
    color: #94A3B8;
    margin-top: 0.25rem;
    font-weight: 500;
  }

  /* Grilla del horario estilo Google Calendar / Notion */
  .horario-wrap {
    background: #FFFFFF;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    border: 1px solid #E2E8F0;
    margin: 0.75rem 0 1.25rem 0;
  }
  .horario {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    table-layout: fixed;
  }
  .horario th {
    background: #F8FAFC;
    color: #334155;
    font-weight: 700;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.75rem 0.5rem;
    text-align: center;
    border-bottom: 2px solid #CBD5E1;
    border-right: 1px solid #E2E8F0;
  }
  .horario th:last-child {
    border-right: none;
  }
  .horario td {
    border-bottom: 1px solid #F1F5F9;
    border-right: 1px solid #F1F5F9;
    padding: 3px;
    vertical-align: top;
    height: 52px;
  }
  .horario td:last-child {
    border-right: none;
  }
  .horario td.hora {
    background: #F8FAFC;
    color: #64748B;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    width: 68px;
    text-align: center;
    vertical-align: middle;
    border-right: 1px solid #CBD5E1;
    user-select: none;
  }

  /* Tarjeta interna de evento en la celda */
  .evento-card {
    border-radius: 6px;
    padding: 4px 6px;
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border-left-width: 4px;
    border-left-style: solid;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    overflow: hidden;
  }
  .evento-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.12);
    z-index: 5;
  }
  .evento-top {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 2px;
  }
  .evento-asig {
    font-weight: 700;
    font-size: 0.82rem;
    line-height: 1.1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .evento-sec {
    font-size: 0.68rem;
    font-weight: 700;
    border-radius: 4px;
    padding: 1px 4px;
    white-space: nowrap;
  }
  .evento-prof {
    font-size: 0.7rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 2px;
    opacity: 0.9;
  }

  /* Violaciones en Fallback */
  .evento-card.violada {
    box-shadow: 0 0 0 2px #DC2626 !important;
    position: relative;
  }
  .evento-card.violada::after {
    content: '⚠️';
    position: absolute;
    top: 1px;
    right: 2px;
    font-size: 0.75rem;
  }

  /* Sidebar Styling */
  section[data-testid="stSidebar"] {
    background-color: #F8FAFC;
    border-right: 1px solid #E2E8F0;
  }
  .sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0 1rem 0;
    margin-bottom: 0.75rem;
    border-bottom: 1px solid #E2E8F0;
  }
  .sidebar-brand-icon {
    font-size: 1.8rem;
    background: #FEE2E2;
    border-radius: 10px;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .sidebar-brand-text h2 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 800;
    color: #7C1010;
    line-height: 1.1;
  }
  .sidebar-brand-text span {
    font-size: 0.75rem;
    color: #64748B;
    font-weight: 500;
  }

  /* User Card en Sidebar */
  .user-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 0.85rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  }
  .user-card .user-name {
    font-weight: 700;
    font-size: 0.92rem;
    color: #0F172A;
  }
  .user-card .user-meta {
    font-size: 0.78rem;
    color: #64748B;
    margin-top: 0.2rem;
  }
  .user-card .user-school {
    font-size: 0.75rem;
    color: #7C1010;
    font-weight: 600;
    margin-top: 0.35rem;
  }

  /* Botones principales con identidad UNMSM */
  div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7C1010 0%, #991B1B 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.25rem !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 6px rgba(124, 16, 16, 0.25) !important;
    transition: all 0.15s ease !important;
  }
  div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(124, 16, 16, 0.35) !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 2px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 0.55rem 1.1rem;
    font-weight: 600;
    font-size: 0.9rem;
    color: #64748B;
    transition: all 0.15s ease;
  }
  .stTabs [data-baseweb="tab"]:hover {
    background: #F1F5F9;
    color: #0F172A;
  }
  .stTabs [aria-selected="true"] {
    background: #FEE2E2 !important;
    color: #7C1010 !important;
    border-bottom: 2px solid #7C1010 !important;
  }

  /* Onboarding / Feature cards */
  .onboarding-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.25rem;
    margin: 1.5rem 0;
  }
  .feature-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.35rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  .feature-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
  }
  .feature-icon-wrap {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    margin-bottom: 0.85rem;
  }
  .feature-icon-wrap.sum     { background: #FEE2E2; color: #7C1010; }
  .feature-icon-wrap.prefs   { background: #FEF3C7; color: #B45309; }
  .feature-icon-wrap.ga      { background: #EEF2FF; color: #4338CA; }
  .feature-title {
    font-weight: 700;
    font-size: 1.05rem;
    color: #0F172A;
    margin-bottom: 0.4rem;
  }
  .feature-text {
    font-size: 0.85rem;
    color: #64748B;
    line-height: 1.5;
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
        "historial_convergencia": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


def _usuario_actual() -> str:
    """Retorna el código/identificador del usuario logeado en la sesión actual."""
    if st.session_state.get("credenciales_usuario"):
        return str(st.session_state.credenciales_usuario).strip()
    if st.session_state.get("alumno") and hasattr(st.session_state.alumno, "raw"):
        cod = st.session_state.alumno.raw.get("codAlumno")
        if cod:
            return str(cod).strip()
    return ""


# ─────────────────────────────────────────────────────────────────────
# HELPERS DE BACKEND (envuelven el async)
# ─────────────────────────────────────────────────────────────────────

def _scrape_o_cargar_cache(login: str, password: str, forzar_scrape: bool):
    cache = Cache(usuario=login)
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

    # Intentar restaurar automáticamente el último cálculo de horarios del usuario
    u = _usuario_actual()
    if u:
        _restaurar_cache_ga(u)


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


def _guardar_cache_ga(usuario: str, resultado) -> None:
    """Persiste los resultados de la optimización en el disco para el usuario actual."""
    if not usuario or not getattr(resultado, "horarios", None):
        return
    try:
        cache = Cache(usuario=usuario)
        datos_guardar = {
            "duracion": getattr(resultado, "duracion", 0.0),
            "gen_validos_ini": getattr(resultado, "gen_validos_ini", 0),
            "gen_validos_fin": getattr(resultado, "gen_validos_fin", 0),
            "modo_fallback": getattr(resultado, "modo_fallback", False),
            "hard_relajadas": getattr(resultado, "hard_relajadas", []),
            "omitidas": getattr(resultado, "omitidas", []),
            "fitness_fin": getattr(resultado, "fitness_fin", []),
            "historial_convergencia": getattr(resultado, "historial_convergencia", []),
            "horarios": [
                [[s.codAsignatura, s.codSeccion] for s in c.secciones]
                for c in resultado.horarios
            ],
        }
        cache.set("ultimo_resultado_ga", datos_guardar)
    except Exception:
        pass


def _restaurar_cache_ga(usuario: str) -> bool:
    """Restaura los últimos horarios y curva de convergencia guardados en caché si la sesión está vacía."""
    if not usuario or not st.session_state.get("secciones") or st.session_state.get("horarios"):
        return False
    try:
        cache = Cache(usuario=usuario)
        datos = cache.get("ultimo_resultado_ga")
        if not datos or not datos.get("horarios"):
            return False

        sec_map = {(s.codAsignatura, s.codSeccion): s for s in st.session_state.secciones}
        horarios_rest = []
        for c_firmas in datos["horarios"]:
            secs_cromo = [sec_map[tuple(f)] for f in c_firmas if tuple(f) in sec_map]
            if secs_cromo:
                horarios_rest.append(Cromosoma(secs_cromo))

        if not horarios_rest:
            return False

        st.session_state.horarios = horarios_rest
        st.session_state.duracion_ga = datos.get("duracion", 0.0)
        st.session_state.gen_validos_ini = datos.get("gen_validos_ini", 0)
        st.session_state.gen_validos_fin = datos.get("gen_validos_fin", 0)
        st.session_state.modo_fallback = datos.get("modo_fallback", False)
        st.session_state.hard_relajadas = datos.get("hard_relajadas", [])
        st.session_state.omitidas = datos.get("omitidas", [])
        st.session_state.fitness_fin = datos.get("fitness_fin", [])
        st.session_state.historial_convergencia = datos.get("historial_convergencia", [])
        st.session_state.ga_ya_corrio = True
        return True
    except Exception:
        return False


def _correr_ga(contexto: ContextoAlumno, config_ga: Optional[ParametrosGA] = None):
    """
    Ejecuta la optimización delegando al servicio de dominio (optimizer_service).
    Maneja el pase estándar, el fallback y la recolección de métricas de convergencia.
    """
    codigos_asig = [p["codAsignatura"] for p in st.session_state.prematricula]
    resultado = ejecutar_optimizacion(
        secciones=st.session_state.secciones,
        codigos_asignaturas=codigos_asig,
        contexto=contexto,
        config_ga=config_ga,
    )
    st.session_state.horarios = resultado.horarios
    st.session_state.fitness_fin = resultado.fitness_fin
    st.session_state.omitidas = resultado.omitidas
    st.session_state.duracion_ga = resultado.duracion
    st.session_state.gen_validos_ini = resultado.gen_validos_ini
    st.session_state.gen_validos_fin = resultado.gen_validos_fin
    st.session_state.modo_fallback = resultado.modo_fallback
    st.session_state.hard_relajadas = resultado.hard_relajadas
    st.session_state.contexto_original = resultado.contexto_original
    st.session_state.historial_convergencia = getattr(resultado, "historial_convergencia", [])
    st.session_state.ga_ya_corrio = True

    # Persistir en el almacenamiento local del usuario
    u = _usuario_actual()
    _guardar_cache_ga(u, resultado)


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
    Renderiza la grilla del horario con diseño visual de calendario moderno.

    Cada celda con clase muestra una tarjeta (.evento-card):
      1. Top: Asignatura abreviada en negrita + Badge de sección estilizado.
      2. Bottom: Docente a cargo con avatar sutil.

    Si `contexto_original` se pasa (modo fallback), los bloques que violan
    alguna HARD configurable del alumno se marcan con estilo de advertencia (violada).
    """
    prefs_para_violar = None
    if contexto_original is not None and detectar_hard_activas(contexto_original.prefs_horario):
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
            violaciones = detectar_violaciones_bloque(b, prefs_para_violar) if prefs_para_violar else []
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

    tema_de = {cod: PALETA_CURSOS[i % len(PALETA_CURSOS)] for i, cod in enumerate(asignaturas_orden)}

    # Solo horas con clase
    if celdas:
        horas = sorted({h for (h, _) in celdas.keys()})
        horas = list(range(min(horas), max(horas) + 1))
    else:
        horas = list(range(HORA_INICIO, HORA_FIN))

    html = [
        "<div class='horario-wrap'>",
        "<table class='horario'>",
        "<tr><th style='width:68px;'>HORA</th>" + "".join(f"<th>{d}</th>" for d in DIAS_ABREV) + "</tr>",
    ]
    for h in horas:
        fila = [f"<td class='hora'>{h:02d}:00</td>"]
        for d in DIAS:
            celda = celdas.get((h, d))
            if celda:
                tema = tema_de[celda["cod_asig"]]
                card_cls = "evento-card violada" if celda.get("violaciones") else "evento-card"
                tooltip = f"{celda['abrev']} · Sección {celda['seccion']} · Prof. {celda['docente']}"
                if celda.get("violaciones"):
                    motivos_txt = ", ".join(_MOTIVO_DESC.get(m, m) for m in celda["violaciones"])
                    tooltip += f" | ⚠️ Viola: {motivos_txt}"

                fila.append(
                    f"<td>"
                    f"<div class='{card_cls}' "
                    f"style='background:{tema['bg']}; border-left-color:{tema['border']}; color:{tema['text']};' "
                    f"title='{tooltip}'>"
                    f"<div class='evento-top'>"
                    f"<span class='evento-asig' style='color:{tema['text']};'>{celda['abrev']}</span>"
                    f"<span class='evento-sec' style='background:{tema['badge_bg']}; color:{tema['badge_text']};'>Sec {celda['seccion']}</span>"
                    f"</div>"
                    f"<div class='evento-prof' style='color:{tema['text']};'>👤 {celda['docente']}</div>"
                    f"</div>"
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
    st.dataframe(filas, hide_index=True)


# ─────────────────────────────────────────────────────────────────────
# SIDEBAR: login + control de caché
# ─────────────────────────────────────────────────────────────────────

def _sidebar():
    with st.sidebar:
        # Branding institucional
        st.markdown(
            """
            <div class="sidebar-brand">
              <div class="sidebar-brand-icon">🎓</div>
              <div class="sidebar-brand-text">
                <h2>UNMSM Horarios</h2>
                <span>Ingeniería de Sistemas · FISI</span>
              </div>
            </div>
            """,
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

            if st.button("Conectar al SUM", type="primary", width="stretch"):
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
                    except SumCredencialesInvalidasError as e:
                        st.error("🔑 **Credenciales incorrectas**: Usuario o contraseña no válidos en el SUM.")
                    except SumMantenimientoError as e:
                        st.error("🚧 **SUM no disponible**: El servidor de la universidad está en mantenimiento o no responde.")
                    except SumTimeoutError as e:
                        st.error("⏱️ **Tiempo de espera agotado**: El portal del SUM está respondiendo muy lento. Intentá nuevamente.")
                    except SumDatosIncompletosError as e:
                        st.warning("⚠️ **Datos incompletos**: No se encontraron cursos en prematrícula o programación para este alumno.")
                    except Exception as e:
                        st.error(f"❌ Error al conectar: {e}")
        else:
            alumno = st.session_state.alumno
            raw = alumno.raw
            nombre_completo = f"{raw.get('nomAlumno', '').strip()} {raw.get('apePaterno', '').strip()} {raw.get('apeMaterno', '').strip()}"

            # Card ejecutiva del alumno
            st.markdown("#### 👤 Sesión activa")
            st.markdown(
                f"""
                <div class="user-card">
                    <div class="user-name">{nombre_completo}</div>
                    <div class="user-meta">Código: <strong>{raw.get('codAlumno', '?')}</strong> · Ciclo {alumno.cicloActual}</div>
                    <div class="user-meta">Ponderado: <strong>{alumno.promedioPonderado}</strong></div>
                    <div class="user-school">🏛️ {raw.get('desEscuela', '').strip() or 'FISI'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Acciones
            st.markdown("#### ⚙️ Acciones")
            if st.button("🔄 Re-scrapear datos", width="stretch", help="Ignora el caché y consulta el SUM"):
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
                    except SumCredencialesInvalidasError:
                        st.error("🔑 **Credenciales incorrectas**: Verificá tu usuario y contraseña del SUM.")
                    except SumMantenimientoError:
                        st.error("🚧 **SUM en mantenimiento**: El portal del SUM reportó errores temporales.")
                    except SumTimeoutError:
                        st.error("⏱️ **Tiempo agotado**: El servidor tardó demasiado en responder.")
                    except SumDatosIncompletosError:
                        st.warning("⚠️ **Datos incompletos**: No se recibieron todos los endpoints requeridos.")
                    except Exception as e:
                        st.error(f"Fallo: {e}")

            if st.button("🚪 Cerrar sesión", width="stretch"):
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
# COMPONENTE DE CONVERGENCIA GENERACIONAL (TESIS)
# ─────────────────────────────────────────────────────────────────────

def _render_graficos_convergencia(historial: list, compacto: bool = False, key_prefix: str = "conv"):
    """
    Renderiza los gráficos y métricas de convergencia generacional del GA.
    Separa limpiamente:
    1. Curva de Fitness Factible (en rango positivo [0.0, 1.0]).
    2. Curva de Factibilidad Poblacional (resolución de restricciones duras / CSP).
    """
    if not historial:
        st.info("ℹ️ No hay historial de convergencia disponible para graficar.")
        return

    import pandas as pd
    df_hist = pd.DataFrame(historial)
    n_gen = len(df_hist)
    mejor_max = df_hist["mejor"].max()
    mejor_ini = df_hist["mejor"].iloc[0]
    mejor_fin = df_hist["mejor"].iloc[-1]
    val_ini = df_hist["validos"].iloc[0]
    val_fin = df_hist["validos"].iloc[-1]

    # Asegurar promedio_validos positivo
    if "promedio_validos" not in df_hist.columns:
        df_hist["promedio_validos"] = df_hist["mejor"]

    df_fitness = df_hist.set_index("generacion")[["mejor", "promedio_validos"]].copy()
    df_fitness.columns = ["Mejor Fitness Factible", "Promedio Soluciones Válidas"]

    df_validos = df_hist.set_index("generacion")[["validos"]].copy()
    df_validos.columns = ["Cromosomas Válidos (Sin Choques)"]

    if compacto:
        # Versión para la pestaña principal de Horarios
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Generaciones", n_gen)
        col_m2.metric("Mejor Fitness", f"{mejor_fin:.4f}", delta=f"{(mejor_fin - mejor_ini):+.4f}" if (mejor_fin != mejor_ini) else None)
        col_m3.metric("Factibilidad Final", f"{val_fin} válidos", delta=f"{(val_fin - val_ini):+d} desde Gen 1" if (val_fin != val_ini) else None)
        gen_conv = df_hist[df_hist["mejor"] >= (0.99 * mejor_max)]["generacion"].iloc[0] if mejor_max > 0 else n_gen
        col_m4.metric("Convergencia Estimada", f"Gen #{gen_conv}", help="Generación donde el algoritmo alcanzó el 99% de su óptimo final.")

        tab_fit, tab_val = st.tabs(["🧬 Curva de Fitness Factible", "🛡️ Evolución de Factibilidad"])
        with tab_fit:
            st.line_chart(df_fitness, height=270)
            st.caption("Aptitud del mejor horario encontrado y del promedio de cromosomas factibles a lo largo de las generaciones.")
        with tab_val:
            st.line_chart(df_validos, height=270)
            st.caption("Evolución de cromosomas factibles (sin choques). El atractor estacionario (~50%–65%) refleja el equilibrio dinámico entre la selección y la disrupción de operadores (Burke et al., 2004; Lewis, 2008).")
    else:
        # Versión analítica para la pestaña de Tesis y Experimentación
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        col_k1.metric("Total Generaciones", n_gen)
        col_k2.metric("Mejor Fitness", f"{mejor_fin:.4f}", delta=f"{(mejor_fin - mejor_ini):+.4f}")
        col_k3.metric("Cromosomas Válidos", f"{val_ini} → {val_fin}", delta=f"{(val_fin - val_ini):+d} factibles")
        dur_ga = st.session_state.get("duracion_ga", 0.0) or 0.0
        col_k4.metric("Duración GA", f"{dur_ga:.2f}s")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### 🧬 Evolución del Fitness Factible")
            st.line_chart(df_fitness, height=310)
            st.caption("Monitorea la convergencia de la función multiobjetivo (docentes, turnos, cupos) en escala positiva [0.0, 1.0].")
        with col_g2:
            st.markdown("##### 🛡️ Satisfacción de Restricciones Duras (CSP)")
            st.line_chart(df_validos, height=310)
            st.caption("Dinámica de factibilidad: rápida absorción en gen 1–5 y atractor estacionario (~60%) por equilibrio entre presión selectiva y disrupción estocástica (Burke et al., 2004).")

        # Tabla y descarga de datos para el informe de tesis
        with st.expander("📋 Ver dataset generacional completo (Tabla paso a paso)"):
            st.dataframe(df_hist, hide_index=True)
            u = _usuario_actual() or "alumno"
            csv_bytes = df_hist.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar Datos de Convergencia (.CSV para informe de tesis)",
                data=csv_bytes,
                file_name=f"convergencia_ga_{u}_{n_gen}gen.csv",
                mime="text/csv",
                width="stretch",
                key=f"{key_prefix}_dl_csv",
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

    u = _usuario_actual()
    if not st.session_state.horarios:
        _restaurar_cache_ga(u)

    col1, col2 = st.columns([1, 3])
    with col1:
        k = cargar_config().ga.top_k
        if st.button(f"🧬 Generar {k} horarios", type="primary", width="stretch"):
            with st.spinner("Ejecutando algoritmo genético..."):
                u = _usuario_actual()
                scores = cargar_scores_docentes(usuario=u)
                prefs = cargar_preferencias_horarios(usuario=u)
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

    # ── Curva de Convergencia del GA en la pestaña principal ──
    historial = st.session_state.get("historial_convergencia", [])
    if historial and st.session_state.horarios:
        with st.expander("📈 Curva de Convergencia del Algoritmo Genético (Evolución Generacional)", expanded=False):
            _render_graficos_convergencia(historial, compacto=True, key_prefix="tab_horarios")

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
    u = _usuario_actual()
    scores = cargar_scores_docentes(usuario=u)
    prefs = cargar_preferencias_horarios(usuario=u)
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

        # Métricas ejecutivas estilo KPI Card
        m1, m2, m3, m4, m5 = st.columns(5)
        kpis = [
            (m1, "fitness",  "Fitness",   "🧬", f"{fit:.4f}",   "Puntaje global"),
            (m2, "horarios", "Horarios",  "🕒", f"{p_hor:.2f}",  "Afinidad de turnos"),
            (m3, "docentes", "Docentes",  "👨‍🏫", f"{p_doc:.2f}",  "Preferencia docente"),
            (m4, "cupos",    "Cupos",     "📊", f"{p_cup:.2f}",  "Disponibilidad"),
            (m5, "creditos", "Créditos",  "🎓", f"{creditos:.0f}", "Carga lectiva"),
        ]
        for col, cls, label, icon, valor, desc in kpis:
            col.markdown(
                f"""
                <div class='kpi-card {cls}'>
                  <div class='kpi-header'>
                    <span class='kpi-label'>{label}</span>
                    <span class='kpi-icon'>{icon}</span>
                  </div>
                  <div class='kpi-value'>{valor}</div>
                  <div class='kpi-desc'>{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.write("")  # aire

        # En modo fallback, pasamos el contexto original a la grilla para que
        # marque las celdas violadoras con borde rojo.
        ctx_para_grilla = contexto if modo_fallback else None
        st.markdown(_render_grilla_html(c, ctx_para_grilla), unsafe_allow_html=True)

        # Expander con recomendaciones (solo en modo fallback)
        if modo_fallback:
            recs = generar_recomendaciones_horario(c, contexto.prefs_horario)
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
                width="stretch",
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
                width="stretch",
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
    u = _usuario_actual()
    st.header("Preferencias")
    user_label = f"del alumno **{u}**" if u else "de la sesión local"
    st.caption(
        f"Ajustá tus preferencias. El GA usa estos valores para puntuar cada horario. "
        f"Los cambios se guardan de forma aislada para tu usuario ({user_label}) "
        f"en `data/users/` (ignorados por git)."
    )

    sub_doc, sub_hor = st.tabs(["🎓 Docentes", "🕒 Horarios"])

    # ───── Docentes ─────
    with sub_doc:
        st.write("**Slider 0 = evitar, 0.5 = neutral, 1 = preferido.**")
        scores_actuales = cargar_scores_docentes(usuario=u)
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
                guardar_scores_docentes(nuevos_scores, usuario=u)
                st.success("Guardado. Regenerá los horarios para que apliquen.")

    # ───── Horarios ─────
    with sub_hor:
        prefs_actual = cargar_preferencias_horarios(usuario=u)

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
            prefs_nuevas = PreferenciasHorario(
                turno_preferido=nuevo_turno,
                dias_libres_deseados=nuevos_dias,
                densidad=nueva_dens,
                dias_libres_obligatorios=nuevos_dias_hard,
                hora_min=nueva_hora_min,
                hora_max=nueva_hora_max,
            )
            guardar_preferencias_horarios(prefs_nuevas, usuario=u)
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
    st.dataframe(pre_rows, hide_index=True)

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
        st.dataframe(plan_rows, hide_index=True)

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
        st.dataframe(hist_rows, hide_index=True)


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
    situacion = raw.get("desSituacion", "REGULAR").strip()
    st.markdown(
        f"""
        <div class="app-header">
            <div>
                <h1>🎓 Optimizador de Horarios UNMSM</h1>
                <div class="subtitulo">
                    Sistema Inteligente de Generación Horaria · Algoritmos Genéticos
                </div>
            </div>
            <div class="alumno-chips">
                <span class="badge-chip destacado">🏛️ {escuela or 'FISI'}</span>
                <span class="badge-chip">👤 {nombre}</span>
                <span class="badge-chip">🆔 {codigo}</span>
                <span class="badge-chip">📚 Ciclo {alumno.cicloActual}</span>
                <span class="badge-chip">⭐ Promedio {alumno.promedioPonderado}</span>
                <span class="badge-chip">✅ {situacion}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_bienvenida():
    """Pantalla de bienvenida y onboarding interactivo."""
    st.markdown(
        """
        <div class="app-header">
            <div>
                <h1>🎓 Optimizador de Horarios UNMSM</h1>
                <div class="subtitulo">
                    Sistema Inteligente de Planificación de Matrícula · Algoritmos Genéticos
                </div>
            </div>
            <div class="alumno-chips">
                <span class="badge-chip destacado">🏛️ FISI UNMSM</span>
                <span class="badge-chip">✨ Portal Web de Matrícula</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="onboarding-grid">
            <div class="feature-card">
                <div class="feature-icon-wrap sum">🔐</div>
                <div class="feature-title">1. Conexión Directa al SUM</div>
                <div class="feature-text">
                    Autenticación segura con tus credenciales institucionales. Extrae automáticamente tu prematrícula, plan de estudios, vacantes y prerequisitos en tiempo real.
                </div>
            </div>
            <div class="feature-card">
                <div class="feature-icon-wrap prefs">⚙️</div>
                <div class="feature-title">2. Preferencias a Tu Medida</div>
                <div class="feature-text">
                    Personalizá turnos (mañana, tarde, noche), días libres obligatorios, docentes favoritos y límites de horarios. El optimizador adapta el cronograma a tu vida.
                </div>
            </div>
            <div class="feature-card">
                <div class="feature-icon-wrap ga">🧬</div>
                <div class="feature-title">3. Algoritmo Genético</div>
                <div class="feature-text">
                    Evolución cromosómica de 5 horarios óptimos y libres de choques. Visualizá la grilla interactiva, métricas de calidad y exportá directamente en Excel o PDF.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.info(
            "👉 **Para comenzar:** Ingresá tus credenciales del SUM en la barra lateral izquierda y presioná **Conectar al SUM**."
        )
    with col_right:
        st.caption(
            "🔒 **Seguridad y Privacidad:** Las credenciales y preferencias se procesan localmente en tu sesión y están aisladas por usuario en `data/users/`."
        )


def _tab_comparador():
    st.markdown("### ⚖️ Comparador de Horarios Lado a Lado")
    st.markdown(
        "<div style='color:#6B7280; margin-bottom:1rem;'>"
        "Analizá y contrastá las diferencias cualitativas y cuantitativas entre dos soluciones generadas por el algoritmo genético."
        "</div>",
        unsafe_allow_html=True,
    )

    horarios = st.session_state.horarios
    if not horarios:
        st.info("ℹ️ Todavía no se han generado los horarios para poder compararlos.")
        if st.button("🧬 Generar Horarios Ahora", type="primary", key="btn_gen_comp"):
            if not st.session_state.prematricula:
                st.warning("Conectate al SUM primero para cargar tu prematrícula.")
            else:
                with st.spinner("Ejecutando algoritmo genético..."):
                    u = _usuario_actual()
                    scores = cargar_scores_docentes(usuario=u)
                    prefs = cargar_preferencias_horarios(usuario=u)
                    contexto = _construir_contexto(scores, prefs)
                    _correr_ga(contexto)
                st.rerun()
        return

    if len(horarios) < 2:
        st.warning("⚠️ Se generó un único horario posible. No hay múltiples variantes para contrastar.")
        return

    n_hor = len(horarios)
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        idx_a = st.selectbox(
            "Seleccionar Horario A",
            options=list(range(n_hor)),
            format_func=lambda i: f"Horario #{i+1}",
            index=0,
            key="cmp_idx_a",
        )
    with col_sel2:
        idx_b = st.selectbox(
            "Seleccionar Horario B",
            options=list(range(n_hor)),
            format_func=lambda i: f"Horario #{i+1}",
            index=1 if n_hor > 1 else 0,
            key="cmp_idx_b",
        )

    cA = horarios[idx_a]
    cB = horarios[idx_b]

    u = _usuario_actual()
    scores = cargar_scores_docentes(usuario=u)
    prefs = cargar_preferencias_horarios(usuario=u)
    contexto = _construir_contexto(scores, prefs)

    resA = HorarioResultado.construir(idx_a + 1, cA, contexto)
    resB = HorarioResultado.construir(idx_b + 1, cB, contexto)

    # Métricas contrastadas
    st.markdown("#### 📊 Balance Comparativo")
    m1, m2, m3, m4 = st.columns(4)
    delta_fit = resB.fitness - resA.fitness
    delta_hor = resB.score_horarios - resA.score_horarios
    delta_doc = resB.score_docentes - resA.score_docentes
    delta_cup = resB.score_cupos - resA.score_cupos

    m1.metric("🧬 Fitness", f"{resA.fitness:.4f} vs {resB.fitness:.4f}", delta=f"{delta_fit:+.4f}" if delta_fit != 0 else None)
    m2.metric("🕒 Turnos & Días", f"{resA.score_horarios:.2f} vs {resB.score_horarios:.2f}", delta=f"{delta_hor:+.2f}" if delta_hor != 0 else None)
    m3.metric("👨‍🏫 Docentes", f"{resA.score_docentes:.2f} vs {resB.score_docentes:.2f}", delta=f"{delta_doc:+.2f}" if delta_doc != 0 else None)
    m4.metric("📊 Cupos", f"{resA.score_cupos:.2f} vs {resB.score_cupos:.2f}", delta=f"{delta_cup:+.2f}" if delta_cup != 0 else None)

    # Tabla comparativa de cursos y secciones
    st.markdown("#### 🔄 Matriz de Asignaturas y Docentes")
    sec_A = {s.codAsignatura: s for s in cA.secciones}
    sec_B = {s.codAsignatura: s for s in cB.secciones}
    todas_asig = sorted(set(sec_A.keys()) | set(sec_B.keys()))

    filas_comp = []
    diferencias = 0
    for cod in todas_asig:
        sA = sec_A.get(cod)
        sB = sec_B.get(cod)
        nombre = sA.desAsignatura.strip() if sA else (sB.desAsignatura.strip() if sB else cod)
        secA_txt = f"Sec {sA.codSeccion} · {sA.apePatDocente}" if sA else "—"
        secB_txt = f"Sec {sB.codSeccion} · {sB.apePatDocente}" if sB else "—"

        coincide = (sA and sB and sA.codSeccion == sB.codSeccion)
        if not coincide:
            diferencias += 1

        filas_comp.append({
            "Código": cod,
            "Asignatura": nombre,
            f"Horario #{idx_a+1}": secA_txt,
            f"Horario #{idx_b+1}": secB_txt,
            "Estado": "✅ Idéntico" if coincide else "🔄 Distinta Sección",
        })

    st.dataframe(filas_comp, hide_index=True)
    if diferencias == 0:
        st.success("Ambos horarios seleccionados tienen exactamente las mismas secciones.")
    else:
        st.info(f"💡 Se encontraron **{diferencias} asignatura(s) con distinta sección / docente** entre los dos horarios.")


def _tab_tesis_experimentacion():
    st.markdown("### 🔬 Panel de Experimentación Científica & Métricas del GA")
    st.markdown(
        "<div style='color:#6B7280; margin-bottom:1rem;'>"
        "Herramientas de evaluación empírica para la sustentación de tesis: análisis de convergencia generacional, "
        "trazabilidad del fitness y calibración de hiperparámetros del algoritmo genético."
        "</div>",
        unsafe_allow_html=True,
    )

    u = _usuario_actual()
    if not st.session_state.horarios:
        _restaurar_cache_ga(u)

    historial = st.session_state.get("historial_convergencia", [])

    # 1. Gráfica de convergencia y métricas
    st.markdown("#### 📈 Curva de Convergencia Generacional")
    if not historial:
        st.info("ℹ️ Todavía no se ha ejecutado el algoritmo genético para este usuario.")
        if st.button("🧬 Generar Horarios y Curva de Convergencia Ahora", type="primary", key="btn_gen_tesis"):
            if not st.session_state.prematricula:
                st.warning("Conectate al SUM primero para cargar tu prematrícula.")
            else:
                with st.spinner("Ejecutando algoritmo genético..."):
                    scores = cargar_scores_docentes(usuario=u)
                    prefs = cargar_preferencias_horarios(usuario=u)
                    contexto = _construir_contexto(scores, prefs)
                    _correr_ga(contexto)
                st.rerun()
    else:
        _render_graficos_convergencia(historial, compacto=False, key_prefix="tab_tesis")

    st.divider()

    # 2. Calibración de Hiperparámetros
    st.markdown("#### ⚙️ Calibración de Hiperparámetros del GA")
    st.caption("Ajustá los parámetros del algoritmo para evaluar su impacto en la calidad de la solución y la velocidad de convergencia.")

    cfg_def = cargar_config().ga
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        p_tam = st.slider("Tamaño de población", min_value=20, max_value=200, value=cfg_def.tamano_poblacion, step=10)
        p_gen = st.slider("Número de generaciones", min_value=10, max_value=150, value=cfg_def.generaciones, step=5)
    with col_p2:
        p_mut = st.slider("Tasa de mutación", min_value=0.01, max_value=0.40, value=cfg_def.tasa_mutacion, step=0.01)
        p_tor = st.slider("Tamaño de torneo", min_value=2, max_value=6, value=cfg_def.tamano_torneo, step=1)
    with col_p3:
        p_eli = st.slider("Elitismo (individuos)", min_value=1, max_value=5, value=cfg_def.elitismo, step=1)
        p_topk = st.slider("Horarios a devolver (top-k)", min_value=1, max_value=8, value=cfg_def.top_k, step=1)

    if st.button("🧪 Ejecutar Experimento con Nuevos Parámetros", type="primary", width="stretch", key="btn_run_exp"):
        if not st.session_state.prematricula:
            st.warning("Conectate al SUM primero para cargar tu prematrícula.")
            return

        with st.spinner(f"Ejecutando GA experimental ({p_gen} gen, {p_tam} cromosomas)..."):
            scores = cargar_scores_docentes(usuario=u)
            prefs = cargar_preferencias_horarios(usuario=u)
            contexto = _construir_contexto(scores, prefs)
            custom_ga = ParametrosGA(
                tamano_poblacion=p_tam,
                generaciones=p_gen,
                tasa_mutacion=p_mut,
                tamano_torneo=p_tor,
                elitismo=p_eli,
                top_k=p_topk,
                distancia_minima=cfg_def.distancia_minima,
            )
            _correr_ga(contexto, config_ga=custom_ga)
            st.rerun()


def main():
    _sidebar()

    if st.session_state.alumno is None:
        _render_bienvenida()
        return

    _render_header()

    tab_h, tab_comp, tab_tesis, tab_p, tab_d = st.tabs([
        "📅 Mis horarios",
        "⚖️ Comparador",
        "🔬 Métricas de Tesis",
        "⚙️ Preferencias",
        "🎓 Datos académicos",
    ])
    with tab_h:
        _tab_horarios()
    with tab_comp:
        _tab_comparador()
    with tab_tesis:
        _tab_tesis_experimentacion()
    with tab_p:
        _tab_preferencias()
    with tab_d:
        _tab_datos()


if __name__ == "__main__":
    main()

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
)


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


def _correr_ga(contexto: ContextoAlumno):
    """Ejecuta el GA completo. Devuelve (horarios_top_k, fitness_final)."""
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

    st.session_state.horarios = top
    st.session_state.fitness_fin = fitness_fin
    st.session_state.omitidas = omitidas
    st.session_state.duracion_ga = duracion
    st.session_state.gen_validos_ini = sum(1 for f in fitness_ini if f > 0)
    st.session_state.gen_validos_fin = sum(1 for f in fitness_fin if f > 0)


# ─────────────────────────────────────────────────────────────────────
# COMPONENTES DE UI
# ─────────────────────────────────────────────────────────────────────

def _render_grilla_html(cromosoma) -> str:
    """Renderiza la grilla del horario como tabla HTML coloreada."""
    # Mapear celdas (hora, día) → (etiqueta, codAsignatura)
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

    color_de = {cod: PALETA[i % len(PALETA)] for i, cod in enumerate(asignaturas_orden)}

    # Solo horas con clase
    if celdas:
        horas = sorted({h for (h, _) in celdas.keys()})
        horas = list(range(min(horas), max(horas) + 1))
    else:
        horas = list(range(HORA_INICIO, HORA_FIN))

    # HTML
    html = [
        "<style>",
        ".horario {border-collapse: collapse; width: 100%; font-size: 0.85em; margin: 0.5em 0;}",
        ".horario th, .horario td {border: 1px solid #888; padding: 6px; text-align: center;}",
        ".horario th {background: #DDDDDD;}",
        ".horario td.hora {background: #EEEEEE; font-weight: bold; width: 60px;}",
        "</style>",
        "<table class='horario'>",
        "<tr><th>HORA</th>" + "".join(f"<th>{d}</th>" for d in DIAS_ABREV) + "</tr>",
    ]
    for h in horas:
        fila = [f"<td class='hora'>{h:02d}:00</td>"]
        for d in DIAS:
            celda = celdas.get((h, d))
            if celda:
                etiqueta, cod = celda
                fila.append(f"<td style='background:{color_de[cod]};'>{etiqueta}</td>")
            else:
                fila.append("<td></td>")
        html.append("<tr>" + "".join(fila) + "</tr>")
    html.append("</table>")
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
        st.title("🎓 Horarios UNMSM")

        if st.session_state.alumno is None:
            st.subheader("Ingresar al SUM")
            usuario = st.text_input("Usuario / código", value=os.getenv("LOGIN", ""))
            password = st.text_input("Contraseña", type="password", value=os.getenv("PASSWORD", ""))
            forzar = st.checkbox("Forzar re-scraping (ignorar caché)", value=False)

            if st.button("Conectar al SUM", type="primary", use_container_width=True):
                if not usuario or not password:
                    st.error("Faltan credenciales.")
                    return
                with st.spinner("Conectando al SUM..."):
                    try:
                        datos, origen = _scrape_o_cargar_cache(usuario, password, forzar)
                        _parsear_y_guardar(datos)
                        st.success(f"Datos cargados ({'caché' if origen == 'cache' else 'scrape'})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fallo: {e}")
        else:
            alumno = st.session_state.alumno
            st.markdown(f"**👤 {alumno.raw.get('nomAlumno', '')} {alumno.raw.get('apePaterno', '')}**")
            st.caption(f"Código: {alumno.raw.get('codAlumno', '?')}")
            st.caption(f"Ciclo {alumno.cicloActual} · Ponderado {alumno.promedioPonderado}")
            st.divider()

            if st.button("🔄 Re-scrapear (forzar)", use_container_width=True):
                with st.spinner("Re-scrapeando..."):
                    try:
                        usuario = os.getenv("LOGIN", "") or st.session_state.credenciales_usuario
                        password = os.getenv("PASSWORD", "") or st.session_state.credenciales_password
                        if not usuario or not password:
                            st.error("Cerrá sesión y volvé a loguearte para forzar scrape.")
                        else:
                            datos, _ = _scrape_o_cargar_cache(usuario, password, forzar_scrape=True)
                            _parsear_y_guardar(datos)
                            st.success("Re-scrape OK")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Fallo: {e}")

            if st.button("Cerrar sesión", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                _init_state()
                st.rerun()


# ─────────────────────────────────────────────────────────────────────
# TAB 1: MIS HORARIOS
# ─────────────────────────────────────────────────────────────────────

def _tab_horarios():
    st.header("Mis horarios")
    st.caption(
        "Genera 5 horarios diferentes optimizados con algoritmo genético, "
        "ajustados a tus preferencias y la realidad de cupos del semestre."
    )

    if not st.session_state.prematricula:
        st.warning("Tu prematrícula está vacía. No hay asignaturas para optimizar.")
        return

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🧬 Generar 5 horarios", type="primary", use_container_width=True):
            with st.spinner("Ejecutando algoritmo genético..."):
                scores = cargar_scores_docentes()
                prefs = cargar_preferencias_horarios()
                contexto = _construir_contexto(scores, prefs)
                _correr_ga(contexto)
                st.rerun()
    with col2:
        if st.session_state.horarios:
            st.success(
                f"Top-{len(st.session_state.horarios)} generados en {st.session_state.duracion_ga:.2f}s · "
                f"Válidos: {st.session_state.gen_validos_ini} → {st.session_state.gen_validos_fin}"
            )

    if not st.session_state.horarios:
        st.info("Aún no se generaron horarios. Apretá el botón de arriba.")
        return

    if st.session_state.omitidas:
        with st.expander(f"⚠️ {len(st.session_state.omitidas)} asignatura(s) sin sección disponible"):
            for cod in st.session_state.omitidas:
                desc = next(
                    (p["desAsignatura"].strip() for p in st.session_state.prematricula
                     if p["codAsignatura"] == cod), "?"
                )
                st.write(f"- **{cod}** — {desc}")

    # Pestañas por horario
    horarios = st.session_state.horarios
    scores = cargar_scores_docentes()
    prefs = cargar_preferencias_horarios()
    contexto = _construir_contexto(scores, prefs)

    tabs = st.tabs([f"Horario #{i+1}" for i in range(len(horarios))])
    for i, (tab, c) in enumerate(zip(tabs, horarios)):
        with tab:
            fit = evaluar_fitness(c, contexto)
            p_hor = preferencia_horarios(c, contexto)
            p_doc = preferencia_docentes(c, contexto)
            p_cup = preferencia_cupos(c, contexto)
            creditos = sum(s.creditos for s in c.secciones)

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Fitness", f"{fit:.4f}")
            m2.metric("Horarios", f"{p_hor:.2f}")
            m3.metric("Docentes", f"{p_doc:.2f}")
            m4.metric("Cupos", f"{p_cup:.2f}")
            m5.metric("Créditos", f"{creditos:.0f}")

            st.markdown(_render_grilla_html(c), unsafe_allow_html=True)
            st.subheader("Leyenda")
            _render_leyenda(c)

    # Descargas
    st.divider()
    st.subheader("Descargas")
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
        )

        densidades = [DENSIDAD_INDIFERENTE, DENSIDAD_COMPACTO, DENSIDAD_DISTRIBUIDO]
        dens_idx = densidades.index(prefs_actual.densidad) if prefs_actual.densidad in densidades else 0
        nueva_dens = st.selectbox(
            "Densidad",
            options=densidades,
            index=dens_idx,
            help="Compacto = clases en pocos días; Distribuido = repartidas",
        )

        if st.button("💾 Guardar preferencias de horario", type="primary", key="save_hor"):
            Path("data/preferencias_horarios.json").write_text(
                json.dumps({
                    "turno_preferido": nuevo_turno,
                    "dias_libres_deseados": nuevos_dias,
                    "densidad": nueva_dens,
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

def main():
    _sidebar()

    if st.session_state.alumno is None:
        st.title("Optimizador de horarios UNMSM")
        st.write(
            "Iniciá sesión desde la barra lateral con tus credenciales del SUM "
            "para que el sistema arme tus 5 mejores horarios."
        )
        st.info(
            "💡 Tip: si configurás `LOGIN` y `PASSWORD` en un archivo `.env`, "
            "se cargan como valores por defecto en el formulario de login."
        )
        return

    tab_h, tab_p, tab_d = st.tabs(["📅 Mis horarios", "⚙️ Preferencias", "🎓 Datos académicos"])
    with tab_h:
        _tab_horarios()
    with tab_p:
        _tab_preferencias()
    with tab_d:
        _tab_datos()


if __name__ == "__main__":
    main()

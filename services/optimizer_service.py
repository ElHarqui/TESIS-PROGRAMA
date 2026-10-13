import dataclasses
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config import ParametrosGA, cargar_config
from fitness import ContextoAlumno, PreferenciasHorario, evaluar_fitness
from fitness.hard_constraints import _hhmm_a_minutos
from genetic import ejecutar_ga, generar_poblacion_inicial, top_k_diversos
from genetic.population import _es_seccion_valida
from models import BloqueHorario, Cromosoma, Seccion


@dataclass
class ResultadoPaseGA:
    """Resultado bruto de una ejecución del algoritmo genético."""
    top: List[Cromosoma]
    fitness_fin: List[float]
    omitidas: List[str]
    duracion: float
    gen_validos_ini: int
    gen_validos_fin: int
    historial_convergencia: List[dict] = field(default_factory=list)


@dataclass
class ResultadoOptimizacion:
    """
    Resultado completo del proceso de optimización, incluyendo posibles
    relajaciones automáticas de restricciones duras del alumno (fallback).
    """
    horarios: List[Cromosoma]
    fitness_fin: List[float]
    omitidas: List[str]
    duracion: float
    gen_validos_ini: int
    gen_validos_fin: int
    modo_fallback: bool = False
    hard_relajadas: List[str] = field(default_factory=list)
    contexto_original: Optional[ContextoAlumno] = None
    historial_convergencia: List[dict] = field(default_factory=list)


def detectar_hard_activas(prefs: PreferenciasHorario) -> List[str]:
    """
    Devuelve los nombres de las HARD configurables por el alumno que están activas.
    Vacío si el alumno no configuró ninguna (defaults: [], None, None).
    """
    activas = []
    if prefs.dias_libres_obligatorios:
        activas.append("dias_libres_obligatorios")
    if prefs.hora_min:
        activas.append("hora_min")
    if prefs.hora_max:
        activas.append("hora_max")
    return activas


def relajar_hard_constraints(prefs: PreferenciasHorario) -> PreferenciasHorario:
    """
    Devuelve una copia de `prefs` con las 3 HARD configurables desactivadas
    ([], None, None). Preserva las preferencias SOFT (turno, días deseados, densidad).
    """
    return dataclasses.replace(
        prefs,
        dias_libres_obligatorios=[],
        hora_min=None,
        hora_max=None,
    )


def detectar_violaciones_bloque(bloque: BloqueHorario, prefs: Optional[PreferenciasHorario]) -> List[str]:
    """
    Devuelve la lista de motivos por los que este bloque viola las HARD
    configurables de `prefs`. Cada motivo es uno de: 'dia_libre', 'hora_min', 'hora_max'.
    Vacía si el bloque no viola ninguna o si prefs es None.
    """
    if prefs is None:
        return []

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


def generar_recomendaciones_horario(cromosoma: Cromosoma, prefs: PreferenciasHorario) -> List[dict]:
    """
    Analiza un horario candidato e identifica secciones que violan restricciones relajadas.
    Útil para diagnosticar y ofrecer feedback al alumno en modo fallback.
    """
    items = []
    for s in cromosoma.secciones:
        bloques_violadores = []
        for b in s.bloques:
            motivos = detectar_violaciones_bloque(b, prefs)
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


def ejecutar_pase_ga(
    secciones: List[Seccion],
    codigos_asignaturas: List[str],
    contexto: ContextoAlumno,
    config_ga: Optional[ParametrosGA] = None,
) -> ResultadoPaseGA:
    """
    Ejecuta un pase único del algoritmo genético para los cursos solicitados.
    """
    if config_ga is None:
        config_ga = cargar_config().ga

    sec_por_asig: Dict[str, List[Seccion]] = {}
    for s in secciones:
        if _es_seccion_valida(s):
            sec_por_asig.setdefault(s.codAsignatura, []).append(s)

    poblacion, omitidas = generar_poblacion_inicial(
        codigos_asignaturas,
        secciones,
        tamano_poblacion=config_ga.tamano_poblacion,
        seed=config_ga.seed,
    )
    fitness_ini = [evaluar_fitness(c, contexto) for c in poblacion]

    t0 = time.time()
    poblacion_final, historial = ejecutar_ga(
        poblacion,
        evaluador=lambda c: evaluar_fitness(c, contexto),
        secciones_por_asig=sec_por_asig,
        max_generaciones=config_ga.generaciones,
        tasa_mutacion=config_ga.tasa_mutacion,
        tamano_torneo=config_ga.tamano_torneo,
        elitismo=config_ga.elitismo,
        retornar_historial=True,
    )
    duracion = time.time() - t0

    fitness_fin = [evaluar_fitness(c, contexto) for c in poblacion_final]
    top = top_k_diversos(
        poblacion_final,
        fitness_fin,
        k=config_ga.top_k,
        distancia_minima=config_ga.distancia_minima,
    )

    return ResultadoPaseGA(
        top=top,
        fitness_fin=fitness_fin,
        omitidas=omitidas,
        duracion=duracion,
        gen_validos_ini=sum(1 for f in fitness_ini if f >= 0.0),
        gen_validos_fin=sum(1 for f in fitness_fin if f >= 0.0),
        historial_convergencia=historial,
    )


def ejecutar_optimizacion(
    secciones: List[Seccion],
    codigos_asignaturas: List[str],
    contexto: ContextoAlumno,
    config_ga: Optional[ParametrosGA] = None,
) -> ResultadoOptimizacion:
    """
    Orquestador principal de optimización con estrategia de fallback.
    1. Ejecuta pase normal respetando todas las restricciones.
    2. Si no hay horarios válidos y hay restricciones configurables activas,
       ejecuta segundo pase relajando esas restricciones para brindar alternativas.
    """
    r1 = ejecutar_pase_ga(secciones, codigos_asignaturas, contexto, config_ga)
    hard_activas = detectar_hard_activas(contexto.prefs_horario)

    if r1.top or not hard_activas:
        # Se encontraron horarios factibles o no había restricciones relajables
        return ResultadoOptimizacion(
            horarios=r1.top,
            fitness_fin=r1.fitness_fin,
            omitidas=r1.omitidas,
            duracion=r1.duracion,
            gen_validos_ini=r1.gen_validos_ini,
            gen_validos_fin=r1.gen_validos_fin,
            modo_fallback=False,
            hard_relajadas=[],
            contexto_original=contexto,
            historial_convergencia=r1.historial_convergencia,
        )

    # Fallback: relajar las restricciones duras configurables del alumno
    contexto_relajado = ContextoAlumno(
        prerequisitos=contexto.prerequisitos,
        aprobados=contexto.aprobados,
        max_creditos=contexto.max_creditos,
        scores_docentes=contexto.scores_docentes,
        prefs_horario=relajar_hard_constraints(contexto.prefs_horario),
        pesos=contexto.pesos,
    )
    r2 = ejecutar_pase_ga(secciones, codigos_asignaturas, contexto_relajado, config_ga)

    return ResultadoOptimizacion(
        horarios=r2.top,
        fitness_fin=r2.fitness_fin,
        omitidas=r2.omitidas,
        duracion=r1.duracion + r2.duracion,
        gen_validos_ini=r2.gen_validos_ini,
        gen_validos_fin=r2.gen_validos_fin,
        modo_fallback=bool(r2.top),
        hard_relajadas=hard_activas if r2.top else [],
        contexto_original=contexto,
        historial_convergencia=r2.historial_convergencia or r1.historial_convergencia,
    )

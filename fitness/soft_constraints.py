from models.cromosoma import Cromosoma
from .contexto import (
    ContextoAlumno,
    PreferenciasHorario,
    RANGOS_TURNO,
    TURNO_INDIFERENTE,
    DENSIDAD_COMPACTO,
    DENSIDAD_DISTRIBUIDO,
    DENSIDAD_INDIFERENTE,
)
from .preferencias import SCORE_NEUTRAL


def _score_turno(cromosoma: Cromosoma, prefs: PreferenciasHorario) -> float:
    """% de bloques cuya hora de inicio cae dentro del rango del turno preferido."""
    if prefs.turno_preferido == TURNO_INDIFERENTE:
        return SCORE_NEUTRAL
    rango = RANGOS_TURNO.get(prefs.turno_preferido)
    if rango is None:
        return SCORE_NEUTRAL
    inicio, fin = rango

    bloques = [b for s in cromosoma.secciones for b in s.bloques]
    if not bloques:
        return SCORE_NEUTRAL

    en_turno = sum(1 for b in bloques if inicio <= b.hora_inicio_int < fin)
    return en_turno / len(bloques)


def _score_dias_libres(cromosoma: Cromosoma, prefs: PreferenciasHorario) -> float:
    """
    Fracción de días deseados que efectivamente quedan SIN clases.
    Sin lista de deseados → SCORE_NEUTRAL.
    """
    if not prefs.dias_libres_deseados:
        return SCORE_NEUTRAL

    dias_con_clase = {b.dia for s in cromosoma.secciones for b in s.bloques}
    libres_efectivos = sum(1 for d in prefs.dias_libres_deseados if d not in dias_con_clase)
    return libres_efectivos / len(prefs.dias_libres_deseados)


def _score_densidad(cromosoma: Cromosoma, prefs: PreferenciasHorario) -> float:
    """
    compacto    → premia menos días con clase (clases agrupadas)
    distribuido → premia más días con clase (clases repartidas)
    indiferente → SCORE_NEUTRAL

    Normalizado por max 6 días útiles (LUN-SAB, descartamos DOMINGO).
    """
    if prefs.densidad == DENSIDAD_INDIFERENTE:
        return SCORE_NEUTRAL

    dias_con_clase = {b.dia for s in cromosoma.secciones for b in s.bloques}
    n_dias = len(dias_con_clase)
    MAX_DIAS = 6

    if prefs.densidad == DENSIDAD_COMPACTO:
        return max(0.0, 1.0 - n_dias / MAX_DIAS)
    if prefs.densidad == DENSIDAD_DISTRIBUIDO:
        return min(1.0, n_dias / MAX_DIAS)
    return SCORE_NEUTRAL


def preferencia_horarios(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    """
    Score (0-1) combinando 3 sub-criterios de horario:
    - score_turno: bloques en el turno preferido
    - score_dias_libres: días deseados sin clase
    - score_densidad: compacto vs distribuido

    Cada sub-criterio en "indiferente" cuenta como neutral (0.5).
    Los sub-pesos viven en contexto.pesos (externalizables vía config_ga.json).
    """
    if not cromosoma.secciones:
        return SCORE_NEUTRAL
    prefs = contexto.prefs_horario
    pesos = contexto.pesos
    return (
        pesos.sub_peso_turno * _score_turno(cromosoma, prefs)
        + pesos.sub_peso_dias_libres * _score_dias_libres(cromosoma, prefs)
        + pesos.sub_peso_densidad * _score_densidad(cromosoma, prefs)
    )


def preferencia_docentes(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    """
    Score promedio (0-1) de los docentes del cromosoma según contexto.scores_docentes.
    Docentes sin score asignado se cuentan como SCORE_NEUTRAL (0.5).
    """
    if not cromosoma.secciones:
        return SCORE_NEUTRAL
    scores = [
        contexto.scores_docentes.get(s.codDocente, SCORE_NEUTRAL)
        for s in cromosoma.secciones
    ]
    return sum(scores) / len(scores)


def preferencia_cupos(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    """
    Score (0-1) basado en disponibilidad de cupos.

    Es SOFT (no hard) porque el sistema de matrícula UNMSM funciona por turnos
    según el ponderado: un cupo lleno HOY puede liberarse en otro turno. El
    módulo predictivo de vacantes refinará este score cuando esté disponible.

    Promedio de Seccion.disponibilidad (% libre, 0-100) normalizado a 0-1.
    """
    if not cromosoma.secciones:
        return SCORE_NEUTRAL
    return sum(s.disponibilidad for s in cromosoma.secciones) / (100 * len(cromosoma.secciones))

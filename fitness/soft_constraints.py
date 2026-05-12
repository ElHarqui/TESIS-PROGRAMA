from models import Cromosoma
from .contexto import ContextoAlumno
from .preferencias import SCORE_NEUTRAL


def preferencia_horarios(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    """
    TODO: ronda futura. Requiere modelar preferencia del alumno por turno
    (mañana / tarde / noche), por densidad (clases compactas vs distribuidas)
    y por días libres.
    """
    return SCORE_NEUTRAL


def preferencia_docentes(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    """
    Score promedio (0-1) de los docentes del cromosoma según contexto.scores_docentes.
    Docentes sin score asignado se cuentan como SCORE_NEUTRAL (0.5).

    Como las preferencias son por docente y una sección tiene un docente, promediamos
    sección por sección — no por bloque (los bloques de una misma sección comparten docente).
    """
    if not cromosoma.secciones:
        return SCORE_NEUTRAL
    scores = [
        contexto.scores_docentes.get(s.codDocente, SCORE_NEUTRAL)
        for s in cromosoma.secciones
    ]
    return sum(scores) / len(scores)

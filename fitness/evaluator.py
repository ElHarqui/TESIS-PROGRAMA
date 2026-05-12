from models import Cromosoma
from .contexto import ContextoAlumno
from .hard_constraints import (
    verificar_choques,
    verificar_cupos,
    verificar_prerequisitos,
    verificar_asignaturas_unicas,
    verificar_limite_creditos,
)
from .soft_constraints import preferencia_horarios, preferencia_docentes


def evaluar_fitness(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    if not verificar_choques(cromosoma):
        return 0.0
    if not verificar_cupos(cromosoma):
        return 0.0
    if not verificar_asignaturas_unicas(cromosoma):
        return 0.0
    if not verificar_limite_creditos(cromosoma, contexto):
        return 0.0
    if not verificar_prerequisitos(cromosoma, contexto):
        return 0.0

    score_horarios = preferencia_horarios(cromosoma, contexto)
    score_docentes = preferencia_docentes(cromosoma, contexto)

    return 0.7 * score_horarios + 0.3 * score_docentes

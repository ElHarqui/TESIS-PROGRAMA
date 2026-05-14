from models import Cromosoma
from .contexto import ContextoAlumno
from .hard_constraints import (
    verificar_choques,
    verificar_prerequisitos,
    verificar_asignaturas_unicas,
    verificar_limite_creditos,
)
from .soft_constraints import preferencia_horarios, preferencia_docentes, preferencia_cupos


# Pesos soft: cupos pesa fuerte porque la matrícula UNMSM por turnos hace que
# las secciones con poco cupo libre tengan baja probabilidad real de tomarse.
PESO_HORARIOS = 0.4
PESO_DOCENTES = 0.3
PESO_CUPOS    = 0.3


def evaluar_fitness(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    if not verificar_choques(cromosoma):
        return 0.0
    if not verificar_asignaturas_unicas(cromosoma):
        return 0.0
    if not verificar_limite_creditos(cromosoma, contexto):
        return 0.0
    if not verificar_prerequisitos(cromosoma, contexto):
        return 0.0

    score_horarios = preferencia_horarios(cromosoma, contexto)
    score_docentes = preferencia_docentes(cromosoma, contexto)
    score_cupos    = preferencia_cupos(cromosoma, contexto)

    return (
        PESO_HORARIOS * score_horarios
        + PESO_DOCENTES * score_docentes
        + PESO_CUPOS * score_cupos
    )

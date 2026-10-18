from models.cromosoma import Cromosoma
from .contexto import ContextoAlumno
from .hard_constraints import calcular_penalizacion_hard
from .soft_constraints import preferencia_horarios, preferencia_docentes, preferencia_cupos


def evaluar_fitness(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    """
    Calcula el fitness de un cromosoma mediante penalización progresiva:

    1. Si tiene violaciones de restricciones duras (penalización > 0):
       Retorna un valor negativo: -penalización (< 0.0).
       Esto preserva el gradiente de optimización para que la selección natural
       pueda guiar la población hacia la región factible, premiando soluciones con
       menos violaciones sobre aquellas con muchas.

    2. Si es 100% factible (penalización == 0):
       Retorna un score positivo en [0.0, 1.0], combinando linealmente las
       preferencias de horario, docentes y cupos según contexto.pesos.
    """
    penalizacion = calcular_penalizacion_hard(cromosoma, contexto)
    if penalizacion > 0:
        return -penalizacion

    pesos = contexto.pesos
    score_horarios = preferencia_horarios(cromosoma, contexto)
    score_docentes = preferencia_docentes(cromosoma, contexto)
    score_cupos    = preferencia_cupos(cromosoma, contexto)

    return (
        pesos.peso_horarios * score_horarios
        + pesos.peso_docentes * score_docentes
        + pesos.peso_cupos * score_cupos
    )

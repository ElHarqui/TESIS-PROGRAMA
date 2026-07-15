from models import Cromosoma
from .contexto import ContextoAlumno
from .hard_constraints import (
    verificar_choques,
    verificar_prerequisitos,
    verificar_asignaturas_unicas,
    verificar_limite_creditos,
    verificar_dias_libres_obligatorios,
    verificar_rango_horario,
)
from .soft_constraints import preferencia_horarios, preferencia_docentes, preferencia_cupos


def evaluar_fitness(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    """
    Fitness 0-1 de un cromosoma. 0.0 si viola algún hard constraint.

    Orden de checks (cortocircuito al primer fallo):
    1. Choques horarios (barato, filtra la mayoría).
    2. Asignaturas únicas.
    3. Límite de créditos.
    4. Prerequisitos aprobados.
    5. Días obligatoriamente libres (preferencia HARD del alumno).
    6. Rango horario obligatorio (preferencia HARD del alumno).

    Los pesos de los 3 soft constraints viven en contexto.pesos
    (externalizables vía config_ga.json).
    """
    if not verificar_choques(cromosoma):
        return 0.0
    if not verificar_asignaturas_unicas(cromosoma):
        return 0.0
    if not verificar_limite_creditos(cromosoma, contexto):
        return 0.0
    if not verificar_prerequisitos(cromosoma, contexto):
        return 0.0
    if not verificar_dias_libres_obligatorios(cromosoma, contexto):
        return 0.0
    if not verificar_rango_horario(cromosoma, contexto):
        return 0.0

    pesos = contexto.pesos
    score_horarios = preferencia_horarios(cromosoma, contexto)
    score_docentes = preferencia_docentes(cromosoma, contexto)
    score_cupos    = preferencia_cupos(cromosoma, contexto)

    return (
        pesos.peso_horarios * score_horarios
        + pesos.peso_docentes * score_docentes
        + pesos.peso_cupos * score_cupos
    )

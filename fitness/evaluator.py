# Score final ponderado

from .hard_constraints import verificar_choques, verificar_cupos, verificar_prerequisitos
from .soft_constraints import preferencia_horarios, preferencia_docentes
from ..models import Cromosoma


def evaluar_fitness(cromosoma: Cromosoma) -> float:
    # Verificar restricciones hard
    if not verificar_choques(cromosoma) or not verificar_cupos(cromosoma) or not verificar_prerequisitos(cromosoma):
        return 0.0  # Penalización máxima

    # Calcular score soft
    score_horarios = preferencia_horarios(cromosoma)
    score_docentes = preferencia_docentes(cromosoma)

    # Ponderar y retornar
    return 0.7 * score_horarios + 0.3 * score_docentes
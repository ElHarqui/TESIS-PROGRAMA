from dataclasses import dataclass
from typing import TYPE_CHECKING
from .cromosoma import Cromosoma

if TYPE_CHECKING:
    from fitness.contexto import ContextoAlumno


@dataclass(frozen=True)
class HorarioResultado:
    """
    DTO que encapsula un horario óptimo junto con todas sus métricas calculadas.
    Permite desacoplar los componentes de presentación y exportación del motor de fitness.
    """
    rank: int
    cromosoma: Cromosoma
    fitness: float
    score_horarios: float
    score_docentes: float
    score_cupos: float
    creditos: float
    es_factible: bool = True

    @classmethod
    def construir(
        cls,
        rank: int,
        cromosoma: Cromosoma,
        contexto: "ContextoAlumno",
    ) -> "HorarioResultado":
        """Factory method que construye el DTO evaluando el fitness una sola vez."""
        from fitness import (
            evaluar_fitness,
            preferencia_horarios,
            preferencia_docentes,
            preferencia_cupos,
            es_factible,
        )

        fit = evaluar_fitness(cromosoma, contexto)
        p_hor = preferencia_horarios(cromosoma, contexto)
        p_doc = preferencia_docentes(cromosoma, contexto)
        p_cup = preferencia_cupos(cromosoma, contexto)
        factible = es_factible(cromosoma, contexto)

        return cls(
            rank=rank,
            cromosoma=cromosoma,
            fitness=fit,
            score_horarios=p_hor,
            score_docentes=p_doc,
            score_cupos=p_cup,
            creditos=cromosoma.creditos_totales,
            es_factible=factible,
        )

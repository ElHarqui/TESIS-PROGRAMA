from dataclasses import dataclass, field
from typing import Dict, Optional, Set


@dataclass
class ContextoAlumno:
    """
    Contexto necesario para evaluar un cromosoma contra las restricciones del alumno.

    Se construye una sola vez en main.py a partir del plan de estudios, el historial y
    las preferencias del alumno, y se reutiliza durante toda la evolución del GA — los
    evaluadores son puros respecto a este contexto, no lo mutan.
    """
    prerequisitos: Dict[str, Optional[str]] = field(default_factory=dict)
    aprobados: Set[str] = field(default_factory=set)
    max_creditos: float = 24.0
    # codDocente → score (0-1). 0.5 si no está mapeado.
    scores_docentes: Dict[str, float] = field(default_factory=dict)

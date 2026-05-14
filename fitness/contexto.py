from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


# ──────────────────────────────────────────────
# Constantes de preferencias de horario
# ──────────────────────────────────────────────
TURNO_MANANA       = "manana"
TURNO_TARDE        = "tarde"
TURNO_NOCHE        = "noche"
TURNO_INDIFERENTE  = "indiferente"

DENSIDAD_COMPACTO    = "compacto"
DENSIDAD_DISTRIBUIDO = "distribuido"
DENSIDAD_INDIFERENTE = "indiferente"

# Rangos horarios en minutos desde medianoche
RANGOS_TURNO = {
    TURNO_MANANA: (7 * 60,  13 * 60),   # 07:00 - 13:00
    TURNO_TARDE:  (13 * 60, 18 * 60),   # 13:00 - 18:00
    TURNO_NOCHE:  (18 * 60, 22 * 60),   # 18:00 - 22:00
}


@dataclass
class PreferenciasHorario:
    """
    Preferencias del alumno sobre la distribución horaria de su semana.

    - turno_preferido: en qué franja del día prefiere tener clases.
    - dias_libres_deseados: lista de días que prefiere SIN clase (ej. ["SABADO"]).
    - densidad: compacto (clases agrupadas en pocos días) o distribuido (repartidas).

    Valores "indiferente" desactivan el sub-score (cuenta como neutral 0.5).
    """
    turno_preferido: str = TURNO_INDIFERENTE
    dias_libres_deseados: List[str] = field(default_factory=list)
    densidad: str = DENSIDAD_INDIFERENTE


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
    # Preferencias sobre la distribución horaria.
    prefs_horario: PreferenciasHorario = field(default_factory=PreferenciasHorario)

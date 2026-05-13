import random
from typing import List, Optional, Tuple

from models import Cromosoma, Seccion


def _es_seccion_valida(seccion: Seccion) -> bool:
    """
    Filtra 'secciones fantasma' que devuelve el SUM:
    horario 'NR', horaInicio/horaFin en None, o sin bloques.
    Si entran al cromosoma rompen BloqueHorario.choca_con().
    """
    if not seccion.bloques:
        return False
    return all(
        b.dia and b.dia != "NR" and b.horaInicio and b.horaFin
        for b in seccion.bloques
    )


def generar_poblacion_inicial(
    asignaturas_a_matricular: List[str],
    secciones_disponibles: List[Seccion],
    tamano_poblacion: int = 100,
    seed: Optional[int] = None,
) -> Tuple[List[Cromosoma], List[str]]:
    """
    Genera N cromosomas aleatorios. Cada cromosoma tiene UNA sección elegida
    al azar por cada asignatura que tenga al menos una sección VÁLIDA disponible.

    Asignaturas sin sección válida (no se dictan este semestre, todas fantasma,
    etc.) se OMITEN del cromosoma — no es obligatorio matricularse en todas si
    no hay cursos disponibles. El caller recibe la lista de omitidas para poder
    informarle al alumno.

    Levanta ValueError SOLO si ninguna asignatura tiene sección disponible —
    en ese caso es imposible generar siquiera un cromosoma.

    Returns:
        (poblacion, asignaturas_omitidas)
    """
    if seed is not None:
        random.seed(seed)

    secciones_por_asig: dict[str, List[Seccion]] = {}
    for s in secciones_disponibles:
        if _es_seccion_valida(s):
            secciones_por_asig.setdefault(s.codAsignatura, []).append(s)

    asignaturas_validas = [a for a in asignaturas_a_matricular if secciones_por_asig.get(a)]
    asignaturas_omitidas = [a for a in asignaturas_a_matricular if not secciones_por_asig.get(a)]

    if not asignaturas_validas:
        raise ValueError(
            f"Ninguna asignatura pedida tiene sección válida disponible: "
            f"{asignaturas_a_matricular}. Imposible generar horarios."
        )

    poblacion = []
    for _ in range(tamano_poblacion):
        elegidas = [
            random.choice(secciones_por_asig[asig])
            for asig in asignaturas_validas
        ]
        poblacion.append(Cromosoma(elegidas))

    return poblacion, asignaturas_omitidas

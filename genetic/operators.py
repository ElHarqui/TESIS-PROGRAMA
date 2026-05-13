import random
from typing import Dict, List

from models import Cromosoma, Seccion


def cruce(padre1: Cromosoma, padre2: Cromosoma) -> Cromosoma:
    """
    Cruce uniforme por asignatura.

    Para cada asignatura (gen) elegimos al azar si tomar la sección del padre1
    o del padre2. Asume que ambos padres tienen las MISMAS asignaturas en el
    MISMO orden — invariante que mantiene generar_poblacion_inicial.

    Más adecuado que el cruce de un punto para este problema: cada gen es
    independiente (no hay correlación posicional entre asignaturas), así que
    el cruce uniforme mezcla mejor el espacio de búsqueda.
    """
    hijos_secciones = [
        random.choice((s1, s2))
        for s1, s2 in zip(padre1.secciones, padre2.secciones)
    ]
    return Cromosoma(hijos_secciones)


def mutacion(
    cromosoma: Cromosoma,
    secciones_por_asig: Dict[str, List[Seccion]],
    tasa: float = 0.1,
) -> Cromosoma:
    """
    Mutación por gen: con probabilidad `tasa`, reemplaza cada sección por otra
    aleatoria de la misma asignatura.

    `secciones_por_asig` mapea codAsignatura → lista de Seccion disponibles
    (ya filtradas por validez en population). El motor del GA debe pasarlo
    pre-computado para no reconstruirlo en cada mutación.
    """
    nuevas = []
    for s in cromosoma.secciones:
        if random.random() < tasa:
            opciones = secciones_por_asig.get(s.codAsignatura, [s])
            nuevas.append(random.choice(opciones))
        else:
            nuevas.append(s)
    return Cromosoma(nuevas)

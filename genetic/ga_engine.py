from typing import Callable, Dict, List, Sequence

from models import Cromosoma, Seccion
from .operators import cruce, mutacion
from .selection import seleccion_torneo


def ejecutar_ga(
    poblacion_inicial: List[Cromosoma],
    evaluador: Callable[[Cromosoma], float],
    secciones_por_asig: Dict[str, List[Seccion]],
    max_generaciones: int = 100,
    tasa_mutacion: float = 0.1,
    tamano_torneo: int = 3,
    elitismo: int = 2,
) -> List[Cromosoma]:
    """
    Loop generacional estándar con elitismo.

    1. Evaluar fitness de cada cromosoma de la generación.
    2. Preservar los `elitismo` mejores cromosomas (van directo a la siguiente generación).
    3. Llenar el resto con cruce(p1, p2) + mutación, donde p1, p2 vienen de selección por torneo.
    4. Repetir `max_generaciones` veces.

    Devuelve la población FINAL (no la mejor — para extraer top-K diverso usar top_k_diversos).
    """
    poblacion = list(poblacion_inicial)
    pob_size = len(poblacion)

    for _ in range(max_generaciones):
        fitness = [evaluador(c) for c in poblacion]
        idx_ord = sorted(range(pob_size), key=lambda i: fitness[i], reverse=True)
        nueva = [poblacion[i] for i in idx_ord[:elitismo]]
        while len(nueva) < pob_size:
            p1 = seleccion_torneo(poblacion, fitness, tamano_torneo)
            p2 = seleccion_torneo(poblacion, fitness, tamano_torneo)
            hijo = cruce(p1, p2)
            hijo = mutacion(hijo, secciones_por_asig, tasa_mutacion)
            nueva.append(hijo)
        poblacion = nueva
    return poblacion


def distancia_cromosomas(c1: Cromosoma, c2: Cromosoma) -> int:
    """
    Distancia = número de secciones DISTINTAS entre los cromosomas.
    Asume mismo orden de asignaturas (invariante de generar_poblacion_inicial).
    Rango: 0 (idénticos) a len(c1.secciones).
    """
    return sum(
        1 for s1, s2 in zip(c1.secciones, c2.secciones)
        if s1.codSeccion != s2.codSeccion or s1.codAsignatura != s2.codAsignatura
    )


def _deduplicar_estricto(
    poblacion: Sequence[Cromosoma],
    fitness: Sequence[float],
) -> tuple:
    """
    Elimina duplicados estrictos (cromosomas con distancia == 0 entre sí).

    Conserva la primera aparición de cada cromosoma único. Defensa contra el caso
    típico del GA convergente: cuando el espacio de búsqueda es pequeño o el GA
    converge fuerte, la población final tiende a tener varias copias del mismo
    óptimo. Sin dedup, esas copias se cuelan al output y los "5 horarios" salen
    visualmente idénticos.

    Devuelve (poblacion_unica, fitness_de_esos).
    """
    unicos: List[Cromosoma] = []
    fitness_unicos: List[float] = []
    for c, f in zip(poblacion, fitness):
        if any(distancia_cromosomas(c, u) == 0 for u in unicos):
            continue
        unicos.append(c)
        fitness_unicos.append(f)
    return unicos, fitness_unicos


def top_k_diversos(
    poblacion: Sequence[Cromosoma],
    fitness: Sequence[float],
    k: int = 5,
    distancia_minima: int = 1,
) -> List[Cromosoma]:
    """
    Selecciona K cromosomas con fitness alto Y suficientemente distintos entre sí.

    Algoritmo:
    1. Filtra cromosomas con fitness > 0.
    2. Dedup estricto: elimina duplicados (distancia == 0) por seguridad.
    3. Ordena por fitness descendente.
    4. Toma el mejor sí o sí.
    5. Para cada siguiente candidato, lo incluye solo si su distancia a TODOS
       los ya elegidos es >= distancia_minima.
    6. Para cuando tiene K o se agotan candidatos.

    `distancia_minima=1`: al menos UNA sección distinta. Subir el valor fuerza
    horarios más radicalmente diferentes.

    Si no hay K cromosomas suficientemente diversos, devuelve MENOS. En el caso
    extremo de un espacio de búsqueda con una sola solución óptima, devuelve 1
    (el caller debe avisar al usuario que no hay más combinaciones posibles).
    """
    # Solo cromosomas válidos
    poblacion_valida = [c for c, f in zip(poblacion, fitness) if f > 0]
    fitness_valido = [f for f in fitness if f > 0]
    if not poblacion_valida:
        return []

    # Defensa contra GA convergente: eliminar duplicados estrictos
    poblacion_valida, fitness_valido = _deduplicar_estricto(poblacion_valida, fitness_valido)

    # Ordenar y aplicar greedy con distancia mínima
    candidatos = sorted(
        zip(poblacion_valida, fitness_valido),
        key=lambda x: -x[1],
    )
    elegidos = [candidatos[0][0]]
    for cand, _ in candidatos[1:]:
        if len(elegidos) >= k:
            break
        if all(distancia_cromosomas(cand, e) >= distancia_minima for e in elegidos):
            elegidos.append(cand)
    return elegidos

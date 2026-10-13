from typing import Callable, Dict, List, Sequence, Tuple, Union

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
    retornar_historial: bool = False,
) -> Union[List[Cromosoma], Tuple[List[Cromosoma], List[dict]]]:
    """
    Loop generacional estándar con elitismo diverso.

    1. Evaluar fitness de cada cromosoma de la generación.
    2. Si `retornar_historial` está activo, registrar métricas de convergencia
       (mejor, promedio, peor, válidos) de la generación.
    3. Preservar los `elitismo` mejores cromosomas sin duplicados.
    4. Llenar el resto con cruce + mutación vía selección por torneo.
    5. Repetir `max_generaciones` veces.

    Devuelve la población final o (poblacion_final, historial) si retornar_historial=True.
    """
    poblacion = list(poblacion_inicial)
    pob_size = len(poblacion)
    historial: List[dict] = []

    for gen in range(max_generaciones):
        fitness = [evaluador(c) for c in poblacion]

        if retornar_historial:
            validos = sum(1 for f in fitness if f >= 0.0)
            fitness_validos = [f for f in fitness if f >= 0.0]
            prom_validos = (sum(fitness_validos) / len(fitness_validos)) if fitness_validos else 0.0
            historial.append({
                "generacion": gen + 1,
                "mejor": max(fitness) if fitness else 0.0,
                "promedio": (sum(fitness) / pob_size) if pob_size > 0 else 0.0,
                "promedio_validos": prom_validos,
                "peor": min(fitness) if fitness else 0.0,
                "validos": validos,
                "porcentaje_validos": (validos / pob_size * 100.0) if pob_size > 0 else 0.0,
            })

        idx_ord = sorted(range(pob_size), key=lambda i: fitness[i], reverse=True)

        # Elitismo diverso: preservar los mejores individuos evitando duplicados idénticos
        nueva = []
        for i in idx_ord:
            c = poblacion[i]
            if not any(distancia_cromosomas(c, elite) == 0 for elite in nueva):
                nueva.append(c)
                if len(nueva) >= elitismo:
                    break
        # Si no hay suficientes cromosomas únicos, completar con los mejores disponibles
        if len(nueva) < elitismo:
            for i in idx_ord:
                if len(nueva) >= elitismo:
                    break
                nueva.append(poblacion[i])

        while len(nueva) < pob_size:
            p1 = seleccion_torneo(poblacion, fitness, tamano_torneo)
            p2 = seleccion_torneo(poblacion, fitness, tamano_torneo)
            hijo = cruce(p1, p2)
            hijo = mutacion(hijo, secciones_por_asig, tasa_mutacion)
            nueva.append(hijo)
        poblacion = nueva

    if retornar_historial:
        return poblacion, historial
    return poblacion


def distancia_cromosomas(c1: Cromosoma, c2: Cromosoma) -> int:
    """
    Calcula la Distancia de Hamming (Hamming, 1950) entre dos cromosomas.

    Representa el número de posiciones (secciones de asignaturas) en las que
    ambos cromosomas difieren entre sí sobre el espacio vectorial discreto:
        d_H(C_1, C_2) = sum(I(s_1_i != s_2_i))
    Asume el mismo orden de asignaturas (invariante de población).
    Rango: 0 (cromosomas genéticamente idénticos) a len(c1.secciones).
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
    Extractor Greedy de nichos y diversidad fenotípica (Mahfoud, 1995):
    Selecciona un portafolio de K cromosomas con alto fitness y garantizando
    una separación estructural mínima entre sí basada en Distancia de Hamming.

    Algoritmo:
    1. Filtra soluciones factibles (aptitud no negativa: fitness >= 0.0).
    2. Deduplicación estricta: descarta réplicas genéticas idénticas (d_H == 0).
    3. Ordena los candidatos de forma descendente por aptitud (elitismo).
    4. Selecciona de forma incondicional a la mejor solución global.
    5. Para cada candidato subsecuente, lo incorpora si y solo si su distancia
       de Hamming respecto a TODOS los ya seleccionados cumple:
           d_H(candidato, elegido) >= distancia_minima (defecto: 1 sección)
    6. Detiene el proceso al completar K soluciones o agotar el espacio factible.

    Parámetros:
    - `distancia_minima`: Cota inferior de diferencia de secciones (d_H >= 1).
    - Si el espacio admite menos de K alternativas viables, retorna exactamente
      las encontradas informando el límite físico al usuario.
    """
    # Solo cromosomas válidos (factibles, fitness >= 0.0)
    poblacion_valida = [c for c, f in zip(poblacion, fitness) if f >= 0.0]
    fitness_valido = [f for f in fitness if f >= 0.0]
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

import random
from typing import List, Sequence

from models import Cromosoma


def seleccion_torneo(
    poblacion: Sequence[Cromosoma],
    fitness: Sequence[float],
    tamano_torneo: int = 3,
) -> Cromosoma:
    """
    Selección por torneo: elige K cromosomas al azar y devuelve el de mayor fitness.

    Más simple y robusto que ruleta — funciona bien aunque haya muchos cromosomas
    con fitness=0 (típico en este problema cuando hay choques o créditos excedidos).
    """
    indices = random.sample(range(len(poblacion)), min(tamano_torneo, len(poblacion)))
    ganador = max(indices, key=lambda i: fitness[i])
    return poblacion[ganador]


def seleccion_ruleta(
    poblacion: Sequence[Cromosoma],
    fitness: Sequence[float],
) -> Cromosoma:
    """
    Selección por ruleta: probabilidad proporcional al fitness.

    Si TODOS los fitness son 0 (caso degenerado), cae a selección uniforme aleatoria.
    """
    total = sum(fitness)
    if total <= 0:
        return random.choice(poblacion)
    return random.choices(poblacion, weights=fitness, k=1)[0]

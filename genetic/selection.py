import random
from typing import List, Sequence

from models import Cromosoma


def seleccion_torneo(
    poblacion: Sequence[Cromosoma],
    fitness: Sequence[float],
    tamano_torneo: int = 3,
) -> Cromosoma:
    """
    Selección por torneo determinista (Blickle & Thiele, 1996):
    Elige K cromosomas al azar y devuelve el de mayor fitness.

    Al fundamentarse en una relación de orden parcial / dominancia ordinal
    (max_key), es invariante ante traslaciones de escala y resulta plenamente
    compatible con el esquema de penalización progresiva negativa de Deb (2000)
    y Coello Coello (2002), donde los individuos infactibles toman valores
    en el semieje negativo (-penalizacion < 0.0).
    """
    indices = random.sample(range(len(poblacion)), min(tamano_torneo, len(poblacion)))
    ganador = max(indices, key=lambda i: fitness[i])
    return poblacion[ganador]


def seleccion_ruleta(
    poblacion: Sequence[Cromosoma],
    fitness: Sequence[float],
) -> Cromosoma:
    """
    Selección por ruleta proporcional (Goldberg, 1989).

    Nota metodológica: La ruleta clásica exige valores estrictamente no
    negativos proporcionales a la aptitud. En presencia de penalizaciones
    negativas continuas (Deb, 2000), la selección por torneo es el operador
    estándar recomendado. Esta función se preserva para fines comparativos
    y de referencia teórica.
    """
    total = sum(fitness)
    if total <= 0:
        return random.choice(poblacion)
    return random.choices(poblacion, weights=fitness, k=1)[0]

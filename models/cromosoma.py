# Cromosoma: lista de secciones = un horario completo

from typing import List
from .seccion import Seccion


class Cromosoma:
    def __init__(self, secciones: List[Seccion]):
        self.secciones = secciones

    # TODO: métodos para evaluar fitness, etc.
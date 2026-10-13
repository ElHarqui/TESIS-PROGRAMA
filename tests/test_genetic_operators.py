import random
import pytest
from models import Seccion, Cromosoma
from genetic.operators import cruce, mutacion
from genetic.ga_engine import distancia_cromosomas, _deduplicar_estricto, top_k_diversos


def _sec(cod_asig: str, cod_sec: int) -> Seccion:
    return Seccion(
        ciclo=7,
        codAsignatura=cod_asig,
        desAsignatura=f"CURSO {cod_asig}",
        creditos=4.0,
        codSeccion=cod_sec,
        codDocente="DOC1",
        nomDocente="JUAN",
        apePatDocente="PEREZ",
        apeMatDocente="GARCIA",
        topeAlumnos=40,
        matriculados=20,
        bloques=[],
    )


class TestGeneticOperators:
    def test_cruce_preserva_asignaturas_e_invariantes(self):
        p1 = Cromosoma([_sec("A", 1), _sec("B", 1), _sec("C", 1)])
        p2 = Cromosoma([_sec("A", 2), _sec("B", 2), _sec("C", 2)])

        random.seed(42)
        hijo = cruce(p1, p2)

        assert len(hijo.secciones) == 3
        # Cada gen debe corresponder a la misma asignatura
        assert [s.codAsignatura for s in hijo.secciones] == ["A", "B", "C"]
        # Cada sección debe provenir del padre1 o del padre2
        for i, s in enumerate(hijo.secciones):
            assert s.codSeccion in (p1.secciones[i].codSeccion, p2.secciones[i].codSeccion)

    def test_mutacion_tasa_cero(self):
        c = Cromosoma([_sec("A", 1), _sec("B", 1)])
        sec_map = {
            "A": [_sec("A", 1), _sec("A", 2)],
            "B": [_sec("B", 1), _sec("B", 2)],
        }
        mutado = mutacion(c, sec_map, tasa=0.0)
        assert [s.codSeccion for s in mutado.secciones] == [1, 1]

    def test_mutacion_tasa_uno(self):
        c = Cromosoma([_sec("A", 1), _sec("B", 1)])
        sec_map = {
            "A": [_sec("A", 2)],  # fuerza a cambiar a seccion 2
            "B": [_sec("B", 2)],
        }
        mutado = mutacion(c, sec_map, tasa=1.0)
        assert [s.codSeccion for s in mutado.secciones] == [2, 2]
        assert [s.codAsignatura for s in mutado.secciones] == ["A", "B"]

    def test_distancia_cromosomas(self):
        c1 = Cromosoma([_sec("A", 1), _sec("B", 1), _sec("C", 1)])
        c2 = Cromosoma([_sec("A", 1), _sec("B", 1), _sec("C", 1)])
        c3 = Cromosoma([_sec("A", 1), _sec("B", 2), _sec("C", 1)])
        c4 = Cromosoma([_sec("A", 2), _sec("B", 2), _sec("C", 2)])

        assert distancia_cromosomas(c1, c2) == 0
        assert distancia_cromosomas(c1, c3) == 1
        assert distancia_cromosomas(c1, c4) == 3

    def test_deduplicar_estricto(self):
        c1 = Cromosoma([_sec("A", 1), _sec("B", 1)])
        c2 = Cromosoma([_sec("A", 1), _sec("B", 1)])  # clon de c1
        c3 = Cromosoma([_sec("A", 2), _sec("B", 1)])

        unicos, fits = _deduplicar_estricto([c1, c2, c3], [0.8, 0.7, 0.6])
        assert len(unicos) == 2
        assert len(fits) == 2
        # Conservó el primero (0.8) y descartó el segundo clon (0.7)
        assert fits == [0.8, 0.6]

    def test_top_k_diversos(self):
        c1 = Cromosoma([_sec("A", 1), _sec("B", 1)])
        c2 = Cromosoma([_sec("A", 1), _sec("B", 1)])  # duplicado
        c3 = Cromosoma([_sec("A", 2), _sec("B", 1)])
        c4 = Cromosoma([_sec("A", 1), _sec("B", 2)])
        c_invalido = Cromosoma([_sec("A", 3), _sec("B", 3)])

        poblacion = [c1, c2, c3, c4, c_invalido]
        fitness = [0.9, 0.9, 0.85, 0.8, -5.0]

        top = top_k_diversos(poblacion, fitness, k=3, distancia_minima=1)
        assert len(top) == 3
        # No debe incluir c_invalido (fitness < 0) ni c2 (duplicado de c1)
        assert c_invalido not in top
        assert distancia_cromosomas(top[0], top[1]) >= 1
        assert distancia_cromosomas(top[0], top[2]) >= 1
        assert distancia_cromosomas(top[1], top[2]) >= 1

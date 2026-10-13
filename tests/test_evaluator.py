import pytest
from models import BloqueHorario, Seccion, Cromosoma
from fitness.contexto import ContextoAlumno, PreferenciasHorario
from fitness.hard_constraints import calcular_penalizacion_hard, es_factible
from fitness.evaluator import evaluar_fitness


def _crear_bloque(cod: str, dia: str, h_ini: str, h_fin: str) -> BloqueHorario:
    return BloqueHorario(
        codAsignatura=cod,
        codSeccion=1,
        codDocente="DOC1",
        horario=1,
        dia=dia,
        horaInicio=h_ini,
        horaFin=h_fin,
        codAula="A101",
        tipo="T",
        desTipo="TEORIA",
    )


def _crear_seccion(cod: str, bloques: list, creditos: float = 4.0) -> Seccion:
    return Seccion(
        ciclo=7,
        codAsignatura=cod,
        desAsignatura=f"CURSO {cod}",
        creditos=creditos,
        codSeccion=1,
        codDocente="DOC1",
        nomDocente="JUAN",
        apePatDocente="PEREZ",
        apeMatDocente="GARCIA",
        topeAlumnos=40,
        matriculados=20,
        bloques=bloques,
    )


class TestEvaluatorProgressivePenalty:
    def test_factible_tiene_fitness_positivo(self):
        s1 = _crear_seccion("C1", [_crear_bloque("C1", "LUNES", "08:00", "10:00")])
        s2 = _crear_seccion("C2", [_crear_bloque("C2", "MARTES", "08:00", "10:00")])
        c = Cromosoma([s1, s2])
        ctx = ContextoAlumno()

        assert es_factible(c, ctx) is True
        assert calcular_penalizacion_hard(c, ctx) == 0.0
        fit = evaluar_fitness(c, ctx)
        assert 0.0 <= fit <= 1.0

    def test_penalizacion_progresiva_diferencia_gravedad_de_choques(self):
        # c_leve: 1 solo choque entre C1 y C2
        s1 = _crear_seccion("C1", [_crear_bloque("C1", "LUNES", "08:00", "10:00")])
        s2 = _crear_seccion("C2", [_crear_bloque("C2", "LUNES", "09:00", "11:00")])
        c_leve = Cromosoma([s1, s2])

        # c_grave: C1 choca con C2 y también con C3 (múltiples choques)
        s3 = _crear_seccion("C3", [_crear_bloque("C3", "LUNES", "08:30", "10:30")])
        c_grave = Cromosoma([s1, s2, s3])

        ctx = ContextoAlumno()

        fit_leve = evaluar_fitness(c_leve, ctx)
        fit_grave = evaluar_fitness(c_grave, ctx)

        assert fit_leve < 0.0
        assert fit_grave < 0.0
        # El casi-factible DEBE tener un fitness mayor (más cercano a 0) que el grave
        assert fit_leve > fit_grave, "La penalización progresiva debe premiar la solución con menos choques"

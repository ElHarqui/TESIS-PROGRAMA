import pytest
from models import BloqueHorario, Seccion, Cromosoma
from fitness.contexto import ContextoAlumno, PreferenciasHorario
from fitness.hard_constraints import (
    verificar_choques,
    verificar_asignaturas_unicas,
    verificar_limite_creditos,
    verificar_dias_libres_obligatorios,
    verificar_rango_horario,
    verificar_prerequisitos,
)


def _crear_bloque(cod_asig: str, dia: str, h_ini: str, h_fin: str, sec: int = 1) -> BloqueHorario:
    return BloqueHorario(
        codAsignatura=cod_asig,
        codSeccion=sec,
        codDocente="DOC1",
        horario=1,
        dia=dia,
        horaInicio=h_ini,
        horaFin=h_fin,
        codAula="A101",
        tipo="T",
        desTipo="TEORIA",
    )


def _crear_seccion(cod_asig: str, sec: int, creditos: float, bloques: list) -> Seccion:
    return Seccion(
        ciclo=7,
        codAsignatura=cod_asig,
        desAsignatura=f"CURSO {cod_asig}",
        creditos=creditos,
        codSeccion=sec,
        codDocente="DOC1",
        nomDocente="JUAN",
        apePatDocente="PEREZ",
        apeMatDocente="GARCIA",
        topeAlumnos=40,
        matriculados=20,
        bloques=bloques,
    )


class TestBloqueHorarioChoques:
    def test_dias_distintos_no_chocan(self):
        b1 = _crear_bloque("A", "LUNES", "08:00", "10:00")
        b2 = _crear_bloque("B", "MARTES", "08:00", "10:00")
        assert not b1.choca_con(b2)
        assert not b2.choca_con(b1)

    def test_bloques_contiguos_no_chocan(self):
        # 08:00 - 10:00 y 10:00 - 12:00: un bloque termina exactamente cuando el otro empieza
        b1 = _crear_bloque("A", "LUNES", "08:00", "10:00")
        b2 = _crear_bloque("B", "LUNES", "10:00", "12:00")
        assert not b1.choca_con(b2)
        assert not b2.choca_con(b1)

    def test_solapamiento_parcial_chocan(self):
        # 08:00 - 10:00 y 09:00 - 11:00
        b1 = _crear_bloque("A", "LUNES", "08:00", "10:00")
        b2 = _crear_bloque("B", "LUNES", "09:00", "11:00")
        assert b1.choca_con(b2)
        assert b2.choca_con(b1)

    def test_inclusion_total_chocan(self):
        # 08:00 - 14:00 contiene a 10:00 - 12:00
        b1 = _crear_bloque("A", "LUNES", "08:00", "14:00")
        b2 = _crear_bloque("B", "LUNES", "10:00", "12:00")
        assert b1.choca_con(b2)
        assert b2.choca_con(b1)

    def test_bloques_separados_no_chocan(self):
        b1 = _crear_bloque("A", "LUNES", "08:00", "10:00")
        b2 = _crear_bloque("B", "LUNES", "14:00", "16:00")
        assert not b1.choca_con(b2)
        assert not b2.choca_con(b1)


class TestHardConstraints:
    def test_verificar_choques_cromosoma_valido(self):
        s1 = _crear_seccion("C1", 1, 4.0, [_crear_bloque("C1", "LUNES", "08:00", "10:00")])
        s2 = _crear_seccion("C2", 1, 4.0, [_crear_bloque("C2", "LUNES", "10:00", "12:00")])
        s3 = _crear_seccion("C3", 1, 3.0, [_crear_bloque("C3", "MARTES", "08:00", "10:00")])
        c = Cromosoma([s1, s2, s3])
        assert verificar_choques(c) is True

    def test_verificar_choques_cromosoma_con_conflicto(self):
        s1 = _crear_seccion("C1", 1, 4.0, [_crear_bloque("C1", "LUNES", "08:00", "11:00")])
        s2 = _crear_seccion("C2", 1, 4.0, [_crear_bloque("C2", "LUNES", "10:00", "12:00")])
        c = Cromosoma([s1, s2])
        assert verificar_choques(c) is False

    def test_verificar_asignaturas_unicas(self):
        s1 = _crear_seccion("C1", 1, 4.0, [])
        s2 = _crear_seccion("C2", 1, 4.0, [])
        assert verificar_asignaturas_unicas(Cromosoma([s1, s2])) is True

        s3 = _crear_seccion("C1", 2, 4.0, [])
        assert verificar_asignaturas_unicas(Cromosoma([s1, s3])) is False

    def test_verificar_limite_creditos(self):
        s1 = _crear_seccion("C1", 1, 10.0, [])
        s2 = _crear_seccion("C2", 1, 14.0, [])
        c = Cromosoma([s1, s2])

        ctx_ok = ContextoAlumno(max_creditos=24.0)
        assert verificar_limite_creditos(c, ctx_ok) is True

        ctx_excedido = ContextoAlumno(max_creditos=22.0)
        assert verificar_limite_creditos(c, ctx_excedido) is False

    def test_verificar_dias_libres_obligatorios(self):
        s1 = _crear_seccion("C1", 1, 4.0, [_crear_bloque("C1", "SABADO", "08:00", "12:00")])
        s2 = _crear_seccion("C2", 1, 4.0, [_crear_bloque("C2", "LUNES", "08:00", "12:00")])

        ctx = ContextoAlumno(prefs_horario=PreferenciasHorario(dias_libres_obligatorios=["SABADO"]))
        assert verificar_dias_libres_obligatorios(Cromosoma([s1]), ctx) is False
        assert verificar_dias_libres_obligatorios(Cromosoma([s2]), ctx) is True

    def test_verificar_rango_horario(self):
        s_temprana = _crear_seccion("C1", 1, 4.0, [_crear_bloque("C1", "LUNES", "07:00", "10:00")])
        s_ok = _crear_seccion("C2", 1, 4.0, [_crear_bloque("C2", "LUNES", "09:00", "13:00")])
        s_tardia = _crear_seccion("C3", 1, 4.0, [_crear_bloque("C3", "LUNES", "18:00", "22:00")])

        ctx_rango = ContextoAlumno(prefs_horario=PreferenciasHorario(hora_min="08:00", hora_max="20:00"))
        assert verificar_rango_horario(Cromosoma([s_temprana]), ctx_rango) is False
        assert verificar_rango_horario(Cromosoma([s_ok]), ctx_rango) is True
        assert verificar_rango_horario(Cromosoma([s_tardia]), ctx_rango) is False

    def test_verificar_prerequisitos(self):
        s1 = _crear_seccion("CURSO_AVANZADO", 1, 4.0, [])
        s2 = _crear_seccion("CURSO_LIBRE", 1, 4.0, [])

        ctx = ContextoAlumno(
            prerequisitos={"CURSO_AVANZADO": "CURSO_BASE", "CURSO_LIBRE": None},
            aprobados={"OTRO_CURSO"},
        )
        assert verificar_prerequisitos(Cromosoma([s2]), ctx) is True
        assert verificar_prerequisitos(Cromosoma([s1]), ctx) is False

        # Si aprueba CURSO_BASE:
        ctx.aprobados.add("CURSO_BASE")
        assert verificar_prerequisitos(Cromosoma([s1]), ctx) is True

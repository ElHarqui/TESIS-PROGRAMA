import pytest
from models import BloqueHorario, Seccion, Cromosoma
from fitness.contexto import ContextoAlumno, PreferenciasHorario
from services.optimizer_service import (
    detectar_hard_activas,
    relajar_hard_constraints,
    detectar_violaciones_bloque,
    ejecutar_optimizacion,
)
from config import ParametrosGA


def _crear_bloque(dia: str, h_ini: str, h_fin: str) -> BloqueHorario:
    return BloqueHorario(
        codAsignatura="C1",
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


def _crear_seccion(cod_asig: str, sec: int, bloques: list) -> Seccion:
    return Seccion(
        ciclo=7,
        codAsignatura=cod_asig,
        desAsignatura=f"CURSO {cod_asig}",
        creditos=4.0,
        codSeccion=sec,
        codDocente="DOC1",
        nomDocente="JUAN",
        apePatDocente="PEREZ",
        apeMatDocente="GARCIA",
        topeAlumnos=40,
        matriculados=20,
        bloques=bloques,
    )


class TestOptimizerService:
    def test_detectar_hard_activas(self):
        p1 = PreferenciasHorario()
        assert detectar_hard_activas(p1) == []

        p2 = PreferenciasHorario(dias_libres_obligatorios=["DOMINGO"], hora_min="08:00")
        assert set(detectar_hard_activas(p2)) == {"dias_libres_obligatorios", "hora_min"}

    def test_relajar_hard_constraints(self):
        p = PreferenciasHorario(
            turno_preferido="manana",
            dias_libres_obligatorios=["SABADO"],
            hora_min="08:00",
            hora_max="20:00",
        )
        relajada = relajar_hard_constraints(p)
        assert relajada.turno_preferido == "manana"  # preserva soft
        assert relajada.dias_libres_obligatorios == []
        assert relajada.hora_min is None
        assert relajada.hora_max is None

    def test_detectar_violaciones_bloque(self):
        prefs = PreferenciasHorario(dias_libres_obligatorios=["SABADO"], hora_min="08:00", hora_max="20:00")
        b_sabado = _crear_bloque("SABADO", "09:00", "12:00")
        b_temprano = _crear_bloque("LUNES", "07:00", "09:00")
        b_tarde = _crear_bloque("LUNES", "19:00", "22:00")
        b_ok = _crear_bloque("LUNES", "09:00", "12:00")

        assert "dia_libre" in detectar_violaciones_bloque(b_sabado, prefs)
        assert "hora_min" in detectar_violaciones_bloque(b_temprano, prefs)
        assert "hora_max" in detectar_violaciones_bloque(b_tarde, prefs)
        assert detectar_violaciones_bloque(b_ok, prefs) == []

    def test_ejecutar_optimizacion_flujo_normal_y_fallback(self):
        # Seccion que solo se dicta sabado 08:00 a 10:00
        sec_sabado = _crear_seccion("C1", 1, [_crear_bloque("SABADO", "08:00", "10:00")])
        secciones = [sec_sabado]

        # Caso 1: Alumno pide no tener clases el sábado
        ctx_estricto = ContextoAlumno(
            prefs_horario=PreferenciasHorario(dias_libres_obligatorios=["SABADO"])
        )
        config_ga = ParametrosGA(tamano_poblacion=10, generaciones=5, seed=42)

        res = ejecutar_optimizacion(secciones, ["C1"], ctx_estricto, config_ga)
        # Debe disparar el modo fallback porque sin relajar el sábado era imposible encontrar horario
        assert res.modo_fallback is True
        assert "dias_libres_obligatorios" in res.hard_relajadas
        assert len(res.horarios) > 0

import pytest
from models import BloqueHorario, Cromosoma, Seccion
from genetic.ga_engine import ejecutar_ga
from config import ParametrosGA
from fitness.contexto import ContextoAlumno
from fitness.preferencias import PreferenciasHorario
from services.optimizer_service import ejecutar_optimizacion, ResultadoOptimizacion


def _crear_bloque(cod_asig: str, sec: int, dia: str, h_ini: str, h_fin: str) -> BloqueHorario:
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


def _crear_seccion(cod_asig: str, sec: int, dia: str, h_ini: str, h_fin: str) -> Seccion:
    b = _crear_bloque(cod_asig, sec, dia, h_ini, h_fin)
    return Seccion(
        ciclo=7,
        codAsignatura=cod_asig,
        desAsignatura=f"Curso {cod_asig}",
        creditos=4.0,
        codSeccion=sec,
        codDocente="DOC1",
        nomDocente="JUAN",
        apePatDocente="PEREZ",
        apeMatDocente="GARCIA",
        topeAlumnos=30,
        matriculados=10,
        bloques=[b],
    )


def test_ejecutar_ga_retornar_historial():
    s1 = _crear_seccion("C1", 1, "LUNES", "08:00", "10:00")
    s2 = _crear_seccion("C1", 2, "MARTES", "08:00", "10:00")
    c1 = Cromosoma(secciones=[s1])
    c2 = Cromosoma(secciones=[s2])
    poblacion = [c1, c2, c1, c2]

    evaluador = lambda c: 0.85
    sec_map = {"C1": [s1, s2]}

    pob_final, historial = ejecutar_ga(
        poblacion_inicial=poblacion,
        evaluador=evaluador,
        secciones_por_asig=sec_map,
        max_generaciones=5,
        tasa_mutacion=0.1,
        tamano_torneo=2,
        elitismo=1,
        retornar_historial=True,
    )

    assert len(pob_final) == len(poblacion)
    assert len(historial) == 5
    for i, h in enumerate(historial, 1):
        assert h["generacion"] == i
        assert "mejor" in h
        assert "promedio" in h
        assert "peor" in h
        assert "validos" in h
        assert h["mejor"] == 0.85


def test_optimizer_service_incluye_historial_convergencia():
    s1 = _crear_seccion("C1", 1, "LUNES", "08:00", "10:00")
    s2 = _crear_seccion("C2", 1, "MARTES", "10:00", "12:00")

    contexto = ContextoAlumno(
        prefs_horario=PreferenciasHorario(),
    )
    config_ga = ParametrosGA(tamano_poblacion=6, generaciones=4, top_k=2)

    resultado = ejecutar_optimizacion(
        secciones=[s1, s2],
        codigos_asignaturas=["C1", "C2"],
        contexto=contexto,
        config_ga=config_ga,
    )

    assert isinstance(resultado, ResultadoOptimizacion)
    assert len(resultado.historial_convergencia) == 4
    assert resultado.historial_convergencia[0]["generacion"] == 1
    assert resultado.historial_convergencia[-1]["generacion"] == 4
    assert "promedio_validos" in resultado.historial_convergencia[0]
    assert "porcentaje_validos" in resultado.historial_convergencia[0]


def test_render_graficos_convergencia_dataframes():
    """Valida que la lógica de dataframes de convergencia no genera datos vacíos ni negativos."""
    import pandas as pd
    historial = [
        {"generacion": 1, "mejor": 0.42, "promedio": -4.0, "promedio_validos": 0.38, "peor": -8.0, "validos": 15, "porcentaje_validos": 15.0},
        {"generacion": 2, "mejor": 0.45, "promedio": -1.5, "promedio_validos": 0.41, "peor": -6.0, "validos": 50, "porcentaje_validos": 50.0},
        {"generacion": 3, "mejor": 0.47, "promedio": -0.2, "promedio_validos": 0.44, "peor": -4.0, "validos": 80, "porcentaje_validos": 80.0},
    ]
    df_hist = pd.DataFrame(historial)
    df_fitness = df_hist.set_index("generacion")[["mejor", "promedio_validos"]].copy()
    assert (df_fitness["mejor"] >= 0.0).all()
    assert (df_fitness["promedio_validos"] >= 0.0).all()
    assert len(df_fitness) == 3

    df_validos = df_hist.set_index("generacion")[["validos"]].copy()
    assert df_validos["validos"].iloc[0] == 15
    assert df_validos["validos"].iloc[-1] == 80

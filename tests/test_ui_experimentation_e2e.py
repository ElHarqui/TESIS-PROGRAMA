import pytest
from streamlit.testing.v1 import AppTest
from data.parser import DatosAlumno
from models import BloqueHorario, Seccion
from config import ParametrosGA
from fitness.contexto import ContextoAlumno


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


def test_app_con_sesion_activa_y_experimentacion():
    """Valida que un alumno logueado puede correr el GA y acceder a la pestaña de experimentación sin errores."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert len(at.exception) == 0

    # Inyectar sesión de alumno activa con 2 asignaturas
    s1 = _crear_seccion("C1", 1, "LUNES", "08:00", "10:00")
    s2 = _crear_seccion("C2", 1, "MARTES", "10:00", "12:00")
    alumno = DatosAlumno(
        cicloActual=7,
        promedioPonderado=15.5,
        raw={
            "codAlumno": "22200033",
            "nomAlumno": "HARQUI",
            "apePaterno": "DEF",
            "apeMaterno": "TEST",
            "desEscuela": "SISTEMAS",
            "desFacultad": "FISI",
            "desSituacion": "REGULAR",
        }
    )
    prematricula = [
        {"codAsignatura": "C1", "desAsignatura": "Curso C1", "num_creditaje": 4},
        {"codAsignatura": "C2", "desAsignatura": "Curso C2", "num_creditaje": 4},
    ]

    at.session_state["alumno"] = alumno
    at.session_state["secciones"] = [s1, s2]
    at.session_state["prematricula"] = prematricula
    at.session_state["plan"] = []
    at.session_state["historial"] = []
    at.session_state["credenciales_usuario"] = "22200033"

    # Correr la app con el estado inyectado
    at.run()
    assert len(at.exception) == 0

    # Buscar el botón de generar horarios y clickearlo
    btn_generar = next((b for b in at.button if "Generar" in b.label), None)
    assert btn_generar is not None, "Debe existir el botón de generar horarios"
    btn_generar.click().run()

    assert len(at.exception) == 0
    assert at.session_state.horarios is not None
    assert len(at.session_state.horarios) > 0
    assert len(at.session_state.historial_convergencia) > 0

    # Buscar el botón experimental de tesis y clickearlo
    btn_experimento = next((b for b in at.button if "Experimento" in b.label), None)
    assert btn_experimento is not None, "Debe existir el botón de experimentación"
    btn_experimento.click().run()

    assert len(at.exception) == 0
    assert at.session_state.historial_convergencia is not None
